"""Game-level context table: R_skill, residuals, sessions, previous result, behaviour markers.

Definitions follow docs/research/psychology-and-context.md and psych-tilt-and-stop-loss.md.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .games import move_times, own_plies, t_est

SESSION_GAP = 30 * 60      # end -> next start, seconds
GEE_GAP = {"bullet": 300, "blitz": 420}   # start -> next start (Gee et al. 2025)


def elo_factor(E: np.ndarray) -> float:
    """Multiply a mean residual by this to get Elo: 1 / (mean(E(1-E)) * ln10/400)."""
    return 1.0 / (float(np.mean(E * (1 - E))) * math.log(10) / 400)


def game_table(games: list[dict]) -> pd.DataFrame:
    live = [g for g in games if g["time_class"] in ("bullet", "blitz", "rapid") and g.get("base") is not None]
    rows = []
    for g in live:
        T = t_est(g)
        mt = move_times(g)
        own = own_plies(g)
        # share of T_est used on own moves 10-25 (games that reach own move 25)
        tu = None
        if len(own) >= 25 and all(p in mt for p in own[9:25]):
            tu = sum(mt[p][1] for p in own[9:25]) / T
        rows.append({
            "url": g["url"], "end": g["end_time"], "start": g["start_ts"], "tclass": g["time_class"],
            "tc": g["time_control"], "T_est": T, "rated": g["rated"], "my_post": g["my_rating"],
            "opp_post": g["opp_rating"], "score": g["score"], "my_result": g["my_result"],
            "opp_result": g["opp_result"], "n_own": len(own), "time_use_10_25": tu,
        })
    df = pd.DataFrame(rows).sort_values("end").reset_index(drop=True)
    # start time fallback: end minus nothing known -> use end (rare)
    df["start"] = df["start"].fillna(df["end"])
    # pre-game rating = post-game rating of previous rated game in the same time class
    df["my_pre"] = np.nan
    for tcl, idx in df[df["rated"]].groupby("tclass").groups.items():
        idx = sorted(idx, key=lambda i: df.at[i, "end"])
        posts = df.loc[idx, "my_post"].to_numpy(dtype=float)
        pre = np.concatenate([[np.nan], posts[:-1]])
        df.loc[idx, "my_pre"] = pre
        # R_skill: median pre-game rating over +-25 neighbouring games, excluding the game itself
        rs = []
        for j in range(len(idx)):
            win = np.concatenate([pre[max(0, j - 25):j], pre[j + 1:j + 26]])
            win = win[np.isfinite(win)]
            rs.append(np.median(win) if len(win) >= 10 else np.nan)
        df.loc[idx, "R_skill"] = rs
    df["opp_pre"] = df["opp_post"] + (df["my_post"] - df["my_pre"])   # approximation (symmetric change)
    df["E"] = 1 / (1 + 10 ** ((df["opp_pre"] - df["R_skill"]) / 400))
    df["resid"] = df["score"] - df["E"]
    df["rating_diff"] = df["opp_pre"] - df["R_skill"]
    # sessions (all live games, rated or not): new session when start - previous end > 30 min
    gap = df["start"] - df["end"].shift(1)
    df["gap_prev"] = gap
    df["session"] = (gap.isna() | (gap > SESSION_GAP)).cumsum()
    prev_score = df["score"].shift(1)
    same = df["session"] == df["session"].shift(1)
    df["prev"] = np.where(~same, None, np.where(prev_score == 0, "L", np.where(prev_score == 1, "W", "D")))
    df["requeue60"] = np.where(same, (gap <= 60).astype(float), np.nan)
    # Gee et al. start-to-start rule (bullet/blitz only)
    sgap = df["start"] - df["start"].shift(1)
    gee_lim = df["tclass"].map(GEE_GAP)
    same_gee = (sgap <= gee_lim) & gee_lim.notna() & (df["tclass"] == df["tclass"].shift(1))
    df["session_gee"] = (~same_gee).cumsum()
    df["prev_gee"] = np.where(~same_gee, None, np.where(prev_score == 0, "L", np.where(prev_score == 1, "W", "D")))
    df["timeout_loss"] = df["my_result"] == "timeout"
    df["timeout_win"] = df["opp_result"] == "timeout"
    return df


def diff_means_cr(y: np.ndarray, grp: np.ndarray, cl: np.ndarray) -> tuple[float, float]:
    """Difference of means (grp True minus False) with a cluster-robust (CR1) standard error."""
    a, b = grp, ~grp
    na, nb = a.sum(), b.sum()
    if na < 2 or nb < 2:
        return float("nan"), float("nan")
    ma, mb = y[a].mean(), y[b].mean()
    infl = np.where(a, (y - ma) / na, -(y - mb) / nb)
    s = pd.Series(infl).groupby(cl).sum().to_numpy()
    G = len(s)
    var = G / (G - 1) * np.sum(s ** 2)
    return float(ma - mb), float(math.sqrt(var))
