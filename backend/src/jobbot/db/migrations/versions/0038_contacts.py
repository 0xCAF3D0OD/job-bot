"""Contacts dans l'entreprise (docs/31) : prises de contact suivies, relance après 7 jours

Revision ID: 0038
Revises: 0037
Create Date: 2026-10-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0038"
down_revision: str | None = "0037"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contacts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "offer_id",
            sa.BigInteger(),
            sa.ForeignKey("offers.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column(
            "application_id",
            sa.BigInteger(),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("name", sa.Text()),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column("contacted_on", sa.Date(), nullable=False),
        sa.Column("answered_on", sa.Date()),
        sa.Column("note", sa.Text()),
        sa.Column("reminded_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("contacts")
