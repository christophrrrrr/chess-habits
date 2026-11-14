"""HTTP API of the games service."""

from collections.abc import Iterator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.chesscom import ChessComClient, ChessComNotFound, ChessComUnavailable
from app.config import get_settings
from app.db import get_session
from app.importer import import_month, utcnow
from app.models import Game, ImportedMonth, Player
from app.schemas import (
    ArchiveMonth,
    GameOut,
    GamePage,
    GameWithPgn,
    ImportRequest,
    ImportResult,
    PlayerCreate,
    PlayerDetail,
    PlayerKind,
    PlayerOut,
    PlayerUpdate,
)

router = APIRouter()


def get_chesscom() -> Iterator[ChessComClient]:
    client = ChessComClient(get_settings())
    try:
        yield client
    finally:
        client.close()


def _unavailable(exc: ChessComUnavailable) -> HTTPException:
    return HTTPException(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"chess.com is not reachable right now ({exc}). Stored data is still available.",
    )


def _get_player(session: Session, player_id: int) -> Player:
    player = session.get(Player, player_id)
    if player is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="player not found")
    return player


@router.get("/health", tags=["ops"])
def health() -> dict:
    return {"status": "ok", "service": get_settings().service_name}


# ---- Players (CRUD) -------------------------------------------------------------------


@router.post("/players", response_model=PlayerOut, status_code=201, tags=["players"])
def create_player(
    body: PlayerCreate,
    session: Session = Depends(get_session),
    chesscom: ChessComClient = Depends(get_chesscom),
) -> Player:
    username = body.username.lower()
    exists = session.scalar(
        select(Player).where(Player.platform == body.platform, Player.username == username)
    )
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="player is already tracked")
    try:
        profile = chesscom.get_profile(username)
    except ChessComNotFound:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="no chess.com account with that name"
        ) from None
    except ChessComUnavailable as exc:
        raise _unavailable(exc) from exc
    now = utcnow()
    player = Player(
        platform=body.platform,
        username=username,
        kind=body.kind,
        display_name=(profile.get("name") or None),
        notes=body.notes,
        created_at=now,
        updated_at=now,
    )
    session.add(player)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="player is already tracked") from None
    return player


@router.get("/players", response_model=list[PlayerOut], tags=["players"])
def list_players(
    kind: PlayerKind | None = None, session: Session = Depends(get_session)
) -> list[Player]:
    query = select(Player).order_by(Player.created_at)
    if kind:
        query = query.where(Player.kind == kind)
    return list(session.scalars(query))


@router.get("/players/{player_id}", response_model=PlayerDetail, tags=["players"])
def get_player(player_id: int, session: Session = Depends(get_session)) -> PlayerDetail:
    player = _get_player(session, player_id)
    rows = session.execute(
        select(Game.time_class, func.count())
        .where(Game.player_id == player_id)
        .group_by(Game.time_class)
    ).all()
    return PlayerDetail(
        **PlayerOut.model_validate(player).model_dump(),
        game_counts={tc: n for tc, n in rows},
    )


@router.patch("/players/{player_id}", response_model=PlayerOut, tags=["players"])
def update_player(
    player_id: int, body: PlayerUpdate, session: Session = Depends(get_session)
) -> Player:
    player = _get_player(session, player_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(player, field, value)
    player.updated_at = utcnow()
    session.commit()
    return player


@router.delete("/players/{player_id}", status_code=204, tags=["players"])
def delete_player(player_id: int, session: Session = Depends(get_session)) -> Response:
    player = _get_player(session, player_id)
    session.delete(player)
    session.commit()
    return Response(status_code=204)


# ---- Import ---------------------------------------------------------------------------


@router.get("/players/{player_id}/archives", response_model=list[ArchiveMonth], tags=["import"])
def list_archives(
    player_id: int,
    session: Session = Depends(get_session),
    chesscom: ChessComClient = Depends(get_chesscom),
) -> list[ArchiveMonth]:
    player = _get_player(session, player_id)
    try:
        months = chesscom.list_archive_months(player.username)
    except ChessComNotFound:
        months = []
    except ChessComUnavailable as exc:
        raise _unavailable(exc) from exc
    done = {
        r.month: r
        for r in session.scalars(select(ImportedMonth).where(ImportedMonth.player_id == player_id))
    }
    return [
        ArchiveMonth(
            month=m,
            imported=m in done,
            complete=bool(done[m].complete) if m in done else False,
            game_count=done[m].game_count if m in done else None,
        )
        for m in months
    ]


@router.post("/players/{player_id}/imports", response_model=ImportResult, tags=["import"])
def import_games(
    player_id: int,
    body: ImportRequest,
    session: Session = Depends(get_session),
    chesscom: ChessComClient = Depends(get_chesscom),
) -> ImportResult:
    player = _get_player(session, player_id)
    try:
        result = import_month(session, chesscom, player, body.month)
    except ChessComNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="no archive for that month") from None
    except ChessComUnavailable as exc:
        session.rollback()
        raise _unavailable(exc) from exc
    return ImportResult(**result.__dict__)


# ---- Games ----------------------------------------------------------------------------


@router.get("/players/{player_id}/games", response_model=GamePage, tags=["games"])
def list_games(
    player_id: int,
    time_class: str | None = None,
    since: datetime | None = None,
    include_pgn: bool = False,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> GamePage:
    _get_player(session, player_id)
    query = select(Game).where(Game.player_id == player_id)
    if time_class:
        query = query.where(Game.time_class == time_class)
    if since:
        query = query.where(Game.ended_at >= since)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = session.scalars(
        query.order_by(Game.ended_at.desc(), Game.id.desc()).limit(limit).offset(offset)
    ).all()
    model = GameWithPgn if include_pgn else GameOut
    return GamePage(
        items=[model.model_validate(g) for g in rows], total=total, limit=limit, offset=offset
    )


@router.get("/games/{game_id}", response_model=GameWithPgn, tags=["games"])
def get_game(game_id: int, session: Session = Depends(get_session)) -> Game:
    game = session.get(Game, game_id)
    if game is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="game not found")
    return game
