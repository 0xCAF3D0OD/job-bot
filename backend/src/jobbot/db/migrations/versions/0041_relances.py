"""Relancer une candidature (docs/38) : date de la relance

Revision ID: 0041
Revises: 0040
Create Date: 2026-10-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0041"
down_revision: str | None = "0040"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("followed_up_at", sa.Date(), nullable=True))
    # Candidatures déjà passées en « Relancée » : la date du changement de statut.
    op.execute("UPDATE applications SET followed_up_at = status_at WHERE status = 'relancee'")


def downgrade() -> None:
    op.drop_column("applications", "followed_up_at")
