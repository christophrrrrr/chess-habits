"""HTTP API of the insights service."""

from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis.analyses import ANALYSES
from app.config import get_settings
from app.db import get_session
from app.games_client import GamesClient, GamesServiceUnavailable, PlayerNotFound
from app.models import AnalysisRun
from app.runner import run_analyses
from app.schemas import AnalysisInfo, RunDetail, RunOut

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
    return run_analyses(session, player_id, raw)


@router.get("/players/{player_id}/runs", response_model=list[RunOut], tags=["runs"])
def list_runs(player_id: int, session: Session = Depends(get_session)) -> list[AnalysisRun]:
    return list(
        session.scalars(
            select(AnalysisRun)
            .where(AnalysisRun.player_id == player_id)
            .order_by(AnalysisRun.created_at.desc(), AnalysisRun.id.desc())
        )
    )


@router.get("/players/{player_id}/findings", response_model=RunDetail, tags=["runs"])
def latest_findings(player_id: int, session: Session = Depends(get_session)) -> AnalysisRun:
    run = session.scalar(
        select(AnalysisRun)
        .where(AnalysisRun.player_id == player_id, AnalysisRun.status == "done")
        .order_by(AnalysisRun.created_at.desc(), AnalysisRun.id.desc())
        .limit(1)
    )
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="no analysis run yet")
    return run


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
