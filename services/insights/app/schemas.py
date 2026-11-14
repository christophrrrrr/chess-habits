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
