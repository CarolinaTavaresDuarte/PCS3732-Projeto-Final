#!/usr/bin/env python3
"""
state.py — Estado compartilhado entre todas as threads.

Este é o ponto de encontro do sistema: a thread do jogo escreve, e as
threads de LCD, display, buzzer e RFID leem. Todo acesso passa por um
``RLock``, e os leitores usam ``snapshot()``, que devolve uma cópia
imutável. Assim nenhuma thread periférica segura o lock enquanto faz I/O
lento (escrever no LCD leva ~8 ms), o que travaria o loop do jogo.

Usamos RLock e não Lock porque alguns métodos compostos chamam outros que
também travam; com Lock simples isso seria deadlock imediato.
"""
from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from enum import Enum, auto

from config import DEFAULT_DIFFICULTY, Difficulty


class GameMode(Enum):
    """Em que tela/situação o jogo está."""
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    HIGH_SCORES = auto()
    SETTINGS = auto()
    QUIT = auto()


class SoundEvent(Enum):
    """Efeitos sonoros que o jogo pode pedir ao buzzer."""
    FRUIT = auto()
    SPECIAL_FRUIT = auto()
    LEVEL_UP = auto()
    GAME_OVER = auto()
    NEW_RECORD = auto()
    MENU_MOVE = auto()
    MENU_SELECT = auto()
    PAUSE = auto()


class MatrixAnim(Enum):
    """Animações disponíveis na matriz de LEDs 8x8."""
    IDLE = auto()
    SMILE = auto()
    FRUIT = auto()
    HEART = auto()
    SKULL = auto()
    LEVEL_UP = auto()


@dataclass(frozen=True)
class StateSnapshot:
    """Cópia imutável do estado, segura para ler fora do lock."""
    mode: GameMode
    score: int
    level: int
    difficulty: Difficulty
    speed_fraction: float
    snake_length: int
    fruits_eaten: int
    best_score: int
    new_record: bool


class GameState:
    """Estado global protegido por lock, com fila de eventos para os periféricos."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.shutdown = threading.Event()


        self._mode: GameMode = GameMode.MENU
        self._score: int = 0
        self._level: int = 1
        self._difficulty: Difficulty = DEFAULT_DIFFICULTY
        self._speed_fraction: float = 0.0
        self._snake_length: int = 3
        self._fruits_eaten: int = 0
        self._best_score: int = 0
        self._new_record: bool = False
        self._pot_value: int = 128


        self.sound_queue: queue.Queue[SoundEvent] = queue.Queue(maxsize=32)
        self.matrix_queue: queue.Queue[MatrixAnim] = queue.Queue(maxsize=8)


    def snapshot(self) -> StateSnapshot:
        """Devolve uma cópia consistente de todo o estado."""
        with self._lock:
            return StateSnapshot(
                mode=self._mode,
                score=self._score,
                level=self._level,
                difficulty=self._difficulty,
                speed_fraction=self._speed_fraction,
                snake_length=self._snake_length,
                fruits_eaten=self._fruits_eaten,
                best_score=self._best_score,
                new_record=self._new_record,
            )

    @property
    def mode(self) -> GameMode:
        with self._lock:
            return self._mode

    @property
    def difficulty(self) -> Difficulty:
        with self._lock:
            return self._difficulty

    @property
    def pot_value(self) -> int:
        with self._lock:
            return self._pot_value


    def set_mode(self, mode: GameMode) -> None:
        with self._lock:
            self._mode = mode

    def set_difficulty(self, difficulty: Difficulty) -> None:
        with self._lock:
            self._difficulty = difficulty

    def set_pot_value(self, value: int) -> None:
        with self._lock:
            self._pot_value = value

    def update_game(self, *, score: int | None = None, level: int | None = None,
                    speed_fraction: float | None = None,
                    snake_length: int | None = None,
                    fruits_eaten: int | None = None,
                    best_score: int | None = None,
                    new_record: bool | None = None) -> None:
        """Atualiza vários campos de uma vez, sob um único lock."""
        with self._lock:
            if score is not None:
                self._score = score
            if level is not None:
                self._level = level
            if speed_fraction is not None:
                self._speed_fraction = max(0.0, min(1.0, speed_fraction))
            if snake_length is not None:
                self._snake_length = snake_length
            if fruits_eaten is not None:
                self._fruits_eaten = fruits_eaten
            if best_score is not None:
                self._best_score = best_score
            if new_record is not None:
                self._new_record = new_record


    def play_sound(self, event: SoundEvent) -> None:
        """
        Pede um efeito sonoro sem bloquear.

        Se a fila encher (buzzer lento, muitos eventos), o som é descartado
        de propósito: é melhor perder um bipe do que travar o loop do jogo.
        """
        try:
            self.sound_queue.put_nowait(event)
        except queue.Full:
            pass

    def show_animation(self, anim: MatrixAnim) -> None:
        """Pede uma animação na matriz de LEDs, sem bloquear."""
        try:
            self.matrix_queue.put_nowait(anim)
        except queue.Full:
            pass

    def request_shutdown(self) -> None:
        """Sinaliza a todas as threads que é hora de encerrar."""
        self.shutdown.set()
        self.set_mode(GameMode.QUIT)
