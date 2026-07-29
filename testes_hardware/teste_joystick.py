#!/usr/bin/env python3
"""
teste_joystick.py — Testa o CLIQUE do joystick (botão no GPIO 7).

O joystick é usado só como botão de confirmar; o manche não faz nada.
Se der 'GPIO busy', o SPI está ocupando o pino 7: desligue o SPI
(comente 'dtparam=spi=on' no /boot/config.txt) e reinicie.

    python3 ../testes_hardware/teste_joystick.py
"""
import time

try:
    from gpiozero import Button
except ImportError:
    raise SystemExit("gpiozero nao encontrado.")

try:
    b = Button(7, pull_up=True, bounce_time=0.05)
except Exception as exc:
    raise SystemExit(f"Nao consegui abrir o GPIO 7: {exc}\n"
                     "Provavel SPI ocupando o pino. Desligue o SPI e reinicie.")

print("Aperte o joystick varias vezes (12 segundos)...")
cliques = 0
t = time.time()
while time.time() - t < 12:
    if b.is_pressed:
        cliques += 1
        print(f"  CLIQUE #{cliques} detectado!")
        time.sleep(0.3)
    time.sleep(0.03)
b.close()
print(f"fim - {cliques} cliques detectados.")
