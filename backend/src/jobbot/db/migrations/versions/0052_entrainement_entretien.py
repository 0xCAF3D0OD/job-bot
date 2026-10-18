"""S'entraîner à l'entretien (docs/75)

Revision ID: 0052
Revises: 0051
Create Date: 2026-10-18

Un entretien blanc avec l'IA dans le rôle du recruteur : ses réglages (type, ton, langue),
les échanges, le retour et son coût. Rangé par compte ; jamais compté comme un vrai entretien.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0052"
down_revision: str | None = "0051"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ROLE = "jobbot_app"
CURRENT = "nullif(current_setting('app.user_id', true), '')::bigint"


def upgrade() -> None:
    op.create_table(
        "interview_practices",
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            server_default=sa.text(CURRENT),
            index=True,
        ),
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "application_id",
            sa.BigInteger(),
            sa.ForeignKey("applications.id", ondelete="SET NULL"),
            index=True,
        ),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("tone", sa.Text(), nullable=False),
        sa.Column("language", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="en_cours"),
        sa.Column("turns", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("feedback", postgresql.JSONB()),
        sa.Column("cost_chf", sa.Numeric(10, 5), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.execute(f"grant all on interview_practices to {ROLE}")
    op.execute(f"grant all on sequence interview_practices_id_seq to {ROLE}")
    op.execute("alter table interview_practices enable row level security")
    op.execute(
        "create policy account_isolation on interview_practices "
        f"using (user_id = {CURRENT}) with check (user_id = {CURRENT})"
    )


def downgrade() -> None:
    op.drop_table("interview_practices")
