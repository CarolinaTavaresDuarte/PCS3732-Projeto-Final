#!/usr/bin/env python3
"""
renderer.py — Toda a renderização Pygame no monitor HDMI.

Camada puramente visual: recebe o motor do jogo e o estado, e desenha.
Não decide regra nenhuma. Isso mantém a lógica testável sem abrir janela
(ver ``tests/``) e permitiria trocar o Pygame por outra coisa sem tocar em
``game/``.
"""
from __future__ import annotations

import pygame

import config
from game.engine import GameEngine
from game.fruit import FruitKind
from game.menu import Menu
from game.score import ScoreBoard
from game.state import GameMode, StateSnapshot


class Renderer:
    """Desenha o jogo, os menus e o HUD."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Snake Pi — Laboratório de Processadores")

        flags = pygame.FULLSCREEN | pygame.SCALED if config.FULLSCREEN else 0
        self.screen = pygame.display.set_mode(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), flags)
        pygame.mouse.set_visible(False)

        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.Font(None, 74)
        self.font_mid = pygame.font.Font(None, 44)
        self.font_small = pygame.font.Font(None, 28)
        self.font_hud = pygame.font.Font(None, 36)

        self._grid_surface = self._build_grid()


    def _build_grid(self) -> pygame.Surface:
        """
        Pré-renderiza a grade de fundo uma única vez.

        Desenhar ~40 linhas a cada quadro é desperdício: a grade nunca
        muda. Guardamos numa Surface e só damos blit.
        """
        surf = pygame.Surface((config.SCREEN_WIDTH,
                               config.GRID_ROWS * config.CELL_SIZE))
        surf.fill(config.COLOR_BG)
        for c in range(config.GRID_COLS + 1):
            x = c * config.CELL_SIZE
            pygame.draw.line(surf, config.COLOR_GRID, (x, 0),
                             (x, surf.get_height()))
        for r in range(config.GRID_ROWS + 1):
            y = r * config.CELL_SIZE
            pygame.draw.line(surf, config.COLOR_GRID, (0, y),
                             (config.SCREEN_WIDTH, y))
        return surf

    def _cell_rect(self, col: int, row: int, margin: int = 2) -> pygame.Rect:
        """Retângulo em pixels de uma célula da grade."""
        return pygame.Rect(
            col * config.CELL_SIZE + margin,
            row * config.CELL_SIZE + config.HUD_HEIGHT + margin,
            config.CELL_SIZE - 2 * margin,
            config.CELL_SIZE - 2 * margin,
        )

    def _text(self, texto: str, fonte: pygame.font.Font,
              cor: tuple[int, int, int], centro: tuple[int, int]) -> None:
        """Desenha texto centralizado num ponto."""
        img = fonte.render(texto, True, cor)
        self.screen.blit(img, img.get_rect(center=centro))


    def _draw_hud(self, s: StateSnapshot) -> None:
        """Faixa superior com score, nível, dificuldade e velocidade."""
        pygame.draw.rect(self.screen, config.COLOR_HUD_BG,
                         (0, 0, config.SCREEN_WIDTH, config.HUD_HEIGHT))
        pygame.draw.line(self.screen, config.COLOR_GRID,
                         (0, config.HUD_HEIGHT),
                         (config.SCREEN_WIDTH, config.HUD_HEIGHT), 2)

        y = config.HUD_HEIGHT // 2
        self._text(f"SCORE {s.score}", self.font_hud, config.COLOR_TEXT, (110, y))
        self._text(f"NIVEL {s.level}", self.font_hud, config.COLOR_TEXT, (280, y))
        self._text(s.difficulty.value.upper(), self.font_hud,
                   config.COLOR_ACCENT, (440, y))
        self._text(f"REC {s.best_score}", self.font_small,
                   config.COLOR_TEXT_DIM, (580, y))


        bar_x, bar_w = config.SCREEN_WIDTH - 230, 200
        bar_y, bar_h = y - 9, 18
        pygame.draw.rect(self.screen, config.COLOR_GRID,
                         (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        preenchido = int(bar_w * s.speed_fraction)
        if preenchido > 0:
            pygame.draw.rect(self.screen, config.COLOR_SNAKE_HEAD,
                             (bar_x, bar_y, preenchido, bar_h), border_radius=4)
        self._text("VEL", self.font_small, config.COLOR_TEXT_DIM,
                   (bar_x - 28, y))

    def _draw_special_timer(self, engine: GameEngine) -> None:
        """
        Contagem regressiva da fruta especial, no alto da tela.

        Sem isso o jogador não tem como saber quanto tempo resta — e ela
        simplesmente sumia, o que parecia bug em vez de regra do jogo.
        """
        if engine.special is None:
            return
        restante = engine.special.remaining
        cor = (config.COLOR_FRUIT if restante <= 3.0
               else config.COLOR_FRUIT_SPECIAL)
        self._text(f"ESPECIAL  {restante:.0f}s", self.font_hud, cor,
                   (config.SCREEN_WIDTH // 2, config.HUD_HEIGHT + 26))


    def draw_game(self, engine: GameEngine, s: StateSnapshot) -> None:
        """Desenha o tabuleiro, a cobra, as frutas e os obstáculos."""
        self.screen.fill(config.COLOR_BG)
        self.screen.blit(self._grid_surface, (0, config.HUD_HEIGHT))

        for col, row in engine.board.obstacles:
            pygame.draw.rect(self.screen, config.COLOR_OBSTACLE,
                             self._cell_rect(col, row, 1), border_radius=3)

        if engine.fruit is not None:
            pygame.draw.ellipse(self.screen, config.COLOR_FRUIT,
                                self._cell_rect(*engine.fruit.position, margin=4))

        if engine.special is not None:
            rect = self._cell_rect(*engine.special.position, margin=3)

            restante = engine.special.remaining
            piscar = restante > 2.0 or int(restante * 6) % 2 == 0
            if piscar:
                pygame.draw.ellipse(self.screen, config.COLOR_FRUIT_SPECIAL, rect)
                pygame.draw.ellipse(self.screen, config.COLOR_TEXT, rect, 2)

        corpo = engine.snake.body
        for i, (col, row) in enumerate(corpo):
            cor = config.COLOR_SNAKE_HEAD if i == 0 else config.COLOR_SNAKE_BODY
            pygame.draw.rect(self.screen, cor, self._cell_rect(col, row),
                             border_radius=6)

        self._draw_hud(s)
        self._draw_special_timer(engine)

        if s.mode is GameMode.PAUSED:
            self._draw_overlay("PAUSA",
                               "Aperte o botao de pausa para continuar")

    def _draw_overlay(self, titulo: str, subtitulo: str = "") -> None:
        """Escurece a tela e escreve uma mensagem por cima."""
        veu = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        veu.set_alpha(190)
        veu.fill(config.COLOR_BG)
        self.screen.blit(veu, (0, 0))
        cx = config.SCREEN_WIDTH // 2
        cy = config.SCREEN_HEIGHT // 2
        self._text(titulo, self.font_big, config.COLOR_TEXT, (cx, cy - 30))
        if subtitulo:
            self._text(subtitulo, self.font_small, config.COLOR_TEXT_DIM,
                       (cx, cy + 30))

    def draw_menu(self, menu: Menu, s: StateSnapshot) -> None:
        """Desenha um menu com o cursor sobre o item selecionado."""
        self.screen.fill(config.COLOR_BG)
        cx = config.SCREEN_WIDTH // 2

        self._text(menu.title, self.font_big, config.COLOR_SNAKE_HEAD, (cx, 120))
        self._text("Laboratorio de Processadores  ·  Freenove Projects Board",
                   self.font_small, config.COLOR_TEXT_DIM, (cx, 175))

        y0 = 280
        for i, item in enumerate(menu.items):
            selecionado = (i == menu.index)
            cor = config.COLOR_ACCENT if selecionado else config.COLOR_TEXT
            rotulo = item.label
            if item.label == "Dificuldade":
                rotulo = f"Dificuldade: {s.difficulty.value}"
            prefixo = ">  " if selecionado else "   "
            self._text(prefixo + rotulo, self.font_mid, cor, (cx, y0 + i * 58))

        if menu.selected.hint:
            self._text(menu.selected.hint, self.font_small,
                       config.COLOR_TEXT_DIM, (cx, config.SCREEN_HEIGHT - 110))
        self._text("Joystick move  ·  botao do joystick confirma",
                   self.font_small, config.COLOR_TEXT_DIM,
                   (cx, config.SCREEN_HEIGHT - 60))

    def draw_game_over(self, s: StateSnapshot) -> None:
        """Tela de fim de partida."""
        cx = config.SCREEN_WIDTH // 2
        cy = config.SCREEN_HEIGHT // 2
        veu = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        veu.set_alpha(215)
        veu.fill(config.COLOR_BG)
        self.screen.blit(veu, (0, 0))

        self._text("GAME OVER", self.font_big, config.COLOR_FRUIT, (cx, cy - 110))
        if s.new_record:
            self._text("NOVO RECORDE!", self.font_mid,
                       config.COLOR_FRUIT_SPECIAL, (cx, cy - 40))
        self._text(f"Pontuacao: {s.score}", self.font_mid,
                   config.COLOR_TEXT, (cx, cy + 20))
        self._text(f"Nivel alcancado: {s.level}   ·   Modo: {s.difficulty.value}",
                   self.font_small, config.COLOR_TEXT_DIM, (cx, cy + 70))
        self._text("Botao REINICIAR joga de novo  ·  botao do joystick volta ao menu",
                   self.font_small, config.COLOR_TEXT_DIM, (cx, cy + 140))

    def draw_high_scores(self, board: ScoreBoard, s: StateSnapshot) -> None:
        """Tela de ranking."""
        self.screen.fill(config.COLOR_BG)
        cx = config.SCREEN_WIDTH // 2
        self._text("RANKING", self.font_big, config.COLOR_SNAKE_HEAD, (cx, 100))

        if not board.entries:
            self._text("Nenhuma partida registrada ainda.", self.font_mid,
                       config.COLOR_TEXT_DIM, (cx, 260))
        else:
            for i, e in enumerate(board.entries[:8]):
                y = 200 + i * 44
                cor = config.COLOR_FRUIT_SPECIAL if i == 0 else config.COLOR_TEXT
                self._text(f"{i + 1:2d}.", self.font_mid, config.COLOR_TEXT_DIM,
                           (cx - 300, y))
                self._text(f"{e.score:5d}", self.font_mid, cor, (cx - 180, y))
                self._text(e.difficulty, self.font_small,
                           config.COLOR_TEXT_DIM, (cx - 20, y))
                self._text(f"nivel {e.level}", self.font_small,
                           config.COLOR_TEXT_DIM, (cx + 120, y))
                self._text(e.date_str, self.font_small,
                           config.COLOR_TEXT_DIM, (cx + 300, y))

        self._text("Botao do joystick volta ao menu", self.font_small,
                   config.COLOR_TEXT_DIM, (cx, config.SCREEN_HEIGHT - 60))


    def flip(self) -> None:
        """Publica o quadro e segura o frame rate."""
        pygame.display.flip()
        self.clock.tick(config.FPS)

    def close(self) -> None:
        """Fecha a janela do Pygame."""
        pygame.quit()
