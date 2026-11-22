"""After a loss: does the player's behaviour change, do results change, and would a stop-loss
rule have helped?

Research: docs/research/psych-tilt-and-stop-loss.md and experiments/e2-after-loss.md. E2 found
that per-player result effects are mostly too noisy to show, while requeue speed changes
reliably, so the card leads with behaviour and always states what size of effect the data
could have detected.
"""

from datetime import timedelta

from app.analysis.base import FindingDraft, by_category
from app.analysis.games import GameRecord
from app.analysis.stats import (
    MIN_OUTCOME_GROUP,
    MIN_RATE_GROUP,
    cluster_bootstrap,
    cluster_mean,
    pct,
    to_elo,
)

QUICK_REQUEUE = timedelta(seconds=60)
# Buckets for the "time before the next game" chart: (label, upper bound or None).
GAP_BUCKETS = [
    ("under 30 s", timedelta(seconds=30)),
    ("30-60 s", timedelta(seconds=60)),
    ("1-2 min", timedelta(minutes=2)),
    ("2-5 min", timedelta(minutes=5)),
    ("5-30 min", timedelta(minutes=30)),
    ("new session", None),
]
MAX_SESSION_GAME = 8  # the session chart pools game 8 and later


def _gap_shares(gs: list[GameRecord]) -> dict[str, float] | None:
    if not gs:
        return None
    counts = dict.fromkeys((label for label, _ in GAP_BUCKETS), 0)
    for g in gs:
        for label, upper in GAP_BUCKETS:
            if upper is None or g.next_start_gap <= upper:
                counts[label] += 1
                break
    return {k: v / len(gs) for k, v in counts.items()}


def _by_session_game(gs: list[GameRecord]) -> list[dict]:
    """Score against expectation (Elo) by position in the session: game 1, 2, ... 8+."""
    out = []
    for i in range(1, MAX_SESSION_GAME + 1):
        group = [
            g
            for g in gs
            if (g.session_index == i or (i == MAX_SESSION_GAME and g.session_index > i))
        ]
        m = cluster_mean([(g.session_id, g.residual) for g in group])
        if m is None or m["n"] < MIN_RATE_GROUP:
            continue
        out.append(
            {
                "game": i,
                "plus": i == MAX_SESSION_GAME,
                "elo": to_elo(m["mean"]),
                "low": to_elo(m["low"]),
                "high": to_elo(m["high"]),
                "games": m["n"],
            }
        )
    return out


STOP_RULES = [
    ("two_in_a_row", "Stop after 2 losses in a row"),
    ("three_in_a_row", "Stop after 3 losses in a row"),
    ("three_in_session", "Stop after 3 losses in one session"),
]


def triggered(rule: str, results: list[str]) -> bool:
    """True if `rule` says stop after this sequence of results in a session."""
    if rule == "two_in_a_row":
        return results[-2:] == ["loss", "loss"]
    if rule == "three_in_a_row":
        return results[-3:] == ["loss", "loss", "loss"]
    return results.count("loss") >= 3


def skipped_by(rule: str, g: GameRecord) -> bool:
    """True if `rule` had already told the player to stop before this game started."""
    history = g.previous_results
    return any(triggered(rule, history[:i]) for i in range(1, len(history) + 1))


def after_loss(games: list[GameRecord]) -> list[FindingDraft]:
    drafts: list[FindingDraft] = []
    for cat, gs in by_category(games).items():
        drafts.append(_requeue(cat, gs))
        drafts.append(_result(cat, gs))
        drafts.append(_stop_rules(cat, gs))
    return drafts


def _requeue(cat: str, gs: list[GameRecord]) -> FindingDraft:
    known = [g for g in gs if g.next_start_gap is not None and g.result in ("win", "loss")]

    def quick(g: GameRecord) -> float:
        return 1.0 if g.next_start_gap <= QUICK_REQUEUE else 0.0

    c = cluster_bootstrap(
        [(g.session_id, quick(g)) for g in known if g.result == "loss"],
        [(g.session_id, quick(g)) for g in known if g.result == "win"],
    )

    def text(label: str) -> tuple[str, str]:
        name = cat.capitalize()
        if c is None or label == "not_enough_data":
            return (
                f"{name}: not enough games to compare how fast you start the next game",
                f"Needs at least {MIN_RATE_GROUP} wins and losses followed by another game.",
            )
        body = (
            f"You start the next game within a minute after {c.mean_a:.0%} of your {cat} losses "
            f"and after {c.mean_b:.0%} of your wins ({pct(c.effect)} percentage points, 95% CI "
            f"{pct(c.ci_low)} to {pct(c.ci_high)}; {c.n_a} losses, {c.n_b} wins). "
            "Most players requeue faster after a loss (research E2: 4 of 5 strong players). "
            "Whether it costs you shows in the result card below."
        )
        if label in ("finding", "exploratory") and c.effect > 0:
            tag = "" if label == "finding" else " (exploratory)"
            return f"{name}: you requeue faster after a loss{tag}", body
        if label in ("finding", "exploratory"):
            return f"{name}: you take more time before the next game after a loss", body
        return f"{name}: losing does not change how fast you start the next game", body

    return FindingDraft(
        "after_loss_requeue",
        cat,
        "contrast",
        "share",
        text,
        contrast=c,
        min_n=MIN_RATE_GROUP,
        sample_size=len(known),
        details={
            "charts": {
                "next_game_gap": {
                    "after_loss": _gap_shares([g for g in known if g.result == "loss"]),
                    "after_win": _gap_shares([g for g in known if g.result == "win"]),
                }
            }
        },
    )


def _result(cat: str, gs: list[GameRecord]) -> FindingDraft:
    follow = [g for g in gs if g.previous is not None]
    c = cluster_bootstrap(
        [(g.session_id, g.residual) for g in follow if g.previous.result == "loss"],
        [(g.session_id, g.residual) for g in follow if g.previous.result == "win"],
    )

    def text(label: str) -> tuple[str, str]:
        name = cat.capitalize()
        if c is None or label == "not_enough_data":
            n_loss = sum(1 for g in follow if g.previous.result == "loss")
            return (
                f"{name}: not enough games to judge your play right after a loss",
                f"Needs at least {MIN_OUTCOME_GROUP} games right after a loss and after a win "
                f"in the same session (now {n_loss} after a loss).",
            )
        body = (
            f"Right after a loss you score {pct(c.mean_a)} points against expectation, after a "
            f"win {pct(c.mean_b)}: a difference of {to_elo(c.effect):+.0f} Elo (95% CI "
            f"{to_elo(c.ci_low):+.0f} to {to_elo(c.ci_high):+.0f}; {c.n_a} vs {c.n_b} games). "
            "Expectation uses your smoothed rating, so normal rating ups and downs do not "
            "create a fake effect."
        )
        tag = " (exploratory)" if label == "exploratory" else ""
        if label in ("finding", "exploratory") and c.effect < 0:
            return f"{name}: you play below your level right after a loss{tag}", body
        if label in ("finding", "exploratory"):
            return (
                f"{name}: you play above your level right after a loss{tag}",
                body + " You choose whether to keep playing, so part of this can be "
                "self-selection.",
            )
        return (
            f"{name}: no tilt larger than {to_elo(c.mde):.0f} Elo after a loss",
            body + f" Effects smaller than about {to_elo(c.mde):.0f} Elo cannot be seen yet.",
        )

    return FindingDraft(
        "after_loss_result",
        cat,
        "contrast",
        "score",
        text,
        contrast=c,
        min_n=MIN_OUTCOME_GROUP,
        sample_size=len(follow),
        details={
            "charts": {"by_session_game": _by_session_game([g for g in gs if g.session_index > 0])}
        },
    )


def _stop_rules(cat: str, gs: list[GameRecord]) -> FindingDraft:
    in_session = [g for g in gs if g.session_index > 0]
    rules = []
    for key, name in STOP_RULES:
        skipped = [g for g in in_session if skipped_by(key, g)]
        kept = [g for g in in_session if not skipped_by(key, g)]
        c = cluster_bootstrap(
            [(g.session_id, g.residual) for g in skipped],
            [(g.session_id, g.residual) for g in kept],
        )
        verdict = "not_enough_data"
        if c is not None and len(skipped) >= MIN_RATE_GROUP:
            verdict = "helps" if c.ci_high < 0 else "costs" if c.ci_low > 0 else "no_difference"
        rules.append(
            {
                "rule": key,
                "name": name,
                "skipped_games": len(skipped),
                "skipped_mean_elo": to_elo(c.mean_a) if c else None,
                "difference_elo": to_elo(c.effect) if c else None,
                "ci_elo": [to_elo(c.ci_low), to_elo(c.ci_high)] if c else None,
                "verdict": verdict,
            }
        )

    def text(_label: str) -> tuple[str, str]:
        name = cat.capitalize()
        helps = [r for r in rules if r["verdict"] == "helps"]
        costs = [r for r in rules if r["verdict"] == "costs"]
        if helps:
            best = max(helps, key=lambda r: r["skipped_games"])
            return (
                f"{name}: “{best['name'].lower()}” would have saved you points",
                f"The {best['skipped_games']} games this rule would have skipped were played "
                f"{abs(best['difference_elo']):.0f} Elo below your other games.",
            )
        if all(r["verdict"] == "not_enough_data" for r in rules):
            return (
                f"{name}: not enough long sessions to test stop-loss rules",
                f"Each rule needs at least {MIN_RATE_GROUP} games it would have skipped.",
            )
        summary = (
            "None of the common stop-loss rules would have skipped games you played below "
            "your level."
        )
        if costs:
            summary += (
                f" “{costs[0]['name']}” would even have skipped games you played "
                f"{costs[0]['difference_elo']:+.0f} Elo better than the rest."
            )
        return f"{name}: a stop-loss rule would not have helped you", summary

    return FindingDraft(
        "stop_loss_rules",
        cat,
        "profile",
        "profile",
        text,
        sample_size=len(in_session),
        details={"rules": rules},
    )
