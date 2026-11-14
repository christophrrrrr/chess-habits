"""Native Stockfish pool with an on-disk eval cache (sqlite).

One Stockfish process per worker (Threads 1, Hash 64). Each position starts with
`ucinewgame` (hash cleared), so a node-limited search is deterministic and the depth-1
"cheap" move is not informed by a deeper search left in the hash.

Win% uses the Lichess formula (https://lichess.org/page/accuracy):
    W = 50 + 50 * (2 / (1 + exp(-0.00368208 * cp)) - 1)
"""
from __future__ import annotations

import atexit
import json
import math
import multiprocessing as mp
import sqlite3
import time
from typing import Iterable

import chess
import chess.engine

from .paths import CACHE, stockfish_path

MATE_CP = 100000
_engine: chess.engine.SimpleEngine | None = None


def win_pct(cp: float) -> float:
    cp = max(-4000.0, min(4000.0, cp))
    return 50 + 50 * (2 / (1 + math.exp(-0.00368208 * cp)) - 1)


def _w(score: chess.engine.PovScore, turn: bool) -> float:
    return win_pct(score.pov(turn).score(mate_score=MATE_CP))


def _init(path: str, hash_mb: int) -> None:
    global _engine
    _engine = chess.engine.SimpleEngine.popen_uci(path)
    _engine.configure({"Threads": 1, "Hash": hash_mb})
    atexit.register(_engine.quit)


def _search(board, nodes, game, multipv=1, root=None):
    kw = {"game": game}
    if root:
        kw["root_moves"] = root
    if multipv > 1:
        return _engine.analyse(board, chess.engine.Limit(nodes=nodes), multipv=multipv, **kw)
    return [_engine.analyse(board, chess.engine.Limit(nodes=nodes), **kw)]


def analyse_task(task: dict) -> dict:
    """Run the searches one position needs.

    task keys: key, fen, played (uci or None), nodes, multipv (1|2), depth1 (bool),
    gate_lo/gate_hi (extra searches only if gate_lo <= W_best <= gate_hi),
    verify_threshold, verify_max, verify_nodes (re-check dW at a higher budget when
    verify_threshold <= dW < verify_max; None = off).
    """
    t0 = time.perf_counter()
    board = chess.Board(task["fen"])
    turn = board.turn
    game = task["key"]
    nodes = task["nodes"]
    legal = board.legal_moves.count()
    res = {"key": task["key"], "legal": legal}
    if legal == 0:
        res["secs"] = 0.0
        return res
    if task.get("depth1"):
        info = _engine.analyse(board, chess.engine.Limit(depth=1), game=game)
        res["m1"] = info["pv"][0].uci() if info.get("pv") else None
    infos = _search(board, nodes, game, multipv=min(task.get("multipv", 1), legal))
    lines = [(i["pv"][0].uci(), _w(i["score"], turn)) for i in infos if i.get("pv")]
    vals = dict(lines)
    res["best"], res["w_best"] = lines[0]
    if len(lines) > 1:
        res["second"], res["w_second"] = lines[1]
    res["depth"] = infos[0].get("depth")
    gated = task.get("gate_lo", 0) <= res["w_best"] <= task.get("gate_hi", 100)
    res["gated_in"] = gated
    if gated:
        need = []
        if task.get("played"):
            need.append(task["played"])
        if res.get("m1"):
            need.append(res["m1"])
        for mv in dict.fromkeys(need):
            if mv not in vals:
                info = _search(board, nodes, game, root=[chess.Move.from_uci(mv)])[0]
                vals[mv] = _w(info["score"], turn)
        if task.get("played"):
            res["w_played"] = vals[task["played"]]
            res["dW"] = max(0.0, res["w_best"] - res["w_played"])
        if res.get("m1"):
            res["w_m1"] = vals[res["m1"]]
            res["dU"] = max(0.0, res["w_best"] - res["w_m1"])
        vt, vn = task.get("verify_threshold"), task.get("verify_nodes")
        vmax = task.get("verify_max", 1000.0)
        if vt is not None and vn and vt <= res.get("dW", 0) < vmax:
            info = _search(board, vn, game)[0]
            vbest = info["pv"][0].uci()
            wb = _w(info["score"], turn)
            if vbest == task["played"]:
                wp = wb
            else:
                wp = _w(_search(board, vn, game, root=[chess.Move.from_uci(task["played"])])[0]["score"], turn)
            res["w_best_v"], res["w_played_v"], res["best_v"] = wb, wp, vbest
            res["dW_v"] = max(0.0, wb - wp)
    res["secs"] = time.perf_counter() - t0
    return res


class EvalCache:
    def __init__(self, name: str):
        self.path = CACHE / f"evals-{name}.sqlite"
        self.db = sqlite3.connect(self.path)
        self.db.execute("CREATE TABLE IF NOT EXISTS ev (key TEXT PRIMARY KEY, val TEXT)")

    def get_many(self, keys: Iterable[str]) -> dict[str, dict]:
        keys = list(keys)
        out = {}
        for i in range(0, len(keys), 500):
            chunk = keys[i : i + 500]
            q = "SELECT key, val FROM ev WHERE key IN (%s)" % ",".join("?" * len(chunk))
            for k, v in self.db.execute(q, chunk):
                out[k] = json.loads(v)
        return out

    def put_many(self, items: list[dict]) -> None:
        self.db.executemany("INSERT OR REPLACE INTO ev VALUES (?, ?)", [(r["key"], json.dumps(r)) for r in items])
        self.db.commit()


def engine_id() -> str:
    eng = chess.engine.SimpleEngine.popen_uci(str(stockfish_path()))
    name = eng.id.get("name", "?")
    eng.quit()
    return name


def run_tasks(tasks: list[dict], cache_name: str, workers: int = 6, hash_mb: int = 64, label: str = "") -> dict[str, dict]:
    """Evaluate tasks (deduplicated by key) with a process pool; returns {key: result}."""
    cache = EvalCache(cache_name)
    uniq = {t["key"]: t for t in tasks}
    have = cache.get_many(uniq.keys())
    todo = [t for k, t in uniq.items() if k not in have]
    print(f"[{label}] {len(uniq)} positions, {len(have)} cached, {len(todo)} to search, {workers} workers", flush=True)
    if todo:
        t0 = time.time()
        buf = []
        ctx = mp.get_context("spawn")
        with ctx.Pool(workers, initializer=_init, initargs=(str(stockfish_path()), hash_mb)) as pool:
            for i, r in enumerate(pool.imap_unordered(analyse_task, todo, chunksize=4), 1):
                buf.append(r)
                have[r["key"]] = r
                if len(buf) >= 200 or i == len(todo):
                    cache.put_many(buf)
                    buf = []
                    el = time.time() - t0
                    print(f"[{label}] {i}/{len(todo)} done, {el / 60:.1f} min, {i / el:.2f} pos/s", flush=True)
    return have
