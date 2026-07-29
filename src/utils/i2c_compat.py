#!/usr/bin/env python3
"""
i2c_compat.py — Abstrai qual biblioteca I2C está disponível.

O Raspberry Pi OS já traz ``smbus`` instalado; o ``smbus2`` é mais moderno
mas precisa ser instalado à parte, o que exige pip (e às vezes sudo). Como
usamos apenas quatro métodos — ``write_byte``, ``read_byte``,
``read_byte_data`` e ``close`` — e as duas bibliotecas os expõem de forma
idêntica, dá para aceitar qualquer uma das duas.

Isso permite rodar o projeto numa Raspberry Pi recém-instalada sem
instalar absolutamente nada via apt ou pip.

Uso:
    from utils.i2c_compat import open_i2c_bus
    bus = open_i2c_bus(1)
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("snake_pi.i2c")

_BACKEND: str | None = None


def i2c_backend() -> str:
    """Nome da biblioteca I2C em uso ('smbus2', 'smbus' ou 'nenhuma')."""
    return _BACKEND or "nenhuma"


def open_i2c_bus(bus_id: int = 1) -> Any:
    """
    Abre o barramento I2C usando a biblioteca que estiver disponível.

    Tenta o smbus2 primeiro por ser a implementação mais completa; cai
    para o smbus, que já vem no sistema, se o primeiro não existir.

    :raises ImportError: se nenhuma das duas estiver instalada.
    :raises OSError: se o barramento existir mas não puder ser aberto
                     (I2C desabilitado, permissão negada).
    """
    global _BACKEND

    try:
        from smbus2 import SMBus
        _BACKEND = "smbus2"
        return SMBus(bus_id)
    except ImportError:
        pass

    try:
        from smbus import SMBus
        _BACKEND = "smbus"
        logger.debug("Usando 'smbus' (smbus2 não encontrado).")
        return SMBus(bus_id)
    except ImportError:
        pass

    _BACKEND = None
    raise ImportError(
        "Nenhuma biblioteca I2C encontrada. Instale uma destas:\n"
        "  sudo apt install python3-smbus2      (ou python3-smbus)\n"
        "  pip3 install --user --break-system-packages smbus2"
    )
