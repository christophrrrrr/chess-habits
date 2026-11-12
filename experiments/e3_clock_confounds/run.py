"""E3: Do the MVP clock cards survive their confounds?

(1) material proxy vs engine Win% for flag games, (2) time-trouble score gap after controlling for
the position at own move 20 and its sharpness, (3) premove detector (0.1 s vs 0.2 s move times).

Run: python -I experiments/e3_clock_confounds/run.py [--workers 7]
Write-up: docs/research/experiments/e3-clock-confounds.md
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
import warnings
from pathlib import Path

import chess
import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
from kexp import engine  # noqa: E402
from kexp.context import game_table  # noqa: E402
from kexp.games import load_games, move_times, own_plies, time_trouble_info  # noqa: E402
from kexp.paths import CHESSCOM, OUT  # noqa: E402
from kexp.positions import material, own_move_rows  # noqa: E402
from kexp.stats import ci  # noqa: E402

warnings.filterwarnings("ignore")
FLAG_NODES = 1_000_000
FSPEC = f"flag-n{FLAG_NODES}"
QSPEC, QNODES = "q-n100000-mpv2", 100_000      # shared with E2
FLAG_CAP_OTHERS = 150
# (who, time class, max games reaching own move 20)
MODEL_SAMPLE = [("owner", "rapid", 600), ("owner", "blitz", 400), ("owner", "bullet", 600),
                ("players[0]", "rapid", 300), ("players[0]", "blitz", 300),
                ("players[2]", "rapid", 300), ("players[2]", "blitz", 300)]


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p, z = k / n, 1.96
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h


def board_after(g: dict, n_plies: int) -> chess.Board:
    b = chess.Board()
    for m in g["moves"][:n_plies]:
        b.push_uci(m)
    return b


def flag_positions(g: dict) -> dict | None:
    me = chess.WHITE if g["color"] == "white" else chess.BLACK
    n = len(g["moves"])
    if n < 20:
        return None
    final = board_after(g, n)
    own = own_plies(g)
    if len(own) < 11:
        return None
    ply10 = own[-10]                     # position before my own move 10 own moves before the end
    early = board_after(g, ply10)
    two_before = board_after(g, n - 2)
    return {"url": g["url"], "lost_on_time": g["my_result"] == "timeout", "tclass": g["time_class"],
            "fen_final": final.fen(), "fen_m10": early.fen(), "me_white": me == chess.WHITE,
            "mat_final": material(final, me), "mat_2before": material(two_before, me), "mat_m10": material(early, me),
            "final_legal": final.legal_moves.count()}


def bucket_mat(m: int) -> str:
    return "win" if m >= 3 else ("lose" if m <= -3 else "level")


def bucket_w(w: float) -> str:
    return "win" if w >= 75 else ("lose" if w <= 25 else "level")


def premove_table(games: list[dict]) -> list[dict]:
    rows = []
    for g in games:
        if g["time_class"] not in ("bullet", "blitz", "rapid"):
            continue
        for _, (clk, t) in move_times(g).items():
            rows.append((g["time_class"], round(t, 1)))
    df = pd.DataFrame(rows, columns=["tclass", "t"])
    out = []
    for tcl, d in df.groupby("tclass"):
        out.append({"tclass": tcl, "n_moves": int(len(d)), "pct_0.1": round(100 * (d["t"] == 0.1).mean(), 2),
                    "pct_0.2": round(100 * (d["t"] == 0.2).mean(), 2), "pct_0.3": round(100 * (d["t"] == 0.3).mean(), 2),
                    "pct_0.0": round(100 * (d["t"] == 0.0).mean(), 2)})
    return out


def fit(df: pd.DataFrame, cols: list[str]) -> np.ndarray:
    X = sm.add_constant(df[cols].astype(float), has_constant="add")
    m = sm.GLM(df["score"].astype(float), X, family=sm.families.Binomial()).fit()
    return m.params.to_numpy()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=7)
    ap.add_argument("--B", type=int, default=1000)
    ap.add_argument("--dry", action="store_true", help="count positions and print premove table, no engine")
    a = ap.parse_args()
    cfg = json.loads((CHESSCOM / "players.json").read_text(encoding="utf-8"))
    names = [cfg["owner"]] + [p["username"] for p in cfg["players"]]
    alias = {cfg["owner"]: "owner", **{p["username"]: f"P{i + 1}" for i, p in enumerate(cfg["players"])}}
    out = {"run_at": time.strftime("%Y-%m-%d %H:%M"), "flag_nodes": FLAG_NODES, "model_nodes": QNODES}
    games_by_user = {u: load_games(u, fetch=False) for u in names}

    # ---------- (3) premove detector
    out["premoves"] = {alias[u]: premove_table(gs) for u, gs in games_by_user.items()}

    # ---------- (1) flag games: material proxy vs engine
    flags = []
    for u, gs in games_by_user.items():
        fg = [g for g in gs if g["time_class"] in ("bullet", "blitz", "rapid") and g["rated"]
              and (g["my_result"] == "timeout" or g["opp_result"] == "timeout")]
        if u != cfg["owner"]:
            fg = fg[-FLAG_CAP_OTHERS:]
        for g in fg:
            p = flag_positions(g)
            if p:
                p["user"] = alias[u]
                flags.append(p)
    fl = pd.DataFrame(flags)
    fl = fl[fl["final_legal"] > 0].reset_index(drop=True)
    tasks = []
    for col in ("fen_final", "fen_m10"):
        tasks += [{"key": f"{FSPEC}|{f}|", "fen": f, "played": None, "nodes": FLAG_NODES, "multipv": 1,
                   "gate_lo": 0, "gate_hi": 100} for f in fl[col]]

    # ---------- (2) model sample: own moves 15-20
    msel, mrows = {}, []
    tables = {}
    for who, tcl, cap in MODEL_SAMPLE:
        u = cfg["owner"] if who == "owner" else cfg["players"][int(who[8:-1])]["username"]
        if u not in tables:
            tables[u] = game_table(games_by_user[u])
        gt = tables[u]
        ok = set(gt.loc[gt["rated"] & gt["R_skill"].notna() & gt["opp_pre"].notna(), "url"])
        gl = [g for g in games_by_user[u] if g["time_class"] == tcl and g["url"] in ok and len(own_plies(g)) >= 20]
        gl = gl[-cap:]
        msel[(u, tcl)] = gl
        for g in gl:
            for r in own_move_rows(g, 0, 2 * 20, None):
                if 15 <= r["move_no"] <= 20:
                    r["user"], r["tclass"] = u, tcl
                    mrows.append(r)
    mv = pd.DataFrame(mrows)
    mv["key"] = [f"{QSPEC}|{f}|{p}" for f, p in zip(mv["fen"], mv["played"])]
    tasks_q = [{"key": k, "fen": f, "played": p, "nodes": QNODES, "multipv": 2, "depth1": False, "gate_lo": 0, "gate_hi": 100}
               for k, f, p in zip(mv["key"], mv["fen"], mv["played"])]
    print(f"flag positions {len(tasks)}, model positions {len(tasks_q)}", flush=True)
    if a.dry:
        print(json.dumps(out["premoves"], indent=1))
        print(fl.groupby(["user", "lost_on_time"]).size())
        return
    t0 = time.time()
    rf = engine.run_tasks(tasks, cache_name="flag", workers=a.workers, label="E3 flags")
    out["flag_engine_wall_s"] = round(time.time() - t0, 1)
    t0 = time.time()
    rq = engine.run_tasks(tasks_q, cache_name="q", workers=a.workers, label="E3 model")
    out["model_engine_wall_s"] = round(time.time() - t0, 1)

    # ---- (1) analysis
    def w_me(fen: str, me_white: bool) -> float:
        r = rf[f"{FSPEC}|{fen}|"]
        stm_white = fen.split()[1] == "w"
        return r["w_best"] if stm_white == me_white else 100 - r["w_best"]
    fl["W_final"] = [w_me(f, m) for f, m in zip(fl["fen_final"], fl["me_white"])]
    fl["W_m10"] = [w_me(f, m) for f, m in zip(fl["fen_m10"], fl["me_white"])]
    fl.drop(columns=["fen_final", "fen_m10"]).to_csv(OUT / "e3_flags.csv", index=False)
    res1 = {}
    for name, sub, target in (("lost_on_time", fl[fl["lost_on_time"]], "win"), ("won_on_time", fl[~fl["lost_on_time"]], "lose")):
        for scope, s in [("all", sub)] + [(f"tc:{t}", d) for t, d in sub.groupby("tclass")] + [(f"user:{u}", d) for u, d in sub.groupby("user")]:
            mb = s["mat_final"].map(bucket_mat)
            wb = s["W_final"].map(bucket_w)
            stable = (s["mat_final"].map(bucket_mat) == target) & (s["mat_2before"].map(bucket_mat) == target)
            tp = int(((mb == target) & (wb == target)).sum())
            npred, npos = int((mb == target).sum()), int((wb == target).sum())
            tp_s = int((stable & (wb == target)).sum())
            r = {"n": int(len(s)), "proxy_hits": npred, "engine_hits": npos, "tp": tp,
                 "precision": tp / npred if npred else None, "precision_ci": wilson(tp, npred),
                 "recall": tp / npos if npos else None, "recall_ci": wilson(tp, npos),
                 "stable_proxy_hits": int(stable.sum()), "stable_precision": tp_s / stable.sum() if stable.sum() else None,
                 "stable_recall": tp_s / npos if npos else None,
                 "engine_target_at_m10": int((s["W_m10"].map(bucket_w) == target).sum())}
            if scope == "all":
                r["confusion"] = pd.crosstab(mb, wb).to_dict()
            res1[f"{name}/{scope}"] = r
    out["flags"] = res1

    # ---- (2) analysis
    mv["w_best"] = [rq.get(k, {}).get("w_best") for k in mv["key"]]
    mv["w_second"] = [rq.get(k, {}).get("w_second") for k in mv["key"]]
    mv["cgap"] = (mv["w_best"] - mv["w_second"]).astype(float)
    res2 = {}
    for (u, tcl), gl in msel.items():
        gt = tables[u].set_index("url")
        m = mv[(mv["user"] == u) & (mv["tclass"] == tcl)]
        w20 = m[m["move_no"] == 20].set_index("url")["w_best"]
        sharp = m[m["n_legal"] > 1].groupby("url")["cgap"].mean()
        rows = []
        for g in gl:
            tt = time_trouble_info(g)
            if g["url"] not in w20.index or g["url"] not in sharp.index:
                continue
            rows.append({"url": g["url"], "score": g["score"], "tt": float(tt["entered"]),
                         "si": float(bool(tt["self_inflicted"])), "rating_diff": gt.at[g["url"], "rating_diff"] / 100,
                         "w20": float(w20[g["url"]]) / 10, "sharp": float(sharp[g["url"]]) / 10,
                         "onset": tt["onset_move"]})
        d = pd.DataFrame(rows).dropna(subset=["rating_diff", "w20", "sharp"]).reset_index(drop=True)
        key = f"{alias[u]}/{tcl}"
        if len(d) < 100 or d["tt"].sum() < 20 or (1 - d["tt"]).sum() < 20:
            res2[key] = {"n": int(len(d)), "n_tt": int(d["tt"].sum()) if len(d) else 0, "note": "too few"}
            continue
        specs = {"raw": ["tt"], "rating": ["tt", "rating_diff"], "full_no_si": ["tt", "rating_diff", "w20", "sharp"],
                 "full_spec": ["tt", "si", "rating_diff", "w20", "sharp"]}
        point = {k: fit(d, c) for k, c in specs.items()}
        rng = np.random.default_rng(3)
        draws = {k: [] for k in specs}
        for _ in range(a.B):
            s = d.iloc[rng.integers(0, len(d), len(d))]
            if s["tt"].nunique() < 2:
                continue
            try:
                fits = {k: fit(s, c) for k, c in specs.items()}
            except Exception:
                continue
            for k in specs:
                draws[k].append(fits[k])
        r = {"n": int(len(d)), "n_tt": int(d["tt"].sum()), "n_si": int(d["si"].sum()),
             "score_tt": float(d.loc[d["tt"] == 1, "score"].mean()), "score_no_tt": float(d.loc[d["tt"] == 0, "score"].mean()),
             "w20_tt": float(d.loc[d["tt"] == 1, "w20"].mean() * 10), "w20_no_tt": float(d.loc[d["tt"] == 0, "w20"].mean() * 10),
             "sharp_tt": float(d.loc[d["tt"] == 1, "sharp"].mean() * 10), "sharp_no_tt": float(d.loc[d["tt"] == 0, "sharp"].mean() * 10)}
        for k, c in specs.items():
            arr = np.array(draws[k])
            r[k] = {name: [round(float(point[k][i + 1]), 4), *[round(x, 4) for x in ci(arr[:, i + 1])]] for i, name in enumerate(c)}
        raw_d = np.array(draws["raw"])[:, 1]
        for k in ("full_no_si", "full_spec"):
            arr = np.array(draws[k])[:, 1]
            n_ = min(len(arr), len(raw_d))
            ratio = arr[:n_] / raw_d[:n_]
            r[f"ratio_{k}"] = [round(float(point[k][1] / point["raw"][1]), 3), *[round(x, 3) for x in ci(ratio)]]
        res2[key] = r
        print(key, json.dumps({k: v for k, v in r.items() if k in ("n", "n_tt", "raw", "full_no_si", "ratio_full_no_si")}), flush=True)
    out["model"] = res2
    (OUT / "e3_summary.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print("wrote", OUT / "e3_summary.json")


if __name__ == "__main__":
    main()
