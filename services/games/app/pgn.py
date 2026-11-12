"""Small, pure helpers for turning platform data into Game rows."""

import io
import re
from dataclasses import dataclass

import chess.pgn

DRAW_CODES = {
    "agreed",
    "repetition",
    "stalemate",
    "insufficient",
    "50move",
    "timevsinsufficient",
}

_OPENING_URL = re.compile(r"/openings/([^?#]+)")


@dataclass(frozen=True)
class ParsedMoves:
    ply_count: int
    clocks: str | None  # tenths of a second after each ply, comma-separated


def parse_moves(pgn_text: str) -> ParsedMoves:
    """Count plies and extract the remaining clock after each ply from [%clk] comments."""
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        return ParsedMoves(ply_count=0, clocks=None)
    clocks: list[str] = []
    plies = 0
    for node in game.mainline():
        plies += 1
        clk = node.clock()
        if clk is not None:
            clocks.append(str(round(clk * 10)))
    return ParsedMoves(ply_count=plies, clocks=",".join(clocks) if clocks else None)


def parse_time_control(tc: str) -> tuple[int | None, int | None]:
    """'180+2' -> (180, 2); '600' -> (600, 0); daily '1/86400' -> (None, None)."""
    if not tc or "/" in tc:
        return None, None
    base, _, inc = tc.partition("+")
    try:
        return int(base), int(inc or 0)
    except ValueError:
        return None, None


def result_from_code(code: str) -> str:
    """Map a chess.com per-player result code to win / loss / draw."""
    if code == "win":
        return "win"
    if code in DRAW_CODES:
        return "draw"
    return "loss"


def opening_from_url(url: str | None) -> str | None:
    """'https://www.chess.com/openings/Sicilian-Defense-Najdorf' -> 'Sicilian Defense Najdorf'."""
    if not url:
        return None
    m = _OPENING_URL.search(url)
    if not m:
        return None
    return m.group(1).replace("-", " ").strip()[:255] or None


def pgn_header(pgn_text: str, name: str) -> str | None:
    m = re.search(rf'\[{re.escape(name)} "([^"]*)"\]', pgn_text)
    return m.group(1) if m else None
