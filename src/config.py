#!/usr/bin/env python3
"""
config.py — Fonte única de verdade do Snake Pi.

Toda a pinagem, endereços de barramento, canais de ADC e parâmetros
ajustáveis do jogo vivem AQUI. Nenhum outro módulo referencia número de
pino diretamente: se a sua placa for diferente, você altera só este arquivo.

A pinagem abaixo foi extraída do código oficial da Freenove para a
Projects Board (kit FNK0054), repositório
``Freenove_Projects_Kit_for_Raspberry_Pi``, pasta ``Python_GPIOZero_Code``.
Numeração BCM.

Barramentos:
    I2C-1  -> ADS7830 (ADC) @0x48, LCD1602 (PCF8574) @0x27 ou 0x3f
    SPI0   -> MFRC522 (RFID), CE0
    74HC595 -> DS=GPIO22, ST_CP=GPIO27, SH_CP=GPIO17 (compartilhado!)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


BASE_DIR: Path = Path(__file__).resolve().parent
ASSETS_DIR: Path = BASE_DIR / "assets"
HIGHSCORE_FILE: Path = BASE_DIR / "highscore.json"
LOG_FILE: Path = BASE_DIR / "snake_pi.log"


I2C_BUS: int = 1
ADC_I2C_ADDR: int = 0x48
LCD_I2C_ADDRS: tuple[int, ...] = (0x27, 0x3F)

SPI_BUS: int = 0
SPI_DEVICE: int = 0


ADC_CH_THERMISTOR: int = 0
ADC_CH_PHOTORESISTOR: int = 1
ADC_CH_POT1: int = 2
ADC_CH_POT2: int = 3
ADC_CH_POT3: int = 4
ADC_CH_JOYSTICK_X: int = 5
ADC_CH_JOYSTICK_Y: int = 6

ADC_CH_SPEED: int = ADC_CH_POT1


PIN_JOYSTICK_SW: int = 7


PIN_BTN_UP: int = 20
PIN_BTN_DOWN: int = 21
PIN_BTN_LEFT: int = 26
PIN_BTN_RIGHT: int = 16


PIN_BTN_RESTART: int | None = 24

PIN_BUZZER_ACTIVE: int = 12
PIN_BUZZER_PASSIVE: int = 4


PIN_595_DATA: int = 22
PIN_595_LATCH: int = 27
PIN_595_CLOCK: int = 17


class BusTopology(Enum):
    """
    Como matriz, bar graph e display de 4 dígitos estão ligados ao 74HC595.

    EXCLUSIVE: os três compartilham o mesmo barramento e são selecionados
        pelas chaves DIP. Só um funciona por vez; o DisplayManager escolhe
        qual mostrar conforme o estado do jogo. É o padrão, por ser o
        cenário seguro (funciona nos dois casos, só usa menos hardware).

    CASCADE: os três 74HC595 estão em série. Um único latch atualiza todos,
        bastando deslocar os bytes de todos eles. Ative se o teste 5 do
        ``diagnostico_placa.py`` mostrar que 6 bytes acendem mais que 2.
    """
    EXCLUSIVE = "exclusive"
    CASCADE = "cascade"


BUS_TOPOLOGY: BusTopology = BusTopology.EXCLUSIVE


CASCADE_ORDER: tuple[str, ...] = ("matrix", "display4", "bargraph")


EXCLUSIVE_FIXED_DEVICE: str | None = "display4"


EXCLUSIVE_BY_STATE: dict[str, str] = {
    "MENU": "matrix",
    "PLAYING": "display4",
    "PAUSED": "display4",
    "GAME_OVER": "matrix",
    "HIGH_SCORES": "display4",
    "SETTINGS": "bargraph",
}


JOY_CENTER: int = 128
JOY_DEADZONE: int = 30
JOY_INVERT_X: bool = False
JOY_INVERT_Y: bool = True
JOY_MENU_REPEAT_DELAY: float = 0.22


GRID_COLS: int = 24
GRID_ROWS: int = 18
CELL_SIZE: int = 32
HUD_HEIGHT: int = 72
FPS: int = 30

FULLSCREEN: bool = True

SCREEN_WIDTH: int = GRID_COLS * CELL_SIZE
SCREEN_HEIGHT: int = GRID_ROWS * CELL_SIZE + HUD_HEIGHT

COLOR_BG: tuple[int, int, int] = (13, 17, 23)
COLOR_GRID: tuple[int, int, int] = (22, 27, 34)
COLOR_SNAKE_HEAD: tuple[int, int, int] = (86, 211, 100)
COLOR_SNAKE_BODY: tuple[int, int, int] = (46, 160, 67)
COLOR_FRUIT: tuple[int, int, int] = (248, 81, 73)
COLOR_FRUIT_SPECIAL: tuple[int, int, int] = (240, 183, 47)
COLOR_OBSTACLE: tuple[int, int, int] = (110, 118, 129)
COLOR_TEXT: tuple[int, int, int] = (230, 237, 243)
COLOR_TEXT_DIM: tuple[int, int, int] = (125, 133, 144)
COLOR_ACCENT: tuple[int, int, int] = (88, 166, 255)
COLOR_HUD_BG: tuple[int, int, int] = (8, 11, 15)


POINTS_PER_FRUIT: int = 10
POINTS_PER_SPECIAL: int = 50
SPECIAL_FRUIT_EVERY: int = 5
SPECIAL_FRUIT_TTL: float = 12.0


FRUITS_PER_LEVEL: int = 5
MAX_HIGH_SCORES: int = 10


class Difficulty(Enum):
    """Modos de jogo, selecionáveis por cartão RFID ou pelo menu."""
    EASY = "Easy"
    NORMAL = "Normal"
    HARD = "Hard"


@dataclass(frozen=True)
class DifficultySpec:
    """Parâmetros que definem cada dificuldade."""
    base_move_interval: float
    min_move_interval: float
    speedup_per_level: float
    obstacles: int
    wall_kills: bool


DIFFICULTY_TABLE: dict[Difficulty, DifficultySpec] = {
    Difficulty.EASY:   DifficultySpec(0.190, 0.110, 0.010, 0, False),
    Difficulty.NORMAL: DifficultySpec(0.145, 0.075, 0.012, 3, True),
    Difficulty.HARD:   DifficultySpec(0.105, 0.048, 0.014, 8, True),
}

DEFAULT_DIFFICULTY: Difficulty = Difficulty.NORMAL


POT_SPEED_RANGE: float = 0.35


RFID_CARD_MAP: dict[int, Difficulty] = {


}


LCD_REFRESH_HZ: float = 4.0
RFID_POLL_HZ: float = 4.0
SENSOR_POLL_HZ: float = 10.0
INPUT_POLL_HZ: float = 60.0
DISPLAY_MUX_HZ: float = 420.0


ENABLE_RFID: bool = False

FORCE_SIMULATION: bool = False
LOG_LEVEL: str = "INFO"
ENABLE_KEYBOARD: bool = True


BLUE_LED_MODE: str = "clock"
PIN_BLUE_LED: int = 17
