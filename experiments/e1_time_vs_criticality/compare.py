"""E1 cross-player comparison and charts. Reads the per-move tables written by run.py (no engine).

Run: python -I experiments/e1_time_vs_criticality/compare.py [--B 2000] [--img docs/research/experiments/img]
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
sys.path.insert(0, str(HERE))
from kexp.paths import CHESSCOM, OUT  # noqa: E402
from kexp.stats import ci, cluster_bootstrap  # noqa: E402
from run import METRIC_NAMES, matrix, metrics  # noqa: E402

REPO = HERE.parents[1]
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]   # reference categorical slots 1-4 (light)


def logit_time(g: pd.DataFrame) -> dict:
    """Error odds per doubling of relative time, controlling for engine difficulty (game-clustered SE)."""
    import statsmodels.formula.api as smf
    g = g.assign(err_i=g["err"].astype(int), lr=np.log2(g["r"].clip(lower=0.05)), bal=(g["w_best"] - 50).abs())
    out = {}
    for name, sub, f in (("all", g, "err_i ~ lr + c_gap + dU + bal + C(band) + C(phase)"),
                         ("critical", g[g["critical"]], "err_i ~ lr + c_gap + dU + bal")):
        try:
            m = smf.logit(f, data=sub).fit(disp=0, cov_type="cluster", cov_kwds={"groups": pd.factorize(sub["url"])[0]})
            lo, hi = m.conf_int().loc["lr"].tolist()
            out[name] = {"n": int(len(sub)), "coef": round(float(m.params["lr"]), 3), "ci": [round(lo, 3), round(hi, 3)],
                         "odds_ratio": round(float(np.exp(m.params["lr"])), 2)}
        except Exception as exc:  # small groups can fail to converge
            out[name] = {"n": int(len(sub)), "error": str(exc)[:80]}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--B", type=int, default=2000)
    ap.add_argument("--img", default=str(REPO / "docs/research/experiments/img"))
    a = ap.parse_args()
    cfg = json.loads((CHESSCOM / "players.json").read_text(encoding="utf-8"))
    alias = {cfg["owner"]: "owner", **{p["username"]: f"P{i + 1}" for i, p in enumerate(cfg["players"])}}
    frames = [pd.read_csv(p) for p in sorted(OUT.glob("e1_moves_*.csv.gz")) if "_test" not in p.name]
    d = pd.concat(frames).drop_duplicates(subset=["url", "ply", "user"])
    for c in ("critical", "quiet", "fast", "slow", "err"):
        d[c] = d[c].astype(bool)
    d["who"] = d["user"].map(alias)
    res, draws_all = {}, {}
    for (who, tcl), g in d.groupby(["who", "tclass"]):
        g = g.reset_index(drop=True)
        point, draws = cluster_bootstrap(g, "url", metrics, B=a.B, seed=1)
        key = f"{who}/{tcl}"
        draws_all[key] = draws
        r = {"n_games": int(g["url"].nunique()), "n_moves": int(len(g)), "n_critical": int(g["critical"].sum()),
             "n_crit_fast": int((g["critical"] & g["fast"]).sum()), "err_pct": round(100 * g["err"].mean(), 2),
             "critical_per_game": round(g["critical"].sum() / g["url"].nunique(), 2),
             "median_t": float(g["t"].median()), "matrix": matrix(g)}
        for i, n in enumerate(METRIC_NAMES):
            lo, hi = ci(draws[:, i])
            r[n] = [round(float(point[i]), 4), round(lo, 4), round(hi, 4)]
        r["logit_log2r"] = logit_time(g)
        res[key] = r
        print(key, {k: v for k, v in r.items() if k != "matrix"}, flush=True)
    # pairwise differences between players, same time class (independent samples)
    pairs = {}
    for k1, k2 in itertools.combinations(sorted(res), 2):
        if k1.split("/")[1] != k2.split("/")[1]:
            continue
        p = {}
        for i, n in enumerate(METRIC_NAMES):
            diff = draws_all[k1][:, i] - draws_all[k2][:, i]
            lo, hi = ci(diff)
            a1, a2 = res[k1][n], res[k2][n]
            p[n] = {"diff": round(a1[0] - a2[0], 4), "ci": [round(lo, 4), round(hi, 4)],
                    "cis_overlap": not (a1[2] < a2[1] or a2[2] < a1[1])}
        pairs[f"{k1} vs {k2}"] = p
    (OUT / "e1_compare.json").write_text(json.dumps({"groups": res, "pairs": pairs}, indent=1), encoding="utf-8")

    # ---- charts (light theme, PNG)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    img = Path(a.img)
    img.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#8a8984", "axes.labelcolor": "#52514e", "xtick.color": "#52514e",
                         "ytick.color": "#52514e", "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})
    # chart 1: error rate in critical positions by relative-time bin (rapid)
    bins = [0, 0.5, 1.0, 2.0, 1e9]
    labels = ["<0.5", "0.5-1", "1-2", "≥2"]
    fig, axes = plt.subplots(1, 3, figsize=(8.4, 3.3), dpi=110, sharey=True)
    order = ["owner"] + sorted(w for w in d["who"].unique() if w != "owner")
    panels = [("all critical", lambda g: g["dU"] > -1),
              ("obvious (ΔU < 3)", lambda g: g["dU"] < 3),
              ("hidden (ΔU ≥ 10)", lambda g: g["dU"] >= 10)]
    for ax, (title, sel) in zip(axes, panels):
        for i, who in enumerate(order):
            g = d[(d["who"] == who) & (d["tclass"] == "rapid") & d["critical"]].copy()
            g = g[sel(g)]
            if g.empty:
                continue
            g["rbin"] = pd.cut(g["r"], bins, labels=labels)
            s_ = g.groupby("rbin", observed=False)["err"].agg(["mean", "size"])
            y = np.where(s_["size"] >= 10, 100 * s_["mean"], np.nan)
            ax.plot(range(len(labels)), y, color=COLORS[i % 4], lw=2, marker="o", ms=4,
                    label=who + (" (15+10)" if who == "P5" else " (10+0)"))
        ax.set_xticks(range(len(labels)), labels)
        ax.set_title(title, loc="left", fontsize=9, color="#0b0b0b")
        ax.grid(axis="y", color="#e6e5e0", lw=0.8)
        ax.set_xlabel("relative time r")
    axes[0].set_ylabel("error rate (ΔW ≥ 10), %")
    axes[0].legend(frameon=False, loc="upper left")
    fig.suptitle("Critical positions (C_gap ≥ 10), rapid: error rate by relative move time (bins with n ≥ 10)",
                 x=0.01, ha="left", fontsize=10, color="#0b0b0b")
    fig.tight_layout()
    fig.savefig(img / "e1-critical-error-by-time.png")
    plt.close(fig)
    # chart 2: rho(r, dU) per group with 95% CI
    keys = [k for k in sorted(res, key=lambda k: (k.split("/")[1] != "rapid", k.split("/")[0] != "owner", k))]
    fig, ax = plt.subplots(figsize=(6.4, 0.32 * len(keys) + 1.0), dpi=110)
    for j, k in enumerate(keys):
        p, lo, hi = res[k]["rho_r_dU"]
        ax.plot([lo, hi], [j, j], color="#2a78d6", lw=2)
        ax.plot([p], [j], "o", color="#2a78d6", ms=5)
    ax.axvline(0, color="#8a8984", lw=0.8)
    ax.set_yticks(range(len(keys)), keys)
    ax.invert_yaxis()
    ax.set_xlabel("Spearman ρ(relative time, ΔU), 95% game-cluster bootstrap CI")
    ax.grid(axis="x", color="#e6e5e0", lw=0.8)
    fig.tight_layout()
    fig.savefig(img / "e1-rho-by-player.png")
    plt.close(fig)
    print("charts written to", img)


if __name__ == "__main__":
    main()
