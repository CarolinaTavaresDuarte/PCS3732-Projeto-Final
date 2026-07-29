#!/usr/bin/env python3
"""teste_buzzer.py — Ouve os padrões de bip do buzzer ativo (GPIO 12)."""
import time
from hardware.buzzer import BuzzerSet

b = BuzzerSet()
if not b.available:
    raise SystemExit("Buzzer indisponivel. Chave DIP do Active Buzzer ligada?")

print("1) COMIDA (1 bip curto)");          b.beep(0.05);          time.sleep(1)
print("2) VITORIA (3 rapidos + 1 longo)"); b.play("new_record");  time.sleep(1)
print("3) DERROTA (3 longos e lentos)");   b.play("game_over");   time.sleep(1)
print("4) LEVEL UP (2 rapidos)");          b.play("level_up");    time.sleep(1)
b.close()
print("fim")
