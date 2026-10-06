"""Formations : catalogue (vérifié ou suggéré par l'IA) et suivi

Revision ID: 0026
Revises: 0025
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0026"
down_revision: str | None = "0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trainings",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("format", sa.Text(), nullable=False),
        sa.Column("language", sa.Text(), nullable=False),
        sa.Column("price", sa.Text(), nullable=False),
        sa.Column("duration", sa.Text()),
        sa.Column("level", sa.Text()),
        sa.Column("url", sa.Text(), nullable=False, unique=True),
        sa.Column("tags", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("description", sa.Text()),
        sa.Column("prep", sa.Text()),
        sa.Column("origin", sa.Text(), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("dismissed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "training_marks",
        sa.Column(
            "training_id",
            sa.BigInteger(),
            sa.ForeignKey("trainings.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("progress", sa.Text()),
        sa.Column("done_at", sa.Date()),
        sa.Column("certified", sa.Boolean()),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("training_marks")
    op.drop_table("trainings")
