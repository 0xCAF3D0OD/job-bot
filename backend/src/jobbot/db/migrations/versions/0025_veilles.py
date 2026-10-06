"""Actualités : veilles par recherche (mots-clés suivis dans Google Actualités)

Revision ID: 0025
Revises: 0024
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0025"
down_revision: str | None = "0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("news_sources", sa.Column("query", sa.Text()))


def downgrade() -> None:
    op.drop_column("news_sources", "query")
