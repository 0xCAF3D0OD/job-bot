"""« Pas vrai » : les affirmations qu'une personne a marquées fausses dans une lettre (30.10.2026)

Revision ID: 0071
Revises: 0070
Create Date: 2026-10-30

`forbidden_claims` : une phrase marquée « Pas vrai », par compte. La rédaction et la relecture la
reçoivent comme interdite ; la personne la voit et peut la retirer dans son profil.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0071"
down_revision: str | None = "0070"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CURRENT = "nullif(current_setting('app.user_id', true), '')::bigint"


def upgrade() -> None:
    op.create_table(
        "forbidden_claims",
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            server_default=sa.text(CURRENT),
        ),
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("draft_id", sa.BigInteger()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    # La lettre d'où vient l'affirmation, du même compte (docs/78 §3.3).
    op.execute(
        "alter table forbidden_claims add constraint forbidden_claims_draft_id_fkey "
        "foreign key (user_id, draft_id) references drafts (user_id, id) "
        "on delete set null (draft_id)"
    )
    op.create_index("ix_forbidden_claims_user_id", "forbidden_claims", ["user_id"])
    op.execute("alter table forbidden_claims enable row level security")
    op.execute(
        "create policy account_isolation on forbidden_claims "
        f"using (user_id = {CURRENT}) with check (user_id = {CURRENT})"
    )


def downgrade() -> None:
    op.drop_table("forbidden_claims")
