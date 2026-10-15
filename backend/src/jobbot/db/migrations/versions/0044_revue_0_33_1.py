"""Revue 0.33.1 (docs/41) : spontanées expirées par erreur, dates de relance manquantes

Revision ID: 0044
Revises: 0043
Create Date: 2026-10-15
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0044"
down_revision: str | None = "0043"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Une candidature spontanée n'expire pas faute d'annonce (docs/39 §4).
    op.execute(
        "UPDATE offers SET expired_at = NULL, expiry_source = NULL "
        "WHERE spontaneous AND expiry_source = 'age'"
    )
    # Relancées sans date de statut : la date d'envoi, pour la règle des 14 jours (docs/38).
    op.execute(
        "UPDATE applications SET followed_up_at = sent_at "
        "WHERE status = 'relancee' AND followed_up_at IS NULL"
    )


def downgrade() -> None:
    # Corrections de données : rien à défaire.
    pass
