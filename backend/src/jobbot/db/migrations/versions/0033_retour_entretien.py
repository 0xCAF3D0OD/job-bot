"""Retour d'entretien (docs/23)

Revision ID: 0033
Revises: 0032
Create Date: 2026-10-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0033"
down_revision: str | None = "0032"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "interviews",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "application_id",
            sa.BigInteger(),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("kind", sa.Text()),
        sa.Column("held_at", sa.Date()),
        sa.Column("format", sa.Text()),
        sa.Column("duration", sa.Text()),
        sa.Column("interviewers", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("people_count", sa.SmallInteger()),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("stress", sa.SmallInteger()),
        sa.Column("interest", sa.Text()),
        sa.Column("outlook", sa.Text()),
        sa.Column("questions", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("salary_asked", sa.Boolean()),
        sa.Column("salary_answer", sa.Text()),
        sa.Column("went_well", sa.Text()),
        sa.Column("went_badly", sa.Text()),
        sa.Column("to_prepare", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("my_questions", sa.Text()),
        sa.Column("missed_questions", sa.Text()),
        sa.Column("learned", sa.Text()),
        sa.Column("warnings", sa.Text()),
        sa.Column("next_step", sa.Text()),
        sa.Column("next_step_at", sa.Date()),
        sa.Column("thanks", sa.Text()),
        sa.Column("employer_feedback", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # Rappel « Comment s'est passé ton entretien ? » : une fois par date d'entretien.
    op.add_column("applications", sa.Column("interview_reminded_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    op.drop_column("applications", "interview_reminded_at")
    op.drop_table("interviews")
