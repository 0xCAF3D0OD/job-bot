"""Les rendez-vous ORP (docs/83)

Revision ID: 0057
Revises: 0056
Create Date: 2026-10-19

Une table personnelle, rangée par compte comme les autres (`account_isolation`, docs/78) :
la date du rendez-vous, le lieu, le conseiller, et les questions préparées.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0057"
down_revision: str | None = "0056"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CURRENT = "nullif(current_setting('app.user_id', true), '')::bigint"


def upgrade() -> None:
    op.create_table(
        "orp_meetings",
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            server_default=sa.text(CURRENT),
        ),
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("place", sa.Text()),
        sa.Column("advisor", sa.Text()),
        sa.Column("questions", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_orp_meetings_user_id", "orp_meetings", ["user_id"])
    op.create_index("ix_orp_meetings_starts_at", "orp_meetings", ["starts_at"])
    op.execute("alter table orp_meetings enable row level security")
    op.execute(
        "create policy account_isolation on orp_meetings "
        f"using (user_id = {CURRENT}) with check (user_id = {CURRENT})"
    )


def downgrade() -> None:
    op.drop_table("orp_meetings")
