"""Une recherche d'alerte retirée garde sa trace (décision de Kevin du 17.11.2026)

Revision ID: 0091
Revises: 0090
Create Date: 2026-11-17

`alert_searches.removed_at` : le moment où la personne a retiré la recherche (« Ta recherche » des
Alertes ou « Ne plus suivre »… supprimée). La ligne reste, en pause et cachée de la page, pour que
les e-mails que le site continue d'envoyer pour elle soient reconnus et ignorés : aucune offre
n'en arrive dans Offres. Recréer la même recherche (mêmes mots, même lieu) remet la ligne en route.

Colonne d'une table déjà cloisonnée (`alert_searches`) : la règle de sécurité existante s'applique,
l'export et la suppression du compte la prennent avec la ligne. Pas de rattrapage : les recherches
déjà supprimées n'ont plus de ligne. Retour arrière : les lignes retirées sont effacées (ce que
faisait la suppression avant), puis la colonne est retirée.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0091"
down_revision: str | None = "0090"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "alert_searches", sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.execute("delete from alert_searches where removed_at is not null")
    op.drop_column("alert_searches", "removed_at")
