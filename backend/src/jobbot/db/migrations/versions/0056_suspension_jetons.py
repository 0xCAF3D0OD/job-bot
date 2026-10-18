"""Un compte suspendu ne passe plus par ses jetons (docs/78 §2)

Revision ID: 0056
Revises: 0055
Create Date: 2026-10-18

Les fonctions qui reconnaissent un jeton d'extension ou d'agenda ignorent un compte suspendu,
comme la session. La suspension révoque aussi ces jetons (`PATCH /api/platform/accounts/…`).
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0056"
down_revision: str | None = "0055"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SEARCH_PATH = "public, pg_temp"
CONDITIONS = {
    "extension_tokens": (
        "account_of_extension_token",
        "t.revoked_at is null and (t.expires_at is null or t.expires_at > now())",
    ),
    "calendar_tokens": ("account_of_calendar_token", "t.revoked_at is null"),
}


def _function(table: str, name: str, condition: str, *, active_only: bool) -> None:
    join = " join users u on u.id = t.user_id and u.suspended_at is null" if active_only else ""
    op.execute(
        f"create or replace function {name}(hash text) returns bigint "
        f"language sql stable security definer set search_path = {SEARCH_PATH} as $$ "
        f"select t.user_id from {table} t{join} where t.token_hash = hash and {condition} $$"
    )


def upgrade() -> None:
    for table, (name, condition) in CONDITIONS.items():
        _function(table, name, condition, active_only=True)


def downgrade() -> None:
    for table, (name, condition) in CONDITIONS.items():
        _function(table, name, condition, active_only=False)
