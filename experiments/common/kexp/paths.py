"""Where downloaded data, caches and outputs live.

Everything downloaded or computed goes under CHESS_HABITS_EXP_DATA (default: experiments/data,
which is gitignored). Nothing in that folder is ever executed.
"""
from __future__ import annotations

import os
from pathlib import Path

EXP_ROOT = Path(__file__).resolve().parents[2]  # .../experiments
DATA = Path(os.environ.get("CHESS_HABITS_EXP_DATA", EXP_ROOT / "data")).resolve()
CHESSCOM = DATA / "chesscom"
CACHE = DATA / "cache"
OUT = DATA / "out"
STOCKFISH_DIR = DATA / "stockfish"

for _p in (CHESSCOM, CACHE, OUT, STOCKFISH_DIR):
    _p.mkdir(parents=True, exist_ok=True)


def stockfish_path() -> Path:
    env = os.environ.get("CHESS_HABITS_STOCKFISH")
    if env:
        return Path(env)
    hits = sorted(STOCKFISH_DIR.rglob("stockfish*.exe")) + sorted(
        p for p in STOCKFISH_DIR.rglob("stockfish*") if p.is_file() and os.access(p, os.X_OK) and p.suffix == ""
    )
    if not hits:
        raise FileNotFoundError(f"No Stockfish binary under {STOCKFISH_DIR}; set CHESS_HABITS_STOCKFISH")
    return hits[0]
