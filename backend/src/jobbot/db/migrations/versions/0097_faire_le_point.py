"""« Faire le point » en page entière (planche FairePoint, accord de Kevin du 18.11.2026, 14 h 38)

Revision ID: 0097
Revises: 0096
Create Date: 2026-11-18

`interviews.feeling` : « Comment ça s'est passé ? » (bien, moyen, pas_bien). `interviews.notes` :
« Tes notes », ce qui a été dit et ce que la personne veut retenir. `interviews.rating` devient
facultatif : la page ne demande pas de note sur 5, et on n'en invente pas une à partir du ressenti.
Un retour garde au moins l'un des deux (contrainte `interviews_feeling_or_rating`).

La suite (`next_step`) prend une valeur de plus, `refus` (« On m'a dit non ») ; la colonne est un
texte, seule l'API la limite. La relance conseillée est calculée par le serveur (jour de
l'entretien + 7 jours) et rangée dans `next_step_at`, comme avant.

Colonnes d'une table déjà cloisonnée (`interviews`) : la règle de sécurité existante s'applique,
l'export et la suppression du compte les prennent avec la ligne. Rien à rattraper : les retours
existants ont tous une note. Retour arrière : les retours sans note reçoivent la note du ressenti
(bien 4, moyen 3, pas bien 2) pour garder la colonne obligatoire, puis les colonnes sont retirées.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0097"
down_revision: str | None = "0096"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("interviews", sa.Column("feeling", sa.Text(), nullable=True))
    op.add_column("interviews", sa.Column("notes", sa.Text(), nullable=True))
    op.create_check_constraint(
        "interviews_feeling_values", "interviews", "feeling in ('bien', 'moyen', 'pas_bien')"
    )
    op.alter_column("interviews", "rating", existing_type=sa.SmallInteger(), nullable=True)
    op.create_check_constraint(
        "interviews_feeling_or_rating", "interviews", "feeling is not null or rating is not null"
    )


def downgrade() -> None:
    op.drop_constraint("interviews_feeling_or_rating", "interviews", type_="check")
    op.execute(
        "update interviews set rating = "
        "case feeling when 'bien' then 4 when 'moyen' then 3 else 2 end where rating is null"
    )
    op.alter_column("interviews", "rating", existing_type=sa.SmallInteger(), nullable=False)
    op.drop_constraint("interviews_feeling_values", "interviews", type_="check")
    op.drop_column("interviews", "notes")
    op.drop_column("interviews", "feeling")
