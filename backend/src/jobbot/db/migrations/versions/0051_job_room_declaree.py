"""La candidature déclarée dans Job-Room (docs/70 §6)

Revision ID: 0051
Revises: 0050
Create Date: 2026-10-18

La date de saisie dans Job-Room, par l'extension (« C'est déclaré ») ou à la main (« Marquer
comme déclarée ») : la page ORP compte celles qui restent à déclarer.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0051"
down_revision: str | None = "0050"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("job_room_at", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("applications", "job_room_at")
