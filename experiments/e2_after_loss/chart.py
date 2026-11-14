"""E2 chart: after-loss minus after-win residual (Elo) per player and time control. Reads e2_summary.json.

Run: python -I experiments/e2_after_loss/chart.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
from kexp.paths import OUT  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = HERE.parents[1]


def main() -> None:
    s = json.loads((OUT / "e2_summary.json").read_text(encoding="utf-8"))
    rows = []
    for p, v in s["players"].items():
        for tc, t in v["by_tc"].items():
            o = t["outcome"]
            if "point_elo" in o and min(o["nL"], o["nW"]) >= 100:
                rows.append((f"{p} {tc}", o["point_elo"], o["lo_elo"], o["hi_elo"], o["mde_elo"]))
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "axes.edgecolor": "#8a8984",
                         "xtick.color": "#52514e", "ytick.color": "#52514e", "axes.labelcolor": "#52514e"})
    fig, ax = plt.subplots(figsize=(6.4, 0.3 * len(rows) + 1.1), dpi=110)
    for j, (lab, pt, lo, hi, mde) in enumerate(rows):
        c = "#2a78d6" if lab.startswith("owner") else "#52514e"
        ax.plot([lo, hi], [j, j], color=c, lw=2)
        ax.plot([pt], [j], "o", color=c, ms=5)
    ax.axvline(0, color="#8a8984", lw=0.8)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.invert_yaxis()
    ax.grid(axis="x", color="#e6e5e0", lw=0.8)
    ax.set_xlabel("after-loss minus after-win residual, Elo (95% session-cluster bootstrap CI)")
    ax.set_title("Results after a loss vs after a win (groups with ≥ 100 games each)", loc="left", fontsize=10)
    fig.tight_layout()
    out = REPO / "docs/research/experiments/img/e2-outcome-after-loss.png"
    fig.savefig(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
