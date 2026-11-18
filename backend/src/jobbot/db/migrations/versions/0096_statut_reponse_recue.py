"""Statut de candidature « Réponse reçue » (Kevin, 18.11.2026, 13 h 39)

Revision ID: 0096
Revises: 0095
Create Date: 2026-11-18

Nouveau statut `reponse` : l'employeur a répondu, sans entretien ni refus. Il se choisit à la main
dans le menu de statut d'une candidature et sert au filtre « Réponse reçue » des Envoyées
(planche FiltresEnvoyees). Seule la contrainte `applications_status_check` change ; aucune ligne
n'est modifiée. Donnée existante (`applications.status`, déjà cloisonnée par compte) : les règles de
sécurité en place s'appliquent, export et suppression du compte compris.

Retour arrière : les candidatures en `reponse` repassent en `en_attente`, puis l'ancienne contrainte
revient.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0096"
down_revision: str | None = "0095"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

BEFORE = "'en_attente', 'relancee', 'entretien', 'refus', 'engagement', 'sans_reponse'"
AFTER = "'en_attente', 'relancee', 'reponse', 'entretien', 'refus', 'engagement', 'sans_reponse'"


def upgrade() -> None:
    op.drop_constraint("applications_status_check", "applications", type_="check")
    op.create_check_constraint("applications_status_check", "applications", f"status IN ({AFTER})")


def downgrade() -> None:
    op.execute("UPDATE applications SET status = 'en_attente' WHERE status = 'reponse'")
    op.drop_constraint("applications_status_check", "applications", type_="check")
    op.create_check_constraint("applications_status_check", "applications", f"status IN ({BEFORE})")
