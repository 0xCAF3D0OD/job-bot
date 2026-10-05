"""Adresse de l'entreprise : annonce, registre IDE, lettre ou saisie de Kevin

Revision ID: 0015
Revises: 0014
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("offers", sa.Column("company_address", sa.Text()))
    op.add_column("offers", sa.Column("company_address_source", sa.Text()))
    op.create_check_constraint(
        "offers_company_address_source_check",
        "offers",
        "company_address_source IN ('page', 'registry', 'letter', 'manual')",
    )


def downgrade() -> None:
    op.drop_constraint("offers_company_address_source_check", "offers")
    op.drop_column("offers", "company_address_source")
    op.drop_column("offers", "company_address")
