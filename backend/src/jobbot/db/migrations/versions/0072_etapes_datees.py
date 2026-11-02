"""Les étapes datées, pour le test utilisateurs (demande de Kevin du 30.10.2026)

Revision ID: 0072
Revises: 0071
Create Date: 2026-10-30

`account_milestones` : pour chaque compte, la date de la première fois de chaque étape, écrite une
seule fois : première alerte créée, première offre reçue, première candidature préparée (lettre ou
CV), premières preuves exportées. L'inscription est `users.created_at`. Une étape et une date,
rien d'autre : ni texte d'offre, ni lettre, ni coordonnées (nLPD, mentionné dans « Tes données »).

Les dates s'écrivent dans la base, par des déclencheurs : tous les chemins (l'interface, le worker
des alertes, l'extension) sont couverts. Pour les comptes existants, les dates déjà connues sont
reprises. `milestones_progress()` les donne à l'exploitant seul.

Gardées jusqu'à la fin du test (décision de Kevin) : `end_user_test()`, à l'exploitant seul, les
efface pour tous les comptes et arrête l'enregistrement (`user_test_open` à false dans les
réglages de la plateforme) ; un nouveau test le rouvre. La fermeture d'un compte les efface aussi.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0072"
down_revision: str | None = "0071"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP = "jobbot_app"
SEARCH_PATH = "public, pg_temp"
CURRENT = "nullif(current_setting('app.user_id', true), '')::bigint"
STEPS = ("first_alert", "first_offer", "first_prepared", "first_export")
# Chaque déclencheur : la table, l'étape, la date, la condition.
TRIGGERS = (
    ("alert_setups", "first_alert", "new.created_at", "insert", "true"),
    ("searches", "first_alert", "new.received_at", "insert", "true"),
    ("offers", "first_offer", "new.first_seen_at", "insert", "true"),
    ("drafts", "first_prepared", "new.created_at", "insert", "true"),
    ("orp_months", "first_export", "new.exported_at", "insert or update of exported_at",
     "new.exported_at is not null"),
)  # fmt: skip
BACKFILL = (
    ("first_alert", "select user_id, min(created_at) from alert_setups group by user_id"),
    ("first_alert", "select user_id, min(received_at) from searches group by user_id"),
    ("first_offer", "select user_id, min(first_seen_at) from offers group by user_id"),
    ("first_prepared", "select user_id, min(created_at) from drafts group by user_id"),
    (
        "first_export",
        "select user_id, min(exported_at) from orp_months where exported_at is not null "
        "group by user_id",
    ),
)


def upgrade() -> None:
    op.create_table(
        "account_milestones",
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            server_default=sa.text(CURRENT),
        ),
        sa.Column("step", sa.Text(), nullable=False),
        sa.Column("reached_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "step", name="account_milestones_pkey"),
        sa.CheckConstraint(
            "step in (" + ", ".join(f"'{s}'" for s in STEPS) + ")",
            name="account_milestones_step_check",
        ),
    )
    op.execute("alter table account_milestones enable row level security")
    op.execute(
        "create policy account_isolation on account_milestones "
        f"using (user_id = {CURRENT}) with check (user_id = {CURRENT})"
    )
    # La première date de l'étape, jamais remplacée ; une date plus ancienne trouvée plus tard
    # (une alerte d'avant, rangée après) la corrige.
    # Des fonctions ordinaires (pas « security definer ») : elles écrivent sous la séparation par
    # compte, avec le compte de la ligne qui les déclenche ; personne ne date l'étape d'un autre.
    op.execute(
        "create function mark_milestone(account bigint, kind text, at timestamptz) "
        f"returns void language sql set search_path = {SEARCH_PATH} as $$ "
        "insert into account_milestones (user_id, step, reached_at) select account, kind, at "
        "where coalesce((select value #>> '{}' from platform_settings "
        "where key = 'user_test_open'), 'true') = 'true' "
        "on conflict (user_id, step) do update set reached_at = excluded.reached_at "
        "where excluded.reached_at < account_milestones.reached_at $$"
    )
    for table, step, at, when, condition in TRIGGERS:
        op.execute(
            f"create function milestone_{table}() returns trigger language plpgsql "
            f"set search_path = {SEARCH_PATH} as $$ begin "
            f"if {condition} then perform mark_milestone(new.user_id, '{step}', "
            f"coalesce({at}, now())); end if; return new; end $$"
        )
        op.execute(
            f"create trigger milestone after {when} on {table} "
            f"for each row execute function milestone_{table}()"
        )
    for step, query in BACKFILL:
        op.execute(
            "insert into account_milestones (user_id, step, reached_at) "
            f"select s.user_id, '{step}', s.min from ({query}) s(user_id, min) "
            "where s.min is not null "
            "on conflict (user_id, step) do update set reached_at = excluded.reached_at "
            "where excluded.reached_at < account_milestones.reached_at"
        )
    # Pour l'exploitant seul : l'inscription et la date de chaque étape, par compte (sans nom).
    columns = ", ".join(
        f"(select m.reached_at from account_milestones m where m.user_id = u.id and m.step = '{s}')"
        for s in STEPS
    )
    op.execute(
        "create function milestones_progress() "
        "returns table (user_id bigint, created_at timestamptz, first_alert timestamptz, "
        "first_offer timestamptz, first_prepared timestamptz, first_export timestamptz) "
        f"language sql stable security definer set search_path = {SEARCH_PATH} as $$ "
        f"select u.id, u.created_at, {columns} from users u "
        "where u.approved_at is not null and u.id <> platform_owner() "
        f"and {CURRENT} = platform_owner() order by u.created_at desc $$"
    )
    op.execute("revoke all on function milestones_progress() from public")
    op.execute(f"grant execute on function milestones_progress() to {APP}")
    # La fin du test : toutes les dates effacées, l'enregistrement arrêté (l'exploitant seul).
    op.execute(
        "create function end_user_test() returns void language plpgsql security definer "
        f"set search_path = {SEARCH_PATH} as $$ begin "
        f"if {CURRENT} is distinct from platform_owner() then "
        "raise exception 'réservé à l''exploitant'; end if; "
        "delete from account_milestones; "
        "insert into platform_settings (key, value) values ('user_test_open', 'false'::jsonb) "
        "on conflict (key) do update set value = excluded.value; end $$"
    )
    op.execute("revoke all on function end_user_test() from public")
    op.execute(f"grant execute on function end_user_test() to {APP}")


def downgrade() -> None:
    op.execute("drop function end_user_test()")
    op.execute("delete from platform_settings where key = 'user_test_open'")
    op.execute("drop function milestones_progress()")
    for table, *_ in TRIGGERS:
        op.execute(f"drop trigger milestone on {table}")
        op.execute(f"drop function milestone_{table}()")
    op.execute("drop function mark_milestone(bigint, text, timestamptz)")
    op.drop_table("account_milestones")
