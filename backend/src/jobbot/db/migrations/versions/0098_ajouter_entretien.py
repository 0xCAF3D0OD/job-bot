"""« Ajouter un entretien » sur ordinateur (planche AjouterEntretienOrdinateur, §72p ; accord de
Kevin du 19.11.2026, 12 h 58)

Revision ID: 0098
Revises: 0097
Create Date: 2026-11-19

`applications.interview_round` : « Quel entretien ? » de l'entretien prévu (1er, 2e ou Final).

Deux entretiens d'une candidature sont deux éléments séparés (Kevin, 19.11) : ajouter le 2e ne
retire jamais le 1er de « À noter ». L'entretien prévu reste sur la candidature (`interview_at`,
lieu, tour) ; quand on en ajoute un autre alors que le point du précédent n'est pas fait, le
précédent est gardé dans `interviews` comme entretien prévu : `scheduled_at` (date et heure),
`place`, `round`, sans `held_at` ni ressenti. Il reste dans « À venir » puis « À noter » jusqu'à
son point, qui remplit `held_at` et le ressenti sur la même ligne.

La contrainte `interviews_feeling_or_rating` (0097) laisse donc passer une ligne prévue : un
retour (`held_at` rempli, ou ligne sans date prévue) garde au moins un ressenti ou une note.

Colonnes de tables déjà cloisonnées (`applications`, `interviews`) : la règle
`account_isolation` s'applique, l'export et la suppression du compte les prennent avec la ligne.
Rien de modifié dans les lignes existantes. Retour arrière : les entretiens prévus sans point
(ni ressenti ni note) sont effacés, puis la contrainte de 0097 et les colonnes reviennent comme
avant.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0098"
down_revision: str | None = "0097"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ROUNDS = "('1', '2', 'final')"


def upgrade() -> None:
    op.add_column("applications", sa.Column("interview_round", sa.Text(), nullable=True))
    op.create_check_constraint(
        "applications_interview_round_values", "applications", f"interview_round in {ROUNDS}"
    )
    op.add_column("interviews", sa.Column("round", sa.Text(), nullable=True))
    op.add_column(
        "interviews", sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("interviews", sa.Column("place", sa.Text(), nullable=True))
    op.create_check_constraint("interviews_round_values", "interviews", f"round in {ROUNDS}")
    op.drop_constraint("interviews_feeling_or_rating", "interviews", type_="check")
    op.create_check_constraint(
        "interviews_feeling_or_rating",
        "interviews",
        "feeling is not null or rating is not null"
        " or (held_at is null and scheduled_at is not null)",
    )


def downgrade() -> None:
    op.execute("delete from interviews where feeling is null and rating is null")
    op.drop_constraint("interviews_feeling_or_rating", "interviews", type_="check")
    op.create_check_constraint(
        "interviews_feeling_or_rating", "interviews", "feeling is not null or rating is not null"
    )
    op.drop_constraint("interviews_round_values", "interviews", type_="check")
    op.drop_column("interviews", "place")
    op.drop_column("interviews", "scheduled_at")
    op.drop_column("interviews", "round")
    op.drop_constraint("applications_interview_round_values", "applications", type_="check")
    op.drop_column("applications", "interview_round")
