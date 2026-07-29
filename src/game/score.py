#!/usr/bin/env python3
"""
score.py — Pontuação e ranking persistido em JSON.

O ranking sobrevive entre execuções gravando em ``highscore.json``. Toda
escrita é atômica (grava em arquivo temporário e renomeia) porque o jogo
pode ser encerrado a qualquer momento — inclusive puxando o cabo da
Raspberry Pi — e um JSON truncado quebraria a próxima partida.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger("snake_pi.score")


@dataclass(frozen=True)
class ScoreEntry:
    """Uma linha do ranking."""
    score: int
    level: int
    difficulty: str
    timestamp: float

    @property
    def date_str(self) -> str:
        """Data formatada para exibição."""
        return time.strftime("%d/%m/%Y %H:%M", time.localtime(self.timestamp))


class ScoreBoard:
    """Placar da partida atual + ranking histórico."""

    def __init__(self, path: Path, max_entries: int = 10) -> None:
        self.path: Path = path
        self.max_entries: int = max_entries
        self.entries: list[ScoreEntry] = []
        self.current: int = 0
        self.load()


    def reset(self) -> None:
        """Zera a pontuação da partida (não mexe no ranking)."""
        self.current = 0

    def add(self, points: int) -> None:
        """Soma pontos à partida atual."""
        self.current += points

    @property
    def best(self) -> int:
        """Maior pontuação já registrada (0 se o ranking está vazio)."""
        return self.entries[0].score if self.entries else 0

    def is_new_record(self) -> bool:
        """True se a pontuação atual supera o recorde histórico."""
        return self.current > self.best


    def load(self) -> None:
        """Carrega o ranking do disco, tolerando arquivo ausente ou corrompido."""
        if not self.path.exists():
            self.entries = []
            return
        try:
            dados = json.loads(self.path.read_text(encoding="utf-8"))
            self.entries = [ScoreEntry(**item) for item in dados]
            self.entries.sort(key=lambda e: e.score, reverse=True)
        except (json.JSONDecodeError, TypeError, ValueError, OSError) as exc:
            logger.warning("Ranking ilegível (%s); começando um novo.", exc)
            self.entries = []

    def save(self) -> None:
        """Grava o ranking de forma atômica."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = json.dumps([asdict(e) for e in self.entries],
                                 indent=2, ensure_ascii=False)


            fd, tmp = tempfile.mkstemp(dir=str(self.path.parent),
                                       prefix=".highscore-", suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    fh.write(payload)
                os.replace(tmp, self.path)
            except Exception:
                if os.path.exists(tmp):
                    os.unlink(tmp)
                raise
        except OSError as exc:
            logger.warning("Não consegui gravar o ranking: %s", exc)

    def submit(self, level: int, difficulty: str) -> bool:
        """
        Registra a pontuação atual no ranking.

        :return: True se entrou como novo recorde absoluto.
        """
        recorde = self.is_new_record()
        if self.current > 0:
            self.entries.append(ScoreEntry(
                score=self.current,
                level=level,
                difficulty=difficulty,
                timestamp=time.time(),
            ))
            self.entries.sort(key=lambda e: e.score, reverse=True)
            del self.entries[self.max_entries:]
            self.save()
        return recorde
