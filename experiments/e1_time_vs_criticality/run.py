"""E1: Is time spent related to criticality, and do fast critical moves go wrong more often?

See docs/research/experiments/e1-time-vs-criticality.md for the write-up.

Run (engine part is cached, reruns are free):
  python -I experiments/e1_time_vs_criticality/run.py --players chrisaxm,p1,p2 --rapid 300 --blitz 150
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import chess
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
from kexp import engine  # noqa: E402
from kexp.games import load_games, t_est  # noqa: E402
from kexp.paths import OUT  # noqa: E402
from kexp.positions import own_move_rows  # noqa: E402
from kexp.stats import ci, cluster_bootstrap, spearman  # noqa: E402

PLY_LO, PLY_HI = 15, 79          # plies 16-80 (1-based)
MIN_CLOCK = 0.10                 # c >= 10% of T_est
CRIT, QUIET = 10.0, 3.0          # C_gap thresholds
FAST, SLOW = 0.5, 2.0            # relative-time thresholds
ERR = 10.0                       # error = dW >= 10
HIDDEN = 10.0                    # critical position where the depth-1 move loses >= 10 (dU >= 10)
NODES, VERIFY_AT, VERIFY_MAX = 300_000, 7.0, 25.0


def spec_name(verify_nodes: int) -> str:
    return f"e1-n{NODES}-mpv2-d1-v{verify_nodes}-{VERIFY_AT:g}to{VERIFY_MAX:g}"


def pick_games(user: str, tclass: str, n: int) -> list[dict]:
    gs = [g for g in load_games(user, fetch=False) if g["rated"] and g["time_class"] == tclass
          and g.get("base") is not None and t_est(g) < 1500 and len(g["moves"]) >= 20]
    return gs[-n:]


def build_rows(user: str, tclass: str, games: list[dict]) -> pd.DataFrame:
    rows = []
    for g in games:
        for r in own_move_rows(g, PLY_LO, PLY_HI, MIN_CLOCK):
            r.update(user=user, tclass=tclass, tc=g["time_control"])
            rows.append(r)
    df = pd.DataFrame(rows)
    # relative time: own median over the same time control, clock band and phase
    # (all own moves that pass the clock and ply filters; fallback to tc+band if < 20 moves)
    med = df.groupby(["tc", "band", "phase"])["t"].transform("median")
    cnt = df.groupby(["tc", "band", "phase"])["t"].transform("size")
    med2 = df.groupby(["tc", "band"])["t"].transform("median")
    df["t_med"] = np.where(cnt >= 20, med, med2)
    df["r"] = df["t"] / df["t_med"].clip(lower=0.1)
    df["prefilter"] = (~df["in_check"]) & (df["n_legal"] > 3)
    return df


def run_engine(df: pd.DataFrame, verify_nodes: int, workers: int, label: str) -> pd.DataFrame:
    spec = spec_name(verify_nodes)
    sub = df[df["prefilter"]]
    tasks = [{"key": f"{spec}|{f}|{p}", "fen": f, "played": p, "nodes": NODES, "multipv": 2, "depth1": True,
              "gate_lo": 10, "gate_hi": 90, "verify_threshold": VERIFY_AT, "verify_max": VERIFY_MAX,
              "verify_nodes": verify_nodes}
             for f, p in zip(sub["fen"], sub["played"])]
    t0 = time.time()
    res = engine.run_tasks(tasks, cache_name="e1", workers=workers, label=label)
    wall = time.time() - t0
    df = df.copy()
    df["key"] = [f"{spec}|{f}|{p}" for f, p in zip(df["fen"], df["played"])]
    cols = ["w_best", "w_second", "best", "second", "m1", "dU", "dW", "dW_v", "gated_in", "secs", "depth"]
    for c in cols:
        df[c] = [res.get(k, {}).get(c) for k in df["key"]]
    df.attrs["wall"] = wall
    return df


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    d = df[df["prefilter"] & (df["gated_in"] == True)].copy()  # noqa: E712
    d = d[d["w_second"].notna()]
    # trivial: best move recaptures on the square of the opponent's last move
    def recapture(row) -> bool:
        if row["last_to"] is None or pd.isna(row["last_to"]):
            return False
        b = chess.Board(row["fen"])
        m = chess.Move.from_uci(row["best"])
        return b.is_capture(m) and m.to_square == int(row["last_to"])
    d["recapture"] = d.apply(recapture, axis=1)
    d = d[~d["recapture"]].copy()
    d["c_gap"] = (d["w_best"] - d["w_second"]).clip(lower=0)
    d["dW_final"] = np.where(d["dW_v"].notna(), d["dW_v"], d["dW"]).astype(float)
    d["dU"] = d["dU"].astype(float)
    d["err"] = d["dW_final"] >= ERR
    d["critical"] = d["c_gap"] >= CRIT
    d["quiet"] = d["c_gap"] < QUIET
    d["fast"] = d["r"] < FAST
    d["slow"] = d["r"] >= SLOW
    return d


def metrics(d: pd.DataFrame) -> np.ndarray:
    crit = d[d["critical"]]
    cf, cnf = crit[crit["fast"]], crit[~crit["fast"]]
    e_cf = cf["err"].mean() if len(cf) else np.nan
    e_cnf = cnf["err"].mean() if len(cnf) else np.nan
    return np.array([
        spearman(d["r"].to_numpy(), d["dU"].to_numpy()),
        spearman(d["r"].to_numpy(), d["c_gap"].to_numpy()),
        100 * (e_cf - e_cnf),                          # missed-alarm error excess (pp)
        100 * crit["fast"].mean() if len(crit) else np.nan,   # share of critical moves played fast
        100 * e_cf, 100 * e_cnf,
        spearman(crit["r"].to_numpy(), crit["c_gap"].to_numpy()) if len(crit) > 3 else np.nan,
        *_split(crit[crit["dU"] >= HIDDEN]),          # critical and the depth-1 move is a mistake
        *_split(crit[crit["dU"] < 3]),                # critical but the depth-1 move is (near) best
        100 * (crit["dU"] >= HIDDEN).mean() if len(crit) else np.nan,
        spearman(d["r"].to_numpy(), d["dW_final"].to_numpy()),
    ])


def _split(x: pd.DataFrame) -> list[float]:
    f, nf = x[x["fast"]], x[~x["fast"]]
    ef = 100 * f["err"].mean() if len(f) else np.nan
    enf = 100 * nf["err"].mean() if len(nf) else np.nan
    return [ef, enf, ef - enf]


METRIC_NAMES = ["rho_r_dU", "rho_r_Cgap", "crit_fast_minus_notfast_err_pp", "crit_fast_share_pct",
                "crit_fast_err_pct", "crit_notfast_err_pct", "rho_r_Cgap_within_critical",
                "hidden_fast_err_pct", "hidden_notfast_err_pct", "hidden_fast_minus_notfast_pp",
                "obvious_fast_err_pct", "obvious_notfast_err_pct", "obvious_fast_minus_notfast_pp",
                "hidden_share_of_critical_pct", "rho_r_dW"]


def matrix(d: pd.DataFrame) -> list[dict]:
    out = []
    n = len(d)
    for crit_name, cm in (("critical", d["critical"]), ("quiet", d["quiet"])):
        for sp_name, sm in (("fast", d["fast"]), ("slow", d["slow"]), ("middle", ~d["fast"] & ~d["slow"])):
            cell = d[cm & sm]
            out.append({"criticality": crit_name, "speed": sp_name, "n": int(len(cell)),
                        "share_pct": round(100 * len(cell) / n, 1) if n else None,
                        "err_pct": round(100 * cell["err"].mean(), 1) if len(cell) else None,
                        "mean_dW": round(cell["dW_final"].mean(), 2) if len(cell) else None,
                        "median_s": round(cell["t"].median(), 1) if len(cell) else None})
    return out


def summarise(d: pd.DataFrame, raw: pd.DataFrame, B: int) -> dict:
    point, draws = cluster_bootstrap(d.reset_index(drop=True), "url", metrics, B=B, seed=1)
    out = {"n_games": int(raw["url"].nunique()), "n_moves_candidate": int(len(raw)),
           "n_moves_engine": int(raw["prefilter"].sum()), "n_moves_final": int(len(d)),
           "n_critical": int(d["critical"].sum()), "n_crit_fast": int((d["critical"] & d["fast"]).sum()),
           "n_hidden": int((d["critical"] & (d["dU"] >= HIDDEN)).sum()),
           "n_hidden_fast": int((d["critical"] & (d["dU"] >= HIDDEN) & d["fast"]).sum()),
           "critical_per_game": round(d["critical"].sum() / raw["url"].nunique(), 2),
           "verified": int(d["dW_v"].notna().sum()),
           "verified_flipped_below_10": int(((d["dW"] >= ERR) & d["dW_v"].notna() & (d["dW_v"] < ERR)).sum()),
           "verified_raised_to_10": int(((d["dW"] < ERR) & d["dW_v"].notna() & (d["dW_v"] >= ERR)).sum()),
           "err_rate_pct": round(100 * d["err"].mean(), 2),
           "median_t": float(d["t"].median())}
    for i, name in enumerate(METRIC_NAMES):
        lo, hi = ci(draws[:, i])
        out[name] = [round(float(point[i]), 4), round(lo, 4), round(hi, 4)]
    out["matrix"] = matrix(d)
    # error rate by relative-time quintile, critical positions only (for a chart)
    crit = d[d["critical"]].copy()
    if len(crit) > 50:
        crit["rbin"] = pd.cut(crit["r"], [0, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 1e9])
        g = crit.groupby("rbin", observed=True)["err"].agg(["mean", "size"])
        out["crit_err_by_r"] = [{"bin": str(k), "err_pct": round(100 * v["mean"], 1), "n": int(v["size"])} for k, v in g.iterrows()]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--players", default="chrisaxm")
    ap.add_argument("--rapid", type=int, default=300)
    ap.add_argument("--blitz", type=int, default=150)
    ap.add_argument("--workers", type=int, default=7)
    ap.add_argument("--verify-nodes", type=int, default=1_000_000)
    ap.add_argument("--B", type=int, default=2000)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    summary = {"engine": engine.engine_id(), "nodes": NODES, "verify_nodes": a.verify_nodes,
               "run_at": time.strftime("%Y-%m-%d %H:%M"), "results": {}}
    all_rows = []
    for user in a.players.split(","):
        for tclass, n in (("rapid", a.rapid), ("blitz", a.blitz)):
            if n <= 0:
                continue
            games = pick_games(user, tclass, n)
            raw = build_rows(user, tclass, games)
            raw = run_engine(raw, a.verify_nodes, a.workers, f"{user}/{tclass}")
            d = finalize(raw)
            s = summarise(d, raw, a.B)
            s["engine_wall_s"] = round(raw.attrs.get("wall", 0), 1)
            s["engine_cpu_s_per_pos"] = round(float(pd.to_numeric(raw["secs"], errors="coerce").mean()), 3)
            s["first_game"] = games[0]["end_time"] if games else None
            s["last_game"] = games[-1]["end_time"] if games else None
            summary["results"][f"{user}/{tclass}"] = s
            print(json.dumps({k: v for k, v in s.items() if k not in ("matrix", "crit_err_by_r")}), flush=True)
            all_rows.append(d.drop(columns=["fen"]))
    pd.concat(all_rows).to_csv(OUT / f"e1_moves{a.tag}.csv.gz", index=False)
    (OUT / f"e1_summary{a.tag}.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")
    print("wrote", OUT / f"e1_summary{a.tag}.json")


if __name__ == "__main__":
    main()
