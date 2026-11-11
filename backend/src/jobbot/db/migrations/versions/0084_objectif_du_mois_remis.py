"""L'objectif ORP gardé avec le mois remis (lot du 11 novembre au soir, PR 50)

Revision ID: 0084
Revises: 0083
Create Date: 2026-11-11

`orp_months.target` : l'objectif du mois au moment de la remise. Un changement d'objectif fait
plus tard ne touche plus les mois déjà remis. Les mois remis avant cette version reprennent
l'objectif actuel du compte, seule valeur connue.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0084"
down_revision: str | None = "0083"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("orp_months", sa.Column("target", sa.SmallInteger(), nullable=True))
    op.execute(
        """
        UPDATE orp_months AS m
        SET target = (s.value #>> '{}')::smallint
        FROM settings AS s
        WHERE s.user_id = m.user_id
          AND s.key = 'orp_monthly_target'
          AND jsonb_typeof(s.value) = 'number'
          AND m.submitted_at IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_column("orp_months", "target")
