"""Request and response models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Platform = Literal["chesscom"]


class PlayerCreate(BaseModel):
    platform: Platform = "chesscom"
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    notes: str | None = Field(default=None, max_length=500)


class PlayerUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=500)


class PlayerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: str
    username: str
    display_name: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    last_imported_at: datetime | None


class PlayerDetail(PlayerOut):
    game_counts: dict[str, int]


class ArchiveMonth(BaseModel):
    month: str
    imported: bool
    complete: bool
    game_count: int | None


class ImportRequest(BaseModel):
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")


class ImportResult(BaseModel):
    month: str
    fetched: int
    new_games: int
    skipped: bool
    complete: bool


class GameOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_id: int
    platform_game_id: str
    url: str | None
    time_class: str
    time_control: str
    base_seconds: int | None
    increment_seconds: int | None
    rated: bool
    ended_at: datetime
    started_at: datetime | None
    player_color: str
    player_rating: int | None
    opponent_username: str
    opponent_rating: int | None
    result: str
    result_detail: str
    eco: str | None
    opening: str | None
    ply_count: int
    clocks: str | None
    termination: str | None
    final_material: int | None


class GameWithPgn(GameOut):
    pgn: str


class GamePage(BaseModel):
    items: list[GameOut] | list[GameWithPgn]
    total: int
    limit: int
    offset: int
