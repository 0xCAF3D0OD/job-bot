"""Formations par profil d'essai (docs/17 §4) : suggestions de l'IA et suivi par profil

Revision ID: 0028
Revises: 0027
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0028"
down_revision: str | None = "0027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MAIN = "(SELECT id FROM profiles WHERE is_main)"


def upgrade() -> None:
    # Une suggestion de l'IA appartient au profil qui l'a demandée ; le catalogue à personne.
    op.add_column(
        "trainings",
        sa.Column("profile_id", sa.BigInteger(), sa.ForeignKey("profiles.id", ondelete="CASCADE")),
    )
    op.execute(f"UPDATE trainings SET profile_id = {MAIN} WHERE origin = 'ai'")
    op.drop_constraint("trainings_url_key", "trainings", type_="unique")
    op.create_index(
        "trainings_catalog_url",
        "trainings",
        ["url"],
        unique=True,
        postgresql_where=sa.text("profile_id IS NULL"),
    )
    op.create_index(
        "trainings_profile_url",
        "trainings",
        ["profile_id", "url"],
        unique=True,
        postgresql_where=sa.text("profile_id IS NOT NULL"),
    )
    # Suivi par profil : le suivi existant passe au profil principal.
    op.add_column(
        "training_marks",
        sa.Column("profile_id", sa.BigInteger(), sa.ForeignKey("profiles.id", ondelete="CASCADE")),
    )
    op.execute(f"UPDATE training_marks SET profile_id = {MAIN}")
    op.alter_column("training_marks", "profile_id", nullable=False)
    op.drop_constraint("training_marks_pkey", "training_marks", type_="primary")
    op.create_primary_key("training_marks_pkey", "training_marks", ["profile_id", "training_id"])


def downgrade() -> None:
    op.execute(f"DELETE FROM training_marks WHERE profile_id <> {MAIN}")
    op.drop_constraint("training_marks_pkey", "training_marks", type_="primary")
    op.drop_column("training_marks", "profile_id")
    op.create_primary_key("training_marks_pkey", "training_marks", ["training_id"])
    op.execute(f"DELETE FROM trainings WHERE profile_id IS NOT NULL AND profile_id <> {MAIN}")
    op.drop_index("trainings_profile_url", table_name="trainings")
    op.drop_index("trainings_catalog_url", table_name="trainings")
    op.create_unique_constraint("trainings_url_key", "trainings", ["url"])
    op.drop_column("trainings", "profile_id")
