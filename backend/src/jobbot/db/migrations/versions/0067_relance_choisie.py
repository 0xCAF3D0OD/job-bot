"""La date de relance choisie (docs/124 §G)

Revision ID: 0067
Revises: 0066
Create Date: 2026-10-22

`applications.follow_up_on` : le jour où relancer, choisi par la personne dans l'étape
« Suivre » (entre 5 et 30 jours après l'envoi). Vide : 10 jours après l'envoi, comme avant.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0067"
down_revision: str | None = "0066"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("follow_up_on", sa.Date()))


def downgrade() -> None:
    op.drop_column("applications", "follow_up_on")
