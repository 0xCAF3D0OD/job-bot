"""Note IA : colonnes de evaluations, llm_calls, llm_batches, taux USD→CHF

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-05
"""

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EVALUATION_COLUMNS: tuple[sa.Column[Any], ...] = (
    sa.Column("score", sa.SmallInteger()),
    sa.Column("summary_role", sa.Text()),
    sa.Column("summary_asks", sa.Text()),
    sa.Column("summary_offers", sa.Text()),
    sa.Column("summary_partial", sa.Boolean(), nullable=False, server_default=sa.false()),
    sa.Column("strengths", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'")),
    sa.Column("gaps", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'")),
    sa.Column("model", sa.Text()),
    sa.Column("prompt_version", sa.Text()),
    sa.Column("profile_hash", sa.Text()),
    sa.Column("scored_at", sa.DateTime(timezone=True)),
    sa.Column("score_error", sa.Text()),
)


def upgrade() -> None:
    for column in EVALUATION_COLUMNS:
        op.add_column("evaluations", column)
    op.create_check_constraint(
        "evaluations_score_check", "evaluations", "score IS NULL OR score BETWEEN 0 AND 100"
    )
    op.create_index("ix_evaluations_score", "evaluations", ["score"])
    op.create_table(
        "llm_calls",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("offer_id", sa.BigInteger(), sa.ForeignKey("offers.id", ondelete="SET NULL")),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("batch_id", sa.Text()),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cache_read_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cache_write_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(10, 5), nullable=False),
        sa.Column("cost_chf", sa.Numeric(10, 5), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_llm_calls_created_at", "llm_calls", ["created_at"])
    op.create_table(
        "llm_batches",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("provider_batch_id", sa.Text(), nullable=False, unique=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="in_progress"),
        sa.Column("offer_ids", postgresql.ARRAY(sa.BigInteger()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "status IN ('in_progress', 'ended', 'failed')", name="llm_batches_status_check"
        ),
    )
    op.execute(
        "INSERT INTO settings (key, value) VALUES ('usd_chf_rate', '0.8') "
        "ON CONFLICT (key) DO NOTHING"
    )


def downgrade() -> None:
    op.execute("DELETE FROM settings WHERE key = 'usd_chf_rate'")
    op.drop_table("llm_batches")
    op.drop_table("llm_calls")
    op.drop_index("ix_evaluations_score", table_name="evaluations")
    op.drop_constraint("evaluations_score_check", "evaluations")
    for column in reversed(EVALUATION_COLUMNS):
        op.drop_column("evaluations", column.name)
