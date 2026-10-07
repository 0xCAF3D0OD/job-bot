"""Candidatures : courriel de la personne contactée (champ du formulaire Job-Room)

Revision ID: 0030
Revises: 0029
Create Date: 2026-10-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0030"
down_revision: str | None = "0029"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("contact_email", sa.Text()))


def downgrade() -> None:
    op.drop_column("applications", "contact_email")
