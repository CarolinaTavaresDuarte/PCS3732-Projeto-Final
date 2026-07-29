#!/usr/bin/env python3
"""
board.py — O tabuleiro: dimensões, obstáculos e regras de colisão.

Concentra aqui tudo que responde "essa posição é válida?", para que a
lógica da partida não precise saber como os obstáculos foram gerados.
"""
from __future__ import annotations

import random

Position = tuple[int, int]


class Board:
    """Grade retangular com obstáculos fixos opcionais."""

    def __init__(self, cols: int, rows: int, wall_kills: bool = True) -> None:
        self.cols: int = cols
        self.rows: int = rows
        self.wall_kills: bool = wall_kills
        self.obstacles: set[Position] = set()


    def generate_obstacles(self, count: int, keep_clear: set[Position],
                           rng: random.Random | None = None) -> None:
        """
        Espalha ``count`` obstáculos evitando a região inicial da cobra.

        Deixamos uma faixa central livre (``keep_clear`` mais as bordas)
        para o jogador não nascer encurralado — nada mais frustrante do que
        morrer no primeiro segundo por causa do sorteio.
        """
        rng = rng or random
        self.obstacles.clear()
        if count <= 0:
            return

        proibido = set(keep_clear)

        candidatos = [(c, r)
                      for r in range(1, self.rows - 1)
                      for c in range(1, self.cols - 1)
                      if (c, r) not in proibido]
        rng.shuffle(candidatos)
        self.obstacles = set(candidatos[:count])


    @property
    def wrap(self) -> tuple[int, int] | None:
        """Dimensões para atravessar bordas, ou None se a parede mata."""
        return None if self.wall_kills else (self.cols, self.rows)

    def out_of_bounds(self, pos: Position) -> bool:
        """True se a posição está fora da grade."""
        col, row = pos
        return not (0 <= col < self.cols and 0 <= row < self.rows)

    def is_obstacle(self, pos: Position) -> bool:
        """True se há um obstáculo fixo na posição."""
        return pos in self.obstacles

    def is_lethal(self, pos: Position) -> bool:
        """True se ocupar essa posição mata a cobra."""
        if self.wall_kills and self.out_of_bounds(pos):
            return True
        return self.is_obstacle(pos)

    @property
    def area(self) -> int:
        """Número total de células."""
        return self.cols * self.rows
