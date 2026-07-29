#!/usr/bin/env python3
"""
workers.py — As threads periféricas do Snake Pi.

POR QUE EXISTE CADA THREAD
--------------------------
A thread principal roda o Pygame (obrigatório: SDL exige a thread main) e
a simulação do jogo. Tudo que é lento ou tem ritmo próprio sai de lá, para
que nenhum periférico consiga engasgar a imagem.

LCDThread (4 Hz)
    Escrever 32 caracteres no LCD custa ~64 transações I2C, algo em torno
    de 8-15 ms. A 60 fps o quadro inteiro tem 16 ms — escrever o LCD no
    loop principal derrubaria o frame rate quase pela metade.

DisplayThread (~420 Hz)
    A matriz 8x8 e o display de 4 dígitos são multiplexados: só um
    elemento aceso por vez, alternando rápido demais para o olho perceber.
    Isso exige uma cadência alta e constante que não tem nada a ver com a
    taxa de quadros do jogo. Abaixo de ~200 Hz aparece cintilação.

RFIDThread (4 Hz)
    A leitura SPI do RC522 é lenta e, dependendo da biblioteca, chega a
    bloquear. Numa thread própria, um cartão mal lido não trava nada.

BuzzerThread (dirigida por eventos)
    Melodias são sequências de notas com ``sleep`` entre elas — a de game
    over dura quase 1 segundo. Tocar isso no loop principal congelaria a
    tela justamente na hora mais importante.

SensorThread (10 Hz)
    O potenciômetro não muda 60 vezes por segundo; ler a 10 Hz economiza
    barramento I2C, que é compartilhado com o joystick (que precisa de
    resposta rápida e tem prioridade).

Todas terminam observando ``state.shutdown``, um ``threading.Event``, e
são criadas como daemon para que um Ctrl-C nunca deixe o processo pendurado.
"""
from __future__ import annotations

import logging
import queue
import threading
import time

import config
from game.state import GameMode, GameState, MatrixAnim, SoundEvent
from hardware.adc import ADCDevice
from hardware.buzzer import BuzzerSet
from hardware.display_manager import DisplayManager
from hardware.lcd import LCD1602
from hardware.rfid import RFIDReader

logger = logging.getLogger("snake_pi.threads")


class BaseWorker(threading.Thread):
    """Thread periódica que respeita o evento de shutdown."""

    def __init__(self, state: GameState, hz: float, name: str) -> None:
        super().__init__(name=name, daemon=True)
        self.state = state
        self.period = 1.0 / hz if hz > 0 else 0.05

    def step(self) -> None:
        """Um ciclo de trabalho. Implemente na subclasse."""
        raise NotImplementedError

    def run(self) -> None:
        logger.debug("Thread %s iniciada.", self.name)
        while not self.state.shutdown.is_set():
            inicio = time.monotonic()
            try:
                self.step()
            except Exception as exc:


                logger.exception("Erro em %s: %s", self.name, exc)
            decorrido = time.monotonic() - inicio

            self.state.shutdown.wait(max(0.0, self.period - decorrido))
        logger.debug("Thread %s encerrada.", self.name)


class LCDThread(BaseWorker):
    """Mantém o LCD1602 espelhando o estado do jogo."""

    def __init__(self, state: GameState, lcd: LCD1602) -> None:
        super().__init__(state, config.LCD_REFRESH_HZ, "LCDThread")
        self.lcd = lcd

    def step(self) -> None:
        s = self.state.snapshot()
        if s.mode is GameMode.GAME_OVER:
            linha0 = "   GAME OVER"
            linha1 = f"Score: {s.score}"
            if s.new_record:
                linha0 = " NOVO RECORDE!"
        elif s.mode is GameMode.PAUSED:
            linha0 = f"Score: {s.score}"
            linha1 = "  == PAUSA =="
        elif s.mode is GameMode.MENU:
            linha0 = "  SNAKE  PI"
            linha1 = f"Recorde: {s.best_score}"
        elif s.mode is GameMode.HIGH_SCORES:
            linha0 = "  RANKING"
            linha1 = f"Melhor: {s.best_score}"
        elif s.mode is GameMode.SETTINGS:
            linha0 = " CONFIGURACOES"
            linha1 = f"Modo: {s.difficulty.value}"
        else:
            linha0 = f"Score: {s.score}"
            linha1 = f"Level: {s.level}"
        self.lcd.write(linha0, linha1)


class DisplayThread(BaseWorker):
    """Multiplexa a matriz, o bar graph e o display de 4 dígitos."""


    ANIM_DURATION = 1.4

    _ANIM_GLYPH = {
        MatrixAnim.IDLE: "snake",
        MatrixAnim.SMILE: "smile",
        MatrixAnim.FRUIT: "fruit",
        MatrixAnim.HEART: "heart",
        MatrixAnim.SKULL: "skull",
        MatrixAnim.LEVEL_UP: "arrow",
    }

    def __init__(self, state: GameState, manager: DisplayManager) -> None:
        super().__init__(state, config.DISPLAY_MUX_HZ, "DisplayThread")
        self.manager = manager
        self._anim_until: float = 0.0
        self._last_content: float = 0.0

    def _refresh_content(self, agora: float) -> None:
        """Atualiza o que os displays mostram (~20x/s, não a cada varredura)."""
        self._last_content = agora
        s = self.state.snapshot()
        self.manager.update_content(score=s.score,
                                    speed_fraction=s.speed_fraction)


        try:
            anim = self.state.matrix_queue.get_nowait()
            self.manager.matrix.set_glyph(self._ANIM_GLYPH.get(anim, "snake"))
            self._anim_until = agora + self.ANIM_DURATION
            fixo = getattr(config, "EXCLUSIVE_FIXED_DEVICE", None)


            if self.manager.topology.name == "EXCLUSIVE" and fixo is None:
                self.manager.force_active("matrix")
        except queue.Empty:
            pass

        if agora >= self._anim_until:
            self.manager.select_for_state(s.mode.name)

    def run(self) -> None:
        """
        Laço próprio de multiplexação.

        Diferente das outras threads, esta NÃO usa o passo periódico da
        BaseWorker: a multiplexação precisa de uma varredura completa e
        contínua, sem esperar entre colunas. A cada volta atualizamos o
        conteúdo (no máximo ~20x/s) e disparamos uma varredura inteira do
        display ativo. A pausa mínima no fim apenas libera o GIL para as
        outras threads — ela fica ENTRE ciclos completos, nunca no meio de
        um, que é o que evita o tremor.
        """
        logger.debug("Thread %s iniciada (varredura contínua).", self.name)
        while not self.state.shutdown.is_set():
            try:
                agora = time.monotonic()
                if agora - self._last_content >= 0.05:
                    self._refresh_content(agora)


                for _ in range(25):
                    self.manager.sweep()
            except Exception as exc:
                logger.exception("Erro em %s: %s", self.name, exc)


            time.sleep(0)
        logger.debug("Thread %s encerrada.", self.name)


class BuzzerThread(threading.Thread):
    """Toca os efeitos sonoros pedidos pelo jogo, um de cada vez."""

    _MELODY = {
        SoundEvent.SPECIAL_FRUIT: "special",
        SoundEvent.LEVEL_UP: "level_up",
        SoundEvent.GAME_OVER: "game_over",
        SoundEvent.NEW_RECORD: "new_record",
        SoundEvent.MENU_MOVE: "menu_move",
        SoundEvent.MENU_SELECT: "menu_select",
        SoundEvent.PAUSE: "pause",
    }

    def __init__(self, state: GameState, buzzers: BuzzerSet,
                 blue_led=None) -> None:
        super().__init__(name="BuzzerThread", daemon=True)
        self.state = state
        self.buzzers = buzzers
        self.blue_led = blue_led

    def _blink(self) -> None:
        """Acende o LED azul enquanto o buzzer soa, se ele existir."""
        if self.blue_led is not None:
            self.blue_led.on()

    def _blink_off(self) -> None:
        if self.blue_led is not None:
            self.blue_led.off()

    def run(self) -> None:
        logger.debug("Thread BuzzerThread iniciada.")
        while not self.state.shutdown.is_set():
            try:

                evento = self.state.sound_queue.get(timeout=0.15)
            except queue.Empty:
                continue
            try:
                self._blink()
                if evento is SoundEvent.FRUIT:
                    self.buzzers.beep(0.04)
                else:
                    melodia = self._MELODY.get(evento)
                    if melodia:
                        self.buzzers.play(melodia)
            except Exception as exc:
                logger.warning("Falha tocando %s: %s", evento, exc)
            finally:
                self._blink_off()
        self.buzzers.silence()
        self._blink_off()
        logger.debug("Thread BuzzerThread encerrada.")


class RFIDThread(BaseWorker):
    """Procura cartões e ajusta a dificuldade quando reconhece um."""

    def __init__(self, state: GameState, leitor: RFIDReader) -> None:
        super().__init__(state, config.RFID_POLL_HZ, "RFIDThread")
        self.leitor = leitor

    def step(self) -> None:


        if self.state.mode not in (GameMode.MENU, GameMode.SETTINGS,
                                   GameMode.GAME_OVER):
            return
        dificuldade = self.leitor.read_difficulty()
        if dificuldade is not None and dificuldade is not self.state.difficulty:
            self.state.set_difficulty(dificuldade)
            self.state.play_sound(SoundEvent.MENU_SELECT)
            logger.info("Dificuldade alterada por RFID: %s", dificuldade.value)


class SensorThread(BaseWorker):
    """Lê o potenciômetro (velocidade) numa cadência baixa."""

    def __init__(self, state: GameState, adc: ADCDevice) -> None:
        super().__init__(state, config.SENSOR_POLL_HZ, "SensorThread")
        self.adc = adc

    def step(self) -> None:
        self.state.set_pot_value(self.adc.read(config.ADC_CH_SPEED))
