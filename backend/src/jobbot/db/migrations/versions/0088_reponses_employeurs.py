"""Les réponses d'employeurs transférées (docs/146, accord de Kevin du 16.11.2026)

Revision ID: 0088
Revises: 0087
Create Date: 2026-11-16

La personne transfère la réponse d'une entreprise vers son adresse jobA1 ; la collecte la
rattache à la candidature et garde seulement :

- `applications.reply_kind` : « entretien », « refus » ou « autre » ;
- `applications.reply_at` : la date de la réponse.

Ni texte, ni expéditeur, ni copie de l'e-mail. Colonnes d'une table déjà cloisonnée
(`applications`) : la règle de sécurité existante s'applique, l'export et la suppression du compte
les prennent avec la ligne. Retour arrière : les deux colonnes sont retirées.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0088"
down_revision: str | None = "0087"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("reply_kind", sa.Text(), nullable=True))
    op.add_column("applications", sa.Column("reply_at", sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint(
        "applications_reply_kind_check",
        "applications",
        "reply_kind IN ('entretien', 'refus', 'autre')",
    )


def downgrade() -> None:
    op.drop_constraint("applications_reply_kind_check", "applications")
    op.drop_column("applications", "reply_at")
    op.drop_column("applications", "reply_kind")
