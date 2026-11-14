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
    title: str
    summary: str
    effect: float
    ci_low: float
    ci_high: float
    sample_size: int
    confidence: str
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
