"""Lieu ou lien de l'entretien sur la candidature (2026-11-06)

Revision ID: 0077
Revises: 0076
Create Date: 2026-11-06

- `applications.interview_place` : texte libre (adresse, « Visio », lien de la visioconférence),
  affiché sur Rendez-vous à la place de l'adresse de l'entreprise quand il est rempli.

Colonne d'une table déjà cloisonnée (`applications`) : la règle de sécurité existante s'applique,
l'export et la suppression du compte la prennent avec la ligne.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0077"
down_revision: str | None = "0076"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("interview_place", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("applications", "interview_place")
