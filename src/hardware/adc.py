#!/usr/bin/env python3
"""
adc.py — Driver do ADS7830, o conversor A/D da placa (I2C @0x48).

A Raspberry Pi não tem nenhuma entrada analógica. Joystick, potenciômetros,
termistor e fotorresistor chegam todos por este chip. A fórmula de seleção
de canal é a oficial da Freenove: os bits do canal são embaralhados antes
de subir 4 casas — trocar isso faz ler o canal errado silenciosamente.
"""
from __future__ import annotations

import logging
import threading

import config
from hardware.base import HardwareComponent, requires_hardware

logger = logging.getLogger("snake_pi.hardware.adc")

_ADS7830_CMD = 0x84


class ADCDevice(HardwareComponent):
    """ADS7830 de 8 canais e 8 bits (0..255)."""

    def __init__(self, address: int = config.ADC_I2C_ADDR,
                 bus_id: int = config.I2C_BUS, simulate: bool = False) -> None:
        super().__init__(name="ADS7830")
        self.address: int = address
        self._bus = None
        self._lock = threading.Lock()
        self.simulate: bool = simulate

        if simulate:
            self.available = True
            logger.info("ADC em modo simulação.")
            return

        try:
            from utils.i2c_compat import open_i2c_bus
            self._bus = open_i2c_bus(bus_id)
            self._bus.write_byte(self.address, 0x00)
            self.available = True
            logger.info("ADS7830 detectado em 0x%02x.", address)
        except Exception as exc:
            logger.warning("ADC indisponível em 0x%02x: %s", address, exc)
            self.available = False

    @requires_hardware(default=128)
    def read(self, channel: int) -> int:
        """
        Lê um canal (0..7) e devolve o valor bruto de 8 bits.

        O padrão em caso de falha é 128 (meio da escala) de propósito: para
        o joystick isso equivale a "centro", ou seja, um ADC morto deixa a
        cobra seguindo reto em vez de virar sozinha.
        """
        if not 0 <= channel <= 7:
            raise ValueError(f"Canal de ADC inválido: {channel}")
        if self.simulate:
            return 128
        assert self._bus is not None
        comando = _ADS7830_CMD | (((channel << 2 | channel >> 1) & 0x07) << 4)
        with self._lock:
            return self._bus.read_byte_data(self.address, comando)

    def read_voltage(self, channel: int, vref: float = 3.3) -> float:
        """Converte a leitura bruta em tensão aproximada."""
        return self.read(channel) / 255.0 * vref

    def close(self) -> None:
        if self._bus is not None:
            try:
                self._bus.close()
            except Exception:
                pass
            self._bus = None
        self.available = False


if __name__ == "__main__":

    import time
    logging.basicConfig(level=logging.INFO)
    adc = ADCDevice()
    print("Lendo canais... Ctrl-C para sair.")
    try:
        while True:
            vals = " ".join(f"A{c}={adc.read(c):3d}" for c in range(7))
            print("\r" + vals, end="", flush=True)
            time.sleep(0.2)
    except KeyboardInterrupt:
        print()
    finally:
        adc.close()
