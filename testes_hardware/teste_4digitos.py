#!/usr/bin/env python3
"""
teste_4digitos.py — Mostra a pontuação no display de 4 dígitos (GPIO 17/22/27).

Ligue SÓ a chave DIP do display de 4 dígitos (desligue matriz e bar graph).
Roda de dentro de src/:
    cd ~/snake-v5/projeto/src
    python3 ../testes_hardware/teste_4digitos.py
"""
import os
import sys
import time

# Permite importar os módulos de src/ mesmo rodando a partir de testes_hardware/
_SRC = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, os.path.abspath(_SRC))

from hardware.shift_register import ShiftRegisterBus
from hardware.displays import FourDigitDisplay

bus = ShiftRegisterBus()
if not bus.available:
    raise SystemExit("74HC595 nao inicializou (GPIO 17/22/27 ocupados?)")

disp = FourDigitDisplay()
print("Simulando a pontuacao subindo: 0, 10, 20, ... ate 1230.")
print("O display deve mostrar cada numero por ~0.8s. Ctrl-C para sair.")
try:
    for score in range(0, 1240, 10):
        disp.set_number(score)
        # multiplexa este numero por ~0.8 s (varre os 4 digitos rapido)
        t = time.time()
        while time.time() - t < 0.8:
            for _ in range(4):
                a, b = disp.next_frame()
                bus.write_frame((a, b))
    print("\nfim - o numero apareceu legivel?")
except KeyboardInterrupt:
    print("\nfim")
finally:
    bus.close()
