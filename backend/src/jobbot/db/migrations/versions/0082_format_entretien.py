"""Format d'un entretien d'embauche (paquet du 11 novembre, PR 41)

Revision ID: 0082
Revises: 0081
Create Date: 2026-11-11

- `applications.interview_format` : NULL (non indiqué), « telephone », « visio », « sur_place ».
  L'heure est déjà dans `interview_at`, le lieu ou le lien dans `interview_place`.

Colonne d'une table déjà cloisonnée (`applications`) : la règle de sécurité existante s'applique,
l'export et la suppression du compte la prennent avec la ligne. Retour arrière : la colonne est
retirée, rien d'autre ne change.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0082"
down_revision: str | None = "0081"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("interview_format", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("applications", "interview_format")
