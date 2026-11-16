"""La date de mise à l'écart d'une offre (§30 du 16.11, décision de Kevin du 16.11.2026, 13 h 53)

Revision ID: 0090
Revises: 0089
Create Date: 2026-11-16

`offers.set_aside_at` : le moment où l'offre a été écartée (par la personne, Trier, l'assistant ou
les critères), pour afficher « Écartée le 12 nov. » dans la fiche. Posée à chaque mise à l'écart,
vidée quand l'offre revient dans le tri (`jobbot.db.models._stamp_set_aside`).

Pas de rattrapage (décision de Kevin) : les offres déjà écartées gardent une date vide et affichent
« Écartée » seul. Colonne d'une table déjà cloisonnée (`offers`) : la règle de sécurité existante
s'applique, l'export et la suppression du compte la prennent avec la ligne. Retour arrière : la
colonne est retirée.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0090"
down_revision: str | None = "0089"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("offers", sa.Column("set_aside_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("offers", "set_aside_at")
