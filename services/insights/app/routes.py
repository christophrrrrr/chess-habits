"""HTTP API of the insights service."""

import json
from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis.analyses import ANALYSES
from app.analysis.compare import compare
from app.config import get_settings
from app.db import get_session
from app.games_client import GamesClient, GamesServiceUnavailable, PlayerNotFound
from app.models import AnalysisRun, GameAnalysis, Rule
from app.runner import run_analyses, utcnow
from app.schemas import (
    AnalysisInfo,
    Comparison,
    DeepStatus,
    FindingOut,
    GameAnalysisBatch,
    RuleCreate,
    RuleOut,
    RuleUpdate,
    RunDetail,
    RunOut,
)

router = APIRouter()


def get_games_client() -> Iterator[GamesClient]:
    client = GamesClient(get_settings())
    try:
        yield client
    finally:
        client.close()


@router.get("/health", tags=["ops"])
def health() -> dict:
    return {"status": "ok", "service": get_settings().service_name}


@router.get("/analyses", response_model=list[AnalysisInfo], tags=["analyses"])
def list_analyses() -> list[AnalysisInfo]:
    return [AnalysisInfo(key=a.key, name=a.name, question=a.question) for a in ANALYSES]


@router.post("/players/{player_id}/runs", response_model=RunDetail, status_code=201, tags=["runs"])
def create_run(
    player_id: int,
    utc_offset_minutes: int = Query(
        0, ge=-14 * 60, le=14 * 60, description="Player's time zone, for the time-of-day card"
    ),
    session: Session = Depends(get_session),
    games: GamesClient = Depends(get_games_client),
) -> AnalysisRun:
    try:
        raw = games.get_all_games(player_id)
    except PlayerNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="player not found") from None
    except GamesServiceUnavailable as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"The games service is not reachable right now ({exc}). "
                "Previously computed findings are still available."
            ),
        ) from exc
    return run_analyses(session, player_id, raw, utc_offset_minutes)


@router.get("/players/{player_id}/runs", response_model=list[RunOut], tags=["runs"])
def list_runs(player_id: int, session: Session = Depends(get_session)) -> list[AnalysisRun]:
    return list(
        session.scalars(
            select(AnalysisRun)
            .where(AnalysisRun.player_id == player_id)
            .order_by(AnalysisRun.created_at.desc(), AnalysisRun.id.desc())
        )
    )


def _latest_run(session: Session, player_id: int) -> AnalysisRun | None:
    return session.scalar(
        select(AnalysisRun)
        .where(AnalysisRun.player_id == player_id, AnalysisRun.status == "done")
        .order_by(AnalysisRun.created_at.desc(), AnalysisRun.id.desc())
        .limit(1)
    )


@router.get("/players/{player_id}/findings", response_model=RunDetail, tags=["runs"])
def latest_findings(player_id: int, session: Session = Depends(get_session)) -> AnalysisRun:
    run = _latest_run(session, player_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="no analysis run yet")
    return run


@router.get(
    "/players/{player_id}/compare/{reference_id}", response_model=Comparison, tags=["compare"]
)
def compare_players(
    player_id: int, reference_id: int, session: Session = Depends(get_session)
) -> Comparison:
    """Your habits next to a reference player's (a grandmaster), from both latest runs."""
    if player_id == reference_id:
        raise HTTPException(422, detail="pick a different player to compare with")
    runs = {pid: _latest_run(session, pid) for pid in (player_id, reference_id)}
    missing = [pid for pid, run in runs.items() if run is None]
    if missing:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"no analysis run yet for player {', '.join(map(str, missing))}",
        )

    def findings(run: AnalysisRun) -> list[dict]:
        return [FindingOut.model_validate(f).model_dump() for f in run.findings]

    mine, theirs = runs[player_id], runs[reference_id]
    return Comparison(
        player_id=player_id,
        reference_id=reference_id,
        player_run=RunOut.model_validate(mine),
        reference_run=RunOut.model_validate(theirs),
        blocks=compare(findings(mine), findings(theirs)),
    )


@router.get("/runs/{run_id}", response_model=RunDetail, tags=["runs"])
def get_run(run_id: int, session: Session = Depends(get_session)) -> AnalysisRun:
    run = session.get(AnalysisRun, run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="run not found")
    return run


@router.delete("/runs/{run_id}", status_code=204, tags=["runs"])
def delete_run(run_id: int, session: Session = Depends(get_session)) -> Response:
    run = session.get(AnalysisRun, run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="run not found")
    session.delete(run)
    session.commit()
    return Response(status_code=204)


# ---- rules ------------------------------------------------------------------------------


def _get_rule(session: Session, rule_id: int) -> Rule:
    rule = session.get(Rule, rule_id)
    if rule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="rule not found")
    return rule


def _ensure_single_active(session: Session, rule: Rule) -> None:
    """One active rule per kind and time class keeps the cards readable."""
    clash = session.scalar(
        select(Rule).where(
            Rule.player_id == rule.player_id,
            Rule.time_class == rule.time_class,
            Rule.kind == rule.kind,
            Rule.retired_at.is_(None),
            Rule.id != (rule.id or -1),
        )
    )
    if clash is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"There is already an active rule of this kind for {rule.time_class}. "
            "Stop tracking it first.",
        )


@router.post("/players/{player_id}/rules", response_model=RuleOut, status_code=201, tags=["rules"])
def create_rule(player_id: int, body: RuleCreate, session: Session = Depends(get_session)) -> Rule:
    now = utcnow()
    rule = Rule(
        player_id=player_id,
        time_class=body.time_class,
        kind=body.kind,
        move=body.move,
        min_share=body.min_share,
        stop_rule=body.stop_rule,
        note=body.note,
        adopted_at=body.adopted_at or now,
        created_at=now,
    )
    _ensure_single_active(session, rule)
    session.add(rule)
    session.commit()
    return rule


@router.get("/players/{player_id}/rules", response_model=list[RuleOut], tags=["rules"])
def list_rules(
    player_id: int, include_retired: bool = False, session: Session = Depends(get_session)
) -> list[Rule]:
    query = select(Rule).where(Rule.player_id == player_id).order_by(Rule.id)
    if not include_retired:
        query = query.where(Rule.retired_at.is_(None))
    return list(session.scalars(query))


@router.get("/rules/{rule_id}", response_model=RuleOut, tags=["rules"])
def get_rule(rule_id: int, session: Session = Depends(get_session)) -> Rule:
    return _get_rule(session, rule_id)


@router.patch("/rules/{rule_id}", response_model=RuleOut, tags=["rules"])
def update_rule(rule_id: int, body: RuleUpdate, session: Session = Depends(get_session)) -> Rule:
    rule = _get_rule(session, rule_id)
    changes = body.model_dump(exclude_unset=True)
    threshold = {k: v for k, v in changes.items() if k in ("move", "min_share")}
    if threshold:
        if rule.kind != "clock_checkpoint" or None in threshold.values():
            raise HTTPException(
                422,
                detail="move and min_share can only be changed on a clock checkpoint",
            )
        for key, value in threshold.items():
            setattr(rule, key, value)
        rule.adopted_at = utcnow()
    if "note" in changes:
        rule.note = changes["note"]
    if changes.get("retired") is True and rule.retired_at is None:
        rule.retired_at = utcnow()
    elif changes.get("retired") is False and rule.retired_at is not None:
        _ensure_single_active(session, rule)
        rule.retired_at = None
    session.commit()
    return rule


@router.delete("/rules/{rule_id}", status_code=204, tags=["rules"])
def delete_rule(rule_id: int, session: Session = Depends(get_session)) -> Response:
    session.delete(_get_rule(session, rule_id))
    session.commit()
    return Response(status_code=204)


# ---- deep analysis: positions and Stockfish, computed in the player's browser ---------------


@router.put("/players/{player_id}/game-analyses", response_model=DeepStatus, tags=["deep analysis"])
def save_game_analyses(
    player_id: int, body: GameAnalysisBatch, session: Session = Depends(get_session)
) -> DeepStatus:
    """Stores deep-analysis results for up to 200 games (insert or replace per game).

    A game sent without `moves` keeps an engine pass it already has, so the cheap positions
    pass can run again without losing Stockfish results.
    """
    ids = [g.game_id for g in body.games]
    existing = {
        a.game_id: a
        for a in session.scalars(
            select(GameAnalysis).where(
                GameAnalysis.player_id == player_id, GameAnalysis.game_id.in_(ids)
            )
        )
    }
    now = utcnow()
    for g in body.games:
        row = existing.get(g.game_id)
        if row is None:
            row = GameAnalysis(player_id=player_id, game_id=g.game_id, position_keys="")
            session.add(row)
            existing[g.game_id] = row
        if g.position_keys:
            row.position_keys = ",".join(g.position_keys)
        if g.moves is not None:
            row.engine = g.engine
            row.moves = json.dumps([m.model_dump(exclude_none=True) for m in g.moves])
        if g.final_cp is not None:
            row.final_cp = g.final_cp
        row.updated_at = now
    session.commit()
    return deep_status(player_id, session)


@router.get(
    "/players/{player_id}/game-analyses/status", response_model=DeepStatus, tags=["deep analysis"]
)
def deep_status(player_id: int, session: Session = Depends(get_session)) -> DeepStatus:
    rows = session.execute(
        select(
            GameAnalysis.game_id,
            GameAnalysis.position_keys,
            GameAnalysis.moves,
            GameAnalysis.final_cp,
        ).where(GameAnalysis.player_id == player_id)
    ).all()
    engine = sorted(r.game_id for r in rows if r.moves is not None)
    positions = sorted(r.game_id for r in rows if r.position_keys)
    return DeepStatus(
        positions=len(positions),
        engine=len(engine),
        engine_game_ids=engine,
        position_game_ids=positions,
        final_game_ids=sorted(r.game_id for r in rows if r.final_cp is not None),
    )
