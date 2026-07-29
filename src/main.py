#!/usr/bin/env python3
"""
main.py — Ponto de entrada do Snake Pi.

Responsabilidades, e só estas:
  1. inicializar os periféricos (tolerando os que faltarem);
  2. injetar essas dependências nas threads e no motor do jogo;
  3. rodar o laço principal (entrada -> simulação -> desenho);
  4. encerrar tudo de forma limpa.

O laço principal fica na thread main porque o Pygame/SDL exige isso.
Todo o resto — LCD, displays, buzzer, RFID, sensores — roda em threads
separadas, cada uma com sua justificativa documentada em
``threads/workers.py``.

Uso:
    python3 main.py                 # normal, na Raspberry Pi
    python3 main.py --sim           # sem hardware nenhum (testar no PC)
    python3 main.py --windowed      # em janela, útil para depurar
"""
from __future__ import annotations

import argparse
import logging
import signal
import sys
import time

import config
from game.engine import GameEngine
from game.menu import MenuAction, build_main_menu, build_settings_menu
from game.score import ScoreBoard
from game.snake import Direction
from game.state import GameMode, GameState, MatrixAnim, SoundEvent
from hardware.adc import ADCDevice
from hardware.base import HardwareComponent
from hardware.blue_led import BlueLED
from hardware.buttons import ButtonPanel
from hardware.buzzer import BuzzerSet
from hardware.display_manager import DisplayManager
from hardware.joystick import Joystick
from hardware.lcd import LCD1602
from hardware.rfid import RFIDReader
from hardware.shift_register import ShiftRegisterBus
from threads.workers import (BuzzerThread, DisplayThread, LCDThread,
                             RFIDThread, SensorThread)
from utils.logger import setup_logging

logger = logging.getLogger("snake_pi.main")

_BTN_TO_DIR = {
    "up": Direction.UP,
    "down": Direction.DOWN,
    "left": Direction.LEFT,
    "right": Direction.RIGHT,
}


class SnakePi:
    """A aplicação inteira."""

    def __init__(self, simulate: bool = False) -> None:
        self.simulate = simulate
        self.state = GameState()
        self.scoreboard = ScoreBoard(config.HIGHSCORE_FILE,
                                     config.MAX_HIGH_SCORES)
        self.engine = GameEngine(self.scoreboard)

        self.main_menu = build_main_menu()
        self.settings_menu = build_settings_menu()
        self._active_menu = self.main_menu

        self._components: list[HardwareComponent] = []
        self._threads: list = []
        self._renderer = None


        self._joy_was_pressed = False
        self._pause_requested = False
        self._restart_requested = False

        self.state.update_game(best_score=self.scoreboard.best)


    def setup_hardware(self) -> None:
        """
        Cria todos os drivers. Nenhuma falha aqui é fatal.

        Cada periférico que não inicializar simplesmente fica marcado como
        indisponível, e suas chamadas viram no-op (ver ``hardware/base.py``).
        """
        sim = self.simulate

        self.adc = ADCDevice(simulate=sim)
        self.joystick = Joystick(self.adc, simulate=sim)
        self.lcd = LCD1602(simulate=sim)
        self.buzzers = BuzzerSet(simulate=sim)
        self.buttons = ButtonPanel(simulate=sim)

        if getattr(config, "ENABLE_RFID", False):
            self.rfid = RFIDReader(simulate=sim)
        else:
            self.rfid = RFIDReader(simulate=True)
            self.rfid.available = False


        self.blue_led = None
        self._led_indicator = getattr(config, "BLUE_LED_MODE", "clock") == "indicator"

        if self._led_indicator:


            self.blue_led = BlueLED(simulate=sim)
            self.bus = ShiftRegisterBus(simulate=sim)
            self.bus.available = False
            self.displays = DisplayManager(self.bus)
            logger.warning("BLUE_LED_MODE='indicator': matriz, bar graph e "
                           "display de 4 dígitos DESLIGADOS (compartilham o "
                           "GPIO17 com o LED azul).")
        else:
            self.bus = ShiftRegisterBus(simulate=sim)
            self.displays = DisplayManager(self.bus)

        self._components = [self.adc, self.joystick, self.lcd, self.buzzers,
                            self.buttons, self.rfid, self.bus]
        if self.blue_led is not None:
            self._components.append(self.blue_led)


        self.buttons.on_press("restart", self._on_restart_button)

        self._report_hardware()

    def _report_hardware(self) -> None:
        """Imprime um resumo de quem subiu e quem não subiu."""
        logger.info("--- Periféricos ---")
        for comp in self._components:
            marca = "OK " if comp.available else "-- "
            logger.info("  [%s] %s", marca, comp.name)
        logger.info("  Topologia do 74HC595: %s", self.displays.topology.value)
        if not any(c.available for c in self._components):
            logger.warning("Nenhum periférico disponível: rodando só com "
                           "teclado e monitor.")

    def start_threads(self) -> None:
        """Sobe as threads periféricas, pulando as que não têm hardware."""
        candidatas = [
            (LCDThread(self.state, self.lcd), self.lcd.available),
            (DisplayThread(self.state, self.displays),
             self.bus.available and not self._led_indicator),
            (BuzzerThread(self.state, self.buzzers, self.blue_led),
             self.buzzers.available),
            (RFIDThread(self.state, self.rfid), self.rfid.available),
            (SensorThread(self.state, self.adc), self.adc.available),
        ]
        for thread, habilitada in candidatas:
            if habilitada:
                thread.start()
                self._threads.append(thread)
                logger.debug("Thread %s no ar.", thread.name)
            else:
                logger.info("Thread %s não iniciada (hardware ausente).",
                            thread.name)


    def _on_pause_button(self) -> None:
        """
        Roda numa thread interna do gpiozero.

        Por isso só levanta uma flag: o tratamento acontece no laço
        principal, onde o estado do jogo pode ser mexido com segurança.
        """
        self._pause_requested = True

    def _on_restart_button(self) -> None:
        self._restart_requested = True


    def _poll_keyboard(self) -> tuple[Direction | None, bool, bool, bool]:
        """
        Lê o teclado como alternativa ao joystick.

        :return: (direção, confirmar, pausar, sair)
        """
        import pygame
        direcao = None
        confirmar = pausar = sair = False

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                sair = True
            elif evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_UP, pygame.K_w):
                    direcao = Direction.UP
                elif evento.key in (pygame.K_DOWN, pygame.K_s):
                    direcao = Direction.DOWN
                elif evento.key in (pygame.K_LEFT, pygame.K_a):
                    direcao = Direction.LEFT
                elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                    direcao = Direction.RIGHT
                elif evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    confirmar = True
                elif evento.key == pygame.K_p:
                    pausar = True
                elif evento.key == pygame.K_r:
                    self._restart_requested = True
                elif evento.key == pygame.K_ESCAPE:
                    sair = True
        return direcao, confirmar, pausar, sair

    def _button_direction(self) -> Direction | None:
        """
        Direção pedida pelos botões coloridos, se houver.

        Com dois botões apertados ao mesmo tempo devolvemos o primeiro da
        ordem cima/baixo/esquerda/direita — arbitrário, mas determinístico,
        o que evita a cobra oscilar entre dois sentidos.
        """
        for nome in self.buttons.pressed_directions():
            direcao = _BTN_TO_DIR.get(nome)
            if direcao is not None:
                return direcao
        return None

    def _joystick_confirm(self) -> bool:
        """True apenas na borda de subida do botão do joystick."""
        agora = self.joystick.is_pressed()
        borda = agora and not self._joy_was_pressed
        self._joy_was_pressed = agora
        return borda


    def _handle_menu(self, direcao_teclado: Direction | None,
                     confirmar: bool) -> None:
        """Navegação e seleção nos menus."""
        menu = self._active_menu


        btn = self._button_direction()
        if btn is Direction.UP and menu.move(-1):
            self.state.play_sound(SoundEvent.MENU_MOVE)
        elif btn is Direction.DOWN and menu.move(1):
            self.state.play_sound(SoundEvent.MENU_MOVE)


        if direcao_teclado is Direction.UP and menu.move(-1, force=True):
            self.state.play_sound(SoundEvent.MENU_MOVE)
        elif direcao_teclado is Direction.DOWN and menu.move(1, force=True):
            self.state.play_sound(SoundEvent.MENU_MOVE)

        if confirmar or self._joystick_confirm():
            self.state.play_sound(SoundEvent.MENU_SELECT)
            self._apply_menu_action(menu.select())

    def _apply_menu_action(self, acao: MenuAction) -> None:
        """Executa a ação escolhida no menu."""
        if acao is MenuAction.START_GAME:
            self._start_game()
        elif acao is MenuAction.HIGH_SCORES:
            self.state.set_mode(GameMode.HIGH_SCORES)
        elif acao is MenuAction.SETTINGS:
            self.settings_menu.reset()
            self._active_menu = self.settings_menu
            self.state.set_mode(GameMode.SETTINGS)
        elif acao is MenuAction.QUIT:
            self.state.request_shutdown()
        elif acao is MenuAction.BACK:
            self._active_menu = self.main_menu
            self.state.set_mode(GameMode.MENU)
        elif acao is MenuAction.CYCLE_DIFFICULTY:
            self._cycle_difficulty()

    def _cycle_difficulty(self) -> None:
        """Passa para a próxima dificuldade, em ciclo."""
        modos = list(config.Difficulty)
        atual = modos.index(self.state.difficulty)
        nova = modos[(atual + 1) % len(modos)]
        self.state.set_difficulty(nova)
        logger.info("Dificuldade: %s", nova.value)

    def _start_game(self) -> None:
        """Começa uma partida nova."""
        self.engine.reset(self.state.difficulty)
        self.state.update_game(score=0, level=1, fruits_eaten=0,
                               snake_length=len(self.engine.snake),
                               new_record=False,
                               best_score=self.scoreboard.best,
                               speed_fraction=self.engine.speed_fraction)
        self.state.set_mode(GameMode.PLAYING)
        self.state.show_animation(MatrixAnim.SMILE)
        logger.info("Partida iniciada (%s).", self.state.difficulty.value)

    def _handle_playing(self, direcao_teclado: Direction | None) -> None:
        """Um quadro de jogo: entrada, simulação e reações."""


        direcao = self._button_direction() or direcao_teclado
        if direcao is not None:
            self.engine.turn(direcao)


        self.engine.set_speed_multiplier(self.state.pot_value / 255.0)

        resultado = self.engine.update()

        if resultado.ate_fruit:
            self.state.play_sound(SoundEvent.FRUIT)
            self.state.show_animation(MatrixAnim.FRUIT)
        if resultado.ate_special:
            self.state.play_sound(SoundEvent.SPECIAL_FRUIT)
            self.state.show_animation(MatrixAnim.HEART)
        if resultado.leveled_up:
            self.state.play_sound(SoundEvent.LEVEL_UP)
            self.state.show_animation(MatrixAnim.LEVEL_UP)
            logger.info("Nível %d.", self.engine.level)

        self.state.update_game(
            score=self.scoreboard.current,
            level=self.engine.level,
            snake_length=len(self.engine.snake),
            fruits_eaten=self.engine.fruits_eaten,
            speed_fraction=self.engine.speed_fraction,
        )

        if resultado.game_over:
            self._end_game()

    def _end_game(self) -> None:
        """Fecha a partida, grava o ranking e dispara os efeitos."""
        recorde = self.engine.finish()
        self.state.update_game(new_record=recorde,
                               best_score=self.scoreboard.best)
        self.state.set_mode(GameMode.GAME_OVER)
        self.state.play_sound(SoundEvent.NEW_RECORD if recorde
                              else SoundEvent.GAME_OVER)
        self.state.show_animation(MatrixAnim.HEART if recorde
                                  else MatrixAnim.SKULL)
        logger.info("Game over. Pontuação %d%s.", self.scoreboard.current,
                    " (NOVO RECORDE)" if recorde else "")

    def _handle_game_over(self, confirmar: bool) -> None:
        """Na tela de Game Over: reiniciar ou voltar ao menu."""
        if self._restart_requested:
            self._restart_requested = False
            self._start_game()
        elif confirmar or self._joystick_confirm():
            self._active_menu = self.main_menu
            self.main_menu.reset()
            self.state.set_mode(GameMode.MENU)

    def _handle_simple_screen(self, confirmar: bool) -> None:
        """Telas informativas (ranking): qualquer confirmação volta ao menu."""
        if confirmar or self._joystick_confirm():
            self._active_menu = self.main_menu
            self.state.set_mode(GameMode.MENU)
            self.state.play_sound(SoundEvent.MENU_SELECT)

    def _handle_pause_request(self) -> None:
        """Alterna entre jogando e pausado."""
        modo = self.state.mode
        if modo is GameMode.PLAYING:
            self.state.set_mode(GameMode.PAUSED)
            self.state.play_sound(SoundEvent.PAUSE)
        elif modo is GameMode.PAUSED:


            self.engine._last_update = time.monotonic()
            self.state.set_mode(GameMode.PLAYING)
            self.state.play_sound(SoundEvent.PAUSE)


    def run(self) -> None:
        """Executa o jogo até pedirem para sair."""
        from display.renderer import Renderer
        self._renderer = Renderer()

        self.state.show_animation(MatrixAnim.IDLE)
        logger.info("Snake Pi no ar. ESC ou 'Sair' encerra.")

        while not self.state.shutdown.is_set():
            direcao, confirmar, pausar_teclado, sair = self._poll_keyboard()
            if sair:
                self.state.request_shutdown()
                break

            if pausar_teclado:
                self._pause_requested = True
            if self._pause_requested:
                self._pause_requested = False
                self._handle_pause_request()


            if self._restart_requested and self.state.mode in (
                    GameMode.PLAYING, GameMode.PAUSED):
                self._restart_requested = False
                self._start_game()


            modo_atual = self.state.mode
            if modo_atual in (GameMode.PLAYING, GameMode.PAUSED):
                if self._joystick_confirm():
                    self._handle_pause_request()

            modo = self.state.mode
            if modo in (GameMode.MENU, GameMode.SETTINGS):
                self._handle_menu(direcao, confirmar)
            elif modo is GameMode.PLAYING:
                self._handle_playing(direcao)
            elif modo is GameMode.GAME_OVER:
                self._handle_game_over(confirmar)
            elif modo is GameMode.HIGH_SCORES:
                self._handle_simple_screen(confirmar)

            self._draw()

        logger.info("Encerrando...")

    def _draw(self) -> None:
        """Escolhe e desenha a tela do estado atual."""
        assert self._renderer is not None
        s = self.state.snapshot()
        modo = s.mode

        if modo in (GameMode.MENU, GameMode.SETTINGS):
            self._renderer.draw_menu(self._active_menu, s)
        elif modo in (GameMode.PLAYING, GameMode.PAUSED):
            self._renderer.draw_game(self.engine, s)
        elif modo is GameMode.GAME_OVER:
            self._renderer.draw_game(self.engine, s)
            self._renderer.draw_game_over(s)
        elif modo is GameMode.HIGH_SCORES:
            self._renderer.draw_high_scores(self.scoreboard, s)

        self._renderer.flip()


    def shutdown(self) -> None:
        """Encerra threads e libera todo o hardware, na ordem certa."""
        self.state.shutdown.set()


        for thread in self._threads:
            thread.join(timeout=1.5)
            if thread.is_alive():
                logger.warning("Thread %s não encerrou a tempo.", thread.name)


        try:
            self.displays.blank()
        except Exception:
            pass
        for comp in self._components:
            try:
                comp.close()
            except Exception as exc:
                logger.debug("Erro fechando %s: %s", comp.name, exc)

        if self._renderer is not None:
            try:
                self._renderer.close()
            except Exception:
                pass
        logger.info("Tudo encerrado. Até a próxima.")


def parse_args() -> argparse.Namespace:
    """Argumentos de linha de comando."""
    p = argparse.ArgumentParser(description="Snake Pi — Freenove Projects Board")
    p.add_argument("--sim", action="store_true",
                   help="roda sem hardware nenhum (para testar no PC)")
    p.add_argument("--windowed", action="store_true",
                   help="abre em janela em vez de tela cheia")
    p.add_argument("--log", default=config.LOG_LEVEL,
                   help="nível de log: DEBUG, INFO, WARNING, ERROR")
    return p.parse_args()


def main() -> int:
    """Entrada do programa."""
    args = parse_args()
    setup_logging(args.log, config.LOG_FILE)

    if args.windowed:
        config.FULLSCREEN = False

    simulate = args.sim or config.FORCE_SIMULATION
    app = SnakePi(simulate=simulate)


    def _sinal(signum, _frame):
        logger.info("Sinal %s recebido; encerrando.", signum)
        app.state.request_shutdown()

    signal.signal(signal.SIGINT, _sinal)
    signal.signal(signal.SIGTERM, _sinal)

    try:
        app.setup_hardware()
        app.start_threads()
        app.run()
    except Exception as exc:
        logger.exception("Erro fatal: %s", exc)
        return 1
    finally:
        app.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
