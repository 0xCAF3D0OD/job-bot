"""Passages de l'annonce qui correspondent au profil (lot du 11 novembre au soir, PR 45 et 47)

Revision ID: 0083
Revises: 0082
Create Date: 2026-11-11

`evaluations.passages` : les citations données par l'IA dans l'appel de la note (score-v8), dont
il ne reste que celles retrouvées dans l'annonce, écrites comme dans l'annonce. Vide pour une note
plus ancienne : pas de surlignage, pas de légende. Aucune note existante n'est refaite.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0083"
down_revision: str | None = "0082"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "evaluations",
        sa.Column(
            "passages", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
    )


def downgrade() -> None:
    op.drop_column("evaluations", "passages")
