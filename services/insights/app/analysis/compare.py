"""You next to a grandmaster: the same habits from two players' latest analysis runs.

Nothing is recomputed from games: every number comes from the stored findings of both runs.
Each row shows both players' values with their 95% intervals and, where both have enough data,
the difference with its own interval. Differences are tested with a normal approximation and
corrected over the whole table (Benjamini-Hochberg), like the findings of a single run.
Definitions: docs/definitions.md, section "Grandmaster comparison".
"""

import math
from collections.abc import Callable
from dataclasses import dataclass

from app.analysis.base import CATEGORIES
from app.analysis.stats import (
    MIN_RATE_GROUP,
    Q_EXPLORATORY,
    Q_FINDING,
    benjamini_hochberg,
    to_elo,
    wilson,
)

Z = 1.96


@dataclass(frozen=True)
class Side:
    """One player's value for one row. `count` is set for rates (k of n)."""

    value: float
    ci_low: float | None
    ci_high: float | None
    n: int
    count: int | None = None


@dataclass(frozen=True)
class RowSpec:
    key: str
    name: str
    unit: str  # "share" (0-1), "points" (percentage points as 0-1), "elo", "move"
    better: str | None  # "lower", "higher" or None (no better or worse)
    source: str  # analysis_key of the finding
    read: Callable[[dict], Side | None]
    testable: bool = True


def _rate(path: str) -> Callable[[dict], Side | None]:
    def read(f: dict) -> Side | None:
        r = f["details"].get(path) or {}
        if not r.get("n") or r.get("rate") is None:
            return None
        lo, hi = r.get("ci") or wilson(r["count"], r["n"])
        return Side(r["rate"], lo, hi, r["n"], r["count"])

    return read


def _contrast(elo: bool) -> Callable[[dict], Side | None]:
    def read(f: dict) -> Side | None:
        if f["label"] == "not_enough_data" or f["effect"] is None or f["ci_low"] is None:
            return None
        conv = to_elo if elo else (lambda x: x)
        return Side(conv(f["effect"]), conv(f["ci_low"]), conv(f["ci_high"]), f["sample_size"])

    return read


def _onset(f: dict) -> Side | None:
    m = (f["details"].get("onset_move") or {}).get("median")
    n = (f["details"].get("entry") or {}).get("count") or 0
    return Side(m, None, None, n) if m is not None and n >= MIN_RATE_GROUP else None


def _clock_at_20(f: dict) -> Side | None:
    v = ((f["details"].get("pace") or {}).get("wins") or {}).get("20")
    n = (f["details"].get("entry") or {}).get("n") or 0
    return Side(v, None, None, n) if v is not None else None


ROWS: list[RowSpec] = [
    RowSpec(
        "time_trouble",
        "Games with time trouble",
        "share",
        "lower",
        "clock_profile",
        _rate("entry"),
    ),
    RowSpec(
        "scramble",
        "Games with a last-seconds scramble (below 3%)",
        "share",
        "lower",
        "clock_profile",
        _rate("scramble"),
    ),
    RowSpec(
        "self_inflicted",
        "Time trouble with more time on the opponent's clock",
        "share",
        "lower",
        "clock_profile",
        _rate("self_inflicted"),
    ),
    RowSpec(
        "onset_move",
        "Time trouble usually starts at move",
        "move",
        None,
        "clock_profile",
        _onset,
        testable=False,
    ),
    RowSpec(
        "clock_at_20",
        "Clock left at move 20 in wins",
        "share",
        None,
        "clock_profile",
        _clock_at_20,
        testable=False,
    ),
    RowSpec(
        "trouble_cost",
        "What time trouble costs (Elo)",
        "elo",
        "higher",
        "time_trouble_score",
        _contrast(elo=True),
    ),
    RowSpec(
        "requeue_after_loss",
        "Extra quick requeues after a loss (vs. after a win)",
        "points",
        "lower",
        "after_loss_requeue",
        _contrast(elo=False),
    ),
    RowSpec(
        "play_after_loss",
        "Play right after a loss (vs. after a win, Elo)",
        "elo",
        "higher",
        "after_loss_result",
        _contrast(elo=True),
    ),
]


def _normal_p(z: float) -> float:
    return math.erfc(abs(z) / math.sqrt(2))


def _difference(spec: RowSpec, you: Side, ref: Side) -> tuple[dict, float] | None:
    """Difference you minus reference, its 95% interval and a two-sided p-value."""
    d = you.value - ref.value
    if spec.unit == "share" and you.count is not None and ref.count is not None:
        if min(you.n, ref.n) < MIN_RATE_GROUP:
            return None
        # Newcombe's hybrid score interval for two independent proportions.
        lo = d - math.sqrt((you.value - you.ci_low) ** 2 + (ref.ci_high - ref.value) ** 2)
        hi = d + math.sqrt((you.ci_high - you.value) ** 2 + (ref.value - ref.ci_low) ** 2)
        pooled = (you.count + ref.count) / (you.n + ref.n)
        se = math.sqrt(pooled * (1 - pooled) * (1 / you.n + 1 / ref.n))
        p = 1.0 if se == 0 else _normal_p(d / se)
        return {"value": d, "ci_low": lo, "ci_high": hi}, p
    # Contrasts: each side's standard error from its 95% interval.
    se = math.hypot((you.ci_high - you.ci_low) / (2 * Z), (ref.ci_high - ref.ci_low) / (2 * Z))
    if se == 0:
        return None
    return {"value": d, "ci_low": d - Z * se, "ci_high": d + Z * se}, _normal_p(d / se)


def _side(s: Side | None) -> dict | None:
    if s is None:
        return None
    return {"value": s.value, "ci_low": s.ci_low, "ci_high": s.ci_high, "n": s.n}


def compare(you: list[dict], reference: list[dict]) -> list[dict]:
    """One block per time control both players have, each with one row per habit.

    `you` and `reference` are the findings of each player's latest run (as API dicts)."""

    def index(findings: list[dict]) -> dict[tuple[str, str], dict]:
        return {(f["time_class"], f["analysis_key"]): f for f in findings}

    mine, theirs = index(you), index(reference)
    sources = {spec.source for spec in ROWS}
    classes = [
        c
        for c in CATEGORIES
        if any((c, k) in mine for k in sources) and any((c, k) in theirs for k in sources)
    ]

    blocks: list[dict] = []
    tests: list[tuple[dict, float]] = []
    for c in classes:
        rows = []
        for spec in ROWS:
            a, b = mine.get((c, spec.source)), theirs.get((c, spec.source))
            you_side = spec.read(a) if a else None
            ref_side = spec.read(b) if b else None
            if you_side is None and ref_side is None:
                continue
            row = {
                "key": spec.key,
                "name": spec.name,
                "unit": spec.unit,
                "better": spec.better,
                "you": _side(you_side),
                "reference": _side(ref_side),
                "difference": None,
                "q_value": None,
                "verdict": "descriptive" if not spec.testable else "not_enough_data",
            }
            if spec.testable and you_side and ref_side:
                diff = _difference(spec, you_side, ref_side)
                if diff is not None:
                    row["difference"] = diff[0]
                    tests.append((row, diff[1]))
            rows.append(row)
        blocks.append({"time_class": c, "rows": rows})

    for (row, _), q in zip(tests, benjamini_hochberg([p for _, p in tests]), strict=True):
        row["q_value"] = q
        row["verdict"] = (
            "different"
            if q <= Q_FINDING
            else "maybe_different"
            if q <= Q_EXPLORATORY
            else "similar"
        )
    return blocks
