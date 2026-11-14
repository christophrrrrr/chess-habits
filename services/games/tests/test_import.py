from datetime import UTC, datetime

import httpx
from conftest import chesscom_game

ARCHIVES = {
    "archives": [
        "https://api.chess.com/pub/player/chrisaxm/games/2026/09",
        "https://api.chess.com/pub/player/chrisaxm/games/2026/10",
    ]
}


def test_list_archives_marks_imported_months(client, chesscom, player):
    pid = player["id"]
    chesscom.get("/player/chrisaxm/games/archives").respond(200, json=ARCHIVES)
    chesscom.get("/player/chrisaxm/games/2026/09").respond(
        200, json={"games": [chesscom_game("a1"), chesscom_game("a2")]}
    )
    client.post(f"/players/{pid}/imports", json={"month": "2026-09"})

    months = client.get(f"/players/{pid}/archives").json()
    assert months == [
        {"month": "2026-09", "imported": True, "complete": True, "game_count": 2},
        {"month": "2026-10", "imported": False, "complete": False, "game_count": None},
    ]


def test_import_month_stores_games_and_skips_variants(client, chesscom, player):
    pid = player["id"]
    chesscom.get("/player/chrisaxm/games/2026/09").respond(
        200,
        json={
            "games": [
                chesscom_game("g1"),
                chesscom_game("g2", time_class="rapid", time_control="600"),
                chesscom_game("g3", rules="chess960"),
            ]
        },
    )
    resp = client.post(f"/players/{pid}/imports", json={"month": "2026-09"})
    assert resp.status_code == 200
    body = resp.json()
    assert body == {
        "month": "2026-09",
        "fetched": 3,
        "new_games": 2,
        "skipped": False,
        "complete": True,
    }

    page = client.get(f"/players/{pid}/games").json()
    assert page["total"] == 2
    game = page["items"][0]
    assert game["player_color"] == "white"
    assert game["result"] == "win"
    assert game["result_detail"] == "win"
    assert game["opponent_username"] == "opponent1"
    assert game["eco"] == "C50"
    assert game["opening"] == "Italian Game"
    assert game["ply_count"] == 5
    assert game["clocks"] == "1819,1815,1823,1798,1831"
    assert "pgn" not in game

    detail = client.get(f"/players/{pid}").json()
    assert detail["game_counts"] == {"blitz": 1, "rapid": 1}
    assert detail["last_imported_at"] is not None


def test_completed_month_is_not_fetched_again(client, chesscom, player):
    pid = player["id"]
    route = chesscom.get("/player/chrisaxm/games/2026/09").respond(
        200, json={"games": [chesscom_game("g1")]}
    )
    client.post(f"/players/{pid}/imports", json={"month": "2026-09"})
    resp = client.post(f"/players/{pid}/imports", json={"month": "2026-09"})
    assert resp.json()["skipped"] is True
    assert route.call_count == 1


def test_current_month_can_be_reimported_without_duplicates(client, chesscom, player):
    pid = player["id"]
    month = datetime.now(UTC).strftime("%Y-%m")
    y, m = month.split("-")
    route = chesscom.get(f"/player/chrisaxm/games/{y}/{m}")
    route.respond(200, json={"games": [chesscom_game("c1")]})
    first = client.post(f"/players/{pid}/imports", json={"month": month}).json()
    assert first["complete"] is False

    route.respond(200, json={"games": [chesscom_game("c1"), chesscom_game("c2")]})
    second = client.post(f"/players/{pid}/imports", json={"month": month}).json()
    assert second["new_games"] == 1
    assert client.get(f"/players/{pid}/games").json()["total"] == 2


def test_import_when_chesscom_down_returns_503(client, chesscom, player):
    pid = player["id"]
    chesscom.get("/player/chrisaxm/games/2026/09").respond(503)
    resp = client.post(f"/players/{pid}/imports", json={"month": "2026-09"})
    assert resp.status_code == 503
    assert "Stored data is still available" in resp.json()["detail"]


def test_import_rate_limited(client, chesscom, player):
    pid = player["id"]
    chesscom.get("/player/chrisaxm/games/2026/09").respond(429)
    resp = client.post(f"/players/{pid}/imports", json={"month": "2026-09"})
    assert resp.status_code == 503
    assert "rate limit" in resp.json()["detail"]


def test_archives_when_chesscom_down(client, chesscom, player):
    chesscom.get("/player/chrisaxm/games/archives").mock(side_effect=httpx.ReadTimeout("slow"))
    assert client.get(f"/players/{player['id']}/archives").status_code == 503


def test_import_validates_month(client, player):
    resp = client.post(f"/players/{player['id']}/imports", json={"month": "2026-13"})
    assert resp.status_code == 422


def test_games_filters_and_pagination(client, chesscom, player):
    pid = player["id"]
    games = [chesscom_game(f"b{i}", end_time=1790000000 + i) for i in range(5)]
    games.append(chesscom_game("r1", time_class="rapid", end_time=1795000000))
    chesscom.get("/player/chrisaxm/games/2026/09").respond(200, json={"games": games})
    client.post(f"/players/{pid}/imports", json={"month": "2026-09"})

    blitz = client.get(f"/players/{pid}/games", params={"time_class": "blitz", "limit": 2}).json()
    assert blitz["total"] == 5
    assert len(blitz["items"]) == 2

    with_pgn = client.get(f"/players/{pid}/games", params={"include_pgn": True}).json()
    assert with_pgn["items"][0]["platform_game_id"] == "r1"
    assert with_pgn["items"][0]["pgn"].startswith("[Event")

    game_id = with_pgn["items"][0]["id"]
    assert client.get(f"/games/{game_id}").json()["pgn"].startswith("[Event")
    assert client.get("/games/99999").status_code == 404
    assert client.get("/players/99999/games").status_code == 404


def test_deleting_player_deletes_games(client, chesscom, player):
    pid = player["id"]
    chesscom.get("/player/chrisaxm/games/2026/09").respond(
        200, json={"games": [chesscom_game("d1")]}
    )
    client.post(f"/players/{pid}/imports", json={"month": "2026-09"})
    game_id = client.get(f"/players/{pid}/games").json()["items"][0]["id"]
    client.delete(f"/players/{pid}")
    assert client.get(f"/games/{game_id}").status_code == 404
