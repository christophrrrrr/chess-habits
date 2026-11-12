"""Parse chess.com game JSON into compact per-game records (cached as gzipped JSON lines).

Clock facts used (verified on real data in docs/research/clock-and-time.md):
- [%clk] is the mover's remaining time after the move, increment already included.
- move time t_k = clk_{k-1} - clk_k + inc, with clk_0 = base.
"""
from __future__ import annotations

import gzip
import io
import json
from datetime import datetime, timezone

import chess
import chess.pgn

from . import chesscom
from .paths import CACHE

DRAW_CODES = {"agreed", "repetition", "stalemate", "insufficient", "50move", "timevsinsufficient"}
PARSE_VERSION = 3


def score_of(code: str) -> float:
    if code == "win":
        return 1.0
    if code in DRAW_CODES:
        return 0.5
    return 0.0


def parse_tc(tc: str) -> tuple[int, int] | None:
    if not tc or "/" in tc:
        return None  # daily
    if "+" in tc:
        b, i = tc.split("+")
        return int(b), int(i)
    return int(tc), 0


def _start_ts(headers) -> float | None:
    d, t = headers.get("UTCDate"), headers.get("UTCTime")
    if not d or not t or "?" in d:
        return None
    try:
        return datetime.strptime(f"{d} {t}", "%Y.%m.%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
    except ValueError:
        return None


def parse_game(g: dict, username: str) -> dict | None:
    if g.get("rules") != "chess" or not g.get("pgn"):
        return None
    u = username.lower()
    if g["white"]["username"].lower() == u:
        color, me, opp = "white", g["white"], g["black"]
    elif g["black"]["username"].lower() == u:
        color, me, opp = "black", g["black"], g["white"]
    else:
        return None
    tc = parse_tc(g.get("time_control", ""))
    pg = chess.pgn.read_game(io.StringIO(g["pgn"]))
    if pg is None:
        return None
    if pg.headers.get("SetUp") == "1" or pg.headers.get("FEN"):
        return None
    moves, clocks = [], []
    node = pg
    while node.variations:
        node = node.variations[0]
        moves.append(node.move.uci())
        clocks.append(node.clock())
    return {
        "url": g.get("url"),
        "end_time": g.get("end_time"),
        "start_ts": _start_ts(pg.headers),
        "time_class": g.get("time_class"),
        "time_control": g.get("time_control"),
        "base": tc[0] if tc else None,
        "inc": tc[1] if tc else None,
        "rated": bool(g.get("rated")),
        "color": color,
        "my_rating": me.get("rating"),
        "opp_rating": opp.get("rating"),
        "opp": opp.get("username"),
        "my_result": me.get("result"),
        "opp_result": opp.get("result"),
        "score": score_of(me.get("result")),
        "moves": moves,
        "clocks": clocks,
    }


def load_games(username: str, refresh: bool = False, fetch: bool = True) -> list[dict]:
    """Parsed standard-chess games of `username`, oldest first."""
    u = username.lower()
    path = CACHE / f"games-{u}-v{PARSE_VERSION}.jsonl.gz"
    if path.exists() and not refresh:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return [json.loads(line) for line in f]
    raw = chesscom.fetch_games(u) if fetch else []
    out = []
    for g in raw:
        try:
            rec = parse_game(g, u)
        except Exception as exc:  # malformed PGN: skip, but say so
            print(f"  skip {g.get('url')}: {exc}")
            continue
        if rec:
            out.append(rec)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for rec in out:
            f.write(json.dumps(rec) + "\n")
    return out


def t_est(g: dict) -> float | None:
    if g.get("base") is None:
        return None
    return g["base"] + 40 * g["inc"]


def own_plies(g: dict) -> list[int]:
    """Ply indices (0-based) of the player's own moves."""
    start = 0 if g["color"] == "white" else 1
    return list(range(start, len(g["moves"]), 2))


def move_times(g: dict) -> dict[int, tuple[float, float]]:
    """{ply: (clock_before, move_time)} for own moves with valid clocks. Own move 1 is dropped."""
    out = {}
    if g.get("base") is None:
        return out
    prev = float(g["base"])
    for k, ply in enumerate(own_plies(g)):
        clk = g["clocks"][ply]
        if clk is None:
            return out
        t = prev - clk + g["inc"]
        if k >= 1 and t >= 0:
            out[ply] = (prev, t)
        prev = clk
    return out


def board_at(g: dict, ply: int) -> chess.Board:
    """Board before ply `ply` is played."""
    b = chess.Board()
    for m in g["moves"][:ply]:
        b.push_uci(m)
    return b


def time_trouble_info(g: dict, frac: float = 0.10, min_moves_left: int = 5) -> dict:
    """Clock-only time-trouble facts per docs/research/clock-time-trouble.md."""
    T = t_est(g)
    own = own_plies(g)
    res = {"entered": False, "onset_move": None, "self_inflicted": None}
    if not T:
        return res
    clocks = g["clocks"]
    for k, ply in enumerate(own):
        c = clocks[ply]
        if c is None:
            return res
        if c < frac * T and len(own) - k - 1 >= min_moves_left:
            res["entered"] = True
            res["onset_move"] = k + 1
            opp_ply = ply - 1 if ply >= 1 else None
            opp_c = clocks[opp_ply] if opp_ply is not None and opp_ply >= 0 else float(g["base"])
            res["self_inflicted"] = bool(opp_c is not None and opp_c > c)
            return res
    return res
