#!/usr/bin/env python3
"""
display_manager.py — Arbitra o barramento 74HC595 entre os três displays.

Este é o módulo que resolve a principal restrição de hardware da placa.
Matriz, bar graph e display de 4 dígitos compartilham os mesmos GPIOs
(22/27/17), e existem duas montagens possíveis:

CASCADE
    Os três 74HC595 estão em série. Um único quadro contendo os bytes de
    todos eles atualiza os três simultaneamente. Todos funcionam juntos.

EXCLUSIVE
    Os três dividem o mesmo barramento e são selecionados pelas chaves DIP
    da placa. Só um responde por vez; se dois estiverem ligados, ambos
    recebem os mesmos bytes e mostram lixo. Neste modo o manager escolhe
    qual dispositivo "ganha" o barramento conforme o estado do jogo
    (tabela ``EXCLUSIVE_BY_STATE`` no config).

O modo é lido de ``config.BUS_TOPOLOGY``. Rode ``diagnostico_placa.py``
para descobrir qual é o seu caso e ajuste uma linha no config.
"""
from __future__ import annotations

import logging

import config
from config import BusTopology
from hardware.displays import FourDigitDisplay, LEDBarGraph, LEDMatrix8x8
from hardware.shift_register import ShiftRegisterBus

logger = logging.getLogger("snake_pi.hardware.displays")


class DisplayManager:
    """Dono dos três displays e do barramento que eles compartilham."""

    def __init__(self, bus: ShiftRegisterBus,
                 topology: BusTopology | None = None) -> None:
        self.bus: ShiftRegisterBus = bus
        self.topology: BusTopology = topology or config.BUS_TOPOLOGY

        self.matrix: LEDMatrix8x8 = LEDMatrix8x8()
        self.display4: FourDigitDisplay = FourDigitDisplay()
        self.bargraph: LEDBarGraph = LEDBarGraph()

        self._devices = {
            "matrix": self.matrix,
            "display4": self.display4,
            "bargraph": self.bargraph,
        }
        fixo = getattr(config, "EXCLUSIVE_FIXED_DEVICE", None)
        self._active: str = fixo if fixo in self._devices else "display4"

        logger.info("DisplayManager em modo %s (ativo inicial: %s).",
                    self.topology.value, self._active)


    def select_for_state(self, mode_name: str) -> None:
        """
        Escolhe qual display ocupa o barramento, conforme o estado do jogo.

        Em CASCADE não faz nada: todos são atualizados de qualquer forma.
        """
        if self.topology is BusTopology.CASCADE:
            return

        fixo = getattr(config, "EXCLUSIVE_FIXED_DEVICE", None)
        if fixo in self._devices:
            self._active = fixo
            return
        alvo = config.EXCLUSIVE_BY_STATE.get(mode_name, "display4")
        if alvo != self._active and alvo in self._devices:
            self._active = alvo
            logger.debug("Barramento 595 cedido para '%s'.", alvo)

    @property
    def active(self) -> str:
        """Nome do dispositivo que está com o barramento."""
        return self._active

    def force_active(self, nome: str) -> None:
        """Força um dispositivo específico (usado em animações de Game Over)."""
        if nome in self._devices:
            self._active = nome


    def update_content(self, *, score: int | None = None,
                       speed_fraction: float | None = None,
                       glyph: str | None = None) -> None:
        """Atualiza o que cada display deve mostrar (sem escrever no barramento)."""
        if score is not None:
            self.display4.set_number(score)
        if speed_fraction is not None:
            self.bargraph.set_fraction(speed_fraction)
        if glyph is not None:
            self.matrix.set_glyph(glyph)


    def tick(self) -> None:
        """
        Envia um quadro ao barramento.

        Deve ser chamado a algumas centenas de Hz (ver ``DISPLAY_MUX_HZ``).
        Abaixo de ~200 Hz a multiplexação fica visível como cintilação.
        """
        if not self.bus.available:
            return
        if self.topology is BusTopology.CASCADE:
            self._tick_cascade()
        else:
            self._tick_exclusive()

    def _tick_cascade(self) -> None:
        """Monta um quadro único com os bytes de todos os dispositivos."""
        quadro: list[int] = []
        for nome in config.CASCADE_ORDER:
            dev = self._devices.get(nome)
            if dev is None:
                continue
            a, b = dev.next_frame()
            quadro.extend((a, b))
        self.bus.write_frame(quadro)

    def _tick_exclusive(self) -> None:
        """Envia apenas os bytes do dispositivo que está com o barramento."""
        dev = self._devices[self._active]
        a, b = dev.next_frame()
        self.bus.write_frame((a, b))


    _CYCLE = {"matrix": 8, "display4": 4, "bargraph": 1}

    def sweep(self) -> None:
        """
        Faz um ciclo de multiplexação INTEIRO de uma vez, em laço apertado.

        Esta é a correção do flicker. A matriz e o display de 4 dígitos só
        formam uma imagem estável se todas as colunas/dígitos forem varridos
        em sequência rápida — a persistência de visão junta as partes. Enviar
        um quadro por vez, com pausa entre eles (como era antes), fazia cada
        ciclo levar dezenas de milissegundos e a imagem tremer.

        Aqui varremos o ciclo completo sem pausa nenhuma no meio, exatamente
        como faz o código de referência da Freenove.
        """
        if not self.bus.available:
            return
        if self.topology is BusTopology.CASCADE:
            for _ in range(8):
                self._tick_cascade()
        else:
            n = self._CYCLE.get(self._active, 1)
            for _ in range(n):
                self._tick_exclusive()


    def blank(self) -> None:
        """Apaga tudo o que estiver no barramento."""
        self.matrix.set_glyph("blank")
        self.display4.clear()
        self.bargraph.set_level(0)
        n = 6 if self.topology is BusTopology.CASCADE else 2
        try:
            self.bus.write_frame([0xFF] * n)
        except Exception:
            pass
