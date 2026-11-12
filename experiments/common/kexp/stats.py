"""Cluster bootstrap and small statistics helpers."""
from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

B_DEFAULT = 2000


def cluster_bootstrap(df: pd.DataFrame, cluster: str, fn: Callable[[pd.DataFrame], float | np.ndarray],
                      B: int = B_DEFAULT, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Resample whole clusters with replacement. Returns (point estimate, draws[B, ...])."""
    rng = np.random.default_rng(seed)
    groups = {k: idx for k, idx in df.groupby(cluster).indices.items()}
    keys = np.array(list(groups.keys()), dtype=object)
    idx_list = [groups[k] for k in keys]
    point = np.asarray(fn(df), dtype=float)
    draws = []
    n = len(keys)
    for _ in range(B):
        pick = rng.integers(0, n, n)
        rows = np.concatenate([idx_list[i] for i in pick])
        draws.append(np.asarray(fn(df.iloc[rows]), dtype=float))
    return point, np.array(draws)


def ci(draws: np.ndarray, alpha: float = 0.05) -> tuple[float, float]:
    d = draws[np.isfinite(draws)]
    if len(d) == 0:
        return (float("nan"), float("nan"))
    return float(np.quantile(d, alpha / 2)), float(np.quantile(d, 1 - alpha / 2))


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < 3:
        return float("nan")
    rx = pd.Series(x).rank().to_numpy()
    ry = pd.Series(y).rank().to_numpy()
    if rx.std() == 0 or ry.std() == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def bh(pvals: list[float], q: float = 0.10) -> list[bool]:
    """Benjamini-Hochberg: which hypotheses are rejected at FDR q."""
    p = np.asarray(pvals, dtype=float)
    m = len(p)
    if m == 0:
        return []
    order = np.argsort(p)
    thresh = q * (np.arange(1, m + 1) / m)
    passed = p[order] <= thresh
    k = np.max(np.where(passed)[0]) + 1 if passed.any() else 0
    out = np.zeros(m, dtype=bool)
    out[order[:k]] = True
    return out.tolist()


def fmt_ci(point: float, lo: float, hi: float, nd: int = 1) -> str:
    return f"{point:.{nd}f} [{lo:.{nd}f}, {hi:.{nd}f}]"
