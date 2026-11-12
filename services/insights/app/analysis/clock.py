"""Clock profile: when and why the player runs short of time, and what the clock costs.

Research: docs/research/clock-time-trouble.md, clock-flag-losses.md, experiments/e3.
Definitions: docs/definitions.md.
"""

from dataclasses import dataclass

from app.analysis.base import FindingDraft, by_category
from app.analysis.games import GameRecord
from app.analysis.stats import (
    MIN_OUTCOME_GROUP,
    cluster_bootstrap,
    median,
    pct,
    quantiles,
    to_elo,
    wilson,
)

TROUBLE = 0.10  # clock below 10% of T_est
SCRAMBLE = 0.03
MIN_MOVES_AFTER = 5  # the player still makes at least 5 more moves (not just a mating finish)
OPENING_MOVES = range(2, 13)  # own moves 2-12
SPIKE_FACTOR = 4.0  # a think of 4x the player's usual time
PACE_MOVES = (10, 20, 30, 40)
CAUSE_TEXT = {
    "opening": "time spent in the opening (moves 2-12)",
    "spikes": "single long thinks (4x your usual time or more)",
    "drain": "a steady drain, every move a little slow",
}
EARLY_ESTIMATE_BELOW = 100  # games


@dataclass
class ClockGame:
    game: GameRecord
    n_moves: int
    entry_move: int | None  # first own move started below 10% (with 5+ moves to go)
    scramble: bool
    self_inflicted: bool | None


def _first_below(g: GameRecord, share: float, n_moves: int) -> int | None:
    limit = share * g.t_est * 10
    for k in range(2, n_moves - MIN_MOVES_AFTER + 1):
        if g.clock_before(k) < limit:
            return k
    return None


def analyse_clock(g: GameRecord) -> ClockGame | None:
    own = g.own_clocks
    if not g.t_est or len(own) < 10:
        return None
    n = len(own)
    entry = _first_below(g, TROUBLE, n)
    self_inflicted = None
    if entry is not None:
        self_inflicted = g.opponent_clock_before(entry) > g.clock_before(entry)
    return ClockGame(g, n, entry, _first_below(g, SCRAMBLE, n) is not None, self_inflicted)


def _rate(k: int, n: int) -> dict:
    lo, hi = wilson(k, n)
    return {"count": k, "n": n, "rate": (k / n) if n else None, "ci": [lo, hi]}


def _time_sinks(entries: list[ClockGame], calm: list[ClockGame], usual: float) -> dict:
    """Where the time went before time trouble: opening, single long thinks or steady drain."""

    def shares(cg: ClockGame, upto: int) -> dict[str, float] | None:
        spent = {"opening": 0.0, "spikes": 0.0, "drain": 0.0}
        for k in range(2, min(upto, cg.n_moves + 1)):
            t = max(cg.game.time_spent(k), 0.0)
            if k in OPENING_MOVES:
                spent["opening"] += t
            elif usual > 0 and t >= SPIKE_FACTOR * usual:
                spent["spikes"] += t
            else:
                spent["drain"] += t
        total = sum(spent.values())
        return {k: v / total for k, v in spent.items()} if total > 0 else None

    onset = int(median([e.entry_move for e in entries]) or 30)
    entry_shares = [s for e in entries if (s := shares(e, e.entry_move))]
    calm_shares = [s for c in calm if (s := shares(c, onset))]
    if not entry_shares or not calm_shares:
        return {}

    def avg(rows: list[dict[str, float]]) -> dict[str, float]:
        return {k: sum(r[k] for r in rows) / len(rows) for k in ("opening", "spikes", "drain")}

    calm_avg = avg(calm_shares)
    dominant = {"opening": 0, "spikes": 0, "drain": 0}
    for s in entry_shares:
        cause = max(s, key=lambda k: s[k] - calm_avg[k])
        dominant[cause] += 1
    return {
        "entry_games": len(entry_shares),
        "calm_games": len(calm_shares),
        "main_cause_share": {k: v / len(entry_shares) for k, v in dominant.items()},
        "entry_profile": avg(entry_shares),
        "calm_profile": calm_avg,
    }


def _pace(games: list[ClockGame]) -> dict:
    out: dict[str, dict[str, float | None]] = {}
    for label, result in (("wins", "win"), ("losses", "loss")):
        out[label] = {}
        for k in PACE_MOVES:
            fractions = [
                cg.game.own_clocks[k - 1] / (cg.game.t_est * 10)
                for cg in games
                if cg.game.result == result and cg.n_moves >= k
            ]
            out[label][str(k)] = median(fractions) if len(fractions) >= 10 else None
    return out


def _flags(games: list[GameRecord]) -> dict:
    def bucket(m: int | None) -> str:
        if m is None:
            return "unknown"
        return "winning" if m >= 3 else "losing" if m <= -3 else "level"

    lost = {"winning": 0, "level": 0, "losing": 0, "unknown": 0}
    won = {"winning": 0, "level": 0, "losing": 0, "unknown": 0}
    for g in games:
        if g.lost_on_time:
            lost[bucket(g.final_material)] += 1
        elif g.won_on_time:
            won[bucket(g.final_material)] += 1
    net = (won["losing"] + 0.5 * won["level"]) - (lost["winning"] + 0.5 * lost["level"])
    return {
        "lost_on_time": lost,
        "won_on_time": won,
        "net_points_per_100": 100 * net / len(games) if games else 0.0,
    }


def clock_profile(games: list[GameRecord]) -> list[FindingDraft]:
    drafts: list[FindingDraft] = []
    for cat, gs in by_category(games).items():
        analysed = [cg for g in gs if (cg := analyse_clock(g))]
        if not analysed:
            continue
        entries = [cg for cg in analysed if cg.entry_move is not None]
        calm = [cg for cg in analysed if cg.entry_move is None]
        n = len(analysed)
        thinks = [
            cg.game.time_spent(k) for cg in analysed for k in range(13, min(cg.n_moves, 40) + 1)
        ]
        usual = median([t for t in thinks if t > 0]) or 0.0
        self_inf = [e for e in entries if e.self_inflicted]
        onset = [e.entry_move for e in entries]
        flags = _flags(gs)
        details = {
            "games_with_clock": n,
            "early_estimate": n < EARLY_ESTIMATE_BELOW,
            "entry": _rate(len(entries), n),
            "scramble": _rate(sum(cg.scramble for cg in analysed), n),
            "onset_move": {"median": median(onset), "iqr": quantiles(onset)},
            "self_inflicted": _rate(len(self_inf), len(entries)),
            "time_sinks": _time_sinks(entries, calm, usual) if len(entries) >= 30 else {},
            "pace": _pace(analysed),
            "flags": flags,
            "usual_think_seconds": usual,
        }
        drafts.append(
            FindingDraft(
                "clock_profile",
                cat,
                "profile",
                "profile",
                _profile_text(cat, details),
                sample_size=n,
                details=details,
            )
        )
        drafts.append(_trouble_score(cat, entries, calm))
    return drafts


def _profile_text(cat: str, d: dict):
    def text(_label: str) -> tuple[str, str]:
        label = cat.capitalize()
        entry, si = d["entry"], d["self_inflicted"]
        onset = d["onset_move"]["median"]
        lost = d["flags"]["lost_on_time"]
        title = f"{label}: time trouble in {entry['rate']:.0%} of games"
        if si["n"] and si["rate"] is not None and si["rate"] >= 0.6:
            title += ", mostly self-inflicted"
        parts = [
            f"Your clock drops below {TROUBLE:.0%} of the expected game time with at least "
            f"{MIN_MOVES_AFTER} moves still to play in {entry['count']} of "
            f"{entry['n']} {cat} games ({entry['rate']:.0%})."
        ]
        if onset is not None:
            parts.append(f"It usually starts around your move {onset:.0f}.")
        if si["n"]:
            parts.append(f"In {si['rate']:.0%} of those games your opponent had more time left.")
        causes = d["time_sinks"].get("main_cause_share")
        if causes:
            cause = max(causes, key=causes.get)
            parts.append(f"Main cause: {CAUSE_TEXT[cause]} ({causes[cause]:.0%} of cases).")
        if lost["winning"]:
            parts.append(
                f"At least {lost['winning']} games were lost on time while you were 3+ points "
                "of material up."
            )
        if d["early_estimate"]:
            parts.append("Early estimate: fewer than 100 games.")
        return title, " ".join(parts)

    return text


def _trouble_score(cat: str, entries: list[ClockGame], calm: list[ClockGame]) -> FindingDraft:
    c = cluster_bootstrap(
        [(e.game.id, e.game.residual) for e in entries],
        [(cg.game.id, cg.game.residual) for cg in calm],
    )

    def text(label: str) -> tuple[str, str]:
        name = cat.capitalize()
        if c is None or label == "not_enough_data":
            n_e = len(entries)
            return (
                f"{name}: not enough games yet to price time trouble",
                f"Needs at least {MIN_OUTCOME_GROUP} games with and without time trouble "
                f"(now {n_e} with, {len(calm)} without).",
            )
        diff = (
            f"you score {pct(c.mean_a)} points against expectation in games with time trouble "
            f"and {pct(c.mean_b)} without: {pct(c.effect)} points (about "
            f"{to_elo(c.effect):+.0f} Elo, 95% CI {pct(c.ci_low)} to {pct(c.ci_high)})"
        )
        caveat = (
            " Hard positions also eat time, so this is a link, not a proven cause. On your "
            "own games the link held after controlling for the position at move 20 "
            "(research E3)."
        )
        if label in ("finding", "exploratory"):
            verb = "costs" if c.effect < 0 else "goes with better results for"
            title = f"{name}: time trouble {verb} you about {abs(to_elo(c.effect)):.0f} Elo"
            if label == "exploratory":
                title += " (exploratory)"
            return title, f"In {cat}, {diff}.{caveat}"
        return (
            f"{name}: no score difference larger than {c.mde * 100:.0f} points from time trouble",
            f"In {cat}, {diff}. The data can only detect differences of about "
            f"{c.mde * 100:.0f} points or more.",
        )

    return FindingDraft(
        "time_trouble_score",
        cat,
        "contrast",
        "score",
        text,
        contrast=c,
        min_n=MIN_OUTCOME_GROUP,
        sample_size=len(entries) + len(calm),
    )
