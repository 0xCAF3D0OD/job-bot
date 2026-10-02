"""Tables settings et job_runs, valeurs par défaut des réglages

Revision ID: 0001
Revises:
Create Date: 2026-10-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_SETTINGS = {
    "notify_score_threshold": 70,
    "llm_monthly_budget_chf": 10,
    "orp_monthly_target": None,
}


def upgrade() -> None:
    settings = op.create_table(
        "settings",
        sa.Column("key", sa.Text(), primary_key=True),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_table(
        "job_runs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("job", sa.Text(), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("items_in", sa.Integer()),
        sa.Column("items_out", sa.Integer()),
        sa.Column("error", sa.Text()),
        sa.CheckConstraint(
            "status IN ('running', 'success', 'failure')", name="job_runs_status_check"
        ),
    )
    op.create_index("ix_job_runs_job", "job_runs", ["job"])
    op.create_index("ix_job_runs_started_at", "job_runs", ["started_at"])
    op.bulk_insert(settings, [{"key": k, "value": v} for k, v in DEFAULT_SETTINGS.items()])


def downgrade() -> None:
    op.drop_table("job_runs")
    op.drop_table("settings")
