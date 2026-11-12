"""Serial, cached access to the chess.com Published-Data API.

https://www.chess.com/news/view/published-data-api asks for serial requests; parallel
requests may get HTTP 429. Every response is cached on disk. Past months never change,
the current month is refetched when the cache is older than MAX_AGE_CURRENT seconds.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from .paths import CHESSCOM

UA = "Chess Habits-research/0.1 (research experiments; contact: rintzchristoph@gmail.com)"
BASE = "https://api.chess.com/pub"
MAX_AGE_CURRENT = 6 * 3600
_session = requests.Session()
_session.headers.update({"User-Agent": UA, "Accept": "application/json"})
_last_request = 0.0


def _get(url: str) -> dict | None:
    global _last_request
    for attempt in range(6):
        wait = 0.35 - (time.time() - _last_request)
        if wait > 0:
            time.sleep(wait)
        _last_request = time.time()
        r = _session.get(url, timeout=60)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (404, 410):
            return None
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(5 * (attempt + 1))
            continue
        r.raise_for_status()
    raise RuntimeError(f"giving up on {url}")


def get_cached(url: str, path: Path, max_age: float | None = None) -> dict | None:
    if path.exists():
        age = time.time() - path.stat().st_mtime
        if max_age is None or age < max_age:
            return json.loads(path.read_text(encoding="utf-8"))
    data = _get(url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return data


def player_dir(username: str) -> Path:
    return CHESSCOM / username.lower()


def stats(username: str) -> dict | None:
    u = username.lower()
    return get_cached(f"{BASE}/player/{u}/stats", player_dir(u) / "stats.json", max_age=7 * 86400)


def profile(username: str) -> dict | None:
    u = username.lower()
    return get_cached(f"{BASE}/player/{u}", player_dir(u) / "profile.json", max_age=7 * 86400)


def archives(username: str) -> list[str]:
    u = username.lower()
    d = get_cached(f"{BASE}/player/{u}/games/archives", player_dir(u) / "archives.json", max_age=MAX_AGE_CURRENT)
    return (d or {}).get("archives", [])


def fetch_games(username: str, verbose: bool = True) -> list[dict]:
    """All games of a player (every monthly archive), oldest first."""
    u = username.lower()
    now = datetime.now(timezone.utc)
    cur = f"{now.year:04d}/{now.month:02d}"
    games: list[dict] = []
    urls = archives(u)
    for i, url in enumerate(urls):
        ym = "/".join(url.rstrip("/").split("/")[-2:])
        path = player_dir(u) / "games" / (ym.replace("/", "-") + ".json")
        max_age = MAX_AGE_CURRENT if ym >= cur else None
        if verbose and not path.exists():
            print(f"  {u}: fetching {ym} ({i + 1}/{len(urls)})", flush=True)
        d = get_cached(url, path, max_age=max_age)
        games.extend((d or {}).get("games", []))
    games.sort(key=lambda g: g.get("end_time", 0))
    return games


def titled(title: str) -> list[str]:
    d = get_cached(f"{BASE}/titled/{title}", CHESSCOM / "_lists" / f"titled-{title}.json", max_age=7 * 86400)
    return (d or {}).get("players", [])
