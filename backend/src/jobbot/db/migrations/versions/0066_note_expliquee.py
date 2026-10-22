"""La note expliquée (docs/121 §C)

Revision ID: 0066
Revises: 0065
Create Date: 2026-10-22

`evaluations.why` : pourquoi cette note, en une phrase ; `level` (above | below) et
`level_detail` : quand le poste vise nettement un niveau au-dessus ou en dessous du profil.
Remplis par la notation score-v5 ; vides pour une note plus ancienne.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0066"
down_revision: str | None = "0065"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("evaluations", sa.Column("why", sa.Text()))
    op.add_column("evaluations", sa.Column("level", sa.Text()))
    op.add_column("evaluations", sa.Column("level_detail", sa.Text()))


def downgrade() -> None:
    op.drop_column("evaluations", "level_detail")
    op.drop_column("evaluations", "level")
    op.drop_column("evaluations", "why")
