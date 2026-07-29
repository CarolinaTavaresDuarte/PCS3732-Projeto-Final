#!/usr/bin/env python3
"""
engine.py — O motor da partida: junta cobra, tabuleiro, frutas e pontuação.

Toda a regra do Snake mora aqui, e nada neste arquivo sabe o que é um
GPIO ou uma janela do Pygame. O motor recebe comandos (``turn``) e o
tempo decorrido (``update``), e devolve o que aconteceu — quem desenha na
tela ou acende LEDs é outra camada.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass

import config
from game.board import Board
from game.fruit import Fruit, FruitKind, spawn_fruit
from game.score import ScoreBoard
from game.snake import Direction, Snake

Position = tuple[int, int]


@dataclass
class StepResult:
    """O que mudou no último passo da simulação."""
    moved: bool = False
    ate_fruit: bool = False
    ate_special: bool = False
    leveled_up: bool = False
    game_over: bool = False
    special_expired: bool = False


class GameEngine:
    """Uma partida de Snake, do início ao Game Over."""

    def __init__(self, scoreboard: ScoreBoard,
                 rng: random.Random | None = None) -> None:
        self.scoreboard: ScoreBoard = scoreboard
        self._rng: random.Random = rng or random.Random()

        self.difficulty: config.Difficulty = config.DEFAULT_DIFFICULTY
        self.spec: config.DifficultySpec = config.DIFFICULTY_TABLE[self.difficulty]

        self.board: Board = Board(config.GRID_COLS, config.GRID_ROWS)
        self.snake: Snake = Snake((config.GRID_COLS // 2, config.GRID_ROWS // 2))
        self.fruit: Fruit | None = None
        self.special: Fruit | None = None

        self.level: int = 1
        self.fruits_eaten: int = 0
        self.game_over: bool = False
        self.speed_multiplier: float = 1.0

        self._accumulator: float = 0.0
        self._last_update: float = time.monotonic()


    def reset(self, difficulty: config.Difficulty | None = None) -> None:
        """Começa uma partida nova, opcionalmente trocando a dificuldade."""
        if difficulty is not None:
            self.difficulty = difficulty
        self.spec = config.DIFFICULTY_TABLE[self.difficulty]

        self.board = Board(config.GRID_COLS, config.GRID_ROWS,
                           wall_kills=self.spec.wall_kills)
        centro = (config.GRID_COLS // 2, config.GRID_ROWS // 2)
        self.snake = Snake(centro, Direction.RIGHT, initial_length=3)


        corredor = {(c, centro[1]) for c in range(centro[0] - 4, centro[0] + 7)}
        self.board.generate_obstacles(self.spec.obstacles,
                                      keep_clear=corredor | set(self.snake.body),
                                      rng=self._rng)

        self.level = 1
        self.fruits_eaten = 0
        self.game_over = False
        self.fruit = None
        self.special = None
        self.scoreboard.reset()
        self._accumulator = 0.0
        self._last_update = time.monotonic()
        self._spawn_normal_fruit()


    def turn(self, direction: Direction) -> None:
        """Agenda uma mudança de direção da cobra."""
        if not self.game_over:
            self.snake.turn(direction)

    def set_speed_multiplier(self, value: float) -> None:
        """
        Ajusta a velocidade a partir do potenciômetro.

        :param value: 0.0 (mais lento) a 1.0 (mais rápido).
        """
        faixa = config.POT_SPEED_RANGE

        self.speed_multiplier = (1.0 + faixa) - (2.0 * faixa * max(0.0, min(1.0, value)))


    @property
    def move_interval(self) -> float:
        """Segundos entre dois passos da cobra, no estado atual."""
        base = self.spec.base_move_interval
        base -= self.spec.speedup_per_level * (self.level - 1)
        base *= self.speed_multiplier
        return max(self.spec.min_move_interval, base)

    @property
    def speed_fraction(self) -> float:
        """
        Velocidade normalizada de 0.0 a 1.0, para o bar graph e o HUD.

        Mapeia o intervalo atual entre o mais lento possível (dificuldade
        base, nível 1, potenciômetro no mínimo) e o teto de velocidade.
        """
        mais_lento = self.spec.base_move_interval * (1.0 + config.POT_SPEED_RANGE)
        mais_rapido = self.spec.min_move_interval
        if mais_lento <= mais_rapido:
            return 1.0
        frac = (mais_lento - self.move_interval) / (mais_lento - mais_rapido)
        return max(0.0, min(1.0, frac))

    def update(self, now: float | None = None) -> StepResult:
        """
        Avança a simulação com passo de tempo fixo.

        O acumulador desacopla a velocidade da cobra da taxa de quadros:
        o Pygame roda a 60 fps, mas a cobra anda a cada ``move_interval``
        segundos. Sem isso, um engasgo de renderização mudaria a
        dificuldade do jogo — e a partida ficaria injusta.
        """
        resultado = StepResult()
        if self.game_over:
            return resultado

        agora = now if now is not None else time.monotonic()
        delta = agora - self._last_update
        self._last_update = agora


        self._accumulator += max(0.0, min(delta, 0.25))


        if self.special is not None and self.special.expired:
            self.special = None
            resultado.special_expired = True

        while self._accumulator >= self.move_interval:
            self._accumulator -= self.move_interval
            passo = self._step()
            resultado.moved = True
            resultado.ate_fruit |= passo.ate_fruit
            resultado.ate_special |= passo.ate_special
            resultado.leveled_up |= passo.leveled_up
            if passo.game_over:
                resultado.game_over = True
                break
        return resultado

    def _step(self) -> StepResult:
        """Executa exatamente um passo da cobra."""
        resultado = StepResult(moved=True)
        proxima = self.snake.next_head(self.board.wrap)


        if self.board.is_lethal(proxima):
            return self._die(resultado)


        corpo = self.snake.body
        vai_crescer = (self.fruit is not None and proxima == self.fruit.position) or\
                      (self.special is not None and proxima == self.special.position)
        colidivel = corpo if vai_crescer else corpo[:-1]
        if proxima in colidivel:
            return self._die(resultado)

        self.snake.move(self.board.wrap)
        cabeca = self.snake.head


        if self.fruit is not None and cabeca == self.fruit.position:
            self.snake.grow()
            self.scoreboard.add(config.POINTS_PER_FRUIT)
            self.fruits_eaten += 1
            resultado.ate_fruit = True
            self.fruit = None

            if self.fruits_eaten % config.FRUITS_PER_LEVEL == 0:
                self.level += 1
                resultado.leveled_up = True
            if (config.SPECIAL_FRUIT_EVERY > 0
                    and self.fruits_eaten % config.SPECIAL_FRUIT_EVERY == 0
                    and self.special is None):
                self._spawn_special_fruit()
            self._spawn_normal_fruit()


        elif self.special is not None and cabeca == self.special.position:
            self.snake.grow(2)
            self.scoreboard.add(config.POINTS_PER_SPECIAL)
            resultado.ate_special = True
            self.special = None


        if self.fruit is None:
            self._spawn_normal_fruit()
            if self.fruit is None:
                return self._die(resultado)

        return resultado

    def _die(self, resultado: StepResult) -> StepResult:
        """Encerra a partida e registra a pontuação."""
        self.game_over = True
        resultado.game_over = True
        return resultado


    def _blocked_cells(self) -> set[Position]:
        """Todas as células que não podem receber uma fruta."""
        bloqueadas = set(self.snake.body) | self.board.obstacles
        if self.fruit is not None:
            bloqueadas.add(self.fruit.position)
        if self.special is not None:
            bloqueadas.add(self.special.position)
        return bloqueadas

    def _spawn_normal_fruit(self) -> None:
        self.fruit = spawn_fruit(self.board.cols, self.board.rows,
                                 self._blocked_cells(), FruitKind.NORMAL,
                                 ttl=None, rng=self._rng)

    def _spawn_special_fruit(self) -> None:
        self.special = spawn_fruit(self.board.cols, self.board.rows,
                                   self._blocked_cells(), FruitKind.SPECIAL,
                                   ttl=config.SPECIAL_FRUIT_TTL, rng=self._rng)


    def finish(self) -> bool:
        """
        Consolida a partida no ranking.

        :return: True se foi um novo recorde absoluto.
        """
        return self.scoreboard.submit(self.level, self.difficulty.value)
