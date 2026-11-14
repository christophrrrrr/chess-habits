from datetime import datetime, timedelta

import httpx
from conftest import session_games

T0 = datetime(2026, 10, 1, 18, 0)


def _games(n_sessions: int = 40) -> list[dict]:
    raw = []
    for s in range(n_sessions):
        raw += session_games(s * 10, T0 + timedelta(days=s), ["win", "loss", "loss", "win"])
    return raw


def _mock_pages(games_api, games: list[dict], page: int = 500):
    def handler(request):
        offset = int(request.url.params.get("offset", 0))
        limit = int(request.url.params.get("limit", page))
        items = games[offset : offset + limit]
        return httpx.Response(200, json={"items": items, "total": len(games)})

    games_api.get("/players/1/games").mock(side_effect=handler)


def test_health_and_analyses(client):
    assert client.get("/health").json() == {"status": "ok", "service": "insights"}
    keys = [a["key"] for a in client.get("/analyses").json()]
    assert keys == ["tilt", "session_fatigue", "time_trouble"]


def test_run_stores_findings(client, games_api):
    games = _games()
    _mock_pages(games_api, games)
    resp = client.post("/players/1/runs")
    assert resp.status_code == 201, resp.text
    run = resp.json()
    assert run["games_analyzed"] == len(games)
    keys = {f["analysis_key"] for f in run["findings"]}
    assert keys == {"tilt", "session_fatigue", "time_trouble"}
    tilt = next(f for f in run["findings"] if f["analysis_key"] == "tilt")
    assert tilt["confidence"] in ("high", "medium")
    assert tilt["details"]["n_group"] > 0

    latest = client.get("/players/1/findings").json()
    assert latest["id"] == run["id"]
    assert [r["id"] for r in client.get("/players/1/runs").json()] == [run["id"]]
    assert client.get(f"/runs/{run['id']}").json()["findings"] == run["findings"]


def test_run_pages_through_all_games(client, games_api, monkeypatch):
    import app.games_client as gc

    monkeypatch.setattr(gc, "PAGE_SIZE", 50)
    games = _games()
    _mock_pages(games_api, games, page=50)
    assert client.post("/players/1/runs").json()["games_analyzed"] == 160


def test_run_unknown_player(client, games_api):
    games_api.get("/players/2/games").respond(404, json={"detail": "player not found"})
    assert client.post("/players/2/runs").status_code == 404


def test_games_service_down_keeps_old_findings(client, games_api):
    _mock_pages(games_api, _games())
    first = client.post("/players/1/runs").json()

    games_api.get("/players/1/games").mock(side_effect=httpx.ConnectError("down"))
    resp = client.post("/players/1/runs")
    assert resp.status_code == 503
    assert "still available" in resp.json()["detail"]
    assert client.get("/players/1/findings").json()["id"] == first["id"]

    games_api.get("/players/1/games").respond(500)
    assert client.post("/players/1/runs").status_code == 503


def test_delete_run_and_missing(client, games_api):
    assert client.get("/players/1/findings").status_code == 404
    _mock_pages(games_api, _games())
    run_id = client.post("/players/1/runs").json()["id"]
    assert client.delete(f"/runs/{run_id}").status_code == 204
    assert client.get(f"/runs/{run_id}").status_code == 404
    assert client.delete(f"/runs/{run_id}").status_code == 404


def test_empty_player(client, games_api):
    games_api.get("/players/1/games").respond(200, json={"items": [], "total": 0})
    run = client.post("/players/1/runs").json()
    assert run["games_analyzed"] == 0
    assert run["findings"] == []
