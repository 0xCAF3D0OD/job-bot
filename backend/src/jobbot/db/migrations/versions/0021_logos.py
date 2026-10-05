"""Logos des entreprises : adresse d'origine relevée, logo téléchargé par entreprise

Revision ID: 0021
Revises: 0020
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("offers", sa.Column("logo_url", sa.Text()))
    op.add_column("offers", sa.Column("company_website", sa.Text()))
    op.create_table(
        "company_logos",
        sa.Column("name_key", sa.Text(), primary_key=True),
        sa.Column("storage_key", sa.Text()),
        sa.Column("media_type", sa.Text()),
        sa.Column("source", sa.Text()),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "source IN ('page', 'email', 'site')", name="company_logos_source_check"
        ),
    )


def downgrade() -> None:
    op.drop_table("company_logos")
    op.drop_column("offers", "company_website")
    op.drop_column("offers", "logo_url")
