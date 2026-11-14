"""Le message de relance gardé avec la candidature (décision de Kevin du 14.11)

Revision ID: 0085
Revises: 0084
Create Date: 2026-11-14

`applications.follow_up_subject` et `applications.follow_up_text` : l'objet et le message de la
relance, écrits par l'IA (ou le modèle simple) à la première ouverture du panneau, puis gardés.
Rouvrir le panneau ne refait pas d'appel ; « Réécrire » en demande un nouveau ; « Modifier le
message » enregistre la version de la personne. Vides pour les candidatures existantes.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0085"
down_revision: str | None = "0084"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("follow_up_subject", sa.Text(), nullable=True))
    op.add_column("applications", sa.Column("follow_up_text", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("applications", "follow_up_text")
    op.drop_column("applications", "follow_up_subject")
