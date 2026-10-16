"""Invitations, réinitialisations, comptes suspendus, plafonds de l'IA (docs/65 §2, §4, §5)

Revision ID: 0047
Revises: 0046
Create Date: 2026-10-16

- `users` : plafond de l'IA du compte (fixé par l'exploitant), suspension, dernière connexion.
- `account_links` : lien à usage unique, invitation (7 jours) ou réinitialisation (24 h) ;
  la base n'en garde que l'empreinte.
- `platform_settings` : réglages de l'installation (plafond total de l'IA), communs.
- Deux fonctions donnent à l'exploitant des totaux sur tous les comptes, sans rien de leurs
  données : la dépense du mois de la plateforme, et l'usage de chaque compte (dépense, offres).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0047"
down_revision: str | None = "0046"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ROLE = "jobbot_app"


def upgrade() -> None:
    op.add_column("users", sa.Column("ai_budget_chf", sa.Numeric(8, 2)))
    op.add_column("users", sa.Column("suspended_at", sa.DateTime(timezone=True)))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True)))
    op.create_table(
        "account_links",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("token_hash", sa.Text(), nullable=False, unique=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("kind in ('invite', 'reset')", name="account_links_kind_check"),
        sa.CheckConstraint(
            "(kind = 'reset') = (user_id is not null)", name="account_links_user_check"
        ),
    )
    op.create_table(
        "platform_settings",
        sa.Column("key", sa.Text(), primary_key=True),
        sa.Column("value", JSONB(), nullable=False),
    )
    for table in ("account_links", "platform_settings"):
        op.execute(f"grant all on {table} to {ROLE}")
    op.execute(f"grant all on sequence account_links_id_seq to {ROLE}")

    op.execute(
        "create function platform_month_spend(since timestamptz) returns numeric "
        "language sql stable security definer set search_path = public as $$ "
        "select coalesce(sum(cost_chf), 0) from llm_calls where created_at >= since $$"
    )
    op.execute(
        "create function account_usage(since timestamptz) "
        "returns table (user_id bigint, spend_chf numeric, offers bigint) "
        "language sql stable security definer set search_path = public as $$ "
        "select u.id, "
        "(select coalesce(sum(c.cost_chf), 0) from llm_calls c "
        " where c.user_id = u.id and c.created_at >= since), "
        "(select count(*) from offers o where o.user_id = u.id and o.first_seen_at >= since) "
        "from users u $$"
    )
    for function in ("platform_month_spend(timestamptz)", "account_usage(timestamptz)"):
        op.execute(f"revoke all on function {function} from public")
        op.execute(f"grant execute on function {function} to {ROLE}")


def downgrade() -> None:
    op.execute("drop function account_usage(timestamptz)")
    op.execute("drop function platform_month_spend(timestamptz)")
    op.drop_table("platform_settings")
    op.drop_table("account_links")
    for column in ("last_login_at", "suspended_at", "ai_budget_chf"):
        op.drop_column("users", column)
