"""The analyses Kiebitz runs. Each one is computed per time control, because the same
behaviour means different things in bullet and in rapid.

Adding an analysis = writing one function and registering it in ANALYSES. New analyses
come from the research notes in docs/research/.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from app.analysis.games import GameRecord
from app.analysis.stats import Comparison, compare, pct

TIME_CLASSES = ("bullet", "blitz", "rapid", "classical")
TIME_TROUBLE_SHARE = 0.10  # below 10% of the starting time
LATE_SESSION_FROM = 6  # game 6+ of a session counts as "late"


@dataclass
class FindingDraft:
    analysis_key: str
    time_class: str
    title: str
    summary: str
    comparison: Comparison
    details: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Analysis:
    key: str
    name: str
    question: str
    run: Callable[[list[GameRecord]], list[FindingDraft]]


def _by_time_class(games: list[GameRecord]) -> dict[str, list[GameRecord]]:
    groups: dict[str, list[GameRecord]] = {}
    for g in games:
        if g.time_class in TIME_CLASSES:
            groups.setdefault(g.time_class, []).append(g)
    return groups


def _ci_text(c: Comparison) -> str:
    return f"95% CI {pct(c.ci_low)} to {pct(c.ci_high)} points; {c.n_group} vs {c.n_rest} games"


# ---- Tilt -----------------------------------------------------------------------------


def tilt(games: list[GameRecord]) -> list[FindingDraft]:
    out = []
    for tc, gs in _by_time_class(games).items():
        in_session = [g for g in gs if g.previous_result is not None]
        after_loss = [g.residual for g in in_session if g.previous_result == "loss"]
        otherwise = [g.residual for g in in_session if g.previous_result != "loss"]
        after_two = [g.residual for g in in_session if g.previous_results[-2:] == ["loss"] * 2]
        c = compare(after_loss, otherwise)
        label = tc.capitalize()
        if c.confidence == "insufficient":
            title = f"{label}: not enough games to judge tilt yet"
        elif c.significant and c.effect < 0:
            title = f"{label}: you score worse right after a loss"
        elif c.significant and c.effect > 0:
            title = f"{label}: you bounce back after a loss"
        else:
            title = f"{label}: no clear tilt after a loss"
        summary = (
            f"In the game right after a loss (same session) you score {pct(c.group_mean)} "
            f"points against what the ratings predict, versus {pct(c.rest_mean)} after a win "
            f"or draw: a difference of {pct(c.effect)} points ({_ci_text(c)}). You choose whether "
            f"to keep playing after a loss, so part of this can be self-selection."
        )
        details = {
            "after_two_losses_mean": (sum(after_two) / len(after_two)) if after_two else None,
            "after_two_losses_n": len(after_two),
        }
        out.append(FindingDraft("tilt", tc, title, summary, c, details))
    return out


# ---- Session length -------------------------------------------------------------------


def session_fatigue(games: list[GameRecord]) -> list[FindingDraft]:
    out = []
    buckets = [(1, 2), (3, 5), (6, 10), (11, 10_000)]
    for tc, gs in _by_time_class(games).items():
        in_session = [g for g in gs if g.session_index > 0]
        late = [g.residual for g in in_session if g.session_index >= LATE_SESSION_FROM]
        early = [g.residual for g in in_session if g.session_index < LATE_SESSION_FROM]
        c = compare(late, early)
        label = tc.capitalize()
        if c.confidence == "insufficient":
            title = f"{label}: not enough long sessions to judge fatigue yet"
        elif c.significant and c.effect < 0:
            title = f"{label}: your results drop in long sessions"
        elif c.significant and c.effect > 0:
            title = f"{label}: you get stronger as a session goes on"
        else:
            title = f"{label}: session length makes no clear difference"
        summary = (
            f"From game {LATE_SESSION_FROM} of a session onwards you score {pct(c.group_mean)} "
            f"points against expectation, versus {pct(c.rest_mean)} in games 1-"
            f"{LATE_SESSION_FROM - 1}: a difference of {pct(c.effect)} points ({_ci_text(c)})."
        )
        per_bucket = {}
        for lo, hi in buckets:
            rs = [g.residual for g in in_session if lo <= g.session_index <= hi]
            key = f"{lo}+" if hi >= 10_000 else f"{lo}-{hi}"
            per_bucket[key] = {"n": len(rs), "mean": (sum(rs) / len(rs)) if rs else None}
        out.append(FindingDraft("session_fatigue", tc, title, summary, c, {"buckets": per_bucket}))
    return out


# ---- Time trouble ---------------------------------------------------------------------


def reached_time_trouble(g: GameRecord) -> bool | None:
    """True if the player's clock fell below 10% of the starting time. None if unknown."""
    clocks = g.own_clocks
    if not g.base_seconds or len(clocks) < 5:
        return None
    return min(clocks) < g.base_seconds * 10 * TIME_TROUBLE_SHARE


def time_trouble(games: list[GameRecord]) -> list[FindingDraft]:
    out = []
    for tc, gs in _by_time_class(games).items():
        known = [(g, reached_time_trouble(g)) for g in gs]
        known = [(g, tt) for g, tt in known if tt is not None]
        tt_games = [g for g, tt in known if tt]
        calm_games = [g for g, tt in known if not tt]
        c = compare([g.residual for g in tt_games], [g.residual for g in calm_games])
        share = len(tt_games) / len(known) if known else 0.0
        flag_losses = sum(1 for g in gs if g.result == "loss" and g.result_detail == "timeout")
        label = tc.capitalize()
        if c.confidence == "insufficient":
            title = f"{label}: not enough games with clock data to judge time trouble yet"
        elif c.significant and c.effect < 0:
            title = f"{label}: time trouble costs you points ({share:.0%} of games)"
        else:
            title = f"{label}: you reach time trouble in {share:.0%} of games"
        summary = (
            f"Your clock drops below {TIME_TROUBLE_SHARE:.0%} of the starting time in "
            f"{share:.0%} of {tc} games. In those games you score {pct(c.group_mean)} points "
            f"against expectation, versus {pct(c.rest_mean)} otherwise ({_ci_text(c)}). "
            f"{flag_losses} losses on time. Note: positions that are already difficult also "
            f"cost time, so this shows a link, not a proven cause."
        )
        details = {"share": share, "games_with_clock": len(known), "timeout_losses": flag_losses}
        out.append(FindingDraft("time_trouble", tc, title, summary, c, details))
    return out


ANALYSES: list[Analysis] = [
    Analysis(
        "tilt",
        "Tilt after a loss",
        "Do you play worse in the game right after a loss?",
        tilt,
    ),
    Analysis(
        "session_fatigue",
        "Long sessions",
        "Do your results drop the longer you keep playing in one sitting?",
        session_fatigue,
    ),
    Analysis(
        "time_trouble",
        "Time trouble",
        "How often do you get into time trouble, and what does it cost you?",
        time_trouble,
    ),
]
