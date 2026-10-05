"""Offres expirées : date, origine (page ou ancienneté), dernière revérification

Revision ID: 0013
Revises: 0012
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("offers", sa.Column("expired_at", sa.DateTime(timezone=True)))
    op.add_column("offers", sa.Column("expiry_source", sa.Text()))
    op.add_column("offers", sa.Column("checked_at", sa.DateTime(timezone=True)))
    op.create_check_constraint(
        "offers_expiry_source_check", "offers", "expiry_source IN ('page', 'age')"
    )
    op.create_index("ix_offers_expired_at", "offers", ["expired_at"])
    # Pages jobup déjà trouvées introuvables avant cette version.
    op.execute(
        "UPDATE offers SET expired_at = coalesce(enriched_at, now()), expiry_source = 'page' "
        "WHERE enrich_status = 'expired' AND status <> 'applied'"
    )


def downgrade() -> None:
    op.drop_index("ix_offers_expired_at", table_name="offers")
    op.drop_constraint("offers_expiry_source_check", "offers")
    for column in ("checked_at", "expiry_source", "expired_at"):
        op.drop_column("offers", column)
