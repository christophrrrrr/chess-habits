from datetime import datetime, timedelta

import httpx
import pytest
from conftest import interleave, session_games

from app.analysis.compare import compare
from app.analysis.stats import rate_summary


def _clock(tc: str, trouble: int, n: int, *, onset: float | None = 31.0) -> dict:
    return {
        "analysis_key": "clock_profile",
        "time_class": tc,
        "label": "profile",
        "effect": None,
        "ci_low": None,
        "ci_high": None,
        "sample_size": n,
        "details": {
            "entry": rate_summary(trouble, n),
            "scramble": rate_summary(trouble // 3, n),
            "self_inflicted": rate_summary(trouble // 2, trouble),
            "onset_move": {"median": onset, "iqr": None},
            "pace": {"wins": {"20": 0.55}, "losses": {"20": 0.4}},
        },
    }


def _contrast(key: str, tc: str, effect: float, half: float, label: str = "no_effect") -> dict:
    return {
        "analysis_key": key,
        "time_class": tc,
        "label": label,
        "effect": effect,
        "ci_low": effect - half,
        "ci_high": effect + half,
        "sample_size": 400,
        "details": {},
    }


def _row(blocks: list[dict], tc: str, key: str) -> dict:
    block = next(b for b in blocks if b["time_class"] == tc)
    return next(r for r in block["rows"] if r["key"] == key)


def test_clear_difference_in_time_trouble():
    you = [_clock("blitz", 300, 1000), _contrast("time_trouble_score", "blitz", -0.08, 0.03)]
    gm = [_clock("blitz", 80, 1000), _contrast("time_trouble_score", "blitz", -0.07, 0.03)]
    blocks = compare(you, gm)
    assert [b["time_class"] for b in blocks] == ["blitz"]

    row = _row(blocks, "blitz", "time_trouble")
    assert row["you"]["value"] == pytest.approx(0.30)
    assert row["reference"]["value"] == pytest.approx(0.08)
    d = row["difference"]
    assert d["value"] == pytest.approx(0.22)
    assert d["ci_low"] < 0.22 < d["ci_high"]
    assert d["ci_low"] > 0
    assert row["verdict"] == "different"
    assert row["better"] == "lower"

    cost = _row(blocks, "blitz", "trouble_cost")
    assert cost["unit"] == "elo"
    assert cost["you"]["value"] < 0
    assert cost["verdict"] == "similar"
    assert cost["difference"]["ci_low"] < 0 < cost["difference"]["ci_high"]

    onset = _row(blocks, "blitz", "onset_move")
    assert onset["verdict"] == "descriptive"
    assert onset["difference"] is None
    assert onset["you"]["value"] == 31.0


def test_only_shared_time_controls_and_missing_data():
    you = [_clock("blitz", 30, 200), _clock("rapid", 10, 100)]
    gm = [
        _clock("blitz", 20, 200, onset=None),
        _clock("bullet", 50, 300),
        _contrast("after_loss_result", "blitz", 0.0, 0.0, label="not_enough_data"),
    ]
    blocks = compare(you, gm)
    assert [b["time_class"] for b in blocks] == ["blitz"]

    # Self-inflicted rests on 15 vs 10 trouble games: too few to test.
    si = _row(blocks, "blitz", "self_inflicted")
    assert si["verdict"] == "not_enough_data"
    assert si["difference"] is None

    # Neither side has a usable result: no row at all; one side missing: shown, not tested.
    keys = {r["key"] for r in blocks[0]["rows"]}
    assert "play_after_loss" not in keys
    assert _row(blocks, "blitz", "onset_move")["reference"] is None


def test_nothing_in_common():
    assert compare([_clock("blitz", 30, 200)], [_clock("bullet", 30, 200)]) == []


T0 = datetime(2026, 10, 1, 18, 0)


def _games(clocks: list[int], n_sessions: int = 40) -> list[dict]:
    raw = []
    for s in range(n_sessions):
        raw += session_games(
            s * 10, T0 + timedelta(days=s), ["win", "loss", "loss", "win"], clocks=clocks
        )
    return raw


def test_compare_api(client, games_api):
    slow = interleave([1800 - 75 * k for k in range(30)], [1790 - 30 * k for k in range(30)])
    fast = interleave([1800 - 20 * k for k in range(30)], [1790 - 30 * k for k in range(30)])
    for pid, clocks in ((1, slow), (2, fast)):
        games = _games(clocks)
        games_api.get(f"/players/{pid}/games").mock(
            return_value=httpx.Response(200, json={"items": games, "total": len(games)})
        )

    assert client.get("/players/1/compare/2").status_code == 404
    assert client.post("/players/1/runs").status_code == 201
    resp = client.get("/players/1/compare/2")
    assert resp.status_code == 404
    assert "player 2" in resp.json()["detail"]
    assert client.post("/players/2/runs").status_code == 201

    assert client.get("/players/1/compare/1").status_code == 422
    body = client.get("/players/1/compare/2").json()
    assert body["player_run"]["games_analyzed"] == 160
    assert body["reference_id"] == 2
    [block] = body["blocks"]
    row = next(r for r in block["rows"] if r["key"] == "time_trouble")
    assert row["you"]["value"] == 1.0
    assert row["reference"]["value"] == 0.0
    assert row["verdict"] == "different"
