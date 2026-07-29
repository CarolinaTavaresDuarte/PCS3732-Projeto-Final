#!/usr/bin/env python3
"""
blue_led.py — LED azul da placa (GPIO 17), usado como indicador do buzzer.

ATENÇÃO — conflito de hardware: na Freenove Projects Board o GPIO 17 é ao
mesmo tempo o LED azul E o clock (SH_CP) dos 74HC595. Os dois não podem
coexistir: enquanto os displays de shift register funcionam, o GPIO 17 é
chaveado como clock e o LED apenas reflete essa atividade, sem controle.

Por isso este driver só deve ser instanciado quando ``BLUE_LED_MODE`` está
em ``"indicator"``. Nesse modo, os displays de shift register ficam
desligados (a DisplayThread não sobe) e o GPIO 17 vira um LED de verdade,
que pisca junto com o buzzer.
"""
from __future__ import annotations

import logging

import config
from hardware.base import HardwareComponent, requires_hardware

logger = logging.getLogger("snake_pi.hardware.blue_led")


class BlueLED(HardwareComponent):
    """LED azul no GPIO 17 (só em modo indicador)."""

    def __init__(self, simulate: bool = False) -> None:
        super().__init__(name="LED azul")
        self._led = None
        self.simulate = simulate

        if simulate:
            self.available = True
            return

        try:
            from gpiozero import LED
            self._led = LED(config.PIN_BLUE_LED)
            self.available = True
            logger.info("LED azul pronto (GPIO%d, modo indicador).",
                        config.PIN_BLUE_LED)
        except Exception as exc:
            logger.warning("LED azul indisponível: %s", exc)
            self.available = False

    @requires_hardware()
    def on(self) -> None:
        """Acende o LED."""
        if not self.simulate and self._led is not None:
            self._led.on()

    @requires_hardware()
    def off(self) -> None:
        """Apaga o LED."""
        if not self.simulate and self._led is not None:
            self._led.off()

    def close(self) -> None:
        if self._led is not None:
            try:
                self._led.off()
                self._led.close()
            except Exception:
                pass
            self._led = None
        self.available = False
