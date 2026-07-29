#!/usr/bin/env python3
"""
calibrar_joystick.py — Diagnóstico e calibração do joystick.

Rode NA RASPBERRY PI:
    python3 calibrar_joystick.py

As direções do joystick vêm do ADC (canais 5 e 6, via I²C), NÃO do GPIO 7
— o GPIO 7 é só o botão. Se o joystick "não anda", quase sempre é porque:
  1. o ADC não está respondendo no I²C (ver 'i2cdetect -y 1'), ou
  2. o centro/zona morta não batem com os valores reais do seu joystick.

Este script mostra os valores crus em tempo real e, ao final, sugere os
parâmetros exatos para colar no config.py.
"""
from __future__ import annotations

import sys
import time

import config


def main() -> int:
    from hardware.adc import ADCDevice
    from utils.i2c_compat import i2c_backend

    print("=" * 56)
    print(" CALIBRACAO DO JOYSTICK")
    print("=" * 56)

    adc = ADCDevice()
    print(f"Biblioteca I2C: {i2c_backend()}")
    if not adc.available:
        print("\n!! O ADC NAO respondeu no I2C.")
        print("   O joystick depende dele. Verifique, nesta ordem:")
        print("   - a chave POWER da placa esta ligada?")
        print("   - 'i2cdetect -y 1' mostra o endereco 48?")
        print("   - I2C habilitado? (dtparam=i2c_arm=on no config.txt)")
        return 1

    cx = config.ADC_CH_JOYSTICK_X
    cy = config.ADC_CH_JOYSTICK_Y


    print("\n[1/2] NAO toque no joystick. Lendo o centro por 3 segundos...")
    somas = [0, 0]
    n = 0
    fim = time.time() + 3
    while time.time() < fim:
        somas[0] += adc.read(cx)
        somas[1] += adc.read(cy)
        n += 1
        time.sleep(0.02)
    centro_x, centro_y = somas[0] // n, somas[1] // n
    print(f"    centro X (canal {cx}) = {centro_x}")
    print(f"    centro Y (canal {cy}) = {centro_y}")
    if 100 <= centro_x <= 156 and 100 <= centro_y <= 156:
        print("    OK: centro proximo de 128, como esperado.")
    else:
        print("    ATENCAO: centro longe de 128. Anote os valores acima.")


    print("\n[2/2] Agora MOVA o joystick em todas as direcoes, ate o limite,")
    print("      por 8 segundos. Observe os valores mudarem:\n")
    lo = [255, 255]
    hi = [0, 0]
    fim = time.time() + 8
    while time.time() < fim:
        x = adc.read(cx)
        y = adc.read(cy)
        lo[0], hi[0] = min(lo[0], x), max(hi[0], x)
        lo[1], hi[1] = min(lo[1], y), max(hi[1], y)
        print(f"\r    X={x:3d} (min {lo[0]:3d} max {hi[0]:3d})   "
              f"Y={y:3d} (min {lo[1]:3d} max {hi[1]:3d})   ",
              end="", flush=True)
        time.sleep(0.05)
    print("\n")

    amplitude = min(hi[0] - lo[0], hi[1] - lo[1])
    if amplitude < 40:
        print("!! Os valores quase nao mudaram. O joystick pode estar mal")
        print("   conectado, ou a chave DIP correspondente esta desligada.")
        return 1


    deadzone = max(20, amplitude // 6)
    print("=" * 56)
    print(" Cole no config.py:")
    print("=" * 56)
    print(f"JOY_CENTER: int = {(centro_x + centro_y) // 2}")
    print(f"JOY_DEADZONE: int = {deadzone}")
    print("\n(se um eixo estiver invertido no jogo, troque JOY_INVERT_X")
    print(" ou JOY_INVERT_Y entre True/False)")
    adc.close()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrompido.")
