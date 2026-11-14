"""Statistics shared by all analyses. Definitions: docs/definitions.md.

Rules every finding follows (from docs/research/shortlist.md, sections 2.3 and 9):
- Results are measured as the residual: actual score minus the score expected from the
  player's smoothed strength and the opponent's pre-game rating.
- Uncertainty comes from a cluster bootstrap: sessions are resampled for anything about
  consecutive games, games for everything else. A plain per-game interval is too narrow
  when games in one session are not independent.
- Each contrast reports its minimum detectable effect (MDE): the size of effect the data
  could have detected. "No effect" always means "no effect larger than the MDE".
- All contrasts on one page are corrected for multiple testing (Benjamini-Hochberg):
  q <= 0.05 is a finding, q <= 0.10 is exploratory.
"""

import math
from dataclasses import dataclass

import numpy as np

N_BOOT = 2000
Q_FINDING = 0.05
Q_EXPLORATORY = 0.10
MIN_OUTCOME_GROUP = 100  # games in the smaller group for score findings
MIN_RATE_GROUP = 30  # events in the smaller group for behaviour rates
# Score points -> Elo near an expected score of 0.5: d(score)/d(Elo) = ln(10)/400 * 0.25.
ELO_PER_SCORE_POINT = 400 / (math.log(10) * 0.25)


def expected_score(rating: float | None, opponent_rating: float | None) -> float:
    if rating is None or opponent_rating is None:
        return 0.5
    return 1.0 / (1.0 + 10 ** ((opponent_rating - rating) / 400.0))


def actual_score(result: str) -> float:
    return {"win": 1.0, "draw": 0.5}.get(result, 0.0)


def to_elo(score_points: float) -> float:
    return score_points * ELO_PER_SCORE_POINT


@dataclass(frozen=True)
class Contrast:
    effect: float  # mean of group A minus mean of group B
    ci_low: float
    ci_high: float
    se: float
    p_value: float
    n_a: int
    n_b: int
    mean_a: float
    mean_b: float

    @property
    def mde(self) -> float:
        """Smallest effect this data detects with 80% power at alpha 0.05 (2.8 standard errors)."""
        return 2.8 * self.se

    @property
    def n_small(self) -> int:
        return min(self.n_a, self.n_b)


def cluster_bootstrap(
    a: list[tuple[object, float]],
    b: list[tuple[object, float]],
    n_boot: int = N_BOOT,
    seed: int = 0,
) -> Contrast | None:
    """Difference in means between groups A and B, resampling clusters.

    `a` and `b` are lists of (cluster_key, value). Clusters are resampled with replacement
    from the union of both groups, so a session that contributes to both stays paired.
    Returns None if either group is empty.
    """
    if not a or not b:
        return None
    keys = sorted({k for k, _ in a} | {k for k, _ in b}, key=str)
    index = {k: i for i, k in enumerate(keys)}
    n_clusters = len(keys)
    sum_a, cnt_a = np.zeros(n_clusters), np.zeros(n_clusters)
    sum_b, cnt_b = np.zeros(n_clusters), np.zeros(n_clusters)
    for k, v in a:
        sum_a[index[k]] += v
        cnt_a[index[k]] += 1
    for k, v in b:
        sum_b[index[k]] += v
        cnt_b[index[k]] += 1

    mean_a = sum_a.sum() / cnt_a.sum()
    mean_b = sum_b.sum() / cnt_b.sum()
    effect = mean_a - mean_b

    rng = np.random.default_rng(seed)
    draws = rng.integers(0, n_clusters, size=(n_boot, n_clusters))
    weights = np.zeros((n_boot, n_clusters))
    rows = np.repeat(np.arange(n_boot), n_clusters)
    np.add.at(weights, (rows, draws.ravel()), 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        boot = (weights @ sum_a) / (weights @ cnt_a) - (weights @ sum_b) / (weights @ cnt_b)
    boot = boot[np.isfinite(boot)]
    if boot.size < n_boot // 2:
        return None
    lo, hi = np.percentile(boot, [2.5, 97.5])
    p = 2 * min(np.mean(boot <= 0), np.mean(boot >= 0))
    p = float(min(1.0, max(p, 1.0 / boot.size)))
    return Contrast(
        effect=float(effect),
        ci_low=float(lo),
        ci_high=float(hi),
        se=float(np.std(boot, ddof=1)),
        p_value=p,
        n_a=len(a),
        n_b=len(b),
        mean_a=float(mean_a),
        mean_b=float(mean_b),
    )


def benjamini_hochberg(p_values: list[float]) -> list[float]:
    """Adjusted q-values, in the input order."""
    m = len(p_values)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: p_values[i])
    q = [0.0] * m
    running = 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        running = min(running, p_values[i] * m / rank)
        q[i] = running
    return q


def label_for(q_value: float | None, n_small: int, min_n: int) -> str:
    """finding / exploratory / no_effect / not_enough_data."""
    if n_small < min_n or q_value is None:
        return "not_enough_data"
    if q_value <= Q_FINDING:
        return "finding"
    if q_value <= Q_EXPLORATORY:
        return "exploratory"
    return "no_effect"


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson interval for a proportion."""
    if n == 0:
        return 0.0, 1.0
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def rate_summary(k: int, n: int) -> dict:
    """Count, rate and 95% Wilson interval, as stored in finding details."""
    lo, hi = wilson(k, n)
    return {"count": k, "n": n, "rate": (k / n) if n else None, "ci": [lo, hi]}


def median(xs: list[float]) -> float | None:
    return float(np.median(xs)) if xs else None


def quantiles(xs: list[float]) -> tuple[float, float] | None:
    if not xs:
        return None
    q1, q3 = np.percentile(xs, [25, 75])
    return float(q1), float(q3)


def pct(x: float) -> str:
    """Score points as signed percentage points, e.g. -0.061 -> '-6.1'."""
    return f"{x * 100:+.1f}"
