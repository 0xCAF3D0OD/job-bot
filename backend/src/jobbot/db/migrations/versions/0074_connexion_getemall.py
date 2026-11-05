"""« Se connecter avec jobA1 » depuis Get'emAll (docs/140)

Revision ID: 0074
Revises: 0073
Create Date: 2026-11-05

- `users.getemall_tester` : seuls les testeurs invités relient l'app pendant la phase de test.
- `partner_codes` : le code d'autorisation (60 s, une lecture, empreinte seule), avec le PKCE,
  l'adresse de retour et la case ORP.
- `partner_links` : l'identifiant propre à l'app et l'empreinte du jeton de lecture du suivi.

Deux tables personnelles (règle `account_isolation`). Le code et le jeton arrivent avant que le
compte soit connu : deux fonctions ne rendent que ce qu'il faut, comme pour l'extension
(migrations 0053 et 0056). `take_partner_code` brûle le code dans le même geste, si bien que deux
échanges simultanés du même code ne peuvent pas réussir tous les deux.
"""

from collections.abc import Sequence
from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision: str = "0074"
down_revision: str | None = "0073"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CURRENT = "nullif(current_setting('app.user_id', true), '')::bigint"
SEARCH_PATH = "public, pg_temp"
APP = "jobbot_app"
# Un compte suspendu ou qui n'est plus testeur ne passe plus.
ALLOWED = "u.suspended_at is null and u.getemall_tester"


def _owner_column() -> sa.Column[int]:
    return sa.Column(
        "user_id",
        sa.BigInteger(),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        server_default=sa.text(CURRENT),
    )


def _created() -> sa.Column[datetime]:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )


def _isolate(table: str) -> None:
    op.create_index(f"ix_{table}_user_id", table, ["user_id"])
    op.execute(f"alter table {table} enable row level security")
    op.execute(
        f"create policy account_isolation on {table} "
        f"using (user_id = {CURRENT}) with check (user_id = {CURRENT})"
    )


def _guard(signature: str) -> None:
    op.execute(f"revoke all on function {signature} from public")
    op.execute(f"grant execute on function {signature} to {APP}")


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("getemall_tester", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "partner_codes",
        _owner_column(),
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("partner", sa.Text(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("code_challenge", sa.Text(), nullable=False),
        sa.Column("redirect_uri", sa.Text(), nullable=False),
        sa.Column("orp", sa.Boolean(), nullable=False, server_default=sa.false()),
        _created(),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
    )
    _isolate("partner_codes")
    op.create_table(
        "partner_links",
        _owner_column(),
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("partner", sa.Text(), nullable=False),
        # 192 bits tirés au hasard : sans unicité globale, qui dirait à un compte qu'une ligne
        # existe chez un autre (migration 0055).
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("orp", sa.Boolean(), nullable=False, server_default=sa.false()),
        _created(),
        sa.Column(
            "authorized_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("user_id", "partner", name="partner_links_partner_key"),
    )
    _isolate("partner_links")
    # Le code est brûlé même s'il a expiré ou si le PKCE est faux : un seul essai par code.
    op.execute(
        "create function take_partner_code(hash text) returns table "
        "(user_id bigint, partner text, code_challenge text, redirect_uri text, orp boolean, "
        "expired boolean) "
        f"language sql volatile security definer set search_path = {SEARCH_PATH} as $$ "
        "update partner_codes c set used_at = now() from users u "
        f"where c.token_hash = hash and c.used_at is null and u.id = c.user_id and {ALLOWED} "
        "returning c.user_id, c.partner, c.code_challenge, c.redirect_uri, c.orp, "
        "c.expires_at <= now() $$"
    )
    _guard("take_partner_code(text)")
    op.execute(
        "create function account_of_partner_token(hash text) returns bigint "
        f"language sql stable security definer set search_path = {SEARCH_PATH} as $$ "
        "select l.user_id from partner_links l "
        f"join users u on u.id = l.user_id and {ALLOWED} "
        "where l.token_hash = hash and l.revoked_at is null $$"
    )
    _guard("account_of_partner_token(text)")


def downgrade() -> None:
    op.execute("drop function account_of_partner_token(text)")
    op.execute("drop function take_partner_code(text)")
    op.drop_table("partner_links")
    op.drop_table("partner_codes")
    op.drop_column("users", "getemall_tester")
