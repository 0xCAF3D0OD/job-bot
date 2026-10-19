"""Les certificats de travail, décodés (docs/87)

Revision ID: 0059
Revises: 0058
Create Date: 2026-10-19

Un document peut être marqué certificat de travail (`documents.kind`). Sa lecture est gardée
dans une table personnelle, rattachée au document du même compte (docs/78 §3.3) et effacée
avec lui.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0059"
down_revision: str | None = "0058"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CURRENT = "nullif(current_setting('app.user_id', true), '')::bigint"


def upgrade() -> None:
    op.add_column("documents", sa.Column("kind", sa.Text()))
    op.create_table(
        "certificate_readings",
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            server_default=sa.text(CURRENT),
        ),
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.BigInteger(), nullable=False),
        sa.Column("language", sa.Text()),
        sa.Column("grade", sa.SmallInteger()),
        sa.Column("advice", sa.Text(), nullable=False),
        sa.Column("passages", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("notes", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("rules_version", sa.Text(), nullable=False),
        sa.Column("ai", JSONB()),
        sa.Column("ai_at", sa.DateTime(timezone=True)),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "document_id"],
            ["documents.user_id", "documents.id"],
            name="certificate_readings_document_id_fkey",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_id", "document_id", name="certificate_readings_document_key"),
    )
    op.create_index("ix_certificate_readings_user_id", "certificate_readings", ["user_id"])
    op.execute("alter table certificate_readings enable row level security")
    op.execute(
        "create policy account_isolation on certificate_readings "
        f"using (user_id = {CURRENT}) with check (user_id = {CURRENT})"
    )


def downgrade() -> None:
    op.drop_table("certificate_readings")
    op.drop_column("documents", "kind")
