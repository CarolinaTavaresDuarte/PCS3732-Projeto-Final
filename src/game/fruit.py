#!/usr/bin/env python3
"""
fruit.py — Frutas normais e especiais.

A fruta especial existe para dar ritmo ao jogo: vale 5x mais pontos, mas
some sozinha depois de alguns segundos, forçando o jogador a decidir se
vale o risco de ir buscá-la.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from enum import Enum

Position = tuple[int, int]


class FruitKind(Enum):
    """Tipo da fruta, que define pontuação e aparência."""
    NORMAL = "normal"
    SPECIAL = "special"


@dataclass
class Fruit:
    """Uma fruta no tabuleiro."""
    position: Position
    kind: FruitKind = FruitKind.NORMAL
    spawned_at: float = field(default_factory=time.monotonic)
    ttl: float | None = None

    @property
    def expired(self) -> bool:
        """True se a fruta já passou do tempo de vida."""
        if self.ttl is None:
            return False
        return (time.monotonic() - self.spawned_at) >= self.ttl

    @property
    def remaining(self) -> float:
        """Segundos restantes antes de expirar (0 se não expira)."""
        if self.ttl is None:
            return 0.0
        return max(0.0, self.ttl - (time.monotonic() - self.spawned_at))


def spawn_fruit(cols: int, rows: int, blocked: set[Position],
                kind: FruitKind = FruitKind.NORMAL,
                ttl: float | None = None,
                rng: random.Random | None = None) -> Fruit | None:
    """
    Sorteia uma posição livre e devolve uma fruta nova.

    Percorrer todas as células livres e sortear uma (em vez de tentar
    posições aleatórias até acertar) garante tempo previsível mesmo quando
    o tabuleiro está quase cheio — no fim de uma partida longa, tentativa e
    erro poderia demorar muito ou entrar em laço infinito.

    :return: a fruta, ou None se não houver nenhuma célula livre.
    """
    rng = rng or random
    livres = [(c, r) for r in range(rows) for c in range(cols)
              if (c, r) not in blocked]
    if not livres:
        return None
    return Fruit(position=rng.choice(livres), kind=kind, ttl=ttl)
