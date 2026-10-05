"""Lien de la candidature (formulaire de l'employeur ou annonce), pour l'ORP

Revision ID: 0019
Revises: 0018
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("application_url", sa.Text()))
    # Candidatures déjà enregistrées : formulaire de l'employeur, sinon premier lien d'annonce.
    op.execute(
        """
        UPDATE applications a
        SET application_url = coalesce(
            o.apply_url,
            (SELECT l.url FROM offer_links l WHERE l.offer_id = o.id ORDER BY l.id LIMIT 1)
        )
        FROM offers o
        WHERE a.offer_id = o.id AND a.application_url IS NULL
        """
    )


def downgrade() -> None:
    op.drop_column("applications", "application_url")
