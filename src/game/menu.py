#!/usr/bin/env python3
"""
menu.py — Menus navegáveis pelo joystick.

Um menu é só uma lista de itens e um cursor. A navegação tem repetição
temporizada: segurar o joystick para cima anda um item a cada
``JOY_MENU_REPEAT_DELAY`` segundos, em vez de disparar dezenas de vezes
por segundo — sem isso seria impossível parar no item desejado.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum, auto


class MenuAction(Enum):
    """O que a seleção de um item deve provocar."""
    START_GAME = auto()
    HIGH_SCORES = auto()
    SETTINGS = auto()
    QUIT = auto()
    BACK = auto()
    CYCLE_DIFFICULTY = auto()
    NONE = auto()


@dataclass
class MenuItem:
    """Um item de menu."""
    label: str
    action: MenuAction
    hint: str = ""


class Menu:
    """Lista de itens com cursor e repetição temporizada."""

    def __init__(self, items: list[MenuItem], title: str = "") -> None:
        self.items: list[MenuItem] = items
        self.title: str = title
        self.index: int = 0
        self._last_move: float = 0.0

    @property
    def selected(self) -> MenuItem:
        """Item sob o cursor."""
        return self.items[self.index]

    def _can_move(self) -> bool:
        """True se já passou tempo suficiente desde o último movimento."""
        from config import JOY_MENU_REPEAT_DELAY
        agora = time.monotonic()
        if agora - self._last_move < JOY_MENU_REPEAT_DELAY:
            return False
        self._last_move = agora
        return True

    def move(self, delta: int, force: bool = False) -> bool:
        """
        Move o cursor. ``force=True`` ignora a temporização (uso do teclado).

        :return: True se o cursor realmente andou.
        """
        if force:


            self._last_move = time.monotonic()
        elif not self._can_move():
            return False
        self.index = (self.index + delta) % len(self.items)
        return True

    def select(self) -> MenuAction:
        """Devolve a ação do item atual."""
        return self.selected.action

    def reset(self) -> None:
        """Volta o cursor para o primeiro item."""
        self.index = 0
        self._last_move = 0.0


def build_main_menu() -> Menu:
    """Menu principal exigido no enunciado do projeto."""
    return Menu([
        MenuItem("Start Game", MenuAction.START_GAME, "Comecar uma partida"),
        MenuItem("High Score", MenuAction.HIGH_SCORES, "Ver o ranking"),
        MenuItem("Configuracoes", MenuAction.SETTINGS, "Ajustar dificuldade"),
        MenuItem("Sair", MenuAction.QUIT, "Encerrar o jogo"),
    ], title="SNAKE PI")


def build_settings_menu() -> Menu:
    """Submenu de configurações."""
    return Menu([
        MenuItem("Dificuldade", MenuAction.CYCLE_DIFFICULTY,
                 "Joystick para trocar (ou use um cartao RFID)"),
        MenuItem("Voltar", MenuAction.BACK, "Voltar ao menu principal"),
    ], title="CONFIGURACOES")
