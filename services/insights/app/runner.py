"""Runs every registered analysis over a player's games and stores the findings."""

import json
import math
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.analysis.analyses import ANALYSES
from app.analysis.games import GameRecord, prepare
from app.analysis.stats import benjamini_hochberg, label_for
from app.models import AnalysisRun, Finding


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _clean(value):
    """JSON-safe copy: NaN/inf become null."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_clean(v) for v in value]
    return value


def _r(x: float | None) -> float | None:
    return None if x is None else round(x, 4)


def run_analyses(session: Session, player_id: int, raw_games: list[dict]) -> AnalysisRun:
    games = prepare([GameRecord.from_api(g) for g in raw_games])
    drafts = [d for analysis in ANALYSES for d in analysis.run(games)]

    # Multiple-testing correction over every contrast that has enough data to be judged.
    testable = [d for d in drafts if d.contrast is not None and d.contrast.n_small >= d.min_n]
    q_values = benjamini_hochberg([d.contrast.p_value for d in testable])
    q_by_draft = {id(d): q for d, q in zip(testable, q_values, strict=True)}

    run = AnalysisRun(
        player_id=player_id, status="done", games_analyzed=len(games), created_at=utcnow()
    )
    for d in drafts:
        c = d.contrast
        q = q_by_draft.get(id(d))
        label = "profile" if d.kind == "profile" else label_for(q, c.n_small if c else 0, d.min_n)
        title, summary = d.text(label)
        details = dict(d.details)
        if c is not None:
            details.update(
                n_a=c.n_a, n_b=c.n_b, mean_a=_r(c.mean_a), mean_b=_r(c.mean_b), q_value=_r(q)
            )
        run.findings.append(
            Finding(
                analysis_key=d.analysis_key,
                time_class=d.time_class,
                kind=d.kind,
                metric=d.metric,
                label=label,
                title=title[:200],
                summary=summary[:1000],
                effect=_r(c.effect) if c else None,
                ci_low=_r(c.ci_low) if c else None,
                ci_high=_r(c.ci_high) if c else None,
                mde=_r(c.mde) if c else None,
                p_value=_r(c.p_value) if c else None,
                sample_size=d.sample_size,
                details=json.dumps(_clean(details)),
            )
        )
    run.finished_at = utcnow()
    session.add(run)
    session.commit()
    return run
