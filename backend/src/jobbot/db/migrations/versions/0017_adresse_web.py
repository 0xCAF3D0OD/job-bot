"""Adresse trouvée sur Internet par l'IA, avec la page source

Revision ID: 0017
Revises: 0016
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("offers", sa.Column("company_address_url", sa.Text()))
    op.drop_constraint("offers_company_address_source_check", "offers")
    op.create_check_constraint(
        "offers_company_address_source_check",
        "offers",
        "company_address_source IN ('page', 'registry', 'web', 'letter', 'manual')",
    )
    op.add_column("companies", sa.Column("source_url", sa.Text()))
    op.add_column("companies", sa.Column("web_looked_up_at", sa.DateTime(timezone=True)))
    op.drop_constraint("companies_chosen_by_check", "companies")
    op.create_check_constraint(
        "companies_chosen_by_check", "companies", "chosen_by IN ('auto', 'manual', 'web')"
    )


def downgrade() -> None:
    op.execute("UPDATE companies SET chosen_by = NULL WHERE chosen_by = 'web'")
    op.drop_constraint("companies_chosen_by_check", "companies")
    op.create_check_constraint(
        "companies_chosen_by_check", "companies", "chosen_by IN ('auto', 'manual')"
    )
    op.drop_column("companies", "web_looked_up_at")
    op.drop_column("companies", "source_url")
    op.execute(
        "UPDATE offers SET company_address = NULL, company_address_source = NULL"
        " WHERE company_address_source = 'web'"
    )
    op.drop_constraint("offers_company_address_source_check", "offers")
    op.create_check_constraint(
        "offers_company_address_source_check",
        "offers",
        "company_address_source IN ('page', 'registry', 'letter', 'manual')",
    )
    op.drop_column("offers", "company_address_url")
