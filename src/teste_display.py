#!/usr/bin/env python3
"""teste_display.py — Testa UM display do 74HC595 isoladamente.
Uso: python3 teste_display.py [4digitos|matriz|barra]"""
import sys, time
from hardware.shift_register import ShiftRegisterBus
from hardware.displays import FourDigitDisplay, LEDMatrix8x8, LEDBarGraph

alvo = sys.argv[1] if len(sys.argv) > 1 else "barra"
bus = ShiftRegisterBus()
if not bus.available:
    raise SystemExit("74HC595 nao inicializou (GPIO 17/22/27 ocupados?)")

if alvo == "4digitos":
    dev = FourDigitDisplay(); dev.set_number(1234); n = 4; d = "mostrar 1234"
elif alvo == "matriz":
    dev = LEDMatrix8x8(); dev.set_glyph("smile"); n = 8; d = "carinha :)"
else:
    dev = LEDBarGraph(); dev.set_level(6); n = 1; d = "6 LEDs fixos"

print(f"Testando '{alvo}': deve {d}. Ctrl-C para sair.")
try:
    while True:
        for _ in range(n):
            a, b = dev.next_frame()
            bus.write_frame((a, b))
except KeyboardInterrupt:
    print("\nfim")
finally:
    bus.close()
