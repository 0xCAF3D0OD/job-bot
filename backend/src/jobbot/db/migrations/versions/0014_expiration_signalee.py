"""Expiration signalée par Kevin : son choix passe avant la détection automatique

Revision ID: 0014
Revises: 0013
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("offers", sa.Column("expiry_override", sa.Text()))
    op.create_check_constraint(
        "offers_expiry_override_check", "offers", "expiry_override IN ('expired', 'alive')"
    )
    op.drop_constraint("offers_expiry_source_check", "offers")
    op.create_check_constraint(
        "offers_expiry_source_check", "offers", "expiry_source IN ('page', 'age', 'manual')"
    )


def downgrade() -> None:
    op.execute("UPDATE offers SET expiry_source = 'page' WHERE expiry_source = 'manual'")
    op.drop_constraint("offers_expiry_source_check", "offers")
    op.create_check_constraint(
        "offers_expiry_source_check", "offers", "expiry_source IN ('page', 'age')"
    )
    op.drop_constraint("offers_expiry_override_check", "offers")
    op.drop_column("offers", "expiry_override")
