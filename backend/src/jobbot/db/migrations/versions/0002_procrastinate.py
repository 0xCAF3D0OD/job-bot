"""Schéma de la file de tâches procrastinate (version 3.10)

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-02

Le SQL vient de procrastinate lui-même. Lors d'une montée de version de procrastinate,
ajouter une migration qui exécute ses fichiers sql/migrations correspondants.
"""

from collections.abc import Sequence

from alembic import op
from procrastinate.schema import SchemaManager

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Exécuté directement par psycopg : le SQL contient des « : » et des « % »
    # que SQLAlchemy interpréterait comme des paramètres.
    raw = op.get_bind().connection.driver_connection
    assert raw is not None
    raw.execute(SchemaManager.get_schema())


def downgrade() -> None:
    # procrastinate ne fournit pas de retour arrière de son schéma.
    raise NotImplementedError("Retour arrière non pris en charge pour le schéma procrastinate")
