"""Statistics shared by all analyses.

Every game is scored against the result the rating difference predicts (Elo expected
score), so a finding never just reflects that the player met stronger or weaker opponents.
A finding compares the mean residual (actual - expected) of a group of games with the rest
and reports the difference with a 95% confidence interval (Welch / normal approximation).
"""

import math
from dataclasses import dataclass

MIN_GROUP = 30  # below this, Kiebitz makes no claim at all
Z95 = 1.96
Z99 = 2.576


def expected_score(rating: int | None, opponent_rating: int | None) -> float:
    if rating is None or opponent_rating is None:
        return 0.5
    return 1.0 / (1.0 + 10 ** ((opponent_rating - rating) / 400.0))


def actual_score(result: str) -> float:
    return {"win": 1.0, "draw": 0.5}.get(result, 0.0)


def _mean_var(xs: list[float]) -> tuple[float, float]:
    n = len(xs)
    mean = sum(xs) / n
    var = sum((x - mean) ** 2 for x in xs) / (n - 1) if n > 1 else 0.0
    return mean, var


@dataclass(frozen=True)
class Comparison:
    effect: float  # mean residual of group minus mean residual of rest (score points, 0..1)
    ci_low: float
    ci_high: float
    n_group: int
    n_rest: int
    group_mean: float
    rest_mean: float
    confidence: str  # high / medium / low / insufficient

    @property
    def significant(self) -> bool:
        return self.confidence in ("high", "medium")


def compare(group: list[float], rest: list[float]) -> Comparison:
    """Compare residuals of `group` against `rest`."""
    n1, n2 = len(group), len(rest)
    if n1 < 2 or n2 < 2:
        m1 = sum(group) / n1 if n1 else 0.0
        m2 = sum(rest) / n2 if n2 else 0.0
        return Comparison(m1 - m2, -1.0, 1.0, n1, n2, m1, m2, "insufficient")
    m1, v1 = _mean_var(group)
    m2, v2 = _mean_var(rest)
    effect = m1 - m2
    se = math.sqrt(v1 / n1 + v2 / n2)
    lo, hi = effect - Z95 * se, effect + Z95 * se
    if n1 < MIN_GROUP or n2 < MIN_GROUP:
        confidence = "insufficient"
    elif se == 0:
        confidence = "high" if effect != 0 else "low"
    else:
        z = abs(effect) / se
        confidence = "high" if z >= Z99 else "medium" if z >= Z95 else "low"
    return Comparison(effect, lo, hi, n1, n2, m1, m2, confidence)


def pct(x: float) -> str:
    """Score points as signed percentage points, e.g. -0.061 -> '-6.1'."""
    return f"{x * 100:+.1f}"
