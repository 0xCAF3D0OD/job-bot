"""Formations : diplômes acceptés et vérification des liens (Kevin, 16.11.2026)

- `trainings.prerequisites` : liste des diplômes acceptés ; vide = sans diplôme.
- `trainings.link_status` : « ok », « a_reverifier » ou « mort ». Les fiches déjà là
  restent « ok » ;
  une fiche ajoutée au catalogue entre « a_reverifier » et ne s'affiche qu'une fois vérifiée.
- `trainings.link_next_check` : prochaine vérification par la tâche « liens-formations ».

Table commune (`trainings`), aucune donnée personnelle. Retour arrière : les trois colonnes sont
retirées.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0088"
down_revision: str | None = "0087"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "trainings",
        sa.Column(
            "prerequisites",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "trainings", sa.Column("link_status", sa.Text(), nullable=False, server_default="ok")
    )
    op.add_column(
        "trainings", sa.Column("link_next_check", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_check_constraint(
        "trainings_link_status",
        "trainings",
        "link_status IN ('ok', 'a_reverifier', 'mort')",
    )


def downgrade() -> None:
    op.drop_constraint("trainings_link_status", "trainings", type_="check")
    op.drop_column("trainings", "link_next_check")
    op.drop_column("trainings", "link_status")
    op.drop_column("trainings", "prerequisites")
