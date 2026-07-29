#!/usr/bin/env python3
"""
displays.py — Os três dispositivos ligados ao 74HC595.

Cada classe aqui NÃO fala com o hardware: ela apenas sabe converter o que
deve ser exibido em bytes. Quem envia os bytes é o ``DisplayManager``.
Essa separação é o que permite suportar as duas topologias possíveis da
placa (cascata ou barramento compartilhado) sem duplicar código.

    LEDMatrix8x8   -> 2 bytes por coluna (dados da coluna + seleção)
    FourDigitDisplay -> 2 bytes por dígito (segmentos + seleção)
    LEDBarGraph    -> 2 bytes fixos (10 LEDs)
"""
from __future__ import annotations


GLYPHS: dict[str, tuple[int, ...]] = {
    "blank":  (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    "smile":  (0x1C, 0x22, 0x51, 0x45, 0x45, 0x51, 0x22, 0x1C),
    "heart":  (0x0C, 0x1E, 0x3E, 0x7C, 0x7C, 0x3E, 0x1E, 0x0C),
    "fruit":  (0x18, 0x3C, 0x7E, 0xFF, 0xFF, 0x7E, 0x3C, 0x18),
    "skull":  (0x3C, 0x42, 0xA5, 0x81, 0x81, 0xA5, 0x42, 0x3C),
    "arrow":  (0x18, 0x18, 0x18, 0xFF, 0x7E, 0x3C, 0x18, 0x00),
    "snake":  (0x00, 0x3C, 0x24, 0x27, 0x21, 0x3D, 0x05, 0x07),
    "check":  (0x00, 0x02, 0x04, 0x08, 0x50, 0x20, 0x10, 0x00),
}


class LEDMatrix8x8:
    """
    Matriz 8x8 multiplexada por coluna.

    O 74HC595 não consegue acender as 64 posições ao mesmo tempo: acende
    uma coluna por vez, muito rápido, e a persistência da visão faz o olho
    ver a figura inteira. Por isso a classe mantém um cursor de coluna e
    devolve um par de bytes a cada chamada de ``next_frame()``.
    """

    N_COLS = 8

    def __init__(self) -> None:
        self.pattern: tuple[int, ...] = GLYPHS["blank"]
        self._col: int = 0

    def set_glyph(self, nome: str) -> None:
        """Troca a figura exibida pelo nome (ver ``GLYPHS``)."""
        self.pattern = GLYPHS.get(nome, GLYPHS["blank"])

    def set_pattern(self, padrao: tuple[int, ...]) -> None:
        """Define um padrão arbitrário de 8 bytes."""
        if len(padrao) == 8:
            self.pattern = tuple(padrao)

    def next_frame(self) -> tuple[int, int]:
        """
        Devolve (dados_da_coluna, seleção_da_coluna) e avança o cursor.

        A seleção é ativa em nível baixo (~), como no exemplo oficial da
        Freenove: o bit zerado é a coluna que recebe corrente.
        """
        dados = self.pattern[self._col]
        selecao = ~(0x80 >> self._col) & 0xFF
        self._col = (self._col + 1) % self.N_COLS
        return dados, selecao

    def blank_frame(self) -> tuple[int, int]:
        """Quadro apagado, usado quando outro dispositivo tem o barramento."""
        return 0x00, 0xFF


SEGMENTS: tuple[int, ...] = (
    0xC0, 0xF9, 0xA4, 0xB0, 0x99, 0x92, 0x82, 0xF8,
    0x80, 0x90,
    0x88, 0x83, 0xC6, 0xA1, 0x86, 0x8E,
)
SEG_BLANK: int = 0xFF
SEG_DASH: int = 0xBF


class FourDigitDisplay:
    """
    Display de 4 dígitos multiplexado.

    Mesmo princípio da matriz: um dígito aceso por vez, alternando rápido.
    Guarda o texto já convertido em 4 bytes de segmento para não refazer a
    conversão a cada ciclo de multiplexação (que roda centenas de vezes
    por segundo).
    """

    N_DIGITS = 4

    def __init__(self) -> None:
        self._segments: list[int] = [SEG_BLANK] * self.N_DIGITS
        self._digit: int = 0

    def set_number(self, valor: int) -> None:
        """
        Exibe um inteiro alinhado à direita, sem zeros à esquerda.

        Valores acima de 9999 mostram '----', porque quatro dígitos não
        comportam mais que isso e exibir os dígitos errados seria pior do
        que avisar que estourou.
        """
        if valor < 0 or valor > 9999:
            self._segments = [SEG_DASH] * self.N_DIGITS
            return
        texto = str(valor).rjust(self.N_DIGITS)
        self._segments = [SEG_BLANK if ch == " " else SEGMENTS[int(ch)]
                          for ch in texto]

    def set_raw(self, segmentos: list[int]) -> None:
        """Define diretamente os 4 bytes de segmento."""
        if len(segmentos) == self.N_DIGITS:
            self._segments = list(segmentos)

    def clear(self) -> None:
        """Apaga os quatro dígitos."""
        self._segments = [SEG_BLANK] * self.N_DIGITS

    def next_frame(self) -> tuple[int, int]:
        """
        Devolve (seleção_do_dígito, byte_dos_segmentos) e avança o cursor.

        A ordem dos bytes segue o código da Freenove: a seleção do dígito é
        deslocada PRIMEIRO, os segmentos DEPOIS. Inverter isso manda os
        segmentos para o registrador de seleção e embaralha tudo.
        """
        seg = self._segments[self._digit]
        selecao = 0x01 << self._digit
        self._digit = (self._digit + 1) % self.N_DIGITS
        return selecao, seg

    def blank_frame(self) -> tuple[int, int]:
        """Quadro apagado (nenhum dígito habilitado)."""
        return 0x00, SEG_BLANK


class LEDBarGraph:
    """
    Barra de 10 LEDs indicando a velocidade atual.

    Não precisa de multiplexação: os 10 bits cabem em dois 74HC595 e ficam
    estáticos até a próxima atualização.
    """

    N_LEDS = 10

    def __init__(self) -> None:
        self._level: int = 0

    def set_level(self, acesos: int) -> None:
        """Acende os primeiros ``acesos`` LEDs (0 a 10)."""
        self._level = max(0, min(self.N_LEDS, int(acesos)))

    def set_fraction(self, fracao: float) -> None:
        """Acende proporcionalmente a uma fração de 0.0 a 1.0."""
        self.set_level(round(max(0.0, min(1.0, fracao)) * self.N_LEDS))

    @property
    def level(self) -> int:
        """Quantos LEDs estão acesos."""
        return self._level

    def next_frame(self) -> tuple[int, int]:
        """
        Devolve os dois bytes da barra.

        Os LEDs do bar graph são ativos em nível ALTO (um bit 1 acende),
        conforme o código de referência da Freenove. ``(1 << n) - 1`` liga
        os n primeiros bits a partir do LSB.
        """
        valor = ((1 << self._level) - 1) & 0x3FF
        return (valor >> 8) & 0xFF, valor & 0xFF

    def blank_frame(self) -> tuple[int, int]:
        """Quadro apagado (tudo em 0)."""
        return 0x00, 0x00
