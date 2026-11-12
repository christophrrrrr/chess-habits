"""Initial schema: players, imported_months, games.

Revision ID: 0001
Revises:
Create Date: 2026-11-12
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "players",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("platform", sa.String(16), nullable=False),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("display_name", sa.Unicode(100), nullable=True),
        sa.Column("notes", sa.Unicode(500), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("last_imported_at", sa.DateTime, nullable=True),
        sa.UniqueConstraint("platform", "username", name="uq_players_platform_user"),
    )
    op.create_table(
        "imported_months",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "player_id",
            sa.Integer,
            sa.ForeignKey("players.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("month", sa.String(7), nullable=False),
        sa.Column("game_count", sa.Integer, nullable=False),
        sa.Column("complete", sa.Boolean, nullable=False),
        sa.Column("imported_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("player_id", "month", name="uq_imported_months"),
    )
    op.create_table(
        "games",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "player_id",
            sa.Integer,
            sa.ForeignKey("players.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("platform_game_id", sa.String(64), nullable=False),
        sa.Column("url", sa.String(255), nullable=True),
        sa.Column("time_class", sa.String(16), nullable=False),
        sa.Column("time_control", sa.String(32), nullable=False),
        sa.Column("base_seconds", sa.Integer, nullable=True),
        sa.Column("increment_seconds", sa.Integer, nullable=True),
        sa.Column("rated", sa.Boolean, nullable=False),
        sa.Column("ended_at", sa.DateTime, nullable=False),
        sa.Column("player_color", sa.String(5), nullable=False),
        sa.Column("player_rating", sa.Integer, nullable=True),
        sa.Column("opponent_username", sa.String(64), nullable=False),
        sa.Column("opponent_rating", sa.Integer, nullable=True),
        sa.Column("result", sa.String(4), nullable=False),
        sa.Column("result_detail", sa.String(32), nullable=False),
        sa.Column("eco", sa.String(8), nullable=True),
        sa.Column("opening", sa.Unicode(255), nullable=True),
        sa.Column("ply_count", sa.Integer, nullable=False),
        sa.Column("clocks", sa.UnicodeText, nullable=True),
        sa.Column("pgn", sa.UnicodeText, nullable=False),
        sa.UniqueConstraint("player_id", "platform_game_id", name="uq_games_platform"),
    )
    op.create_index("ix_games_player_id", "games", ["player_id"])
    op.create_index("ix_games_time_class", "games", ["time_class"])
    op.create_index("ix_games_ended_at", "games", ["ended_at"])


def downgrade() -> None:
    op.drop_table("games")
    op.drop_table("imported_months")
    op.drop_table("players")
