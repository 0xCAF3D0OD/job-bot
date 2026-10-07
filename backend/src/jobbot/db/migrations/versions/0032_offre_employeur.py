"""Voir l'offre chez l'employeur (docs/20 §2)

Revision ID: 0032
Revises: 0031
Create Date: 2026-10-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0032"
down_revision: str | None = "0031"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("offers", sa.Column("employer_url", sa.Text()))
    op.add_column("offers", sa.Column("employer_url_source", sa.Text()))
    op.add_column("offers", sa.Column("employer_status", sa.Text()))
    op.add_column("offers", sa.Column("employer_checked_at", sa.DateTime(timezone=True)))
    op.add_column("companies", sa.Column("careers_url", sa.Text()))
    op.add_column("companies", sa.Column("ats", sa.Text()))
    op.add_column("companies", sa.Column("careers_checked_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    for column in ("careers_checked_at", "ats", "careers_url"):
        op.drop_column("companies", column)
    for column in ("employer_checked_at", "employer_status", "employer_url_source", "employer_url"):
        op.drop_column("offers", column)
