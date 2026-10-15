"""Candidatures spontanées (docs/39) : une offre créée par toi, sans annonce

Revision ID: 0042
Revises: 0041
Create Date: 2026-10-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0042"
down_revision: str | None = "0041"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "offers",
        sa.Column("spontaneous", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("offers", sa.Column("spontaneous_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("offers", "spontaneous_reason")
    op.drop_column("offers", "spontaneous")
