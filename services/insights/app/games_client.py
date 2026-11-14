"""HTTP client for the games service. Any failure becomes GamesServiceUnavailable, so the
insights API can answer with a clear 503 while stored findings stay readable."""

import httpx

from app.config import Settings

PAGE_SIZE = 500


class GamesServiceError(Exception):
    pass


class GamesServiceUnavailable(GamesServiceError):
    pass


class PlayerNotFound(GamesServiceError):
    pass


class GamesClient:
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self._client = httpx.Client(
            base_url=settings.games_service_url,
            timeout=settings.games_service_timeout_seconds,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def _get(self, path: str, params: dict | None = None) -> dict:
        try:
            resp = self._client.get(path, params=params)
        except httpx.HTTPError as exc:
            reason = exc.__class__.__name__
            raise GamesServiceUnavailable(f"games service request failed: {reason}") from exc
        if resp.status_code == 404:
            raise PlayerNotFound(path)
        if resp.status_code >= 400:
            raise GamesServiceUnavailable(f"games service answered with HTTP {resp.status_code}")
        return resp.json()

    def get_all_games(self, player_id: int) -> list[dict]:
        games: list[dict] = []
        offset = 0
        while True:
            page = self._get(
                f"/players/{player_id}/games", params={"limit": PAGE_SIZE, "offset": offset}
            )
            games.extend(page["items"])
            offset += len(page["items"])
            if not page["items"] or offset >= page["total"]:
                return games
