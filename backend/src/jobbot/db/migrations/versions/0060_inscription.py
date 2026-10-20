"""S'inscrire, sur demande (docs/102)

Revision ID: 0060
Revises: 0059
Create Date: 2026-10-20

- `users.approved_at` : la date d'acceptation par l'exploitant. Vide : une demande de compte
  en attente. Les comptes existants prennent leur date de création ; un compte créé autrement
  (invitation, `jobbot set-password`) est accepté d'office.
- `users.signup_note` : le mot laissé avec la demande, effacé à l'acceptation.
- Les fonctions qui disent les comptes des tâches et le compte d'une session ignorent un
  compte en attente, comme un compte suspendu.

La demande est créée au nom de l'exploitant, comme une invitation : la règle d'ajout des
comptes ne change pas.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0060"
down_revision: str | None = "0059"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SEARCH_PATH = "public, pg_temp"


def _functions(pending_excluded: bool) -> None:
    approved = " and {}approved_at is not null" if pending_excluded else ""
    op.execute(
        "create or replace function active_accounts() returns setof bigint "
        f"language sql stable security definer set search_path = {SEARCH_PATH} as $$ "
        f"select id from users where suspended_at is null{approved.format('')} order by id $$"
    )
    op.execute(
        "create or replace function account_of_session(hash text) returns bigint "
        f"language sql stable security definer set search_path = {SEARCH_PATH} as $$ "
        "select s.user_id from sessions s join users u on u.id = s.user_id "
        f"where s.token_hash = hash and u.suspended_at is null{approved.format('u.')} $$"
    )


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("approved_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.add_column("users", sa.Column("signup_note", sa.Text()))
    op.execute("update users set approved_at = created_at")
    _functions(pending_excluded=True)


def downgrade() -> None:
    # Sans la colonne, une demande en attente deviendrait un compte actif : elle est effacée.
    op.execute("delete from users where approved_at is null")
    _functions(pending_excluded=False)
    op.drop_column("users", "signup_note")
    op.drop_column("users", "approved_at")
