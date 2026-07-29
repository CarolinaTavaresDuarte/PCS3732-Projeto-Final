#!/usr/bin/env python3
"""logger.py — Configuração central de log (console + arquivo)."""
from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logging(level: str = "INFO", log_file: Path | None = None) -> None:
    """
    Configura o logging da aplicação inteira.

    O console recebe mensagens curtas (para não poluir a tela durante o
    jogo) e o arquivo recebe tudo com timestamp, que é o que salva a vida
    quando algo falha na bancada e não dá para ficar olhando o terminal.
    """
    root = logging.getLogger("snake_pi")
    root.setLevel(logging.DEBUG)
    root.handlers.clear()

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(getattr(logging, level.upper(), logging.INFO))
    console.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    root.addHandler(console)

    if log_file is not None:
        try:
            fh = logging.FileHandler(log_file, mode="w", encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter(
                "%(asctime)s %(levelname)-8s %(name)-28s %(message)s"))
            root.addHandler(fh)
        except OSError:
            root.warning("Não consegui abrir o arquivo de log %s", log_file)
