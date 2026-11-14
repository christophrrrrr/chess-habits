import os
from collections.abc import Iterator

import pytest
import respx
from fastapi.testclient import TestClient

from app.config import get_settings
from app.db import get_engine, get_sessionmaker

CHESSCOM = "https://api.chess.com/pub"

PGN = """[Event "Live Chess"]
[Site "Chess.com"]
[White "chrisaxm"]
[Black "opponent1"]
[Result "1-0"]
[ECO "C50"]
[ECOUrl "https://www.chess.com/openings/Italian-Game"]
[TimeControl "180+2"]
[UTCDate "2026.10.01"]
[UTCTime "18:00:05"]
[CurrentPosition "4k3/8/8/8/8/8/8/R3K3 b - - 0 40"]
[Termination "chrisaxm won by resignation"]

1. e4 {[%clk 0:03:01.9]} 1... e5 {[%clk 0:03:01.5]} 2. Nf3 {[%clk 0:03:02.3]} 2... Nc6
{[%clk 0:02:59.8]} 3. Bc4 {[%clk 0:03:03.1]} 1-0
"""


def chesscom_game(uuid: str, *, end_time: int = 1793000000, rules: str = "chess", **kw) -> dict:
    game = {
        "url": f"https://www.chess.com/game/live/{uuid}",
        "uuid": uuid,
        "pgn": PGN,
        "time_control": "180+2",
        "end_time": end_time,
        "rated": True,
        "time_class": "blitz",
        "rules": rules,
        "eco": "https://www.chess.com/openings/Italian-Game",
        "white": {"username": "ChrisAxm", "rating": 2389, "result": "win"},
        "black": {"username": "opponent1", "rating": 2350, "result": "resigned"},
    }
    game.update(kw)
    return game


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173")
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()
    from app.main import create_app

    with TestClient(create_app()) as c:
        yield c
    get_engine().dispose()
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()
    os.environ.pop("DATABASE_URL", None)


@pytest.fixture
def chesscom() -> Iterator[respx.MockRouter]:
    with respx.mock(base_url=CHESSCOM, assert_all_called=False) as mock:
        yield mock


@pytest.fixture
def player(client, chesscom) -> dict:
    chesscom.get("/player/chrisaxm").respond(200, json={"username": "chrisaxm", "name": "Chris"})
    resp = client.post("/players", json={"username": "ChrisAxm"})
    assert resp.status_code == 201, resp.text
    return resp.json()
