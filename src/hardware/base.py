#!/usr/bin/env python3
"""
base.py — Infraestrutura comum a todos os drivers de hardware.

Define ``HardwareComponent`` e o decorador ``@requires_hardware``, que
juntos implementam a degradação graciosa exigida pelo projeto: se um
periférico não inicializa (não está plugado, GPIO ocupado, I2C desligado)
ou falha no meio da partida (cartão RFID arrancado, cabo solto), as
chamadas àquele driver viram no-op registradas em log — em vez de
derrubar a aplicação inteira.

Na prática: dá para jogar com o LCD queimado, sem RFID e até sem
joystick (caindo no teclado), porque nenhuma dessas falhas propaga.
"""
from __future__ import annotations

import functools
import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger("snake_pi.hardware")

F = TypeVar("F", bound=Callable[..., Any])


class HardwareError(Exception):
    """Erro de inicialização ou comunicação com um periférico."""


class HardwareComponent:
    """
    Classe-base de todo periférico físico.

    Subclasses devem chamar ``super().__init__(nome)`` e marcar
    ``self.available = True`` só depois de inicializar com sucesso. Se a
    inicialização falhar, capture a exceção, registre o motivo e deixe
    ``available = False``.
    """

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.available: bool = False
        self._fail_count: int = 0

    def close(self) -> None:
        """Libera recursos. Sobrescreva quando necessário."""

    def __enter__(self) -> "HardwareComponent":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def __repr__(self) -> str:
        estado = "ok" if self.available else "indisponível"
        return f"<{self.__class__.__name__} '{self.name}' [{estado}]>"


def requires_hardware(default: Any = None, tolerate: int = 3) -> Callable[[F], F]:
    """
    Decorador: só executa o método se o periférico estiver disponível.

    Falhas pontuais de I/O (ruído no barramento, por exemplo) não devem
    condenar o periférico na primeira ocorrência — por isso toleramos
    ``tolerate`` erros consecutivos antes de marcá-lo como indisponível.
    Uma leitura bem-sucedida zera o contador.

    :param default: valor devolvido quando o periférico está fora.
    :param tolerate: erros consecutivos aceitos antes de desistir.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(self: HardwareComponent, *args: Any, **kwargs: Any) -> Any:
            if not self.available:
                return default
            try:
                resultado = func(self, *args, **kwargs)
                self._fail_count = 0
                return resultado
            except Exception as exc:
                self._fail_count += 1
                if self._fail_count >= tolerate:
                    self.available = False
                    logger.warning(
                        "%s.%s falhou %d vezes seguidas (%s); "
                        "desativando o periférico.",
                        self.name, func.__name__, self._fail_count, exc)
                else:
                    logger.debug("%s.%s falhou (%s), tentativa %d/%d",
                                 self.name, func.__name__, exc,
                                 self._fail_count, tolerate)
                return default
        return wrapper
    return decorator
