"""Après le rendez-vous ORP (docs/83, 0.67.2)

Revision ID: 0058
Revises: 0057
Create Date: 2026-10-19

Ce qui a été convenu (objectif, mesures, assignations, note), le rappel de la veille et la
feuille rédigée par l'IA, sur la ligne du rendez-vous.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0058"
down_revision: str | None = "0057"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COLUMNS = (
    sa.Column("outcome_at", sa.DateTime(timezone=True)),
    sa.Column("agreed_target", sa.Integer()),
    sa.Column("measures", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
    sa.Column("assignments", sa.Text()),
    sa.Column("note", sa.Text()),
    sa.Column("reminded_for", sa.DateTime(timezone=True)),
    sa.Column("sheet_text", sa.Text()),
)


def upgrade() -> None:
    for column in COLUMNS:
        op.add_column("orp_meetings", column)


def downgrade() -> None:
    for column in reversed(COLUMNS):
        op.drop_column("orp_meetings", column.name)
