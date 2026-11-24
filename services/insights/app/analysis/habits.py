"""More clock-only habits: warm-up, time of day, opening time, premoves and form over time.

Research: docs/research/shortlist.md (candidates 7, 8, 14 and 24), psych-session-warmup-fatigue.md,
psych-time-of-day.md, clock-opening-speed.md and clock-bullet-premoves.md. Definitions:
docs/definitions.md. Like every other card, results are measured against the player's own
smoothed rating, so a habit is not confused with stronger or weaker opponents.
"""

from collections import Counter

from app.analysis.after_loss import _by_session_game
from app.analysis.base import FindingDraft, by_category
from app.analysis.games import GameRecord
from app.analysis.stats import (
    MIN_OUTCOME_GROUP,
    MIN_RATE_GROUP,
    cluster_bootstrap,
    cluster_mean,
    median,
    pct,
    to_elo,
)

# ---- warm-up: the first game of a session --------------------------------------------------


def warm_up(games: list[GameRecord]) -> list[FindingDraft]:
    drafts = []
    for cat, gs in by_category(games).items():
        in_session = [g for g in gs if g.session_index > 0]
        first = [g for g in in_session if g.session_index == 1]
        later = [g for g in in_session if g.session_index > 1]
        c = cluster_bootstrap(
            [(g.session_id, g.residual) for g in first],
            [(g.session_id, g.residual) for g in later],
        )

        def text(label: str, cat=cat, c=c, first=first, later=later) -> tuple[str, str]:
            name = cat.capitalize()
            if c is None or label == "not_enough_data":
                return (
                    f"{name}: not enough sessions to check the first game",
                    f"Needs at least {MIN_OUTCOME_GROUP} first games and later games "
                    f"(now {len(first)} first, {len(later)} later).",
                )
            body = (
                f"In the first game of a session you score {pct(c.mean_a)} points against "
                f"expectation, in later games {pct(c.mean_b)}: {to_elo(c.effect):+.0f} Elo "
                f"(95% CI {to_elo(c.ci_low):+.0f} to {to_elo(c.ci_high):+.0f}; {c.n_a} first "
                f"games, {c.n_b} later games). A session starts after a break of more than "
                "30 minutes."
            )
            tag = " (exploratory)" if label == "exploratory" else ""
            if label in ("finding", "exploratory") and c.effect < 0:
                return (
                    f"{name}: your first game of a session costs you about "
                    f"{abs(to_elo(c.effect)):.0f} Elo{tag}",
                    body + " A short warm-up (a few puzzles or an unrated game) may help.",
                )
            if label in ("finding", "exploratory"):
                return f"{name}: you play your best in the first game of a session{tag}", body
            return (
                f"{name}: no warm-up effect larger than {to_elo(c.mde):.0f} Elo",
                body + f" Effects smaller than about {to_elo(c.mde):.0f} Elo cannot be seen yet.",
            )

        drafts.append(
            FindingDraft(
                "warm_up",
                cat,
                "contrast",
                "score",
                text,
                contrast=c,
                min_n=MIN_OUTCOME_GROUP,
                sample_size=len(in_session),
                details={"charts": {"by_session_game": _by_session_game(in_session)}},
            )
        )
    return drafts


# ---- time of day ---------------------------------------------------------------------------

WINDOWS = [
    ("night", "at night (0-6 h)", range(0, 6)),
    ("morning", "in the morning (6-12 h)", range(6, 12)),
    ("afternoon", "in the afternoon (12-18 h)", range(12, 18)),
    ("evening", "in the evening (18-24 h)", range(18, 24)),
]


def _hour(g: GameRecord) -> int:
    """Local hour the game started (the runner shifts times into the player's time zone)."""
    return (g.started_at or g.ended_at).hour


def time_of_day(games: list[GameRecord]) -> list[FindingDraft]:
    drafts = []
    for cat, gs in by_category(games).items():
        live = [g for g in gs if g.session_index > 0]
        windows = []
        for key, name, hours in WINDOWS:
            inside = [g for g in live if _hour(g) in hours]
            outside = [g for g in live if _hour(g) not in hours]
            m = cluster_mean([(g.session_id, g.residual) for g in inside])
            row = {"window": key, "name": name, "games": len(inside), "verdict": "not_enough_data"}
            if m is not None:
                row.update(elo=to_elo(m["mean"]), low=to_elo(m["low"]), high=to_elo(m["high"]))
            if len(inside) >= MIN_OUTCOME_GROUP and len(outside) >= MIN_OUTCOME_GROUP:
                c = cluster_bootstrap(
                    [(g.session_id, g.residual) for g in inside],
                    [(g.session_id, g.residual) for g in outside],
                )
                if c is not None:
                    # Four windows are tested at once: Bonferroni keeps the card honest.
                    p = min(1.0, c.p_value * len(WINDOWS))
                    row.update(vs_rest_elo=to_elo(c.effect), p_adjusted=p)
                    row["verdict"] = (
                        ("worse" if c.effect < 0 else "better") if p <= 0.05 else "no_difference"
                    )
            windows.append(row)
        hours = Counter(_hour(g) for g in live)
        details = {
            "windows": windows,
            "games_by_hour": [hours.get(h, 0) for h in range(24)],
        }

        def text(_label: str, cat=cat, windows=windows) -> tuple[str, str]:
            name = cat.capitalize()
            worse = [w for w in windows if w["verdict"] == "worse"]
            better = [w for w in windows if w["verdict"] == "better"]
            tested = [w for w in windows if w["verdict"] != "not_enough_data"]
            note = (
                " Times are in your browser's time zone at the moment you ran the analysis. Four "
                "windows are compared at once, so each needs stronger evidence (Bonferroni)."
            )
            if worse:
                w = min(worse, key=lambda w: w["vs_rest_elo"])
                return (
                    f"{name}: you play about {abs(w['vs_rest_elo']):.0f} Elo below your level "
                    f"{w['name'].split(' (')[0]}",
                    f"Games you start {w['name']} score {w['vs_rest_elo']:+.0f} Elo against your "
                    f"other {cat} games ({w['games']} games). Consider not playing rated games "
                    "then." + note,
                )
            if better:
                w = max(better, key=lambda w: w["vs_rest_elo"])
                return (
                    f"{name}: you play your best {w['name'].split(' (')[0]}",
                    f"Games you start {w['name']} score {w['vs_rest_elo']:+.0f} Elo against your "
                    f"other {cat} games ({w['games']} games)." + note,
                )
            if not tested:
                return (
                    f"{name}: not enough games to compare times of day",
                    f"Each time window needs at least {MIN_OUTCOME_GROUP} games." + note,
                )
            return (
                f"{name}: no time of day stands out",
                "None of the time windows with enough games differs clearly from the rest." + note,
            )

        drafts.append(
            FindingDraft(
                "time_of_day",
                cat,
                "profile",
                "profile",
                text,
                sample_size=len(live),
                details=details,
            )
        )
    return drafts


# ---- opening time ---------------------------------------------------------------------------

OPENING_MOVE = 12  # clock left after own move 12 (definitions: opening = own moves 2-12)
MAX_OPENINGS = 8
MIN_OPENING_GAMES = 20


FAMILY_WORDS = ("Opening", "Defense", "Defence", "Game", "Gambit", "Attack", "System", "Variation")
# Families so broad that the next named part is what tells games apart.
GENERIC_FAMILIES = (
    "Queens Pawn Opening",
    "Kings Pawn Opening",
    "Indian Game",
    "Kings Indian Attack",
)


def _family(opening: str | None) -> str | None:
    """chess.com opening name -> a family to group games by.

    'Caro Kann Defense Exchange Variation 3...cxd5 4.Nf3' -> 'Caro Kann Defense'
    'Queens Pawn Opening Chigorin Variation 2...Nf6 3.Bf4'
        -> 'Queens Pawn Opening Chigorin Variation' (a generic family: keep the next part)
    'Old Benoni Defense' -> 'Old Benoni Defense'
    """
    if not opening:
        return None
    words = []
    for w in opening.split(":")[0].split():
        if any(ch.isdigit() for ch in w) or "..." in w:
            break  # the move list starts
        words.append(w)
    if not words:
        return None
    cuts = [i + 1 for i, w in enumerate(words) if w in FAMILY_WORDS]
    if not cuts:
        return " ".join(words)
    first = " ".join(words[: cuts[0]])
    if first in GENERIC_FAMILIES and len(cuts) > 1:
        return " ".join(words[: cuts[1]])
    return first


def _clock_left(g: GameRecord, k: int) -> float | None:
    own = g.own_clocks
    if not g.t_est or len(own) < k:
        return None
    return own[k - 1] / (g.t_est * 10)


def opening_time(games: list[GameRecord]) -> list[FindingDraft]:
    drafts = []
    for cat, gs in by_category(games).items():
        rows = [(g, left) for g in gs if (left := _clock_left(g, OPENING_MOVE)) is not None]
        if len(rows) < MIN_RATE_GROUP:
            continue
        used_all = [max(0.0, 1 - left) for _, left in rows]
        by_family: dict[str, list[tuple[GameRecord, float]]] = {}
        for g, left in rows:
            if (fam := _family(g.opening)) is not None:
                by_family.setdefault(fam, []).append((g, max(0.0, 1 - left)))
        openings = []
        for fam, items in sorted(by_family.items(), key=lambda kv: -len(kv[1])):
            if len(items) < MIN_OPENING_GAMES or len(openings) >= MAX_OPENINGS:
                continue
            m = cluster_mean([(g.id, g.residual) for g, _ in items])
            openings.append(
                {
                    "opening": fam,
                    "games": len(items),
                    "used": median([u for _, u in items]),
                    "elo": to_elo(m["mean"]) if m else None,
                    "low": to_elo(m["low"]) if m else None,
                    "high": to_elo(m["high"]) if m else None,
                }
            )
        details = {"move": OPENING_MOVE, "used_median": median(used_all), "openings": openings}

        def text(_label: str, cat=cat, details=details) -> tuple[str, str]:
            name = cat.capitalize()
            used = details["used_median"] or 0.0
            ops = details["openings"]
            parts = [
                f"By your move {OPENING_MOVE} you have used {used:.0%} of the estimated game time "
                f"in a typical {cat} game."
            ]
            title = f"{name}: {used:.0%} of your clock is gone by move {OPENING_MOVE}"
            if ops:
                slow = max(ops, key=lambda o: o["used"] or 0)
                parts.append(
                    f"Most in the {slow['opening']} ({slow['used']:.0%}, {slow['games']} games)."
                )
                low = [o for o in ops if o["high"] is not None and o["high"] < 0]
                if low:
                    worst = min(low, key=lambda o: o["elo"])
                    parts.append(
                        f"You score clearly below your level in the {worst['opening']} "
                        f"({worst['elo']:+.0f} Elo, 95% CI {worst['low']:+.0f} to "
                        f"{worst['high']:+.0f}). Openings are compared one by one, so treat a "
                        "single result as a hint."
                    )
            return title, " ".join(parts)

        drafts.append(
            FindingDraft(
                "opening_time",
                cat,
                "profile",
                "profile",
                text,
                sample_size=len(rows),
                details=details,
            )
        )
    return drafts


# ---- premoves ------------------------------------------------------------------------------

PREMOVE_TENTHS = 1  # chess.com charges exactly 0.1 s for a premove
MIN_PREMOVES = 50
PREMOVE_SPIKE = 3.0  # 0.1 s must be this much more common than 0.2 s, or there are no premoves
CLOCK_BANDS = [
    (0.5, "over 50%"),
    (0.25, "25-50%"),
    (0.10, "10-25%"),
    (0.05, "5-10%"),
    (0.0, "under 5%"),
]


def premoves(games: list[GameRecord]) -> list[FindingDraft]:
    drafts = []
    for cat, gs in by_category(games).items():
        if cat not in ("bullet", "blitz"):
            continue
        moves = 0
        tenths = Counter()
        bands = {label: [0, 0] for _, label in CLOCK_BANDS}  # label -> [premoves, moves]
        wins_trouble, losses_trouble = [0, 0], [0, 0]
        for g in gs:
            own = g.own_clocks
            if not g.t_est or len(own) < 10:
                continue
            for k in range(2, len(own) + 1):
                spent = round(g.clock_before(k) + 10 * (g.increment_seconds or 0) - own[k - 1])
                moves += 1
                tenths[spent] += 1
                left = max(g.clock_before(k) / (g.t_est * 10), 0.0)
                label = next(lbl for lo, lbl in CLOCK_BANDS if left >= lo)
                bands[label][1] += 1
                is_pre = spent == PREMOVE_TENTHS
                bands[label][0] += is_pre
                if left < 0.10 and g.result in ("win", "loss"):
                    tgt = wins_trouble if g.result == "win" else losses_trouble
                    tgt[0] += is_pre
                    tgt[1] += 1
        pre = tenths[PREMOVE_TENTHS]
        if moves == 0 or pre < MIN_PREMOVES or pre < PREMOVE_SPIKE * max(tenths[2], 1):
            continue  # no premove spike at 0.1 s: this player does not premove

        def rate(x: list[int]) -> float | None:
            return x[0] / x[1] if x[1] else None

        details = {
            "moves": moves,
            "premoves": pre,
            "rate": pre / moves,
            "by_clock": [
                {"clock_left": label, "rate": rate(bands[label]), "moves": bands[label][1]}
                for _, label in CLOCK_BANDS
            ],
            "trouble_wins": rate(wins_trouble),
            "trouble_losses": rate(losses_trouble),
        }

        def text(_label: str, cat=cat, d=details) -> tuple[str, str]:
            name = cat.capitalize()
            low = next(b for b in d["by_clock"] if b["clock_left"] == "under 5%")
            parts = [
                f"{d['rate']:.0%} of your {cat} moves are premoves (moves that took exactly "
                "0.1 s, which is what chess.com charges for a premove)."
            ]
            if low["rate"] is not None:
                parts.append(f"With under 5% of your clock left it is {low['rate']:.0%}.")
            if d["trouble_wins"] is not None and d["trouble_losses"] is not None:
                parts.append(
                    f"In time trouble you premove {d['trouble_wins']:.0%} of moves in games you "
                    f"win and {d['trouble_losses']:.0%} in games you lose."
                )
            title = f"{name}: {d['rate']:.0%} of your moves are premoves"
            if low["rate"] is not None:
                title += f", {low['rate']:.0%} in a scramble"
            return title, " ".join(parts)

        drafts.append(
            FindingDraft(
                "premoves", cat, "profile", "profile", text, sample_size=moves, details=details
            )
        )
    return drafts


# ---- form over time ------------------------------------------------------------------------


def form(games: list[GameRecord]) -> list[FindingDraft]:
    drafts = []
    for cat, gs in by_category(games).items():
        months: dict[str, list[GameRecord]] = {}
        for g in gs:
            months.setdefault(g.ended_at.strftime("%Y-%m"), []).append(g)
        series = []
        for month in sorted(months):
            ms = months[month]
            ratings = [g.rating for g in ms if g.rating is not None]
            m = cluster_mean([(g.id, g.residual) for g in ms]) if len(ms) >= 10 else None
            series.append(
                {
                    "month": month,
                    "games": len(ms),
                    "rating": median(ratings),
                    "elo": to_elo(m["mean"]) if m else None,
                }
            )
        if len(series) < 2:
            continue
        rated = [s for s in series if s["rating"] is not None]
        details = {"months": series}

        def text(_label: str, cat=cat, series=series, rated=rated) -> tuple[str, str]:
            name = cat.capitalize()
            games_n = sum(s["games"] for s in series)
            if len(rated) < 2:
                return f"{name}: {games_n} games over {len(series)} months", ""
            a, b = rated[0], rated[-1]
            busiest = max(series, key=lambda s: s["games"])
            return (
                f"{name}: rating {a['rating']:.0f} → {b['rating']:.0f} since {a['month']}",
                f"{games_n} games over {len(series)} months; the busiest month was "
                f"{busiest['month']} with {busiest['games']} games. Ratings are monthly medians.",
            )

        drafts.append(
            FindingDraft(
                "form", cat, "profile", "profile", text, sample_size=len(gs), details=details
            )
        )
    return drafts
