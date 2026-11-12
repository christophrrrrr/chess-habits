"""Turn games into per-move rows (position before the move, clock facts, cheap flags)."""
from __future__ import annotations

import chess

from .games import move_times, t_est

PIECE_VALUES = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}


def phase(board: chess.Board) -> str:
    """Simplified phase: endgame when <= 6 minor/major pieces remain in total;
    opening while fullmove <= 12; else middlegame."""
    pieces = sum(len(board.pieces(pt, c)) for pt in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)
                 for c in (chess.WHITE, chess.BLACK))
    if pieces <= 6:
        return "endgame"
    if board.fullmove_number <= 12:
        return "opening"
    return "middlegame"


def clock_band(c: float) -> str:
    """Lichess Insights clock bands (fraction of T_est before the move)."""
    if c >= 0.5:
        return ">=50%"
    if c >= 0.25:
        return "25-50%"
    if c >= 0.10:
        return "10-25%"
    if c >= 0.03:
        return "3-10%"
    return "<3%"


def material(board: chess.Board, color: bool) -> int:
    return sum(v * (len(board.pieces(pt, color)) - len(board.pieces(pt, not color))) for pt, v in PIECE_VALUES.items())


def own_move_rows(g: dict, ply_lo: int, ply_hi: int, min_clock_frac: float | None = None) -> list[dict]:
    """Rows for own moves with 0-based ply index in [ply_lo, ply_hi]. Includes the FEN before the move."""
    T = t_est(g)
    mt = move_times(g)
    rows = []
    board = chess.Board()
    me = chess.WHITE if g["color"] == "white" else chess.BLACK
    for ply, uci in enumerate(g["moves"]):
        if ply > ply_hi:
            break
        if ply >= ply_lo and board.turn == me and ply in mt:
            clk_before, t = mt[ply]
            c = clk_before / T if T else None
            if min_clock_frac is None or (c is not None and c >= min_clock_frac):
                last = board.peek() if board.move_stack else None
                rows.append({
                    "url": g["url"], "ply": ply, "move_no": ply // 2 + 1, "fen": board.fen(), "played": uci,
                    "t": t, "clk": clk_before, "c": c, "band": clock_band(c) if c is not None else None,
                    "phase": phase(board), "in_check": board.is_check(), "n_legal": board.legal_moves.count(),
                    "last_to": last.to_square if last else None,
                    "material": material(board, me),
                })
        board.push_uci(uci)
    return rows
