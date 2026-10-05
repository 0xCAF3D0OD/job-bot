"""Cache des recherches dans le registre IDE (adresse des entreprises)

Revision ID: 0016
Revises: 0015
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("name_key", sa.Text(), primary_key=True),
        sa.Column("uid", sa.Text()),
        sa.Column("address", sa.Text()),
        sa.Column("candidates", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("chosen_by", sa.Text()),
        sa.Column("looked_up_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("chosen_by IN ('auto', 'manual')", name="companies_chosen_by_check"),
    )


def downgrade() -> None:
    op.drop_table("companies")
