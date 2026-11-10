"""Lecture du CV qui continue hors de la page (maquette du 10 novembre au soir, PR 21)

Revision ID: 0080
Revises: 0079
Create Date: 2026-11-10

- `documents.read_state` : NULL (jamais demandée), « reading », « done », « unavailable »,
  « unreadable » ;
- `documents.read_started_at`, `documents.read_at` : début de la dernière lecture, fin de la
  dernière lecture réussie ;
- `documents.read_result` : les blocs proposés, gardés jusqu'au choix de la personne, puis effacés.

Colonnes d'une table déjà cloisonnée (`documents`) : la règle de sécurité existante s'applique,
l'export et la suppression du compte les prennent avec la ligne.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0080"
down_revision: str | None = "0079"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("read_state", sa.Text(), nullable=True))
    op.add_column(
        "documents", sa.Column("read_started_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("documents", sa.Column("read_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("documents", sa.Column("read_result", JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "read_result")
    op.drop_column("documents", "read_at")
    op.drop_column("documents", "read_started_at")
    op.drop_column("documents", "read_state")
