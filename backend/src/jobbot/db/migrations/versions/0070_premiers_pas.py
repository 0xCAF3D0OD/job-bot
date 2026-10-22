"""Les premiers pas : le chiffre de l'équipe (docs/128 §4, version 1.1.0)

Revision ID: 0070
Revises: 0069
Create Date: 2026-10-22

`first_steps_progress(since)` : pour chaque compte accepté créé depuis `since` (l'exploitant
excepté), sa date de création, le nombre d'étapes des premiers pas faites (0 à 5) et sa
première candidature. Des nombres et des dates, rien d'autre : ni nom, ni offre, ni contenu.
Elle ne répond qu'à l'exploitant. Les règles sont celles de `jobbot.first_steps`.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0070"
down_revision: str | None = "0069"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP = "jobbot_app"
SEARCH_PATH = "public, pg_temp"
CURRENT = "nullif(current_setting('app.user_id', true), '')::bigint"


def _has(table: str, where: str = "") -> str:
    return f"exists (select 1 from {table} t where t.user_id = u.id{where})"


STORED = (
    "(select (s.value #>> '{}')::int from settings s where s.user_id = u.id "
    "and s.key = 'first_steps_reached' and jsonb_typeof(s.value) = 'number')"
)
KEPT = " and t.status in ('preparing', 'applied')"
COMPUTED = (
    "case "
    f"when {_has('applications')} then 5 "
    f"when {_has('drafts')} then 4 "
    f"when {_has('offers', KEPT)} then 3 "
    f"when {_has('alert_setups')} or {_has('searches')} or {_has('offers')} then 2 "
    f"when {_has('criteria')} and {_has('documents')} then 1 "
    "else 0 end"
)


def upgrade() -> None:
    op.execute(
        "create function first_steps_progress(since timestamptz) "
        "returns table (user_id bigint, created_at timestamptz, reached int, "
        "first_sent_at timestamptz) "
        f"language sql stable security definer set search_path = {SEARCH_PATH} as $$ "
        f"select u.id, u.created_at, greatest(coalesce({STORED}, 0), {COMPUTED}), "
        "(select min(a.created_at) from applications a where a.user_id = u.id) "
        "from users u where u.created_at >= since and u.approved_at is not null "
        f"and u.id <> platform_owner() and {CURRENT} = platform_owner() "
        "order by u.id $$"
    )
    op.execute("revoke all on function first_steps_progress(timestamptz) from public")
    op.execute(f"grant execute on function first_steps_progress(timestamptz) to {APP}")


def downgrade() -> None:
    op.execute("drop function first_steps_progress(timestamptz)")
