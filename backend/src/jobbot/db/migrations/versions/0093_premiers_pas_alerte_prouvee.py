"""Les premiers pas : une alerte déclarée créée ne compte qu'avec un e-mail du site

Revision ID: 0093
Revises: 0092
Create Date: 2026-11-18

Décision de Kevin du 18.11 (docs/decisions/2026-11-18-1415-alerte-prouvee.md) :
`first_steps_progress` suit la nouvelle règle de `jobbot.first_steps`. « J'ai créé l'alerte »
(`alert_setups`) ne coche plus l'étape seul : il faut aussi un e-mail de ce site arrivé dans la
boîte jobA1 (code, message ou alerte ; ni la recherche publique, ni un e-mail ignoré), au plus un
jour avant la déclaration. Une alerte reçue suffit toujours. Le reste de la fonction ne change
pas.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0093"
down_revision: str | None = "0092"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SEARCH_PATH = "public, pg_temp"
CURRENT = "nullif(current_setting('app.user_id', true), '')::bigint"


def _has(table: str, where: str = "") -> str:
    return f"exists (select 1 from {table} t where t.user_id = u.id{where})"


STORED = (
    "(select (s.value #>> '{}')::int from settings s where s.user_id = u.id "
    "and s.key = 'first_steps_reached' and jsonb_typeof(s.value) = 'number')"
)
KEPT = " and t.status in ('preparing', 'applied')"
# `received_alert()` de jobbot.db.models.
RECEIVED = " and t.message_id not like 'public:%' and t.kind is null"
# `alerts.service.site_heard`.
HEARD = (
    " and exists (select 1 from searches h where h.user_id = u.id and h.source = t.site"
    " and h.received_at >= t.created_at - interval '1 day'"
    " and h.message_id not like 'public:%'"
    " and (h.kind is null or h.kind <> 'ignored'))"
)


def _computed(alerts: str) -> str:
    return (
        "case "
        f"when {_has('applications')} then 5 "
        f"when {_has('drafts')} then 4 "
        f"when {_has('offers', KEPT)} then 3 "
        f"when {alerts} then 2 "
        f"when {_has('criteria')} and {_has('documents')} then 1 "
        "else 0 end"
    )


NEW = f"{_has('alert_setups', HEARD)} or {_has('searches', RECEIVED)}"
# La règle de 0084, pour revenir en arrière.
OLD = f"{_has('alert_setups')} or {_has('searches', RECEIVED)}"


def _function(alerts: str) -> str:
    # `create or replace` garde les droits posés par 0070 (exécution pour jobbot_app seulement).
    return (
        "create or replace function first_steps_progress(since timestamptz) "
        "returns table (user_id bigint, created_at timestamptz, reached int, "
        "first_sent_at timestamptz) "
        f"language sql stable security definer set search_path = {SEARCH_PATH} as $$ "
        f"select u.id, u.created_at, greatest(coalesce({STORED}, 0), {_computed(alerts)}), "
        "(select min(a.created_at) from applications a where a.user_id = u.id) "
        "from users u where u.created_at >= since and u.approved_at is not null "
        f"and u.id <> platform_owner() and {CURRENT} = platform_owner() "
        "order by u.id $$"
    )


def upgrade() -> None:
    op.execute(_function(NEW))


def downgrade() -> None:
    op.execute(_function(OLD))
