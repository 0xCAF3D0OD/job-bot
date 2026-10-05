"""Mois ORP : remise, export, modifications après remise, rappels envoyés

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "orp_months",
        sa.Column("month", sa.Text(), primary_key=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("exported_at", sa.DateTime(timezone=True)),
        sa.Column("changed_after_submit", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "reminders_sent",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.CheckConstraint("month ~ '^[0-9]{4}-[0-9]{2}$'", name="orp_months_month_check"),
    )


def downgrade() -> None:
    op.drop_table("orp_months")
