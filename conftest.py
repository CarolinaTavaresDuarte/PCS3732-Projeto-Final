"""conftest.py — coloca ``src/`` no sys.path para os testes acharem o código."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))
