from pathlib import Path

_arq = Path(__file__).resolve().parent.parent / "VERSION"
__version__ = _arq.read_text().strip() if _arq.exists() else "2.0.0"
