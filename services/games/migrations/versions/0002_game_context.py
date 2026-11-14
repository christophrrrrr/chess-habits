"""Add started_at, termination and final_material to games, and backfill them from the PGN.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-12
"""

import re
from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

# Frozen copies of the helpers in app/pgn.py, so this migration never changes behaviour.
_VALUES = {"p": 1, "n": 3, "b": 3, "r": 5, "q": 9}


def _header(pgn: str, name: str) -> str | None:
    m = re.search(rf'\[{name} "([^"]*)"\]', pgn)
    return m.group(1) if m else None


def _material(fen: str | None, color: str) -> int | None:
    if not fen:
        return None
    board = fen.split(" ", 1)[0]
    white = sum(_VALUES.get(c.lower(), 0) for c in board if c.isupper())
    black = sum(_VALUES.get(c, 0) for c in board if c.islower())
    return white - black if color == "white" else black - white


def _started(pgn: str) -> datetime | None:
    date, time = _header(pgn, "UTCDate"), _header(pgn, "UTCTime")
    if not date or not time:
        return None
    try:
        return datetime.strptime(f"{date} {time}", "%Y.%m.%d %H:%M:%S")
    except ValueError:
        return None


def upgrade() -> None:
    with op.batch_alter_table("games") as batch:
        batch.add_column(sa.Column("started_at", sa.DateTime, nullable=True))
        batch.add_column(sa.Column("termination", sa.Unicode(100), nullable=True))
        batch.add_column(sa.Column("final_material", sa.Integer, nullable=True))

    conn = op.get_bind()
    games = sa.table(
        "games",
        sa.column("id", sa.Integer),
        sa.column("pgn", sa.UnicodeText),
        sa.column("player_color", sa.String),
        sa.column("started_at", sa.DateTime),
        sa.column("termination", sa.Unicode),
        sa.column("final_material", sa.Integer),
    )
    rows = conn.execute(sa.select(games.c.id, games.c.pgn, games.c.player_color)).all()
    for game_id, pgn, color in rows:
        conn.execute(
            games.update()
            .where(games.c.id == game_id)
            .values(
                started_at=_started(pgn),
                termination=((_header(pgn, "Termination") or "")[:100] or None),
                final_material=_material(_header(pgn, "CurrentPosition"), color),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("games") as batch:
        batch.drop_column("final_material")
        batch.drop_column("termination")
        batch.drop_column("started_at")
