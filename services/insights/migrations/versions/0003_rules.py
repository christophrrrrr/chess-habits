"""Rules a player adopts from a card (clock checkpoint or stop-loss).

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-12
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rules",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("player_id", sa.Integer, nullable=False),
        sa.Column("time_class", sa.String(16), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("move", sa.Integer, nullable=True),
        sa.Column("min_share", sa.Float, nullable=True),
        sa.Column("stop_rule", sa.String(32), nullable=True),
        sa.Column("note", sa.Unicode(200), nullable=True),
        sa.Column("adopted_at", sa.DateTime, nullable=False),
        sa.Column("retired_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_rules_player_id", "rules", ["player_id"])


def downgrade() -> None:
    op.drop_index("ix_rules_player_id", table_name="rules")
    op.drop_table("rules")
