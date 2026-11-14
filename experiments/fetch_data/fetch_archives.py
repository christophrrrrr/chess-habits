"""Download (serially, cached) and parse all games of the owner and the chosen players.

Run: python -I experiments/fetch_data/fetch_archives.py [--refresh]
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
from kexp.games import load_games  # noqa: E402
from kexp.paths import CHESSCOM  # noqa: E402


def players() -> list[str]:
    cfg = json.loads((CHESSCOM / "players.json").read_text(encoding="utf-8"))
    return [cfg["owner"]] + [p["username"] for p in cfg["players"]]


def main() -> None:
    refresh = "--refresh" in sys.argv
    for u in players():
        gs = load_games(u, refresh=refresh)
        c = collections.Counter((g["time_class"], g["rated"]) for g in gs)
        print(u, len(gs), dict(c), flush=True)


if __name__ == "__main__":
    main()
