"""Pick comparison players from chess.com's public titled-player lists.

Criteria (all from the public API, fetched serially):
- title FM, CM or NM (stable, public lists at /pub/titled/{title}); account not closed;
- last online within 60 days;
- chess.com rapid rating 2000-2500 (comparable to the owner's 2380);
- at least 500 rated rapid games and at least 1,000 rated live games in total (rapid+blitz+bullet),
  and at most 15,000 live games (keeps downloads small);
- at least 100 rated blitz games (E1 uses rapid and blitz).
Candidates are visited in a seeded random order; the first N that qualify are kept.
The chosen usernames are written to <data>/chesscom/players.json (not to the repo).

Run: python -I experiments/fetch_data/select_players.py [N]
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
from kexp import chesscom  # noqa: E402
from kexp.paths import CHESSCOM  # noqa: E402

OWNER = "chrisaxm"


def n_games(rec: dict | None) -> int:
    if not rec:
        return 0
    r = rec.get("record", {})
    return int(r.get("win", 0)) + int(r.get("loss", 0)) + int(r.get("draw", 0))


def main(n: int = 5, max_checked: int = 150) -> None:
    pool = []
    for t in ("FM", "CM", "NM"):
        pool += [(t, u) for u in chesscom.titled(t)]
    rng = random.Random(20261112)
    rng.shuffle(pool)
    chosen, checked = [], 0
    for title, u in pool:
        if len(chosen) >= n or checked >= max_checked:
            break
        if u.lower() == OWNER:
            continue
        checked += 1
        prof = chesscom.profile(u) or {}
        if str(prof.get("status", "")).startswith("closed"):
            continue
        if time.time() - prof.get("last_online", 0) > 60 * 86400:
            continue
        st = chesscom.stats(u) or {}
        rapid, blitz, bullet = st.get("chess_rapid"), st.get("chess_blitz"), st.get("chess_bullet")
        rr = (rapid or {}).get("last", {}).get("rating", 0)
        total = n_games(rapid) + n_games(blitz) + n_games(bullet)
        if not (2000 <= rr <= 2500):
            continue
        if n_games(rapid) < 500 or n_games(blitz) < 100 or not (1000 <= total <= 15000):
            continue
        chosen.append({"username": u, "title": title, "rapid": rr,
                       "blitz": (blitz or {}).get("last", {}).get("rating"),
                       "bullet": (bullet or {}).get("last", {}).get("rating"),
                       "n_rapid": n_games(rapid), "n_blitz": n_games(blitz), "n_bullet": n_games(bullet)})
        print("chosen", chosen[-1], flush=True)
    out = {"owner": OWNER, "players": chosen, "checked": checked, "selected_on": time.strftime("%Y-%m-%d")}
    (CHESSCOM / "players.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"checked {checked}, chose {len(chosen)} -> {CHESSCOM / 'players.json'}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 5)
