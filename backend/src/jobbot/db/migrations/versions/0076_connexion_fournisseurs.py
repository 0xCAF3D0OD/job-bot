"""Se connecter avec Google, Microsoft ou Apple (docs/65, complément du 2026-11-05)

Revision ID: 0076
Revises: 0075
Create Date: 2026-11-05

- `oauth_links` : le compte du fournisseur (`provider`, `subject`) lié à un compte jobA1, unique
  sur toute la plateforme ; l'e-mail donné par le fournisseur et s'il l'a vérifié.

Table de connexion, comme `sessions` : un compte ne voit et ne modifie que ses liens (règle
`account_isolation`, sans exception pour l'exploitant). Le lien arrive avant que le compte soit
connu : deux fonctions ne rendent que le numéro du compte, comme `account_of_login`.
`account_of_verified_email` ne répond que si un seul compte a cet e-mail vérifié.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0076"
down_revision: str | None = "0075"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CURRENT = "nullif(current_setting('app.user_id', true), '')::bigint"
SEARCH_PATH = "public, pg_temp"
APP = "jobbot_app"


def _guard(signature: str) -> None:
    op.execute(f"revoke all on function {signature} from public")
    op.execute(f"grant execute on function {signature} to {APP}")


def upgrade() -> None:
    op.create_table(
        "oauth_links",
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            server_default=sa.text(CURRENT),
        ),
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("email", sa.Text()),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("provider", "subject", name="oauth_links_subject_key"),
        sa.CheckConstraint(
            "provider in ('google', 'microsoft', 'apple')", name="oauth_links_provider_check"
        ),
    )
    op.create_index("ix_oauth_links_user_id", "oauth_links", ["user_id"])
    op.execute("alter table oauth_links enable row level security")
    op.execute(
        "create policy account_isolation on oauth_links "
        f"using (user_id = {CURRENT}) with check (user_id = {CURRENT})"
    )
    op.execute(
        "create function account_of_oauth(provider_name text, subject_id text) returns bigint "
        f"language sql stable security definer set search_path = {SEARCH_PATH} as $$ "
        "select user_id from oauth_links "
        "where provider = provider_name and subject = subject_id $$"
    )
    _guard("account_of_oauth(text, text)")
    op.execute(
        "create function account_of_verified_email(address text) returns bigint "
        f"language sql stable security definer set search_path = {SEARCH_PATH} as $$ "
        "select case when count(distinct user_id) = 1 then min(user_id) end "
        "from oauth_links where email_verified and lower(email) = lower(address) $$"
    )
    _guard("account_of_verified_email(text)")


def downgrade() -> None:
    op.execute("drop function account_of_verified_email(text)")
    op.execute("drop function account_of_oauth(text, text)")
    op.drop_table("oauth_links")
