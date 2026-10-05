"""Candidatures : suivi et données du formulaire ORP

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "offer_id",
            sa.BigInteger(),
            sa.ForeignKey("offers.id", ondelete="SET NULL"),
            unique=True,
        ),
        sa.Column("sent_at", sa.Date(), nullable=False),
        sa.Column("method", sa.Text(), nullable=False),
        sa.Column("assigned_by_orp", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("company", sa.Text(), nullable=False),
        sa.Column("company_address", sa.Text()),
        sa.Column("contact_name", sa.Text()),
        sa.Column("contact_phone", sa.Text()),
        sa.Column("job_title", sa.Text(), nullable=False),
        sa.Column("location", sa.Text()),
        sa.Column("rate_text", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False, server_default="en_attente"),
        sa.Column("status_reason", sa.Text()),
        sa.Column("status_at", sa.Date()),
        sa.Column("interview_at", sa.DateTime(timezone=True)),
        sa.Column("reminded_at", sa.DateTime(timezone=True)),
        sa.Column("orp_month", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "method IN ('electronique', 'ecrit', 'telephone', 'personnel')",
            name="applications_method_check",
        ),
        sa.CheckConstraint(
            "status IN ('en_attente', 'relancee', 'entretien', 'refus', 'engagement',"
            " 'sans_reponse')",
            name="applications_status_check",
        ),
    )
    op.create_index("ix_applications_orp_month", "applications", ["orp_month"])


def downgrade() -> None:
    op.drop_table("applications")
