"""Empreinte des logos : refuser l'image générique d'une source

Revision ID: 0075
Revises: 0074
Create Date: 2026-11-05

- `company_logos.sha256` : empreinte de la dernière image retenue ou refusée comme générique.
  Gardée même quand le logo est retiré, pour reconnaître la même image chez une autre
  entreprise. Donnée publique (table commune), aucune donnée d'un compte.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0075"
down_revision: str | None = "0074"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("company_logos", sa.Column("sha256", sa.Text()))
    op.create_index("ix_company_logos_sha256", "company_logos", ["sha256"])


def downgrade() -> None:
    op.drop_index("ix_company_logos_sha256", table_name="company_logos")
    op.drop_column("company_logos", "sha256")
