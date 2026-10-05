"""Prérequis et filtre : criteria, evaluations

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

KINDS = (
    "'locations', 'remote_ok', 'min_rate', 'excluded_types', 'banned_words', 'unspoken_languages'"
)


def upgrade() -> None:
    op.create_table(
        "criteria",
        sa.Column("kind", sa.Text(), primary_key=True),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(f"kind IN ({KINDS})", name="criteria_kind_check"),
    )
    op.create_table(
        "evaluations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "offer_id",
            sa.BigInteger(),
            sa.ForeignKey("offers.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("filter_passed", sa.Boolean(), nullable=False),
        sa.Column(
            "filter_reasons", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'")
        ),
        sa.Column("criteria_hash", sa.Text(), nullable=False),
        sa.Column(
            "evaluated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_offers_status", "offers", ["status"])


def downgrade() -> None:
    op.drop_index("ix_offers_status", table_name="offers")
    op.drop_table("evaluations")
    op.drop_table("criteria")
