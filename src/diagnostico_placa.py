#!/usr/bin/env python3
"""
diagnostico_placa.py - Snake Pi / Freenove Projects Board (FNK0054)

Roda NA RASPBERRY PI, no terminal dela:
    python3 diagnostico_placa.py

Objetivo: descobrir a topologia real da placa antes de escrever o projeto.
O teste 5 e o mais importante: define se matriz, bar graph e display de
4 digitos podem funcionar SIMULTANEAMENTE (cascata) ou nao (barramento
compartilhado por chaves DIP).
"""
from __future__ import annotations

import time

DATA_PIN = 22
LATCH_PIN = 27
CLOCK_PIN = 17

ADC_ADDR = 0x48
CH_POT, CH_JOY_X, CH_JOY_Y = 2, 5, 6
JOY_SW_PIN = 7
BOTOES = (20, 21, 24, 26)


def linha(txt: str = "") -> None:
    print(txt)


def titulo(n: int, txt: str) -> None:
    linha()
    linha("=" * 60)
    linha(f"TESTE {n}: {txt}")
    linha("=" * 60)


def teste_i2c() -> dict:
    titulo(1, "Barramento I2C (ADC + LCD)")
    achados = {}
    try:
        from utils.i2c_compat import open_i2c_bus, i2c_backend
    except ImportError:
        linha("!! modulo utils/i2c_compat.py nao encontrado")
        return achados

    try:
        bus = open_i2c_bus(1)
        linha(f"  (biblioteca I2C em uso: {i2c_backend()})")
        with bus:
            for addr in range(0x03, 0x78):
                try:
                    bus.write_byte(addr, 0)
                    achados[addr] = True
                except OSError:
                    pass
    except Exception as exc:
        linha(f"!! Nao consegui abrir o I2C-1: {exc}")
        linha("   Habilite com: sudo raspi-config > Interface Options > I2C")
        return achados

    if not achados:
        linha("!! Nenhum dispositivo I2C encontrado. I2C esta habilitado?")
        return achados

    for addr in sorted(achados):
        nome = ""
        if addr == 0x48:
            nome = "  <-- ADC ADS7830"
        elif addr in (0x27, 0x3F):
            nome = "  <-- LCD1602 (PCF8574)"
        linha(f"  encontrado: 0x{addr:02x}{nome}")

    linha()
    linha(f"  ADC  em 0x48 : {'OK' if 0x48 in achados else 'NAO ENCONTRADO'}")
    lcd = [a for a in (0x27, 0x3F) if a in achados]
    linha(f"  LCD          : {'OK em 0x%02x' % lcd[0] if lcd else 'NAO ENCONTRADO'}")
    return achados


def ler_adc(bus, canal: int) -> int:
    """Le um canal do ADS7830 (0..255). Formula oficial da Freenove."""
    cmd = 0x84 | (((canal << 2 | canal >> 1) & 0x07) << 4)
    return bus.read_byte_data(ADC_ADDR, cmd)


def teste_adc() -> None:
    titulo(2, "ADC: potenciometro e joystick (10 segundos)")
    try:
        from utils.i2c_compat import open_i2c_bus
    except ImportError:
        linha("!! utils/i2c_compat.py ausente, pulando.")
        return

    linha("Gire o potenciometro e mexa o joystick agora.")
    linha("Anote se os numeros mudam e qual eixo responde a qual direcao.")
    linha()
    try:
        with open_i2c_bus(1) as bus:
            fim = time.time() + 10
            while time.time() < fim:
                pot = ler_adc(bus, CH_POT)
                x = ler_adc(bus, CH_JOY_X)
                y = ler_adc(bus, CH_JOY_Y)
                print(f"\r  POT(ch2)={pot:3d}   X(ch5)={x:3d}   Y(ch6)={y:3d}   ",
                      end="", flush=True)
                time.sleep(0.1)
        linha()
        linha()
        linha("  Esperado: valores ~128 com joystick no centro,")
        linha("  indo para ~0 e ~255 nos extremos.")
    except Exception as exc:
        linha(f"\n!! Falha lendo o ADC: {exc}")


def teste_botoes() -> None:
    titulo(3, "Botoes fisicos (15 segundos)")
    try:
        from gpiozero import Button
    except ImportError:
        linha("!! gpiozero ausente: sudo apt install python3-gpiozero")
        return

    pinos = list(BOTOES) + [JOY_SW_PIN]
    botoes = {}
    for p in pinos:
        try:
            botoes[p] = Button(p, pull_up=True, bounce_time=0.05)
        except Exception as exc:
            linha(f"  GPIO {p}: nao consegui abrir ({exc})")

    if not botoes:
        return

    linha(f"Monitorando GPIOs {sorted(botoes)} (o {JOY_SW_PIN} e o do joystick).")
    linha("APERTE CADA BOTAO DA PLACA UM DE CADA VEZ e anote qual GPIO acende.")
    linha()
    vistos = set()
    fim = time.time() + 15
    try:
        while time.time() < fim:
            for p, b in botoes.items():
                if b.is_pressed and p not in vistos:
                    vistos.add(p)
                    linha(f"  >> GPIO {p} PRESSIONADO")
            time.sleep(0.02)
    finally:
        for b in botoes.values():
            b.close()

    linha()
    if vistos:
        linha(f"  Responderam: {sorted(vistos)}")
    else:
        linha("  Nenhum botao detectado. Confira as chaves DIP dos botoes.")


def teste_buzzers() -> None:
    titulo(4, "Buzzers (ativo GPIO12, passivo GPIO4)")
    try:
        from gpiozero import Buzzer, TonalBuzzer
    except ImportError:
        linha("!! gpiozero ausente, pulando.")
        return

    linha("Voce deve ouvir: 2 bipes secos, depois 3 notas musicais.")
    linha()
    try:
        b = Buzzer(12)
        for _ in range(2):
            b.on(); time.sleep(0.15); b.off(); time.sleep(0.15)
        b.close()
        linha("  buzzer ATIVO (GPIO12): comando enviado")
    except Exception as exc:
        linha(f"  buzzer ATIVO  falhou: {exc}")

    try:
        t = TonalBuzzer(4)
        for nota in ("C5", "E5", "G5"):
            t.play(nota); time.sleep(0.25)
        t.stop(); t.close()
        linha("  buzzer PASSIVO (GPIO4): comando enviado")
    except Exception as exc:
        linha(f"  buzzer PASSIVO falhou: {exc}")


def shift_out(data, clock, valor: int, msb_first: bool = True) -> None:
    """Desloca 1 byte para dentro do 74HC595."""
    for i in range(8):
        clock.off()
        if msb_first:
            bit = (0x80 & (valor << i)) == 0x80
        else:
            bit = (0x01 & (valor >> i)) == 0x01
        data.on() if bit else data.off()
        clock.on()


def teste_595() -> None:
    titulo(5, "TOPOLOGIA DO 74HC595  <<< O TESTE QUE IMPORTA >>>")
    try:
        from gpiozero import OutputDevice
    except ImportError:
        linha("!! gpiozero ausente, pulando.")
        return

    linha("ANTES DE CONTINUAR: ligue as chaves DIP da MATRIZ 8x8, do")
    linha("BAR GRAPH e do DISPLAY DE 4 DIGITOS ao mesmo tempo.")
    linha()
    input("Feito isso, aperte ENTER para comecar...")

    try:
        data = OutputDevice(DATA_PIN)
        latch = OutputDevice(LATCH_PIN)
        clock = OutputDevice(CLOCK_PIN)
    except Exception as exc:
        linha(f"!! Nao consegui abrir os GPIOs do 595: {exc}")
        linha("   Algum outro programa esta usando a GPIO?")
        return

    try:

        linha()
        linha("--- FASE A: enviando 2 bytes (0xFF 0xFF) ---")
        linha("OLHE PARA A PLACA. O que acendeu?")
        latch.off()
        shift_out(data, clock, 0xFF)
        shift_out(data, clock, 0xFF)
        latch.on()
        time.sleep(4)


        linha()
        linha("--- FASE B: enviando 6 bytes (cascata) ---")
        linha("OLHE DE NOVO. Acendeu ALGO A MAIS que na fase A?")
        latch.off()
        for _ in range(6):
            shift_out(data, clock, 0xFF)
        latch.on()
        time.sleep(5)


        latch.off()
        for _ in range(6):
            shift_out(data, clock, 0x00)
        latch.on()
    finally:
        data.close(); latch.close(); clock.close()

    linha()
    linha("=" * 60)
    linha("INTERPRETACAO:")
    linha()
    linha("  Se na FASE B acendeu MAIS coisa que na FASE A")
    linha("     -> CASCATA. Da pra usar os tres displays juntos. ")
    linha("        Me diga quantos bytes fazem tudo acender.")
    linha()
    linha("  Se FASE A e FASE B ficaram IGUAIS")
    linha("     -> BARRAMENTO COMPARTILHADO. So um display por vez.")
    linha("        Me diga QUAL dos tres acendeu.")
    linha("=" * 60)


def main() -> None:
    linha()
    linha("#" * 60)
    linha("#  DIAGNOSTICO - Freenove Projects Board (FNK0054)")
    linha("#  Snake Pi / Laboratorio de Processadores")
    linha("#" * 60)

    teste_i2c()
    teste_adc()
    teste_botoes()
    teste_buzzers()
    teste_595()

    linha()
    linha("Diagnostico concluido. Me mande a saida completa deste terminal.")
    linha()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        linha("\nInterrompido pelo usuario.")
