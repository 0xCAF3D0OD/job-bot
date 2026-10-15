"""Formations (docs/37 §1) : une formation terminée devient un bloc de profil

Revision ID: 0039
Revises: 0038
Create Date: 2026-10-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0039"
down_revision: str | None = "0038"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "training_marks",
        sa.Column(
            "chunk_id",
            sa.BigInteger(),
            sa.ForeignKey("profile_chunks.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("training_marks", "chunk_id")
