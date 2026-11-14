import httpx


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "games"}


def test_create_player_normalises_username(player):
    assert player["username"] == "chrisaxm"
    assert player["platform"] == "chesscom"
    assert player["display_name"] == "Chris"


def test_create_duplicate_player_conflicts(client, chesscom, player):
    resp = client.post("/players", json={"username": "chrisaxm"})
    assert resp.status_code == 409


def test_create_unknown_chesscom_user(client, chesscom):
    chesscom.get("/player/nobody123").respond(404)
    resp = client.post("/players", json={"username": "nobody123"})
    assert resp.status_code == 422
    assert "no chess.com account" in resp.json()["detail"]


def test_create_player_when_chesscom_down(client, chesscom):
    chesscom.get("/player/someone").mock(side_effect=httpx.ConnectTimeout("boom"))
    resp = client.post("/players", json={"username": "someone"})
    assert resp.status_code == 503
    assert "not reachable" in resp.json()["detail"]


def test_create_player_rejects_bad_username(client):
    resp = client.post("/players", json={"username": "bad name!"})
    assert resp.status_code == 422


def test_list_get_update_delete(client, player):
    pid = player["id"]
    assert [p["id"] for p in client.get("/players").json()] == [pid]

    detail = client.get(f"/players/{pid}").json()
    assert detail["game_counts"] == {}

    resp = client.patch(f"/players/{pid}", json={"notes": "main account"})
    assert resp.status_code == 200
    assert resp.json()["notes"] == "main account"
    assert resp.json()["display_name"] == "Chris"

    assert client.delete(f"/players/{pid}").status_code == 204
    assert client.get(f"/players/{pid}").status_code == 404
    assert client.delete(f"/players/{pid}").status_code == 404
    assert client.patch(f"/players/{pid}", json={"notes": "x"}).status_code == 404


def test_request_is_logged_as_json(client, caplog):
    import json
    import logging

    from app.logging_setup import JsonFormatter

    with caplog.at_level(logging.INFO, logger="request"):
        client.get("/health")
    records = [r for r in caplog.records if r.name == "request"]
    assert len(records) == 1
    line = json.loads(JsonFormatter("games").format(records[0]))
    assert line["method"] == "GET"
    assert line["path"] == "/health"
    assert line["status"] == 200
    assert line["service"] == "games"
    assert line["duration_ms"] >= 0


def test_cors_allows_ui_origin(client):
    resp = client.options(
        "/players",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"
    resp = client.options(
        "/players",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in resp.headers


def test_reference_players_are_listed_separately(client, chesscom, player):
    chesscom.get("/player/hikaru").respond(200, json={"username": "hikaru", "name": "Hikaru"})
    resp = client.post("/players", json={"username": "Hikaru", "kind": "reference"})
    assert resp.status_code == 201
    assert resp.json()["kind"] == "reference"
    assert player["kind"] == "player"

    assert [p["username"] for p in client.get("/players").json()] == ["chrisaxm", "hikaru"]
    assert [p["username"] for p in client.get("/players?kind=reference").json()] == ["hikaru"]
    assert [p["username"] for p in client.get("/players?kind=player").json()] == ["chrisaxm"]
    assert client.get("/players?kind=robot").status_code == 422
    assert client.post("/players", json={"username": "x_y_z", "kind": "robot"}).status_code == 422
