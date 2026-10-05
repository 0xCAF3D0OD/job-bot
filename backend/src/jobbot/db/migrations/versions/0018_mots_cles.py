"""Mots-clés des offres pour les cartes (poste, demande, offre)

Revision ID: 0018
Revises: 0017
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COLUMNS = ("keywords_role", "keywords_asks", "keywords_offers")


def upgrade() -> None:
    for column in COLUMNS:
        op.add_column(
            "evaluations",
            sa.Column(column, postgresql.JSONB(), nullable=False, server_default="[]"),
        )
    # Consignes du lot : une note arrivée après un changement de consignes reste à refaire.
    op.add_column(
        "llm_batches",
        sa.Column("prompt_version", sa.Text(), nullable=False, server_default="score-v1"),
    )


def downgrade() -> None:
    op.drop_column("llm_batches", "prompt_version")
    for column in COLUMNS:
        op.drop_column("evaluations", column)
