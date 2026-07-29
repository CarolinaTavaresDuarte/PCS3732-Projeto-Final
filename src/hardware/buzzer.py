#!/usr/bin/env python3
"""
buzzer.py — Buzzer ativo (GPIO 12) e passivo (GPIO 4).

  - ATIVO (GPIO 12): tom fixo, usado para o apito curto ao coletar comida.
  - PASSIVO (GPIO 4): via TonalBuzzer, toca notas — usado para as melodias
    de vitória (novo recorde) e derrota (game over).

Confirmado no código oficial da Freenove (6_2_Alertor: TonalBuzzer(4)) e na
serigrafia da placa ("Passive Buzzer (GPIO4)").
"""
from __future__ import annotations

import logging
import time

import config
from hardware.base import HardwareComponent, requires_hardware

logger = logging.getLogger("snake_pi.hardware.buzzer")


MELODIES: dict[str, tuple[tuple[str | None, float], ...]] = {
    "level_up": (("C5", 0.09), ("E5", 0.09), ("G5", 0.14)),


    "game_over": (
        ("E5", 0.22), ("D5", 0.22), ("C5", 0.24), ("B4", 0.24),
        (None, 0.06),
        ("A4", 0.28), ("G4", 0.30), ("F4", 0.34),
        (None, 0.05),
        ("E4", 0.70),
    ),


    "new_record": (
        ("C5", 0.14), ("E5", 0.14), ("G5", 0.18),
        ("E5", 0.12), ("G5", 0.18), ("A5", 0.30),
        (None, 0.05),
        ("G5", 0.14), ("A5", 0.16), ("C6", 0.55),
    ),

    "special": (("E5", 0.07), ("A5", 0.07), ("C6", 0.16)),
    "menu_select": (("C5", 0.05), ("G5", 0.09)),
    "pause": (("E5", 0.07), ("C5", 0.07)),
}


class BuzzerSet(HardwareComponent):
    """Buzzer ativo (apito) + passivo (melodias)."""

    def __init__(self, simulate: bool = False) -> None:
        super().__init__(name="Buzzers")
        self._active = None
        self._passive = None
        self.simulate = simulate

        if simulate:
            self.available = True
            return

        try:
            from gpiozero import Buzzer, TonalBuzzer
            try:
                self._active = Buzzer(config.PIN_BUZZER_ACTIVE)
            except Exception as exc:
                logger.warning("Buzzer ativo (GPIO%d) indisponível: %s",
                               config.PIN_BUZZER_ACTIVE, exc)
            try:

                self._passive = TonalBuzzer(config.PIN_BUZZER_PASSIVE, octaves=2)
            except Exception as exc:
                logger.warning("Buzzer passivo (GPIO%d) indisponível: %s",
                               config.PIN_BUZZER_PASSIVE, exc)
            self.available = self._active is not None or self._passive is not None
            if self.available:
                logger.info("Buzzers prontos (ativo=%s, passivo=%s).",
                            "ok" if self._active else "--",
                            "ok" if self._passive else "--")
        except Exception as exc:
            logger.warning("Buzzers indisponíveis: %s", exc)
            self.available = False

    @requires_hardware()
    def beep(self, duration: float = 0.05) -> None:
        """Apito curto no buzzer ativo (bloqueia por ``duration``)."""
        if self.simulate or self._active is None:
            return
        self._active.on()
        time.sleep(duration)
        self._active.off()

    @requires_hardware()
    def play(self, melody: str) -> None:
        """Toca uma melodia no buzzer passivo (bloqueia até terminar)."""
        notas = MELODIES.get(melody)
        if notas is None or self.simulate or self._passive is None:
            return
        try:
            for nota, dur in notas:
                try:
                    if nota is None:
                        self._passive.stop()
                    else:
                        self._passive.play(nota)
                except Exception:
                    self._passive.stop()
                time.sleep(dur)
        finally:
            self._passive.stop()

    def silence(self) -> None:
        """Cala os dois buzzers."""
        try:
            if self._active is not None:
                self._active.off()
            if self._passive is not None:
                self._passive.stop()
        except Exception:
            pass

    def close(self) -> None:
        self.silence()
        for dev in (self._active, self._passive):
            if dev is not None:
                try:
                    dev.close()
                except Exception:
                    pass
        self._active = self._passive = None
        self.available = False
