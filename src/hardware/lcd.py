#!/usr/bin/env python3
"""
lcd.py — LCD1602 com backpack I2C (PCF8574 + HD44780).

Implementação autocontida em modo 4 bits, sem depender de biblioteca
externa de LCD. O endereço é detectado automaticamente entre 0x27
(PCF8574) e 0x3f (PCF8574A), porque a Freenove usa os dois conforme o lote.

Mapeamento de bits do PCF8574:
    P0=RS  P1=RW  P2=EN  P3=Backlight  P4..P7=D4..D7
"""
from __future__ import annotations

import logging
import threading
import time

import config
from hardware.base import HardwareComponent, requires_hardware

logger = logging.getLogger("snake_pi.hardware.lcd")

_RS = 0x01
_ENABLE = 0x04
_BACKLIGHT = 0x08
_E_PULSE = 0.0005
_E_DELAY = 0.0005
_WIDTH = 16
_LINE_ADDR = (0x80, 0xC0)


class LCD1602(HardwareComponent):
    """Display de 2 linhas por 16 colunas via I2C."""

    def __init__(self, bus_id: int = config.I2C_BUS, simulate: bool = False) -> None:
        super().__init__(name="LCD1602")
        self.address: int | None = None
        self._bus = None
        self._backlight: int = _BACKLIGHT
        self._lock = threading.Lock()
        self._cache: list[str] = ["", ""]
        self.simulate = simulate

        if simulate:
            self.available = True
            logger.info("LCD em modo simulação.")
            return

        try:
            from utils.i2c_compat import open_i2c_bus
            self._bus = open_i2c_bus(bus_id)
            self.address = self._detect()
            if self.address is None:
                raise IOError("LCD não encontrado em 0x27 nem 0x3f")
            self._init_display()
            self.available = True
            logger.info("LCD1602 pronto em 0x%02x.", self.address)
        except Exception as exc:
            logger.warning("LCD indisponível: %s", exc)
            self.available = False

    def _detect(self) -> int | None:
        """Procura o LCD nos endereços conhecidos do backpack."""
        assert self._bus is not None
        for addr in config.LCD_I2C_ADDRS:
            try:
                self._bus.write_byte(addr, 0x00)
                return addr
            except OSError:
                continue
        return None


    def _strobe(self, data: int) -> None:
        """Pulso de ENABLE que faz o HD44780 capturar o nibble."""
        assert self._bus is not None and self.address is not None
        self._bus.write_byte(self.address, data | _ENABLE | self._backlight)
        time.sleep(_E_PULSE)
        self._bus.write_byte(self.address, (data & ~_ENABLE) | self._backlight)
        time.sleep(_E_DELAY)

    def _write_byte(self, valor: int, mode: int) -> None:
        """Envia um byte como dois nibbles (interface de 4 bits)."""
        assert self._bus is not None and self.address is not None
        alto = mode | (valor & 0xF0) | self._backlight
        baixo = mode | ((valor << 4) & 0xF0) | self._backlight
        self._bus.write_byte(self.address, alto)
        self._strobe(alto)
        self._bus.write_byte(self.address, baixo)
        self._strobe(baixo)

    def _init_display(self) -> None:
        """Sequência padrão de inicialização do HD44780 em 4 bits."""
        for cmd in (0x33, 0x32, 0x28, 0x0C, 0x06, 0x01):
            self._write_byte(cmd, mode=0)
            time.sleep(0.005)


    @requires_hardware()
    def write_line(self, row: int, text: str) -> None:
        """
        Escreve uma linha (0 ou 1), truncando ou completando em 16 caracteres.

        Guardamos o que já está na tela e só reescrevemos se mudou. Cada
        caractere custa duas transações I2C; reescrever as duas linhas
        inteiras 4x por segundo sem necessidade seria desperdício puro de
        barramento — que é compartilhado com o ADC do joystick.
        """
        if row not in (0, 1):
            raise ValueError("O LCD1602 só tem as linhas 0 e 1")
        texto = text.ljust(_WIDTH)[:_WIDTH]
        if self._cache[row] == texto:
            return
        if self.simulate:
            self._cache[row] = texto
            return
        with self._lock:
            self._write_byte(_LINE_ADDR[row], mode=0)
            for ch in texto:
                self._write_byte(ord(ch), mode=_RS)
        self._cache[row] = texto

    def write(self, line0: str, line1: str = "") -> None:
        """Atalho para escrever as duas linhas de uma vez."""
        self.write_line(0, line0)
        self.write_line(1, line1)

    @requires_hardware()
    def clear(self) -> None:
        """Limpa o display."""
        self._cache = ["", ""]
        if self.simulate:
            return
        with self._lock:
            self._write_byte(0x01, mode=0)
            time.sleep(0.002)

    @requires_hardware()
    def set_backlight(self, on: bool) -> None:
        """Liga ou desliga a luz de fundo."""
        self._backlight = _BACKLIGHT if on else 0x00
        if self.simulate:
            return
        assert self._bus is not None and self.address is not None
        with self._lock:
            self._bus.write_byte(self.address, self._backlight)

    def close(self) -> None:
        try:
            if self.available and not self.simulate:
                self.clear()
                self.set_backlight(False)
        except Exception:
            pass
        if self._bus is not None:
            try:
                self._bus.close()
            except Exception:
                pass
            self._bus = None
        self.available = False
