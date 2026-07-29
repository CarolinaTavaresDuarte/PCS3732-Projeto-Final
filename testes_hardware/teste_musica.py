#!/usr/bin/env python3
"""
teste_musica.py — Toca as melodias no buzzer passivo (GPIO 4).

Ligue a chave DIP do Passive Buzzer.
    python3 ../testes_hardware/teste_musica.py
"""
import os
import sys
import time

_SRC = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, os.path.abspath(_SRC))

from hardware.buzzer import BuzzerSet

b = BuzzerSet()
if not b.available:
    raise SystemExit("Buzzer indisponivel (chaves DIP ligadas?).")

print("1) APITO da comida (buzzer ativo, GPIO 12)")
b.beep(0.05); time.sleep(1.2)
print("2) VITORIA - musica alegre (buzzer passivo, GPIO 4)")
b.play("new_record"); time.sleep(1.2)
print("3) DERROTA - musica triste e longa (buzzer passivo, GPIO 4)")
b.play("game_over"); time.sleep(1.2)
print("4) LEVEL UP")
b.play("level_up"); time.sleep(1.0)
b.close()
print("fim - ouviu apito + duas musicas diferentes?")
