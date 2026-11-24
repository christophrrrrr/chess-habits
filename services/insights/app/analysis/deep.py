"""Analyses that need the deep pass from the player's browser: positions and Stockfish.

- critical_moments: in positions where only one or two moves hold, how often you find one, by
  the kind of move needed and by clock (docs/research/game-decision-points.md).
- endings: resignations, draws and time losses judged by the engine, not by material
  (docs/research/psych-resignation-and-draws.md, clock-flag-losses.md).
- opening_autopilot: time spent in positions you have reached many times before vs new ones
  (docs/research/clock-opening-speed.md, game-recurring-positions.md).

Every card states how many games had the deep pass; games without it are simply not counted.
"""

import math
from collections import Counter

from app.analysis.base import FindingDraft, by_category
from app.analysis.games import GameRecord
from app.analysis.stats import MIN_RATE_GROUP, median, rate_summary, to_elo

# ---- shared ------------------------------------------------------------------------------


def win_pct(cp: int) -> float:
    """Lichess win% for the side to move, 0-100 (lichess.org/page/accuracy)."""
    return 50 + 50 * (2 / (1 + math.exp(-0.00368208 * cp)) - 1)


# ---- critical moments ----------------------------------------------------------------------

CRITICAL_GAP = 10  # win% points between the best and the second-best move
ONLY_MOVE_GAP = 20
UNDECIDED = (10, 95)  # only positions that are not decided yet (best move's win%)
FOUND_WITHIN = 3  # the played move counts as found if it loses less than 3 win% points
MIN_LEGAL = 4  # 3 legal moves or fewer is not a decision
MIN_CELL = 20  # critical positions behind a breakdown row
CLOCK_BANDS = [(0.5, "over 50%"), (0.25, "25-50%"), (0.10, "10-25%"), (0.0, "under 10%")]
TYPE_NAMES = {
    "quiet": "Quiet move",
    "retreat": "Retreat",
    "capture": "Capture",
    "check": "Check",
    "pawn": "Pawn move",
    "king": "King move",
    "castle": "Castling",
}


def _decision_points(g: GameRecord) -> list[dict]:
    """The player's non-trivial critical positions in one game, with what happened."""
    out = []
    own = g.own_clocks
    for m in g.engine_moves or []:
        if m.get("s") is None or m.get("check") or m.get("recapture"):
            continue
        if m.get("legal", 0) < MIN_LEGAL:
            continue
        wb, ws, wp = win_pct(m["b"]), win_pct(m["s"]), win_pct(m["p"])
        if not (UNDECIDED[0] <= wb <= UNDECIDED[1]):
            continue
        gap = wb - ws
        k = m["k"]
        clock = None
        spent = None
        if g.t_est and k <= len(own):
            clock = g.clock_before(k) / (g.t_est * 10)
            spent = max(g.time_spent(k), 0.0)
        out.append(
            {
                "game": g.id,
                "k": k,
                "gap": gap,
                "critical": gap >= CRITICAL_GAP,
                "only": gap >= ONLY_MOVE_GAP,
                "found": wb - wp < FOUND_WITHIN,
                "type": m["type"],
                "purpose": "defend" if ws < 35 <= wb else "win" if wb >= 65 > ws else "other",
                "clock": clock,
                "spent": spent,
                "lost": max(0.0, wb - wp),
                "fen": m.get("fen"),
                "best": m["best"],
            }
        )
    return out


def _rate(rows: list[dict]) -> dict:
    return rate_summary(sum(r["found"] for r in rows), len(rows))


def _cell(name: str, rows: list[dict]) -> dict:
    s = _rate(rows)
    return {"name": name, "n": s["n"], "rate": s["rate"], "ci": s["ci"]}


def critical_moments(games: list[GameRecord]) -> list[FindingDraft]:
    drafts = []
    for cat, gs in by_category(games).items():
        analysed = [g for g in gs if g.engine_moves is not None]
        if not analysed:
            continue
        points = [p for g in analysed for p in _decision_points(g)]
        critical = [p for p in points if p["critical"]]
        calm = [p for p in points if not p["critical"]]
        thinks = [p["spent"] for p in points if p["spent"] is not None and p["spent"] > 0]
        usual = median(thinks) or 0.0

        def speed(p: dict, usual: float = usual) -> str | None:
            if p["spent"] is None or usual <= 0:
                return None
            r = p["spent"] / usual
            return "fast" if r < 0.5 else "slow" if r > 2 else "normal"

        by_type = [
            _cell(TYPE_NAMES[t], [p for p in critical if p["type"] == t]) for t in TYPE_NAMES
        ]
        by_clock = []
        for lo, label in CLOCK_BANDS:
            hi = next((b for b, _ in CLOCK_BANDS if b > lo), 10.0)
            rows = [p for p in critical if p["clock"] is not None and lo <= p["clock"] < hi]
            by_clock.append(_cell(f"{label} of the clock", rows))
        by_speed = [
            _cell(name, [p for p in critical if speed(p) == key])
            for key, name in (
                ("fast", "Under half your usual time"),
                ("normal", "Your usual time"),
                ("slow", "Over twice your usual time"),
            )
        ]
        by_purpose = [
            _cell("Only move to hold", [p for p in critical if p["purpose"] == "defend"]),
            _cell("Only move to win", [p for p in critical if p["purpose"] == "win"]),
        ]
        crit_think = median([p["spent"] for p in critical if p["spent"] is not None])
        calm_think = median([p["spent"] for p in calm if p["spent"] is not None])
        missed = sorted(
            (p for p in critical if not p["found"] and p["fen"]), key=lambda p: -p["lost"]
        )[:12]
        details = {
            "games": len(analysed),
            "positions": len(points),
            "critical": _rate(critical),
            "only_moves": _rate([p for p in critical if p["only"]]),
            "per_game": len(critical) / len(analysed),
            "by_type": [c for c in by_type if c["n"] >= MIN_CELL],
            "by_clock": [c for c in by_clock if c["n"] >= MIN_CELL],
            "by_speed": [c for c in by_speed if c["n"] >= MIN_CELL],
            "by_purpose": [c for c in by_purpose if c["n"] >= MIN_CELL],
            "think": {"critical": crit_think, "calm": calm_think, "usual": usual},
            "missed": [
                {
                    "game": p["game"],
                    "k": p["k"],
                    "fen": p["fen"],
                    "best": p["best"],
                    "lost": p["lost"],
                }
                for p in missed
            ],
        }

        def text(_label: str, cat=cat, d=details) -> tuple[str, str]:
            name = cat.capitalize()
            c = d["critical"]
            if c["n"] < MIN_RATE_GROUP:
                return (
                    f"{name}: not enough critical moments yet",
                    f"{c['n']} critical positions in {d['games']} analysed games; the card needs "
                    f"{MIN_RATE_GROUP}. Run the deep analysis on more games.",
                )
            parts = [
                f"In {d['games']} analysed {cat} games you faced {c['n']} critical positions "
                f"({d['per_game']:.1f} per game) where the second-best move already loses 10+ "
                f"win% points. You found a good move in {c['rate']:.0%} of them "
                f"(95% CI {c['ci'][0]:.0%}-{c['ci'][1]:.0%})."
            ]
            cells = d["by_type"] + d["by_clock"] + d["by_purpose"]
            if len(cells) >= 2:
                worst = min(cells, key=lambda x: x["rate"])
                parts.append(
                    f"Weakest: {worst['name'].lower()} ({worst['rate']:.0%} of {worst['n']})."
                )
            t = d["think"]
            if t["critical"] and t["calm"]:
                parts.append(
                    f"You think {t['critical']:.1f} s on critical moves and {t['calm']:.1f} s on "
                    "the others (medians)."
                )
            parts.append(
                "Recaptures, checks you must answer and positions with 3 legal moves or fewer "
                "are left out."
            )
            return (
                f"{name}: you find the key move in {c['rate']:.0%} of critical moments",
                " ".join(parts),
            )

        drafts.append(
            FindingDraft(
                "critical_moments",
                cat,
                "profile",
                "profile",
                text,
                sample_size=len(analysed),
                details=details,
            )
        )
    return drafts


# ---- endings: resignations, draws, time losses ----------------------------------------------

PREMATURE = 0.15  # expected score still left when resigning
WINNING_CP = 300  # about three pawns: a clearly winning position
DRAW_BETTER = 0.60


def _ending(g: GameRecord) -> str | None:
    t = (g.termination or "").lower()
    if "resignation" in t:
        return "resigned" if g.result == "loss" else "opponent_resigned"
    if "won on time" in t:
        return "lost_on_time" if g.result == "loss" else "won_on_time"
    if g.result == "draw" and "agreement" in t:
        return "agreed_draw"
    return None


def endings(games: list[GameRecord]) -> list[FindingDraft]:
    drafts = []
    for cat, gs in by_category(games).items():
        judged = [g for g in gs if g.final_cp is not None and _ending(g)]
        if not judged:
            continue
        by = {
            k: [g for g in judged if _ending(g) == k]
            for k in ("resigned", "opponent_resigned", "lost_on_time", "won_on_time", "agreed_draw")
        }
        # Expected score left: the player's when they resign, the opponent's when they do.
        mine = [win_pct(g.final_cp) / 100 for g in by["resigned"]]
        theirs = [1 - win_pct(g.final_cp) / 100 for g in by["opponent_resigned"]]
        premature = sum(e >= PREMATURE for e in mine)
        given = sum(mine)
        n_games = len(gs)
        flags_lost = Counter(
            "winning"
            if g.final_cp >= WINNING_CP
            else "losing"
            if g.final_cp <= -WINNING_CP
            else "level"
            for g in by["lost_on_time"]
        )
        flags_won = Counter(
            "winning"
            if g.final_cp >= WINNING_CP
            else "losing"
            if g.final_cp <= -WINNING_CP
            else "level"
            for g in by["won_on_time"]
        )
        draws_better = sum(win_pct(g.final_cp) / 100 >= DRAW_BETTER for g in by["agreed_draw"])
        details = {
            "games_judged": len(judged),
            "resignations": {
                "n": len(mine),
                "premature": rate_summary(premature, len(mine)),
                "premature_by_threshold": {
                    str(t): sum(e >= t for e in mine) for t in (0.10, 0.15, 0.25)
                },
                "points_per_100": 100 * given / n_games if n_games else 0.0,
                "median_left": median(mine),
            },
            "opponents": {
                "n": len(theirs),
                "premature": rate_summary(sum(e >= PREMATURE for e in theirs), len(theirs)),
                "median_left": median(theirs),
            },
            "lost_on_time": dict(flags_lost),
            "won_on_time": dict(flags_won),
            "agreed_draws": {"n": len(by["agreed_draw"]), "when_better": draws_better},
        }

        def text(_label: str, cat=cat, d=details) -> tuple[str, str]:
            name = cat.capitalize()
            r, o = d["resignations"], d["opponents"]
            parts = []
            title = f"{name}: how your games end, judged by the engine"
            if r["n"]:
                p = r["premature"]
                parts.append(
                    f"In {p['count']} of your {r['n']} resignations ({p['rate']:.0%}) you still "
                    f"had at least {PREMATURE:.0%} expected score left."
                )
                if o["n"]:
                    parts.append(
                        f"Your opponents did that in {o['premature']['rate']:.0%} of "
                        f"{o['n']} resignations."
                    )
                parts.append(
                    f"Resigning gave away about {r['points_per_100']:.1f} points per 100 games "
                    f"(≈ {to_elo(r['points_per_100'] / 100):.0f} Elo per game)."
                )
                if r["n"] >= MIN_RATE_GROUP:
                    title = f"{name}: {p['rate']:.0%} of your resignations came too early"
            lost = d["lost_on_time"].get("winning", 0)
            if lost:
                parts.append(
                    f"{lost} games were lost on time in a winning position (+{WINNING_CP // 100} "
                    "pawns or more by the engine)."
                )
            if d["agreed_draws"]["when_better"]:
                parts.append(
                    f"{d['agreed_draws']['when_better']} of {d['agreed_draws']['n']} agreed draws "
                    f"came when you had {DRAW_BETTER:.0%}+ expected score."
                )
            parts.append(
                f"Judged from {d['games_judged']} games with an engine evaluation of the final "
                "position; expected score uses the Lichess win% curve, which ignores the clock."
            )
            return title, " ".join(parts)

        drafts.append(
            FindingDraft(
                "endings", cat, "profile", "profile", text, sample_size=len(judged), details=details
            )
        )
    return drafts


# ---- opening autopilot --------------------------------------------------------------------

FAMILIAR = 3  # reached at least this often before the game: "you know this position"
AUTOPILOT_MOVES = 20


def opening_autopilot(games: list[GameRecord]) -> list[FindingDraft]:
    drafts = []
    for cat, gs in by_category(games).items():
        ordered = sorted((g for g in gs if g.position_keys and g.t_est), key=lambda g: g.ended_at)
        if len(ordered) < MIN_RATE_GROUP:
            continue
        seen: Counter[str] = Counter()
        familiar_t, new_t = [], []
        by_move: dict[int, dict[str, list[float]]] = {}
        exits, after_exit, before_exit = [], [], []
        for g in ordered:
            own = g.own_clocks
            exit_move = None
            for k, key in enumerate(g.position_keys, start=1):
                if k > len(own) or k > AUTOPILOT_MOVES:
                    break
                spent = max(g.time_spent(k), 0.0) / g.t_est  # share of the game's time
                fam = seen[key] >= FAMILIAR
                (familiar_t if fam else new_t).append(spent)
                by_move.setdefault(k, {"familiar": [], "new": []})[
                    "familiar" if fam else "new"
                ].append(spent)
                if exit_move is None and not fam:
                    exit_move = k
                    after_exit.extend(
                        max(g.time_spent(j), 0.0) / g.t_est
                        for j in range(k, min(k + 3, len(own) + 1))
                    )
                elif exit_move is None:
                    before_exit.append(spent)
            if exit_move is not None and exit_move > 1:
                exits.append(exit_move)
            seen.update(set(g.position_keys))
        details = {
            "games": len(ordered),
            "familiar_positions": len(familiar_t),
            "new_positions": len(new_t),
            "think_familiar": median(familiar_t),
            "think_new": median(new_t),
            "think_before_exit": median(before_exit),
            "think_after_exit": median(after_exit),
            "exit_move": median(exits),
            "by_move": [
                {
                    "move": k,
                    "familiar": median(v["familiar"]) if len(v["familiar"]) >= 10 else None,
                    "new": median(v["new"]) if len(v["new"]) >= 10 else None,
                }
                for k, v in sorted(by_move.items())
            ],
        }

        def text(_label: str, cat=cat, d=details) -> tuple[str, str]:
            name = cat.capitalize()
            f, n = d["think_familiar"], d["think_new"]
            if f is None or n is None or d["familiar_positions"] < MIN_RATE_GROUP:
                return (
                    f"{name}: not enough repeated positions yet",
                    f"Needs at least {MIN_RATE_GROUP} positions you had reached {FAMILIAR}+ "
                    "times before.",
                )
            ratio = n / f if f > 0 else None
            parts = [
                f"In positions you had reached {FAMILIAR}+ times before, you spend a median "
                f"{f:.1%} of the game time per move; in new positions {n:.1%}"
                + (f" ({ratio:.1f}× as much)." if ratio else ".")
            ]
            if d["exit_move"]:
                parts.append(f"You usually leave known ground at your move {d['exit_move']:.0f}.")
            if d["think_after_exit"] and d["think_before_exit"]:
                parts.append(
                    f"The first three moves after that take {d['think_after_exit']:.1%} each."
                )
            parts.append(
                "Positions are recognised exactly (same pieces, side to move, castling and en "
                "passant), counted over all your earlier games in this time control."
            )
            title = (
                f"{name}: you play known positions {ratio:.1f}× faster than new ones"
                if ratio and ratio >= 1.2
                else f"{name}: you take about as long in known positions as in new ones"
            )
            return title, " ".join(parts)

        drafts.append(
            FindingDraft(
                "opening_autopilot",
                cat,
                "profile",
                "profile",
                text,
                sample_size=len(ordered),
                details=details,
            )
        )
    return drafts
