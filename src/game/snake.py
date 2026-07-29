#!/usr/bin/env python3
"""
snake.py — A cobra: corpo, direção e movimento.

Esta classe é pura lógica: não conhece Pygame, GPIO nem nada de hardware.
Isso permite testá-la isoladamente (ver ``tests/test_game_logic.py``) e
rodar o jogo inteiro em um PC comum durante o desenvolvimento.
"""
from __future__ import annotations

from collections import deque
from enum import Enum


class Direction(Enum):
    """Direções possíveis, como deltas (coluna, linha)."""
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def opposite(self) -> "Direction":
        """Direção contrária — usada para impedir a cobra de virar 180°."""
        dx, dy = self.value
        return Direction((-dx, -dy))


Position = tuple[int, int]


class Snake:
    """
    Corpo da cobra como uma fila de posições (cabeça no índice 0).

    Usamos ``deque`` porque as operações de movimento são justamente
    inserir na frente e remover atrás — ambas O(1). Uma lista comum daria
    O(n) na remoção, o que pesaria conforme a cobra cresce.
    """

    def __init__(self, start: Position, direction: Direction = Direction.RIGHT,
                 initial_length: int = 3) -> None:
        self._body: deque[Position] = deque()
        self._direction: Direction = direction
        self._pending_direction: Direction = direction
        self._grow_by: int = 0


        dx, dy = direction.value
        col, row = start
        for i in range(initial_length):
            self._body.append((col - dx * i, row - dy * i))


    @property
    def head(self) -> Position:
        """Posição atual da cabeça."""
        return self._body[0]

    @property
    def body(self) -> tuple[Position, ...]:
        """Corpo inteiro, da cabeça para a cauda (cópia imutável)."""
        return tuple(self._body)

    @property
    def direction(self) -> Direction:
        """Direção efetivamente aplicada no último passo."""
        return self._direction

    def __len__(self) -> int:
        return len(self._body)

    def occupies(self, pos: Position) -> bool:
        """True se a posição faz parte do corpo."""
        return pos in self._body


    def turn(self, direction: Direction) -> None:
        """
        Agenda uma mudança de direção para o próximo passo.

        A virada fica pendente em vez de imediata: se o jogador mandar duas
        direções entre dois passos, só a última vale, e a cobra nunca vira
        180° em cima de si mesma (o que seria morte instantânea).
        """
        if len(self._body) > 1 and direction == self._direction.opposite:
            return
        self._pending_direction = direction

    def grow(self, amount: int = 1) -> None:
        """Faz a cobra crescer nos próximos ``amount`` passos."""
        self._grow_by += amount

    def next_head(self, wrap: tuple[int, int] | None = None) -> Position:
        """
        Calcula onde a cabeça estará no próximo passo, sem mover.

        :param wrap: (colunas, linhas) para atravessar as bordas; None
                     mantém as coordenadas livres (a colisão é decidida fora).
        """
        dx, dy = self._pending_direction.value
        col, row = self._body[0]
        col, row = col + dx, row + dy
        if wrap is not None:
            cols, rows = wrap
            col %= cols
            row %= rows
        return col, row

    def move(self, wrap: tuple[int, int] | None = None) -> Position:
        """
        Avança um passo e devolve a nova posição da cabeça.

        Se houver crescimento pendente a cauda é mantida; caso contrário
        ela é removida, o que dá a ilusão de deslizamento.
        """
        self._direction = self._pending_direction
        new_head = self.next_head(wrap)
        self._body.appendleft(new_head)
        if self._grow_by > 0:
            self._grow_by -= 1
        else:
            self._body.pop()
        return new_head

    def collides_with_self(self) -> bool:
        """True se a cabeça encostou em qualquer outra parte do corpo."""
        return self._body[0] in list(self._body)[1:]
