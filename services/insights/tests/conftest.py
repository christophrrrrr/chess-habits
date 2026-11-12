from collections.abc import Iterator
from datetime import datetime, timedelta

import pytest
import respx
from fastapi.testclient import TestClient

from app.config import get_settings
from app.db import get_engine, get_sessionmaker

GAMES = "http://games.test"


def api_game(
    i: int,
    *,
    ended_at: datetime,
    result: str = "win",
    time_class: str = "blitz",
    base: int | None = 180,
    inc: int = 0,
    rating: int = 2000,
    opp: int = 2000,
    clocks: str | None = None,
    color: str = "white",
    detail: str | None = None,
    started_at: datetime | None = None,
    termination: str | None = None,
    final_material: int | None = 0,
) -> dict:
    return {
        "id": i,
        "time_class": time_class,
        "ended_at": ended_at.isoformat(),
        "player_color": color,
        "result": result,
        "result_detail": detail or ("win" if result == "win" else "resigned"),
        "player_rating": rating,
        "opponent_rating": opp,
        "base_seconds": base,
        "increment_seconds": inc,
        "ply_count": 40,
        "clocks": clocks,
        "started_at": (started_at or ended_at - timedelta(minutes=4)).isoformat(),
        "termination": termination,
        "final_material": final_material,
    }


def interleave(own: list[int], opp: list[int], color: str = "white") -> str:
    """Comma-separated per-ply clocks (tenths) from the player's and opponent's clocks."""
    first, second = (own, opp) if color == "white" else (opp, own)
    plies = [c for pair in zip(first, second, strict=False) for c in pair]
    if len(first) > len(second):
        plies.append(first[-1])
    return ",".join(str(c) for c in plies)


def session_games(start_id: int, start: datetime, results: list[str], **kw) -> list[dict]:
    """Games played back to back (5 minutes apart, 30 s between games) - one session."""
    return [
        api_game(start_id + k, ended_at=start + timedelta(minutes=5 * k), result=r, **kw)
        for k, r in enumerate(results)
    ]


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    monkeypatch.setenv("GAMES_SERVICE_URL", GAMES)
    for f in (get_settings, get_engine, get_sessionmaker):
        f.cache_clear()
    from app.main import create_app

    with TestClient(create_app()) as c:
        yield c
    get_engine().dispose()
    for f in (get_settings, get_engine, get_sessionmaker):
        f.cache_clear()


@pytest.fixture
def games_api() -> Iterator[respx.MockRouter]:
    with respx.mock(base_url=GAMES, assert_all_called=False) as mock:
        yield mock
