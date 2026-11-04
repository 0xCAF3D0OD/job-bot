"""L'avancement d'une formation par modules (B19, décision de Kevin du 2026-11-04)

Revision ID: 0073
Revises: 0072
Create Date: 2026-11-04

`training_marks.modules_total` et `modules_done` : « Module 6 sur 12 ». Facultatifs : sans total, le
texte libre `progress` reste. Contraintes : au moins un module, et le compte des modules faits entre
0 et le total.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0073"
down_revision: str | None = "0072"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("training_marks", sa.Column("modules_total", sa.Integer(), nullable=True))
    op.add_column("training_marks", sa.Column("modules_done", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "training_marks_modules_total", "training_marks", "modules_total >= 1"
    )
    op.create_check_constraint(
        "training_marks_modules_done",
        "training_marks",
        "modules_done >= 0 and (modules_total is null or modules_done <= modules_total)",
    )


def downgrade() -> None:
    op.drop_constraint("training_marks_modules_done", "training_marks", type_="check")
    op.drop_constraint("training_marks_modules_total", "training_marks", type_="check")
    op.drop_column("training_marks", "modules_done")
    op.drop_column("training_marks", "modules_total")
