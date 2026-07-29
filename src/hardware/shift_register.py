#!/usr/bin/env python3
"""
shift_register.py — Barramento 74HC595 compartilhado (GPIO 22/27/17).

Na Freenove Projects Board a matriz 8x8, o bar graph e o display de 4
dígitos são todos alimentados pelos MESMOS três pinos:

    DS (dados) = GPIO22    ST_CP (latch) = GPIO27    SH_CP (clock) = GPIO17

Como só existe um barramento físico e três threads poderiam querer usá-lo,
todo acesso passa por este objeto, que serializa as escritas com um Lock.
Escrever concorrentemente sem trava produziria quadros embaralhados —
metade dos bits de um dispositivo misturados com os do outro.
"""
from __future__ import annotations

import logging
import threading
from typing import Sequence

import config
from hardware.base import HardwareComponent, requires_hardware

logger = logging.getLogger("snake_pi.hardware.595")

MSBFIRST = True
LSBFIRST = False


class ShiftRegisterBus(HardwareComponent):
    """Acesso serializado (thread-safe) ao encadeamento de 74HC595."""

    def __init__(self,
                 data_pin: int = config.PIN_595_DATA,
                 latch_pin: int = config.PIN_595_LATCH,
                 clock_pin: int = config.PIN_595_CLOCK,
                 simulate: bool = False) -> None:
        super().__init__(name="74HC595")
        self.lock = threading.Lock()
        self._data = self._latch = self._clock = None
        self.simulate: bool = simulate
        self.last_frame: tuple[int, ...] = ()

        if simulate:
            self.available = True
            logger.info("74HC595 em modo simulação (sem GPIO).")
            return

        try:
            from gpiozero import OutputDevice
            self._data = OutputDevice(data_pin)
            self._latch = OutputDevice(latch_pin)
            self._clock = OutputDevice(clock_pin)
            self.available = True
            logger.info("74HC595 pronto (DS=%d, ST_CP=%d, SH_CP=%d).",
                        data_pin, latch_pin, clock_pin)
        except Exception as exc:
            logger.warning("74HC595 indisponível: %s", exc)
            self.available = False


    def _shift_byte(self, valor: int, msb_first: bool = MSBFIRST) -> None:
        """
        Desloca um byte para dentro do registrador (sem dar latch).

        Replica exatamente a função ``shiftOut`` do código oficial da
        Freenove, inclusive a ordem dos bits — trocar MSB por LSB aqui faz
        os desenhos saírem espelhados.
        """
        assert self._data is not None and self._clock is not None
        for i in range(8):
            self._clock.off()
            if msb_first:
                bit = (0x80 & (valor << i)) == 0x80
            else:
                bit = (0x01 & (valor >> i)) == 0x01
            if bit:
                self._data.on()
            else:
                self._data.off()
            self._clock.on()

    @requires_hardware()
    def write_frame(self, dados: Sequence[int], msb_first: bool = MSBFIRST) -> None:
        """
        Envia um quadro completo e dá um único latch no fim.

        Os bytes são deslocados na ordem recebida; como o 74HC595 empurra
        o conteúdo adiante a cada byte novo, o PRIMEIRO byte enviado acaba
        no chip mais distante da Raspberry Pi. O latch único no final faz
        todos os dispositivos atualizarem no mesmo instante, evitando
        rasgos visuais.
        """
        self.last_frame = tuple(dados)
        if self.simulate:
            return
        assert self._latch is not None
        with self.lock:
            self._latch.off()
            for byte in dados:
                self._shift_byte(byte & 0xFF, msb_first)
            self._latch.on()

    def clear(self, n_bytes: int = 6) -> None:
        """Apaga tudo (zeros no barramento)."""
        self.write_frame([0x00] * n_bytes)

    def close(self) -> None:
        """Apaga os displays e libera os GPIOs."""
        try:
            if self.available and not self.simulate:
                self.clear()
        except Exception:
            pass
        for dev in (self._data, self._latch, self._clock):
            if dev is not None:
                try:
                    dev.close()
                except Exception:
                    pass
        self._data = self._latch = self._clock = None
        self.available = False
