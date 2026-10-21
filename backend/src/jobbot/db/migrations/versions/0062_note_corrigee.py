"""« Cette note ne me correspond pas » (docs/114)

Revision ID: 0062
Revises: 0061
Create Date: 2026-10-21

- `score_corrections` : une correction par offre (trop haute ou trop basse, la raison, un mot
  libre), le bloc de profil qu'elle a ajouté, le cas échéant. Table personnelle, rattachée à
  l'offre du même compte (docs/78 §3.3) et effacée avec elle.
- `profile_chunks.origin` : d'où vient un bloc ; « correction » quand il a été ajouté en
  corrigeant une note (la mention « Ajouté en corrigeant une note » dans Profil).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0062"
down_revision: str | None = "0061"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CURRENT = "nullif(current_setting('app.user_id', true), '')::bigint"


def upgrade() -> None:
    op.add_column("profile_chunks", sa.Column("origin", sa.Text()))
    op.create_table(
        "score_corrections",
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            server_default=sa.text(CURRENT),
        ),
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("offer_id", sa.BigInteger(), nullable=False),
        sa.Column("direction", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("score_before", sa.SmallInteger()),
        sa.Column("chunk_id", sa.BigInteger()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "offer_id"],
            ["offers.user_id", "offers.id"],
            name="score_corrections_offer_id_fkey",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_id", "offer_id", name="score_corrections_offer_key"),
    )
    # Le bloc ajouté, du même compte (docs/78 §3.3) ; il peut être supprimé dans Profil.
    op.execute(
        "alter table score_corrections add constraint score_corrections_chunk_id_fkey "
        "foreign key (user_id, chunk_id) references profile_chunks (user_id, id) "
        "on delete set null (chunk_id)"
    )
    op.create_index("ix_score_corrections_user_id", "score_corrections", ["user_id"])
    op.execute("alter table score_corrections enable row level security")
    op.execute(
        "create policy account_isolation on score_corrections "
        f"using (user_id = {CURRENT}) with check (user_id = {CURRENT})"
    )


def downgrade() -> None:
    op.drop_table("score_corrections")
    op.drop_column("profile_chunks", "origin")
