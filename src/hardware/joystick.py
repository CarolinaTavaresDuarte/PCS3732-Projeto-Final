#!/usr/bin/env python3
"""
joystick.py — Joystick analógico (eixos no ADC, botão no GPIO 7).

Traduz a posição contínua do manche em uma das quatro direções do Snake,
com zona morta para filtrar ruído. A camada de jogo consome apenas
``JoyDirection`` e não sabe que existe um ADC no meio do caminho.
"""
from __future__ import annotations

import logging
from enum import Enum, auto

import config
from hardware.adc import ADCDevice
from hardware.base import HardwareComponent, requires_hardware

logger = logging.getLogger("snake_pi.hardware.joystick")


class JoyDirection(Enum):
    """Direções discretas emitidas pelo joystick."""
    CENTER = auto()
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()


class Joystick(HardwareComponent):
    """Eixos X/Y via ADC e botão SW via GPIO."""

    def __init__(self, adc: ADCDevice, simulate: bool = False) -> None:
        super().__init__(name="Joystick")
        self._adc = adc
        self._button = None
        self.simulate = simulate

        if simulate:
            self.available = True
            return

        try:
            from gpiozero import Button
            self._button = Button(config.PIN_JOYSTICK_SW,
                                  pull_up=True, bounce_time=0.05)


            self.available = True
            logger.info("Joystick pronto como botão de confirmar (SW=GPIO%d).",
                        config.PIN_JOYSTICK_SW)
        except Exception as exc:
            logger.warning(
                "Botão do joystick (GPIO%d) indisponível: %s. "
                "Se o SPI estiver ligado, ele ocupa o GPIO7 (CE1). "
                "Desligue o SPI ou aplique 'dtoverlay=spi0-1cs'.",
                config.PIN_JOYSTICK_SW, exc)
            self.available = False

    @requires_hardware(default=JoyDirection.CENTER)
    def read_direction(self) -> JoyDirection:
        """
        Direção dominante do manche, ou CENTER dentro da zona morta.

        Compara os módulos dos dois eixos e devolve só o maior: o Snake
        anda em 4 direções, então uma diagonal precisa virar uma escolha
        única — senão a cobra ficaria oscilando entre dois eixos.
        """
        if self.simulate:
            return JoyDirection.CENTER
        x = self._adc.read(config.ADC_CH_JOYSTICK_X) - config.JOY_CENTER
        y = self._adc.read(config.ADC_CH_JOYSTICK_Y) - config.JOY_CENTER
        if config.JOY_INVERT_X:
            x = -x
        if config.JOY_INVERT_Y:
            y = -y

        if abs(x) < config.JOY_DEADZONE and abs(y) < config.JOY_DEADZONE:
            return JoyDirection.CENTER
        if abs(x) >= abs(y):
            return JoyDirection.RIGHT if x > 0 else JoyDirection.LEFT
        return JoyDirection.DOWN if y > 0 else JoyDirection.UP

    @requires_hardware(default=False)
    def is_pressed(self) -> bool:
        """True enquanto o botão do joystick estiver pressionado."""
        if self.simulate or self._button is None:
            return False
        return bool(self._button.is_pressed)

    def close(self) -> None:
        if self._button is not None:
            try:
                self._button.close()
            except Exception:
                pass
            self._button = None
        self.available = False
