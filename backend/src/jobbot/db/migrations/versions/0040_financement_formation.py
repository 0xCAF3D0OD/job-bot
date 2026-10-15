"""Formations (docs/37 §2) : demande de financement à l'ORP, son suivi et sa relance

Revision ID: 0040
Revises: 0039
Create Date: 2026-10-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0040"
down_revision: str | None = "0039"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # requested | accepted | refused
    op.add_column("training_marks", sa.Column("funding_status", sa.Text(), nullable=True))
    op.add_column("training_marks", sa.Column("funding_requested_at", sa.Date(), nullable=True))
    op.add_column(
        "training_marks",
        sa.Column("funding_reminded_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("training_marks", "funding_reminded_at")
    op.drop_column("training_marks", "funding_requested_at")
    op.drop_column("training_marks", "funding_status")
