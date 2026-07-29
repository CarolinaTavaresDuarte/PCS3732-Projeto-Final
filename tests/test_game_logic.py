#!/usr/bin/env python3
"""
test_game_logic.py — Testes da lógica pura do jogo.

Rodam em qualquer máquina, sem Raspberry Pi, sem GPIO e sem monitor —
essa é justamente a vantagem de manter ``game/`` independente do hardware.

    python3 -m pytest tests/ -v        (ou)      python3 tests/test_game_logic.py
"""
from __future__ import annotations

import pathlib
import random
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import config
from game.board import Board
from game.engine import GameEngine
from game.fruit import Fruit, FruitKind, spawn_fruit
from game.menu import MenuAction, build_main_menu
from game.score import ScoreBoard
from game.snake import Direction, Snake
from game.state import GameMode, GameState, SoundEvent
from hardware.displays import (SEGMENTS, FourDigitDisplay, LEDBarGraph,
                               LEDMatrix8x8)


def _scoreboard() -> ScoreBoard:
    """Placar apontando para um arquivo temporário descartável."""
    return ScoreBoard(pathlib.Path(tempfile.mkdtemp()) / "hs.json")


class TestSnake(unittest.TestCase):
    def test_comprimento_e_posicao_inicial(self):
        s = Snake((5, 5), Direction.RIGHT, initial_length=3)
        self.assertEqual(s.head, (5, 5))
        self.assertEqual(len(s), 3)

        self.assertEqual(s.body, ((5, 5), (4, 5), (3, 5)))

    def test_movimento(self):
        s = Snake((5, 5), Direction.RIGHT)
        s.move()
        self.assertEqual(s.head, (6, 5))

    def test_nao_vira_180_graus(self):
        s = Snake((5, 5), Direction.RIGHT)
        s.turn(Direction.LEFT)
        s.move()
        self.assertEqual(s.head, (6, 5), "não pode inverter em cima de si")

    def test_crescimento_preserva_cauda(self):
        s = Snake((5, 5), Direction.RIGHT)
        n = len(s)
        s.grow()
        s.move()
        self.assertEqual(len(s), n + 1)

    def test_colisao_consigo_mesma(self):
        s = Snake((5, 5), Direction.RIGHT, initial_length=5)
        s.grow(3)
        for d in (Direction.UP, Direction.LEFT, Direction.DOWN, Direction.RIGHT):
            s.turn(d)
            s.move()
        self.assertTrue(s.collides_with_self())

    def test_wrap_nas_bordas(self):
        s = Snake((9, 5), Direction.RIGHT)
        s.move(wrap=(10, 10))
        self.assertEqual(s.head, (0, 5))


class TestBoard(unittest.TestCase):
    def test_quantidade_de_obstaculos(self):
        b = Board(20, 15)
        b.generate_obstacles(7, keep_clear=set(), rng=random.Random(0))
        self.assertEqual(len(b.obstacles), 7)

    def test_obstaculos_respeitam_area_livre(self):
        b = Board(20, 15)
        livre = {(5, 5), (6, 5), (7, 5)}
        b.generate_obstacles(30, keep_clear=livre, rng=random.Random(0))
        self.assertTrue(livre.isdisjoint(b.obstacles))

    def test_parede_mata_ou_atravessa(self):
        mata = Board(10, 10, wall_kills=True)
        self.assertTrue(mata.is_lethal((-1, 5)))
        self.assertIsNone(mata.wrap)

        atravessa = Board(10, 10, wall_kills=False)
        self.assertFalse(atravessa.is_lethal((-1, 5)))
        self.assertEqual(atravessa.wrap, (10, 10))


class TestFruit(unittest.TestCase):
    def test_nasce_em_celula_livre(self):
        ocupado = {(c, r) for r in range(3) for c in range(3)} - {(2, 2)}
        f = spawn_fruit(3, 3, ocupado)
        self.assertEqual(f.position, (2, 2))

    def test_sem_espaco_devolve_none(self):
        cheio = {(c, r) for r in range(3) for c in range(3)}
        self.assertIsNone(spawn_fruit(3, 3, cheio))

    def test_expiracao(self):
        normal = Fruit((0, 0), FruitKind.NORMAL, ttl=None)
        self.assertFalse(normal.expired)
        vencida = Fruit((0, 0), FruitKind.SPECIAL, spawned_at=0.0, ttl=0.001)
        self.assertTrue(vencida.expired)


class TestScoreBoard(unittest.TestCase):
    def test_pontuacao_e_recorde(self):
        sb = _scoreboard()
        sb.add(30)
        self.assertEqual(sb.current, 30)
        self.assertTrue(sb.is_new_record())

    def test_persistencia(self):
        sb = _scoreboard()
        sb.add(120)
        sb.submit(3, "Normal")
        recarregado = ScoreBoard(sb.path)
        self.assertEqual(recarregado.best, 120)

    def test_ranking_ordenado_e_limitado(self):
        sb = _scoreboard()
        sb.max_entries = 3
        for pontos in (10, 50, 30, 90, 20):
            sb.reset()
            sb.add(pontos)
            sb.submit(1, "Normal")
        self.assertEqual([e.score for e in sb.entries], [90, 50, 30])

    def test_arquivo_corrompido_nao_quebra(self):
        sb = _scoreboard()
        sb.path.write_text("{ isso nao e json valido", encoding="utf-8")
        recarregado = ScoreBoard(sb.path)
        self.assertEqual(recarregado.entries, [])


class TestEngine(unittest.TestCase):
    def test_morre_na_parede(self):
        e = GameEngine(_scoreboard(), rng=random.Random(1))
        e.reset(config.Difficulty.NORMAL)
        t = 0.0
        for _ in range(500):
            t += 0.05
            if e.update(now=t).game_over:
                break
        self.assertTrue(e.game_over)

    def test_easy_atravessa_parede(self):
        e = GameEngine(_scoreboard(), rng=random.Random(1))
        e.reset(config.Difficulty.EASY)
        t = 0.0
        for _ in range(60):
            t += 0.05
            e.update(now=t)
        self.assertFalse(e.game_over, "no modo Easy a parede não mata")

    def test_comer_pontua_e_cresce(self):
        sb = _scoreboard()
        e = GameEngine(sb, rng=random.Random(1))
        e.reset(config.Difficulty.NORMAL)
        c, r = e.snake.head
        e.fruit = Fruit(position=(c + 1, r))
        t = 0.0
        for _ in range(20):
            t += 0.05
            if e.update(now=t).ate_fruit:
                break
        self.assertEqual(sb.current, config.POINTS_PER_FRUIT)
        t += 0.2
        e.update(now=t)
        self.assertEqual(len(e.snake), 4)

    def test_potenciometro_altera_velocidade(self):
        e = GameEngine(_scoreboard())
        e.reset()
        e.set_speed_multiplier(0.0)
        lento = e.move_interval
        e.set_speed_multiplier(1.0)
        rapido = e.move_interval
        self.assertLess(rapido, lento)

    def test_velocidade_normalizada_no_intervalo(self):
        e = GameEngine(_scoreboard())
        e.reset()
        for v in (0.0, 0.5, 1.0):
            e.set_speed_multiplier(v)
            self.assertGreaterEqual(e.speed_fraction, 0.0)
            self.assertLessEqual(e.speed_fraction, 1.0)

    def test_dificuldades_tem_velocidades_distintas(self):
        e = GameEngine(_scoreboard())
        intervalos = []
        for d in config.Difficulty:
            e.reset(d)
            e.set_speed_multiplier(0.5)
            intervalos.append(e.move_interval)
        self.assertEqual(len(set(intervalos)), 3)


class TestMenu(unittest.TestCase):
    def test_navegacao_circular(self):
        m = build_main_menu()
        self.assertEqual(m.selected.label, "Start Game")
        m.move(-1, force=True)
        self.assertEqual(m.select(), MenuAction.QUIT)

    def test_repeticao_temporizada(self):
        m = build_main_menu()
        self.assertTrue(m.move(1, force=True))
        self.assertFalse(m.move(1), "deve bloquear repetição imediata")


class TestState(unittest.TestCase):
    def test_snapshot_reflete_escrita(self):
        gs = GameState()
        gs.update_game(score=42, level=3)
        s = gs.snapshot()
        self.assertEqual((s.score, s.level), (42, 3))

    def test_fila_de_som_nao_bloqueia_quando_cheia(self):
        gs = GameState()
        for _ in range(100):
            gs.play_sound(SoundEvent.FRUIT)
        self.assertLessEqual(gs.sound_queue.qsize(), 32)

    def test_shutdown(self):
        gs = GameState()
        gs.request_shutdown()
        self.assertTrue(gs.shutdown.is_set())
        self.assertIs(gs.mode, GameMode.QUIT)


class TestDisplays(unittest.TestCase):
    def test_matriz_percorre_8_colunas(self):
        m = LEDMatrix8x8()
        m.set_glyph("smile")
        quadros = [m.next_frame() for _ in range(8)]
        self.assertEqual(len({q[1] for q in quadros}), 8)

    def test_display4_alinha_a_direita(self):
        d = FourDigitDisplay()
        d.set_number(42)

        segs = [d.next_frame()[1] for _ in range(4)]
        self.assertEqual(segs[2], SEGMENTS[4])
        self.assertEqual(segs[3], SEGMENTS[2])

    def test_display4_selecao_de_digito_ativa_alto(self):

        d = FourDigitDisplay()
        d.set_number(1234)
        selecoes = [d.next_frame()[0] for _ in range(4)]
        self.assertEqual(selecoes, [0x01, 0x02, 0x04, 0x08])

    def test_display4_estouro(self):
        d = FourDigitDisplay()
        d.set_number(12345)
        self.assertEqual(d.next_frame()[1], 0xBF, "deve mostrar traços")

    def test_bargraph_proporcional(self):
        b = LEDBarGraph()
        b.set_fraction(0.5)
        self.assertEqual(b.level, 5)
        b.set_fraction(3.0)
        self.assertEqual(b.level, 10, "deve saturar em 10")

    def test_bargraph_vazio_apaga_tudo(self):

        b = LEDBarGraph()
        b.set_level(0)
        hi, lo = b.next_frame()
        self.assertEqual((hi, lo), (0x00, 0x00),
                         "nível 0 tem de apagar tudo (LEDs ativo-alto)")

    def test_bargraph_polaridade_ativo_alto(self):

        b = LEDBarGraph()
        b.set_level(6)
        hi, lo = b.next_frame()
        valor = (hi << 8) | lo
        self.assertEqual(valor, 0x3F)


if __name__ == "__main__":
    unittest.main(verbosity=2)
