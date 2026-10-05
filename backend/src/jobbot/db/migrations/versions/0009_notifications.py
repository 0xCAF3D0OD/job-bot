"""Notifications : offre déjà signalée

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("evaluations", sa.Column("notified_at", sa.DateTime(timezone=True)))
    # Les notes déjà faites ne déclenchent pas de notification rétroactive.
    op.execute("UPDATE evaluations SET notified_at = now() WHERE scored_at IS NOT NULL")


def downgrade() -> None:
    op.drop_column("evaluations", "notified_at")
