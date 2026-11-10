"""Lecture automatique de l'annonce complète (prompt du 10 novembre 2026, PR 13)

Revision ID: 0078
Revises: 0077
Create Date: 2026-11-10

- `offers.text_read` : NULL tant que la lecture est à faire, « done », « refused » ;
- `offers.text_read_reason` : la raison d'un échec, en code court (journalisée aussi par domaine) ;
- `offers.text_read_attempts` et `offers.text_read_at` : une lecture, puis un seul nouvel essai.

Colonnes d'une table déjà cloisonnée (`offers`) : la règle de sécurité existante s'applique,
l'export et la suppression du compte les prennent avec la ligne. Les offres déjà reçues sans texte
complet restent à NULL : la prochaine tâche « enrich » les lit.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0078"
down_revision: str | None = "0077"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("offers", sa.Column("text_read", sa.Text(), nullable=True))
    op.add_column("offers", sa.Column("text_read_reason", sa.Text(), nullable=True))
    op.add_column(
        "offers",
        sa.Column("text_read_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("offers", sa.Column("text_read_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("offers", "text_read_at")
    op.drop_column("offers", "text_read_attempts")
    op.drop_column("offers", "text_read_reason")
    op.drop_column("offers", "text_read")
