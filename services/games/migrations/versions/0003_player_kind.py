"""Add players.kind: "player" (an account you track) or "reference" (a grandmaster to compare with).

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-14
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("players") as batch:
        batch.add_column(sa.Column("kind", sa.String(16), nullable=False, server_default="player"))


def downgrade() -> None:
    with op.batch_alter_table("players") as batch:
        batch.drop_column("kind")
