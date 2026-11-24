from datetime import datetime, timedelta

from app.analysis.deep import critical_moments, endings, opening_autopilot, win_pct
from app.analysis.games import GameRecord, prepare
from tests.conftest import api_game, interleave

T0 = datetime(2026, 3, 2, 18, 0)


def clocks(n_moves: int = 30, per_move: int = 30, base: int = 1800) -> str:
    own = [base - per_move * (i + 1) for i in range(n_moves)]
    return interleave(own, own)


def record(i: int, **kw) -> GameRecord:
    deep = {k: kw.pop(k) for k in ("position_keys", "engine_moves", "final_cp") if k in kw}
    g = GameRecord.from_api(api_game(i, ended_at=T0 + timedelta(hours=i), clocks=clocks(), **kw))
    for k, v in deep.items():
        setattr(g, k, v)
    return g


def move(k: int, b: int, s: int | None, p: int, type_: str = "quiet", **kw) -> dict:
    return {"k": k, "best": "e2e4", "type": type_, "b": b, "s": s, "p": p, "legal": 30, **kw}


def test_win_pct_is_the_lichess_curve():
    assert win_pct(0) == 50
    assert 80 < win_pct(400) < 85
    assert abs(win_pct(-400) - (100 - win_pct(400))) < 1e-9


def test_critical_moments_counts_only_non_trivial_decisions():
    games = []
    for i in range(40):
        rows = [
            move(10, 50, -200, 50),  # critical (gap ~ 18), found
            move(11, 50, -400, -400, type_="retreat", fen="8/8/8/8/8/8/8/8 w - - 0 1"),  # missed
            move(12, 50, 40, 40),  # not critical (gap ~ 0.5)
            move(13, 50, -400, -400, recapture=True),  # trivial: recapture
            move(14, 50, -400, -400, check=True),  # trivial: in check
            move(15, 50, -400, -400, legal=2),  # trivial: 2 legal moves
            move(16, 900, -400, -400),  # decided already (best 88%? no: 96%+)
        ]
        games.append(record(i, engine_moves=rows))
    [d] = critical_moments(prepare(games))
    crit = d.details["critical"]
    assert crit["n"] == 80 and crit["count"] == 40
    types = {c["name"]: c for c in d.details["by_type"]}
    assert types["Retreat"]["rate"] == 0 and types["Quiet move"]["rate"] == 1
    assert d.details["missed"][0]["fen"].startswith("8/8")
    title, summary = d.text("profile")
    assert "50% of critical moments" in title
    assert "Weakest: retreat" in summary


def test_critical_moments_needs_enough_positions():
    games = [record(i, engine_moves=[move(10, 50, -200, 50)]) for i in range(25)]
    [d] = critical_moments(prepare(games))
    assert "not enough critical moments" in d.text("profile")[0]


def test_endings_judge_resignations_and_time_losses():
    games = []
    for i in range(40):
        # 20 resignations in equal positions (premature), 20 in lost ones.
        cp = 0 if i % 2 else -900
        games.append(record(i, result="loss", termination="Opp won by resignation", final_cp=cp))
    for i in range(40, 50):
        games.append(record(i, result="loss", termination="Opp won on time", final_cp=500))
    for i in range(50, 60):
        games.append(record(i, result="win", termination="Me won by resignation", final_cp=900))
    [d] = endings(prepare(games))
    r = d.details["resignations"]
    assert r["n"] == 40 and r["premature"]["count"] == 20
    assert d.details["lost_on_time"] == {"winning": 10}
    assert d.details["opponents"]["n"] == 10
    title, summary = d.text("profile")
    assert title == "Blitz: 50% of your resignations came too early"
    assert "10 games were lost on time in a winning position" in summary


def test_opening_autopilot_separates_known_and_new_positions():
    games = []
    for i in range(40):
        keys = ["aaaaaaaa", "bbbbbbbb", f"{i:08x}"] + [
            f"{1000 + i * 30 + j:08x}" for j in range(17)
        ]
        games.append(record(i, position_keys=keys))
    [d] = opening_autopilot(prepare(games))
    assert d.details["familiar_positions"] == 2 * (40 - 3)
    assert d.details["exit_move"] == 3
    title, _ = d.text("profile")
    assert "known positions" in title


def test_upload_status_and_run(client, games_api):
    import httpx

    from tests.test_api import _games

    raw = _games(10)
    games_api.get("/players/1/games").mock(
        return_value=httpx.Response(200, json={"items": raw, "total": len(raw)})
    )
    body = {"games": [{"game_id": g["id"], "position_keys": ["0000abcd", "1111abcd"]} for g in raw]}
    body["games"][0].update(
        engine="sf19-lite-100k",
        final_cp=-50,
        moves=[move(5, 30, -300, 30) | {"fen": "8/8/8/8/8/8/8/K6k w - - 0 1"}],
    )
    st = client.put("/players/1/game-analyses", json=body).json()
    assert st["positions"] == len(raw) and st["engine"] == 1

    # A second positions-only upload keeps the engine pass.
    client.put(
        "/players/1/game-analyses",
        json={"games": [{"game_id": raw[0]["id"], "position_keys": ["2222abcd"]}]},
    )
    st = client.get("/players/1/game-analyses/status").json()
    assert st["engine_game_ids"] == [raw[0]["id"]]

    bad = client.put(
        "/players/1/game-analyses", json={"games": [{"game_id": 1, "position_keys": ["XYZ"]}]}
    )
    assert bad.status_code == 422

    run = client.post("/players/1/runs").json()
    keys = {f["analysis_key"] for f in run["findings"]}
    assert "critical_moments" in keys
