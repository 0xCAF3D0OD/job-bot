"""Langues avec niveaux (prompt du 10 novembre 2026, PR 17)

Revision ID: 0079
Revises: 0078
Create Date: 2026-11-10

Le prérequis `unspoken_languages` (langues non parlées) devient `language_levels` : chaque langue
a un niveau, « Non renseigné » (par défaut), « Notions », « Courant » ou « Langue maternelle ».
Seul « Notions » écarte une offre qui exige la langue couramment (décision de Kevin, 10.11).

Les anciennes « langues non parlées » ne sont pas reprises : les premiers pas les cochaient pour
toute langue absente du CV, ce qui écartait des offres à tort. Elles redeviennent « Non
renseigné », à choisir de nouveau dans Critères. Table déjà cloisonnée (`criteria`) : la règle de
sécurité existante s'applique, l'export et la suppression du compte prennent la ligne.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0079"
down_revision: str | None = "0078"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

BASE = "'locations', 'remote_policy', 'min_rate', 'excluded_types', 'banned_words'"
OLD_KINDS = f"{BASE}, 'unspoken_languages'"
NEW_KINDS = f"{BASE}, 'language_levels'"
BOTH_KINDS = f"{OLD_KINDS}, 'language_levels'"


def _check(kinds: str) -> None:
    op.drop_constraint("criteria_kind_check", "criteria", type_="check")
    op.create_check_constraint("criteria_kind_check", "criteria", f"kind IN ({kinds})")


def upgrade() -> None:
    _check(BOTH_KINDS)
    op.execute("DELETE FROM criteria WHERE kind = 'unspoken_languages'")
    _check(NEW_KINDS)


def downgrade() -> None:
    _check(BOTH_KINDS)
    op.execute(
        """
        INSERT INTO criteria (user_id, kind, value)
        SELECT user_id, 'unspoken_languages',
               coalesce(
                 (SELECT jsonb_agg(key) FROM jsonb_each_text(value)
                  WHERE value = 'notions' AND key IN ('allemand', 'italien', 'anglais')),
                 '[]'::jsonb)
        FROM criteria WHERE kind = 'language_levels'
        """
    )
    op.execute("DELETE FROM criteria WHERE kind = 'language_levels'")
    _check(OLD_KINDS)
