"""Le paiement de Plus (docs/125 §6, version 0.99.0)

Revision ID: 0069
Revises: 0068
Create Date: 2026-10-22

`users.plan_until` : la fin de la période payée (vide : Plus offert par l'exploitant) ;
`users.plan_cancelled_at` : l'abonnement est résilié, Plus dure jusqu'à `plan_until` ;
`users.billing_gateway_id`, `users.billing_subscription_id` : les références chez Payrexx.
`payments` : les paiements reçus, un par transaction Payrexx confirmée, pour les montrer à la
personne (les justificatifs comptables restent chez Payrexx et l'exploitant).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0069"
down_revision: str | None = "0068"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CURRENT = "nullif(current_setting('app.user_id', true), '')::bigint"


def upgrade() -> None:
    op.add_column("users", sa.Column("plan_until", sa.Date()))
    op.add_column("users", sa.Column("plan_cancelled_at", sa.DateTime(timezone=True)))
    op.add_column("users", sa.Column("billing_gateway_id", sa.Text()))
    op.add_column("users", sa.Column("billing_subscription_id", sa.Text()))
    op.create_table(
        "payments",
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            server_default=sa.text(CURRENT),
        ),
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("provider_ref", sa.Text(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.Text(), nullable=False, server_default="CHF"),
        sa.Column("paid_on", sa.Date(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("user_id", "provider_ref", name="payments_provider_ref_key"),
    )
    op.create_index("ix_payments_user_id", "payments", ["user_id"])
    op.execute("alter table payments enable row level security")
    op.execute(
        "create policy account_isolation on payments "
        f"using (user_id = {CURRENT}) with check (user_id = {CURRENT})"
    )


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_column("users", "billing_subscription_id")
    op.drop_column("users", "billing_gateway_id")
    op.drop_column("users", "plan_cancelled_at")
    op.drop_column("users", "plan_until")
