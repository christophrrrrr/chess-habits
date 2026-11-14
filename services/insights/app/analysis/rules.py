"""Rules a player adopts from a card, and whether they keep them.

A card can suggest a rule ("keep at least 30% of your clock after move 20", "stop after 2
losses in a row"). Once adopted, every analysis run checks each game or session since the
adoption date: was the rule kept? The verdict compares how often it was kept after adoption
with how often the player would have kept it before (the baseline), using the same
statistics as every other card. Until enough games exist after adoption the card says
"too early" instead of guessing.

Research: docs/research/shortlist.md, section 5 item 4. Definitions: docs/definitions.md.
"""

from dataclasses import dataclass
from datetime import datetime

from app.analysis.after_loss import STOP_RULES, triggered
from app.analysis.base import FindingDraft
from app.analysis.clock import analyse_clock
from app.analysis.games import GameRecord
from app.analysis.stats import MIN_RATE_GROUP, cluster_bootstrap, pct, rate_summary

CLOCK_CHECKPOINT = "clock_checkpoint"
STOP_LOSS = "stop_loss"
KINDS = (CLOCK_CHECKPOINT, STOP_LOSS)
STOP_RULE_NAMES = dict(STOP_RULES)
DEFAULT_CHECKPOINT_MOVE = 20
# The baseline is the player's most recent behaviour before adoption, not their whole history.
BASELINE_UNITS = 300
STRIP_LENGTH = 30


@dataclass(frozen=True)
class RuleSpec:
    """A rule as the analysis sees it (decoupled from the ORM model)."""

    id: int
    time_class: str
    kind: str
    adopted_at: datetime
    move: int | None = None
    min_share: float | None = None
    stop_rule: str | None = None


@dataclass
class Unit:
    """One chance to keep or break the rule: a game (clock rule) or a session in which the
    stop-loss rule said stop."""

    cluster: object
    when: datetime
    kept: bool
    trouble: bool = False  # clock rule: the game had time trouble
    games_past_stop: int = 0  # stop-loss rule: games played after the rule said stop


def describe(kind: str, move: int | None, min_share: float | None, stop_rule: str | None) -> str:
    if kind == CLOCK_CHECKPOINT:
        return f"Keep at least {min_share:.0%} of your clock after move {move}"
    return STOP_RULE_NAMES.get(stop_rule or "", stop_rule or "")


def clock_units(rule: RuleSpec, games: list[GameRecord]) -> list[Unit]:
    """Games that reached the checkpoint move: kept if the clock after that move was at
    least `min_share` of T_est."""
    units = []
    for g in games:
        if g.category != rule.time_class or not g.t_est or len(g.own_clocks) < rule.move:
            continue
        share = g.own_clocks[rule.move - 1] / (g.t_est * 10)
        cg = analyse_clock(g)
        units.append(
            Unit(
                cluster=g.id,
                when=g.ended_at,
                kept=share >= rule.min_share,
                trouble=cg is not None and cg.entry_move is not None,
            )
        )
    return units


def stop_units(rule: RuleSpec, games: list[GameRecord]) -> list[Unit]:
    """Sessions in which the rule said stop: kept if no game in this time class followed."""
    sessions: dict[int, list[GameRecord]] = {}
    for g in games:
        if g.category == rule.time_class and g.session_index > 0:
            sessions.setdefault(g.session_id, []).append(g)
    units = []
    for session_id, gs in sessions.items():
        gs.sort(key=lambda g: g.ended_at)
        results = [g.result for g in gs]
        for i in range(len(gs)):
            if triggered(rule.stop_rule, results[: i + 1]):
                past = len(gs) - 1 - i
                units.append(Unit(session_id, gs[i].ended_at, past == 0, games_past_stop=past))
                break
    return units


def check_rule(rule: RuleSpec, games: list[GameRecord]) -> FindingDraft:
    units = clock_units(rule, games) if rule.kind == CLOCK_CHECKPOINT else stop_units(rule, games)
    units.sort(key=lambda u: u.when)
    before = [u for u in units if u.when < rule.adopted_at][-BASELINE_UNITS:]
    after = [u for u in units if u.when >= rule.adopted_at]
    c = cluster_bootstrap(
        [(u.cluster, float(u.kept)) for u in after],
        [(u.cluster, float(u.kept)) for u in before],
    )
    name = describe(rule.kind, rule.move, rule.min_share, rule.stop_rule)
    details: dict = {
        "rule_id": rule.id,
        "rule_kind": rule.kind,
        "rule_name": name,
        "adopted_at": rule.adopted_at.isoformat(),
        "needed": MIN_RATE_GROUP,
        "after": rate_summary(sum(u.kept for u in after), len(after)),
        "before": rate_summary(sum(u.kept for u in before), len(before)),
        "strip": [{"date": u.when.isoformat(), "kept": u.kept} for u in after[-STRIP_LENGTH:]],
    }
    if rule.kind == CLOCK_CHECKPOINT:
        details["trouble"] = {
            "before": rate_summary(sum(u.trouble for u in before), len(before)),
            "after": rate_summary(sum(u.trouble for u in after), len(after)),
        }
    else:
        details["games_past_stop"] = {
            "before": sum(u.games_past_stop for u in before),
            "after": sum(u.games_past_stop for u in after),
        }
    return FindingDraft(
        "rule_check",
        rule.time_class,
        "contrast",
        "share",
        _text(rule, name, details, c),
        contrast=c,
        min_n=MIN_RATE_GROUP,
        sample_size=len(before) + len(after),
        details=details,
    )


def _text(rule: RuleSpec, name: str, d: dict, c):
    unit = "games" if rule.kind == CLOCK_CHECKPOINT else "sessions where the rule said stop"
    since = f"{rule.adopted_at:%d %b %Y}".lstrip("0")
    after, before = d["after"], d["before"]

    def baseline() -> str:
        if not before["n"]:
            return "There is no baseline from before you adopted it."
        return f"Before, you kept it in {before['rate']:.0%} of {before['n']} {unit}."

    def text(label: str) -> tuple[str, str]:
        title = f"Your rule: {name[0].lower()}{name[1:]}"
        if label == "not_enough_data" or c is None:
            if not after["n"]:
                progress = f"No {unit} since you adopted it on {since} yet."
            else:
                progress = f"Kept in {after['count']} of {after['n']} {unit} since {since}."
            to_go = max(MIN_RATE_GROUP - after["n"], 0)
            verdict = (
                f"A verdict needs {MIN_RATE_GROUP} {unit} after adoption ({to_go} to go)."
                if to_go
                else f"A verdict also needs {MIN_RATE_GROUP} {unit} from before adoption."
            )
            return f"{title} (too early)", f"{progress} {baseline()} {verdict}"
        body = (
            f"Since {since} you kept it in {after['rate']:.0%} of {after['n']} {unit}, "
            f"before in {before['rate']:.0%} of {before['n']} ({pct(c.effect)} percentage "
            f"points, 95% CI {pct(c.ci_low)} to {pct(c.ci_high)})."
        )
        if rule.kind == CLOCK_CHECKPOINT:
            t = d["trouble"]
            body += (
                f" Time trouble: {t['before']['rate']:.0%} of games before, "
                f"{t['after']['rate']:.0%} since."
            )
        else:
            p = d["games_past_stop"]
            body += f" Games played past the stop: {p['before']} before, {p['after']} since."
        body += " This compares before and after: anything else that changed counts too."
        tag = " (exploratory)" if label == "exploratory" else ""
        if label in ("finding", "exploratory") and c.effect > 0:
            return f"{title}: you keep it more often since adopting it{tag}", body
        if label in ("finding", "exploratory"):
            return f"{title}: you keep it less often than before{tag}", body
        return (
            f"{title}: no clear change yet",
            body + f" The data can detect changes of about {c.mde * 100:.0f} points or more.",
        )

    return text
