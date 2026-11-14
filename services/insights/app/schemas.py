"""Response models."""

import json
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


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
