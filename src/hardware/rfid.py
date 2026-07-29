#!/usr/bin/env python3
"""
rfid.py — Leitor MFRC522 (SPI0/CE0) para selecionar a dificuldade.

Cada cartão Mifare tem um UID único. Mapeamos UID -> dificuldade em
``config.RFID_CARD_MAP``. Sem cartão reconhecido, o jogo fica no modo
padrão (Normal).

Para descobrir o UID dos seus cartões:

    python3 -m hardware.rfid

Encoste cada cartão e anote o número que aparecer.
"""
from __future__ import annotations

import logging

import config
from config import Difficulty
from hardware.base import HardwareComponent, requires_hardware

logger = logging.getLogger("snake_pi.hardware.rfid")


class RFIDReader(HardwareComponent):
    """Leitor RC522 com detecção de cartão não-bloqueante."""

    def __init__(self, simulate: bool = False) -> None:
        super().__init__(name="RFID RC522")
        self._reader = None
        self.simulate = simulate
        self.last_uid: int | None = None

        if simulate:
            self.available = True
            return

        try:

            from mfrc522 import SimpleMFRC522
            self._reader = SimpleMFRC522()
            self.available = True
            logger.info("Leitor RFID pronto (SPI%d, CE%d).",
                        config.SPI_BUS, config.SPI_DEVICE)
        except Exception as exc:
            logger.warning("RFID indisponível: %s "
                           "(instale com: pip install mfrc522)", exc)
            self.available = False

    @requires_hardware(default=None, tolerate=5)
    def read_uid(self) -> int | None:
        """
        Tenta ler um cartão sem bloquear.

        ``read_no_block`` devolve (None, None) quando não há cartão no
        campo, que é o caso na esmagadora maioria das chamadas. Bloquear
        aqui congelaria a thread do RFID indefinidamente.
        """
        if self.simulate or self._reader is None:
            return None
        uid, _texto = self._reader.read_no_block()
        if uid is not None:
            self.last_uid = int(uid)
        return int(uid) if uid is not None else None

    def read_difficulty(self) -> Difficulty | None:
        """
        Lê um cartão e traduz para a dificuldade correspondente.

        :return: a dificuldade, ou None se não houve cartão ou o UID é
                 desconhecido (nesse caso o jogo mantém a atual).
        """
        uid = self.read_uid()
        if uid is None:
            return None
        dif = config.RFID_CARD_MAP.get(uid)
        if dif is None:
            logger.info("Cartão desconhecido: UID %d "
                        "(adicione em RFID_CARD_MAP para usá-lo).", uid)
        return dif

    def close(self) -> None:
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except Exception:
            pass
        self._reader = None
        self.available = False


if __name__ == "__main__":

    import time
    logging.basicConfig(level=logging.INFO)
    leitor = RFIDReader()
    if not leitor.available:
        raise SystemExit("Leitor RFID não inicializou. SPI está habilitado?")
    print("Encoste um cartão no leitor. Ctrl-C para sair.\n")
    vistos: set[int] = set()
    try:
        while True:
            uid = leitor.read_uid()
            if uid is not None and uid not in vistos:
                vistos.add(uid)
                print(f"  UID detectado: {uid}")
                print(f"  -> cole no config.py:  {uid}: Difficulty.NORMAL,\n")
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\nUIDs encontrados:", sorted(vistos) or "nenhum")
    finally:
        leitor.close()
