"""Brouillons de lettre (et de CV en 0.5.0-c), rattachés aux candidatures

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "drafts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "offer_id",
            sa.BigInteger(),
            sa.ForeignKey("offers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("language", sa.Text(), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column("instruction", sa.Text()),
        sa.Column("model", sa.Text()),
        sa.Column("prompt_version", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("edited_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("offer_id", "kind", "version"),
        sa.CheckConstraint("kind IN ('letter', 'cv')", name="drafts_kind_check"),
        sa.CheckConstraint("language IN ('fr', 'en', 'de')", name="drafts_language_check"),
    )
    for column in ("letter_draft_id", "cv_draft_id"):
        op.add_column(
            "applications",
            sa.Column(column, sa.BigInteger(), sa.ForeignKey("drafts.id", ondelete="SET NULL")),
        )


def downgrade() -> None:
    op.drop_column("applications", "cv_draft_id")
    op.drop_column("applications", "letter_draft_id")
    op.drop_table("drafts")
