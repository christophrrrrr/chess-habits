"""Runs every registered analysis over a player's games and stores the findings."""

import json
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.analysis.analyses import ANALYSES
from app.analysis.games import GameRecord, assign_sessions
from app.models import AnalysisRun, Finding


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def run_analyses(session: Session, player_id: int, raw_games: list[dict]) -> AnalysisRun:
    games = assign_sessions([GameRecord.from_api(g) for g in raw_games])
    run = AnalysisRun(
        player_id=player_id, status="done", games_analyzed=len(games), created_at=utcnow()
    )
    for analysis in ANALYSES:
        for draft in analysis.run(games):
            c = draft.comparison
            run.findings.append(
                Finding(
                    analysis_key=draft.analysis_key,
                    time_class=draft.time_class,
                    title=draft.title[:200],
                    summary=draft.summary[:1000],
                    effect=round(c.effect, 4),
                    ci_low=round(c.ci_low, 4),
                    ci_high=round(c.ci_high, 4),
                    sample_size=c.n_group + c.n_rest,
                    confidence=c.confidence,
                    details=json.dumps(
                        {
                            **draft.details,
                            "n_group": c.n_group,
                            "n_rest": c.n_rest,
                            "group_mean": round(c.group_mean, 4),
                            "rest_mean": round(c.rest_mean, 4),
                        }
                    ),
                )
            )
    run.finished_at = utcnow()
    session.add(run)
    session.commit()
    return run
