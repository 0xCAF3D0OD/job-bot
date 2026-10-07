"""Mes alertes (docs/20 §1) : recherches à suivre et alertes créées sur les sites

Revision ID: 0031
Revises: 0030
Create Date: 2026-10-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0031"
down_revision: str | None = "0030"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "alert_searches",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("terms", sa.Text(), nullable=False),
        sa.Column("location", sa.Text()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "alert_setups",
        sa.Column(
            "search_id",
            sa.BigInteger(),
            sa.ForeignKey("alert_searches.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("site", sa.Text(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("alert_setups")
    op.drop_table("alert_searches")
