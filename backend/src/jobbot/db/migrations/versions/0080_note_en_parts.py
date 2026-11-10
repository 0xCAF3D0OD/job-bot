"""Comment la note est calculée (prompt du 10 novembre, PR 18)

Revision ID: 0080
Revises: 0079
Create Date: 2026-11-10

`evaluations.score_parts` : les cinq parts de la note (compétences /40, expérience /20,
lieu /15, langues /15, taux et contrat /10), chacune avec ses points, sa phrase et `check`
(point à vérifier) ; la note est leur somme. `score_tip` : l'action qui ferait monter la
note. Remplis par la notation score-v7 ; vides pour une note plus ancienne, qui garde son
chiffre sans détail.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0080"
down_revision: str | None = "0079"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "evaluations",
        sa.Column(
            "score_parts", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
    )
    op.add_column("evaluations", sa.Column("score_tip", postgresql.JSONB()))


def downgrade() -> None:
    op.drop_column("evaluations", "score_tip")
    op.drop_column("evaluations", "score_parts")
