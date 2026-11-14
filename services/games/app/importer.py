"""Import chess.com games into the database, one monthly archive at a time.

Importing month by month keeps every HTTP request short (well under the Container Apps
request timeout); the UI drives the loop and shows progress.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.chesscom import ChessComClient
from app.models import Game, ImportedMonth, Player
from app.pgn import opening_from_url, parse_moves, parse_time_control, pgn_header, result_from_code


@dataclass(frozen=True)
class MonthImportResult:
    month: str
    fetched: int
    new_games: int
    skipped: bool  # True if the month was already fully imported and not fetched again
    complete: bool


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def game_from_chesscom(player: Player, data: dict) -> Game | None:
    """Convert one chess.com game JSON object. Returns None for variants and broken data."""
    if data.get("rules", "chess") != "chess" or not data.get("pgn"):
        return None
    username = player.username.lower()
    white, black = data.get("white", {}), data.get("black", {})
    if white.get("username", "").lower() == username:
        color, me, opp = "white", white, black
    elif black.get("username", "").lower() == username:
        color, me, opp = "black", black, white
    else:
        return None

    pgn = data["pgn"]
    moves = parse_moves(pgn)
    base, inc = parse_time_control(data.get("time_control", ""))
    game_id = data.get("uuid") or data.get("url", "").rstrip("/").rsplit("/", 1)[-1]
    if not game_id:
        return None
    return Game(
        platform_game_id=str(game_id)[:64],
        url=(data.get("url") or None),
        time_class=data.get("time_class", "unknown"),
        time_control=data.get("time_control", ""),
        base_seconds=base,
        increment_seconds=inc,
        rated=bool(data.get("rated", False)),
        ended_at=datetime.fromtimestamp(int(data.get("end_time", 0)), UTC).replace(tzinfo=None),
        player_color=color,
        player_rating=me.get("rating"),
        opponent_username=opp.get("username", "?")[:64],
        opponent_rating=opp.get("rating"),
        result=result_from_code(me.get("result", "")),
        result_detail=me.get("result", "unknown")[:32],
        eco=(pgn_header(pgn, "ECO") or None),
        opening=opening_from_url(data.get("eco") or pgn_header(pgn, "ECOUrl")),
        ply_count=moves.ply_count,
        clocks=moves.clocks,
        pgn=pgn,
    )


def import_month(
    session: Session,
    client: ChessComClient,
    player: Player,
    month: str,
    now: datetime | None = None,
) -> MonthImportResult:
    now = now or utcnow()
    current_month = now.strftime("%Y-%m")
    record = session.scalar(
        select(ImportedMonth).where(
            ImportedMonth.player_id == player.id, ImportedMonth.month == month
        )
    )
    if record is not None and record.complete:
        return MonthImportResult(month, 0, 0, skipped=True, complete=True)

    raw_games = client.get_month_games(player.username, month)
    existing = set(
        session.scalars(select(Game.platform_game_id).where(Game.player_id == player.id))
    )
    new = 0
    for data in raw_games:
        game = game_from_chesscom(player, data)
        if game is None or game.platform_game_id in existing:
            continue
        game.player_id = player.id
        session.add(game)
        existing.add(game.platform_game_id)
        new += 1

    complete = month < current_month
    if record is None:
        record = ImportedMonth(player_id=player.id, month=month)
        session.add(record)
    record.game_count = len(raw_games)
    record.complete = complete
    record.imported_at = now
    player.last_imported_at = now
    session.commit()
    return MonthImportResult(month, len(raw_games), new, skipped=False, complete=complete)
