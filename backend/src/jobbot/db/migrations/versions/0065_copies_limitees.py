"""Les copies d'alertes des invités effacées au bout de 90 jours (docs/120 §2)

Revision ID: 0065
Revises: 0064
Create Date: 2026-10-21

`searches.raw_purged_at` : quand la copie brute de l'e-mail a été effacée. La ligne du
journal, les offres et les candidatures restent.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0065"
down_revision: str | None = "0064"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("searches", sa.Column("raw_purged_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    op.drop_column("searches", "raw_purged_at")
