"""Essais de note comptés et état final « Note impossible » (A2 du 13 novembre)

Revision ID: 0085
Revises: 0082
Create Date: 2026-11-13

Une offre jamais notée est reprise par la tâche des 10 minutes, quel que soit son statut
(en préparation, gardée, envoyée, ajoutée à la main puis écartée), jusqu'à 3 essais manqués :

- `evaluations.score_attempts` : essais manqués d'affilée, remis à 0 par une note réussie ;
- `evaluations.score_final` : NULL, ou l'état final « sans_texte », « reponse_vide », « erreur ».

Pas de rattrapage automatique (demande de Kevin) : les offres déjà là et jamais notées,
qui n'étaient pas reprises jusqu'ici, reçoivent `score_final = 'a_rattraper'`.
`jobbot rattraper-notes` les compte, chiffre le coût, puis les rend à la tâche sur demande.

Colonnes d'une table déjà cloisonnée (`evaluations`) : la règle de sécurité existante s'applique,
l'export et la suppression du compte les prennent avec la ligne. Retour arrière : les deux colonnes
sont retirées, rien d'autre ne change.

Numéro : 0083 et 0084 sont pris par le lot « Tri et visuel » (branches non fusionnées) ; celle-ci
suit 0082. Le lot fusionné après elle devra faire suivre son 0083 de 0085.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0085"
down_revision: str | None = "0082"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "evaluations",
        sa.Column("score_attempts", sa.SmallInteger(), nullable=False, server_default="0"),
    )
    op.add_column("evaluations", sa.Column("score_final", sa.Text(), nullable=True))
    op.create_check_constraint(
        "evaluations_score_final_check",
        "evaluations",
        "score_final IN ('sans_texte', 'reponse_vide', 'erreur', 'a_rattraper')",
    )
    # Les offres jamais notées que l'ancienne règle ne reprenait pas : statut hors « nouvelle » et
    # « à traiter », note faite sans profil, ou un échec déjà enregistré.
    op.execute(
        """
        UPDATE evaluations e SET score_final = 'a_rattraper'
          FROM offers o
         WHERE o.id = e.offer_id AND o.user_id = e.user_id
           AND e.score IS NULL AND o.expired_at IS NULL AND o.duplicate_of IS NULL
           AND NOT o.spontaneous
           AND (o.status NOT IN ('new', 'to_review') OR e.scored_at IS NOT NULL
                OR e.score_error IS NOT NULL)
           -- Une offre d'alerte écartée reste sans note : pas de marque, elle sera notée si
           -- la personne la récupère (gardée, préparée, critères changés).
           AND (o.status NOT IN ('filtered_out', 'ignored')
                OR EXISTS (SELECT 1 FROM offer_links l
                            WHERE l.offer_id = o.id AND l.source = 'manual'))
        """
    )


def downgrade() -> None:
    op.drop_constraint("evaluations_score_final_check", "evaluations")
    op.drop_column("evaluations", "score_final")
    op.drop_column("evaluations", "score_attempts")
