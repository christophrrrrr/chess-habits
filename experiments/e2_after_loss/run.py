"""E2: After a loss - results vs move quality vs behaviour, and the false-positive rate of the rule.

Run: python -I experiments/e2_after_loss/run.py [--no-engine] [--workers 7]
Write-up: docs/research/experiments/e2-after-loss.md
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
from kexp import engine  # noqa: E402
from kexp.context import diff_means_cr, elo_factor, game_table  # noqa: E402
from kexp.games import load_games  # noqa: E402
from kexp.paths import CHESSCOM, OUT  # noqa: E402
from kexp.positions import own_move_rows  # noqa: E402
from kexp.stats import bh, ci  # noqa: E402

MIN_N = 100            # smaller group, game-level contrasts
Q_BH = 0.10
QSPEC = "q-n100000-mpv2"   # shared with E3
QNODES = 100_000
# quality sample: (player, time class, max games per group); "players[i]" = i-th chosen player
QUALITY = [("owner", "rapid", 200), ("owner", "bullet", 120), ("players[0]", "rapid", 120), ("players[2]", "rapid", 120)]


def boot_sessions(df: pd.DataFrame, fn, B: int, seed: int, cl: str = "session") -> np.ndarray:
    rng = np.random.default_rng(seed)
    groups = list(df.groupby(cl).indices.values())
    out = []
    for _ in range(B):
        pick = rng.integers(0, len(groups), len(groups))
        rows = np.concatenate([groups[i] for i in pick])
        out.append(fn(df.iloc[rows]))
    return np.array(out, dtype=float)


def contrast(df: pd.DataFrame, col: str, B: int, seed: int, cl: str = "session", prevcol: str = "prev") -> dict:
    d = df[df[prevcol].isin(["L", "W"]) & df[col].notna()].reset_index(drop=True)
    nL, nW = int((d[prevcol] == "L").sum()), int((d[prevcol] == "W").sum())
    if nL < 5 or nW < 5:
        return {"nL": nL, "nW": nW}
    fn = lambda x: x.loc[x[prevcol] == "L", col].mean() - x.loc[x[prevcol] == "W", col].mean()  # noqa: E731
    point = fn(d)
    draws = boot_sessions(d, fn, B, seed, cl)
    lo, hi = ci(draws)
    est, se = diff_means_cr(d[col].to_numpy(float), (d[prevcol] == "L").to_numpy(), d[cl].to_numpy())
    p = math.erfc(abs(est / se) / math.sqrt(2)) if se > 0 else 1.0
    sd = float(d[col].std())
    return {"nL": nL, "nW": nW, "point": float(point), "lo": lo, "hi": hi, "p_cr": p, "se_cr": se, "sd": sd,
            "mean_L": float(d.loc[d[prevcol] == "L", col].mean()), "mean_W": float(d.loc[d[prevcol] == "W", col].mean()),
            "mde": 2.8 * sd * math.sqrt(1 / nL + 1 / nW), "d_ci_width": (hi - lo) / sd if sd > 0 else None}


def decision_family(df: pd.DataFrame, prev: np.ndarray, tests: list[tuple[str, str]]) -> list[bool]:
    """Full rule on one labelling: min n in the smaller group, 95% CI (CR SE) excludes 0, BH q=0.10."""
    pvals, ok = [], []
    for tcl, col in tests:
        m = (df["tclass"].to_numpy() == tcl) & np.isin(prev, ["L", "W"]) & df[col].notna().to_numpy()
        y = df[col].to_numpy(float)[m]
        g = prev[m] == "L"
        cl = df["session"].to_numpy()[m]
        if min(g.sum(), (~g).sum()) < MIN_N:
            pvals.append(1.0); ok.append(False); continue
        est, se = diff_means_cr(y, g, cl)
        z = abs(est / se) if se > 0 else 0
        pvals.append(math.erfc(z / math.sqrt(2)))
        ok.append(z > 1.96)
    rej = bh(pvals, Q_BH)
    return [a and b for a, b in zip(ok, rej)]


def shuffle_labels(df: pd.DataFrame, rng) -> np.ndarray:
    """Permute previous-result labels between sessions: shuffle session blocks, keep within-session order."""
    prev = df["prev"].to_numpy(object)
    sess = df["session"].to_numpy()
    blocks = [prev[idx] for idx in pd.Series(np.arange(len(df))).groupby(sess).indices.values()]
    order = rng.permutation(len(blocks))
    flat = np.concatenate([blocks[i] for i in order])
    # labels follow positions of games that have a label in the original data
    has = np.array([p is not None for p in prev])
    lab = flat[np.array([p is not None for p in flat])]
    out = np.array([None] * len(df), dtype=object)
    idx = np.where(has)[0]
    out[idx] = lab[: len(idx)]
    return out


def quality_tasks(games_by_url: dict, urls: list[str]) -> tuple[list[dict], pd.DataFrame]:
    rows = []
    for u in urls:
        g = games_by_url[u]
        for r in own_move_rows(g, 14, 79, 0.10):
            if 8 <= r["move_no"] <= 40 and r["n_legal"] > 1:
                rows.append(r)
    mv = pd.DataFrame(rows)
    mv["key"] = [f"{QSPEC}|{f}|{p}" for f, p in zip(mv["fen"], mv["played"])]
    tasks = [{"key": k, "fen": f, "played": p, "nodes": QNODES, "multipv": 2, "depth1": False,
              "gate_lo": 0, "gate_hi": 100} for k, f, p in zip(mv["key"], mv["fen"], mv["played"])]
    return tasks, mv


def per_game_quality(mv: pd.DataFrame, res: dict) -> pd.DataFrame:
    for c in ("w_best", "w_second", "dW"):
        mv[c] = [res.get(k, {}).get(c) for k in mv["key"]]
    mv = mv[mv["dW"].notna()].copy()
    mv["err"] = mv["dW"].astype(float) >= 10
    mv["cgap"] = (mv["w_best"] - mv["w_second"]).astype(float)
    live = mv["w_best"].between(10, 90) & mv["cgap"].notna()
    mv["crit"] = np.where(live, (mv["cgap"] >= 10).astype(float), np.nan)
    return mv.groupby("url").agg(err_rate=("err", "mean"), mean_dW=("dW", "mean"), crit_share=("crit", "mean"),
                                 n_moves=("err", "size")).reset_index()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-engine", action="store_true")
    ap.add_argument("--workers", type=int, default=7)
    ap.add_argument("--B", type=int, default=2000)
    ap.add_argument("--shuffles", type=int, default=1000)
    a = ap.parse_args()
    cfg = json.loads((CHESSCOM / "players.json").read_text(encoding="utf-8"))
    names = [cfg["owner"]] + [p["username"] for p in cfg["players"]]
    alias = {cfg["owner"]: "owner", **{p["username"]: f"P{i + 1}" for i, p in enumerate(cfg["players"])}}
    out = {"run_at": time.strftime("%Y-%m-%d %H:%M"), "players": {}}
    tables = {}
    for u in names:
        games = load_games(u, fetch=False)
        df = game_table(games)
        tables[u] = (df, {g["url"]: g for g in games})
        r = df[df["rated"] & df["R_skill"].notna() & df["opp_pre"].notna()].reset_index(drop=True)
        res = {"n_live_rated": int(len(r)), "by_tc": {}}
        tests = []
        for tcl in ("bullet", "blitz", "rapid"):
            d = r[r["tclass"] == tcl].reset_index(drop=True)
            if len(d) < 200:
                continue
            fac = elo_factor(d["E"].to_numpy())
            o = contrast(d, "resid", a.B, 1)
            if "point" in o:
                for k in ("point", "lo", "hi", "mde", "se_cr", "mean_L", "mean_W"):
                    o[k + "_elo"] = o[k] * fac
            o_gee = contrast(d, "resid", a.B, 2, cl="session_gee", prevcol="prev_gee") if tcl in ("bullet", "blitz") else None
            if o_gee and "point" in o_gee:
                for k in ("point", "lo", "hi"):
                    o_gee[k + "_elo"] = o_gee[k] * fac
            rq = contrast(d, "requeue60", a.B, 3)
            tu = contrast(d, "time_use_10_25", a.B, 4)
            res["by_tc"][tcl] = {"n_games": int(len(d)), "n_sessions": int(d["session"].nunique()), "elo_factor": fac,
                                 "outcome": o, "outcome_gee": o_gee, "requeue60": rq, "time_use_10_25": tu}
            tests += [(tcl, "resid"), (tcl, "requeue60"), (tcl, "time_use_10_25")]
        # observed decision rule
        res["observed_findings"] = dict(zip([f"{t}:{c}" for t, c in tests],
                                            decision_family(r, r["prev"].to_numpy(object), tests)))
        # false-positive check on shuffled labels
        rng = np.random.default_rng(7)
        any_hit, per_test = 0, np.zeros(len(tests))
        for _ in range(a.shuffles):
            hits = decision_family(r, shuffle_labels(r, rng), tests)
            any_hit += any(hits)
            per_test += np.array(hits, dtype=float)
        res["shuffle"] = {"n": a.shuffles, "familywise_rate": any_hit / a.shuffles,
                          "per_test_rate": dict(zip([f"{t}:{c}" for t, c in tests], (per_test / a.shuffles).round(4).tolist()))}
        out["players"][alias[u]] = res
        print(alias[u], json.dumps({k: v for k, v in res.items() if k != "by_tc"}), flush=True)

    # ---- move quality on a sample of games right after a loss or a win
    all_tasks, mvs, sel = [], {}, {}
    for who, tcl, cap in QUALITY:
        u = cfg["owner"] if who == "owner" else cfg["players"][int(who[8:-1])]["username"]
        df, gmap = tables[u]
        d = df[df["rated"] & (df["tclass"] == tcl) & df["prev"].isin(["L", "W"]) & df["R_skill"].notna()]
        rng = np.random.default_rng(11)
        pick = []
        for lab in ("L", "W"):
            urls = d.loc[d["prev"] == lab, "url"].tolist()
            pick += list(rng.choice(urls, size=min(cap, len(urls)), replace=False))
        tasks, mv = quality_tasks(gmap, pick)
        all_tasks += tasks
        mvs[(u, tcl)] = mv
        sel[(u, tcl)] = pick
    print(f"quality: {len(all_tasks)} positions", flush=True)
    if a.no_engine:
        return
    t0 = time.time()
    resq = engine.run_tasks(all_tasks, cache_name="q", workers=a.workers, label="E2 quality")
    out["quality_engine_wall_s"] = round(time.time() - t0, 1)
    out["quality"] = {}
    for (u, tcl), mv in mvs.items():
        df, _ = tables[u]
        pg = per_game_quality(mv, resq)
        d = df[df["url"].isin(sel[(u, tcl)]) & df["E"].notna()].merge(pg, on="url", how="inner").reset_index(drop=True)
        fac = elo_factor(d["E"].to_numpy())
        q = {"n_games": int(len(d)), "n_moves": int(d["n_moves"].sum()), "elo_factor": fac}
        for col in ("err_rate", "mean_dW", "crit_share", "resid", "time_use_10_25"):
            q[col] = contrast(d, col, a.B, 5)
        # Elo-equivalent of the quality contrast: slope of residual on mean_dW (re-estimated per draw)
        def elo_eq(x: pd.DataFrame) -> float:
            slope = np.polyfit(x["mean_dW"], x["resid"], 1)[0]
            dq = x.loc[x["prev"] == "L", "mean_dW"].mean() - x.loc[x["prev"] == "W", "mean_dW"].mean()
            return slope * dq * fac
        dd = d[d["mean_dW"].notna()].reset_index(drop=True)
        pt = elo_eq(dd)
        draws = boot_sessions(dd, elo_eq, a.B, 6)
        lo, hi = ci(draws)
        q["elo_equiv_mean_dW"] = {"point": pt, "lo": lo, "hi": hi,
                                  "slope_resid_per_dW": float(np.polyfit(dd["mean_dW"], dd["resid"], 1)[0])}
        out["quality"][f"{alias[u]}/{tcl}"] = q
        print(alias[u], tcl, json.dumps({k: (v if not isinstance(v, dict) else {kk: v.get(kk) for kk in ("point", "lo", "hi", "nL", "nW", "d_ci_width")}) for k, v in q.items()}, default=str), flush=True)
    (OUT / "e2_summary.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print("wrote", OUT / "e2_summary.json")


if __name__ == "__main__":
    main()
