"""Response models."""

import json
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TimeClass = Literal["bullet", "blitz", "rapid", "classical"]
RuleKind = Literal["clock_checkpoint", "stop_loss"]
StopRule = Literal["two_in_a_row", "three_in_a_row", "three_in_session"]


class AnalysisInfo(BaseModel):
    key: str
    name: str
    question: str


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    analysis_key: str
    time_class: str
    kind: str
    metric: str
    label: str
    title: str
    summary: str
    effect: float | None
    ci_low: float | None
    ci_high: float | None
    mde: float | None
    p_value: float | None
    sample_size: int
    details: dict

    @field_validator("details", mode="before")
    @classmethod
    def _parse(cls, v):
        return json.loads(v) if isinstance(v, str) else v


class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_id: int
    status: str
    games_analyzed: int
    created_at: datetime
    finished_at: datetime | None


class RunDetail(RunOut):
    findings: list[FindingOut]


def _naive_utc(value: datetime) -> datetime:
    return value.astimezone(UTC).replace(tzinfo=None) if value.tzinfo else value


class RuleCreate(BaseModel):
    """A clock checkpoint needs `min_share` (and optionally `move`, default 20); a stop-loss
    rule needs `stop_rule`. `adopted_at` defaults to now and may lie in the past (for a rule
    the player already follows), never in the future."""

    time_class: TimeClass
    kind: RuleKind
    move: int | None = Field(default=None, ge=10, le=40)
    min_share: float | None = Field(default=None, gt=0, lt=1)
    stop_rule: StopRule | None = None
    note: str | None = Field(default=None, max_length=200)
    adopted_at: datetime | None = None

    @model_validator(mode="after")
    def _check(self) -> "RuleCreate":
        if self.kind == "clock_checkpoint":
            if self.min_share is None or self.stop_rule is not None:
                raise ValueError("a clock checkpoint needs min_share and no stop_rule")
            self.move = self.move or 20
        elif self.stop_rule is None or self.move is not None or self.min_share is not None:
            raise ValueError("a stop-loss rule needs stop_rule and no move or min_share")
        if self.adopted_at is not None:
            self.adopted_at = _naive_utc(self.adopted_at)
            if self.adopted_at > datetime.now(UTC).replace(tzinfo=None):
                raise ValueError("adopted_at cannot be in the future")
        return self


class RuleUpdate(BaseModel):
    """Changing the threshold restarts the count (the old baseline no longer applies)."""

    move: int | None = Field(default=None, ge=10, le=40)
    min_share: float | None = Field(default=None, gt=0, lt=1)
    note: str | None = Field(default=None, max_length=200)
    retired: bool | None = None


class RuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_id: int
    time_class: str
    kind: str
    move: int | None
    min_share: float | None
    stop_rule: str | None
    note: str | None
    description: str
    adopted_at: datetime
    retired_at: datetime | None
    created_at: datetime


class CompareSide(BaseModel):
    value: float
    ci_low: float | None
    ci_high: float | None
    n: int


class CompareDifference(BaseModel):
    value: float
    ci_low: float
    ci_high: float


class CompareRow(BaseModel):
    key: str
    name: str
    unit: Literal["share", "points", "elo", "move"]
    better: Literal["lower", "higher"] | None
    you: CompareSide | None
    reference: CompareSide | None
    difference: CompareDifference | None
    q_value: float | None
    verdict: Literal["different", "maybe_different", "similar", "not_enough_data", "descriptive"]


class CompareBlock(BaseModel):
    time_class: str
    rows: list[CompareRow]


class Comparison(BaseModel):
    """A player's habits next to a reference player's (a grandmaster), per time control."""

    player_id: int
    reference_id: int
    player_run: RunOut
    reference_run: RunOut
    blocks: list[CompareBlock]


# ---- deep analysis (computed in the browser) ----------------------------------------------

MoveType = Literal["capture", "check", "quiet", "retreat", "pawn", "king", "castle"]


class EngineMove(BaseModel):
    """Stockfish on one of the player's positions. Evaluations are centipawns from the
    player's side (mate scores capped at +-10000), from a MultiPV-2 search."""

    k: int = Field(ge=1, le=400, description="own move number (1 = first move)")
    best: str = Field(min_length=4, max_length=5, description="best move, UCI")
    type: MoveType = Field(description="kind of move the best move is")
    b: int = Field(ge=-10000, le=10000, description="eval of the best move")
    s: int | None = Field(default=None, ge=-10000, le=10000, description="eval of the 2nd best")
    p: int = Field(ge=-10000, le=10000, description="eval of the move played")
    legal: int = Field(ge=0, le=300)
    check: bool = False
    recapture: bool = False
    fen: str | None = Field(default=None, max_length=100, description="only for critical ones")


class GameAnalysisIn(BaseModel):
    game_id: int
    position_keys: list[str] = Field(default_factory=list, max_length=40)
    engine: str | None = Field(default=None, max_length=32)
    final_cp: int | None = Field(default=None, ge=-10000, le=10000)
    moves: list[EngineMove] | None = Field(default=None, max_length=300)

    @field_validator("position_keys")
    @classmethod
    def _hex_keys(cls, keys: list[str]) -> list[str]:
        for k in keys:
            if len(k) != 8 or any(c not in "0123456789abcdef" for c in k):
                raise ValueError("position keys are 8 lowercase hex characters")
        return keys


class GameAnalysisBatch(BaseModel):
    games: list[GameAnalysisIn] = Field(min_length=1, max_length=200)


class DeepStatus(BaseModel):
    positions: int  # games with position keys
    engine: int  # games with a Stockfish pass
    engine_game_ids: list[int]
    position_game_ids: list[int]
    final_game_ids: list[int]  # games whose final position has an engine evaluation
