#!/usr/bin/env python3
"""
buttons.py — Botões físicos da placa.

Os quatro botões coloridos formam um direcional (D-pad):

    AZUL     GPIO 20  -> cima
    VERMELHO GPIO 21  -> baixo
    AMARELO  GPIO 26  -> esquerda
    VERDE    GPIO 16  -> direita

Durante a partida eles movem a cobra; nos menus, cima e baixo navegam.

A leitura das direções é por polling (``pressed_directions``) e não por
callback. O motivo: para direção interessa o estado no instante do quadro,
e segurar o botão deve manter a cobra indo naquele sentido. Callback de
borda daria um passo por aperto, o que seria péssimo de jogar.

Os botões de ação usam callback, porque aí importa o evento, não a duração.
"""
from __future__ import annotations

import logging
from typing import Callable

import config
from hardware.base import HardwareComponent

logger = logging.getLogger("snake_pi.hardware.buttons")


_DIRECTION_PINS = {
    "up": "PIN_BTN_UP",
    "down": "PIN_BTN_DOWN",
    "left": "PIN_BTN_LEFT",
    "right": "PIN_BTN_RIGHT",
}


class ButtonPanel(HardwareComponent):
    """Painel de botões: direcional por polling, ações por callback."""

    def __init__(self, simulate: bool = False) -> None:
        super().__init__(name="Botões")
        self._buttons: dict[str, object] = {}
        self.simulate = simulate

        if simulate:
            self.available = True
            return

        try:
            from gpiozero import Button
        except Exception as exc:
            logger.warning("gpiozero indisponível: %s", exc)
            self.available = False
            return


        for nome, attr in _DIRECTION_PINS.items():
            pino = getattr(config, attr, None)
            if pino is not None:
                self._abrir(Button, nome, pino, bounce=0.02)


        if getattr(config, "PIN_BTN_RESTART", None) is not None:
            self._abrir(Button, "restart", config.PIN_BTN_RESTART, bounce=0.08)

        self.available = bool(self._buttons)
        if self.available:
            logger.info("Botões ativos: %s", ", ".join(sorted(self._buttons)))
        else:
            logger.warning("Nenhum botão pôde ser aberto.")

    def _abrir(self, Button, nome: str, pino: int, bounce: float) -> None:
        """Tenta abrir um botão; falha individual não derruba os outros."""
        try:
            self._buttons[nome] = Button(pino, pull_up=True, bounce_time=bounce)
            logger.info("Botão '%s' em GPIO%d.", nome, pino)
        except Exception as exc:
            logger.warning("Botão '%s' (GPIO%d) indisponível: %s",
                           nome, pino, exc)


    def is_pressed(self, nome: str) -> bool:
        """Estado instantâneo de um botão."""
        botao = self._buttons.get(nome)
        if botao is None:
            return False
        try:
            return bool(botao.is_pressed)
        except Exception:
            return False

    def pressed_directions(self) -> list[str]:
        """
        Direções pressionadas neste instante.

        Devolve lista porque o jogador pode apertar dois botões ao mesmo
        tempo; quem decide o que fazer com isso é a camada de jogo.
        """
        return [nome for nome in _DIRECTION_PINS if self.is_pressed(nome)]

    def on_press(self, nome: str, callback: Callable[[], None]) -> None:
        """
        Registra callback de borda para um botão de ação.

        O callback roda numa thread interna do gpiozero, então deve ser
        rápido e apenas levantar uma flag.
        """
        botao = self._buttons.get(nome)
        if botao is not None:
            botao.when_pressed = callback

    def close(self) -> None:
        for botao in self._buttons.values():
            try:
                botao.close()
            except Exception:
                pass
        self._buttons.clear()
        self.available = False
