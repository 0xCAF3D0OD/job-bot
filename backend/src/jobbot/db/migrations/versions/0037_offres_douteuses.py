"""Offres douteuses (docs/30) : doublons regroupés, ancienneté d'une annonce, arnaques relevées

Revision ID: 0037
Revises: 0036
Create Date: 2026-10-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0037"
down_revision: str | None = "0036"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Doublon (même titre, même entreprise) : rattaché à l'offre gardée, caché des listes.
    op.add_column(
        "offers",
        sa.Column(
            "duplicate_of",
            sa.BigInteger(),
            sa.ForeignKey("offers.id", ondelete="SET NULL"),
            index=True,
        ),
    )
    # Première apparition de l'annonce, doublons compris (« annonce permanente »).
    op.add_column("offers", sa.Column("seen_since", sa.DateTime(timezone=True)))
    op.execute("UPDATE offers SET seen_since = first_seen_at")
    op.add_column(
        "evaluations",
        sa.Column("scam_signals", postgresql.JSONB(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("evaluations", "scam_signals")
    op.drop_column("offers", "seen_since")
    op.drop_column("offers", "duplicate_of")
