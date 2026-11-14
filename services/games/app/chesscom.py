"""Thin client for the chess.com Published-Data API (https://www.chess.com/news/view/published-data-api).

Requests are made one at a time (chess.com asks clients not to parallelise) with a
User-Agent that identifies Kiebitz. Any network problem surfaces as ChessComUnavailable
so the API can answer with a clear 503 instead of hanging.
"""

import re

import httpx

from app.config import Settings

_ARCHIVE = re.compile(r"/games/(\d{4})/(\d{2})$")


class ChessComError(Exception):
    pass


class ChessComUnavailable(ChessComError):
    """chess.com did not answer in time, rate-limited us or returned a server error."""


class ChessComNotFound(ChessComError):
    pass


class ChessComClient:
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self._client = httpx.Client(
            base_url=settings.chesscom_base_url,
            headers={"User-Agent": settings.chesscom_user_agent, "Accept": "application/json"},
            timeout=settings.chesscom_timeout_seconds,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def _get(self, path: str) -> dict:
        try:
            resp = self._client.get(path)
        except httpx.HTTPError as exc:
            raise ChessComUnavailable(
                f"chess.com request failed: {exc.__class__.__name__}"
            ) from exc
        if resp.status_code == 404:
            raise ChessComNotFound(path)
        if resp.status_code == 429:
            raise ChessComUnavailable("chess.com rate limit reached, try again in a minute")
        if resp.status_code >= 400:
            raise ChessComUnavailable(f"chess.com answered with HTTP {resp.status_code}")
        return resp.json()

    def get_profile(self, username: str) -> dict:
        return self._get(f"/player/{username.lower()}")

    def list_archive_months(self, username: str) -> list[str]:
        """Months with games, oldest first, as 'YYYY-MM'."""
        data = self._get(f"/player/{username.lower()}/games/archives")
        months = []
        for url in data.get("archives", []):
            m = _ARCHIVE.search(url)
            if m:
                months.append(f"{m.group(1)}-{m.group(2)}")
        return months

    def get_month_games(self, username: str, month: str) -> list[dict]:
        year, mon = month.split("-")
        return self._get(f"/player/{username.lower()}/games/{year}/{mon}").get("games", [])
