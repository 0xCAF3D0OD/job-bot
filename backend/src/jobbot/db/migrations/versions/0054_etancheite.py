"""Étanchéité des comptes dans la base (docs/78 §3.1 et §3.2)

Revision ID: 0054
Revises: 0053
Create Date: 2026-10-18

- Deux rôles de connexion sans privilège : `jobbot_app` (l'API) et `jobbot_worker` (le
  worker, qui a les droits de l'API et écrit en plus les tables communes). Ni superutilisateur,
  ni contournement de la séparation : l'API n'a plus à se restreindre elle-même.
- Droits précis : lire, ajouter, modifier, supprimer ; plus de TRUNCATE, REFERENCES ni TRIGGER.
  La version des migrations est en lecture seule.
- Tables de connexion (`users`, `sessions`, `account_links`) séparées par la base : un compte
  ne voit que sa ligne, l'exploitant voit les comptes ; un jeton ou un identifiant n'est
  reconnu, avant que le compte soit connu, que par une fonction qui ne rend que son numéro.
- Tables communes lisibles par tous, écrites par le worker et l'exploitant seulement ; le
  catalogue des formations aussi.
- Les fonctions spéciales cherchent leurs noms dans `public` puis `pg_temp` (en dernier).

Les rôles valent pour tout le serveur PostgreSQL : ils ne sont jamais supprimés au retour
arrière, une autre base peut s'en servir.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0054"
down_revision: str | None = "0053"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP = "jobbot_app"
WORKER = "jobbot_worker"
CURRENT = "nullif(current_setting('app.user_id', true), '')::bigint"
IS_OWNER = f"{CURRENT} = platform_owner()"
SEARCH_PATH = "public, pg_temp"

SHARED = (
    "companies",
    "company_logos",
    "sites",
    "news_sources",
    "news_items",
    "platform_settings",
    "job_runs",
)
EXISTING_FUNCTIONS = (
    "account_of_extension_token(text)",
    "account_of_calendar_token(text)",
    "account_usage(timestamptz)",
    "platform_month_spend(timestamptz)",
    "collected_message_ids(text[])",
)
# (nom, arguments, types des arguments, résultat, requête)
NEW_FUNCTIONS = (
    # Le compte de l'exploitant : le premier créé.
    ("platform_owner", "", "", "bigint", "select min(id) from users"),
    # Les comptes pour qui tournent les tâches planifiées (pas les suspendus).
    (
        "active_accounts",
        "",
        "",
        "setof bigint",
        "select id from users where suspended_at is null order by id",
    ),
    # Expirée ou non : la session expirée est effacée ensuite, au nom de son compte.
    (
        "account_of_session",
        "hash text",
        "text",
        "bigint",
        "select s.user_id from sessions s join users u on u.id = s.user_id "
        "where s.token_hash = hash and u.suspended_at is null",
    ),
    (
        "account_of_login",
        "name text",
        "text",
        "bigint",
        "select id from users where lower(username) = lower(name)",
    ),
    # La plateforme a-t-elle déjà un compte avec mot de passe (premier démarrage) ?
    (
        "platform_has_password",
        "",
        "",
        "boolean",
        "select exists (select 1 from users where password_hash <> '!')",
    ),
)


def _definer(name: str, args: str, types: str, result: str, query: str) -> None:
    op.execute(
        f"create function {name}({args}) returns {result} language sql stable "
        f"security definer set search_path = {SEARCH_PATH} as $$ {query} $$"
    )
    op.execute(f"revoke all on function {name}({types}) from public")
    op.execute(f"grant execute on function {name}({types}) to {APP}")


def _shared_policies(table: str) -> None:
    op.execute(f"alter table {table} enable row level security")
    op.execute(f"create policy shared_read on {table} for select using (true)")
    op.execute(f"create policy owner_insert on {table} for insert with check ({IS_OWNER})")
    op.execute(
        f"create policy owner_update on {table} for update "
        f"using ({IS_OWNER}) with check ({IS_OWNER})"
    )
    op.execute(f"create policy owner_delete on {table} for delete using ({IS_OWNER})")
    op.execute(f"create policy worker_write on {table} to {WORKER} using (true) with check (true)")


def upgrade() -> None:
    # Les rôles : connexion directe, sans aucun privilège particulier.
    op.execute(
        f"""
        do $$ begin
          if not exists (select 1 from pg_roles where rolname = '{WORKER}') then
            create role {WORKER} nologin;
          end if;
        end $$;
        """
    )
    for role in (APP, WORKER):
        op.execute(
            f"alter role {role} login nosuperuser nobypassrls nocreatedb nocreaterole inherit"
        )
    op.execute(f"grant {APP} to {WORKER}")
    # L'utilisateur des migrations peut encore endosser ces rôles (ancienne configuration).
    op.execute(f"grant {WORKER} to current_user")

    # Les droits : seulement lire, ajouter, modifier, supprimer.
    op.execute(f"revoke all on all tables in schema public from {APP}")
    op.execute(f"grant select, insert, update, delete on all tables in schema public to {APP}")
    op.execute(f"revoke insert, update, delete on alembic_version from {APP}")
    op.execute(f"revoke all on all sequences in schema public from {APP}")
    op.execute(f"grant usage, select on all sequences in schema public to {APP}")
    op.execute(f"alter default privileges in schema public revoke all on tables from {APP}")
    op.execute(
        "alter default privileges in schema public "
        f"grant select, insert, update, delete on tables to {APP}"
    )
    op.execute(f"alter default privileges in schema public revoke all on sequences from {APP}")
    op.execute(
        f"alter default privileges in schema public grant usage, select on sequences to {APP}"
    )

    # Les fonctions spéciales.
    for definition in NEW_FUNCTIONS:
        _definer(*definition)
    op.execute(
        "create function drop_unfollowed_news_source(source bigint) returns void "
        f"language sql volatile security definer set search_path = {SEARCH_PATH} as $$ "
        "delete from news_sources where id = source and not exists "
        "(select 1 from profile_sources where source_id = source) $$"
    )
    op.execute("revoke all on function drop_unfollowed_news_source(bigint) from public")
    op.execute(f"grant execute on function drop_unfollowed_news_source(bigint) to {APP}")
    op.execute("drop function news_source_followers(bigint)")
    for function in EXISTING_FUNCTIONS:
        op.execute(f"alter function {function} set search_path = {SEARCH_PATH}")

    # Les tables de connexion.
    op.execute("alter table users enable row level security")
    mine_or_owner = f"(id = {CURRENT} or {IS_OWNER})"
    op.execute(f"create policy account_read on users for select using {mine_or_owner}")
    op.execute(
        f"create policy account_update on users for update "
        f"using {mine_or_owner} with check {mine_or_owner}"
    )
    op.execute(f"create policy account_delete on users for delete using {mine_or_owner}")
    # La collecte des e-mails range chaque alerte par l'adresse du compte (docs/65 §3).
    op.execute(f"create policy worker_read on users for select to {WORKER} using (true)")
    # Le premier compte se crée sur une base vide ; les suivants, par l'exploitant.
    op.execute(
        "create policy account_create on users for insert "
        f"with check ({IS_OWNER} or platform_owner() is null)"
    )
    op.execute("alter table sessions enable row level security")
    op.execute(
        "create policy account_isolation on sessions "
        f"using (user_id = {CURRENT} or {IS_OWNER}) "
        f"with check (user_id = {CURRENT} or {IS_OWNER})"
    )
    op.execute("alter table account_links enable row level security")
    op.execute(
        f"create policy owner_only on account_links using ({IS_OWNER}) with check ({IS_OWNER})"
    )

    # Les tables communes.
    for table in SHARED:
        _shared_policies(table)
    mine = "profile_id in (select id from profiles)"
    catalog = f"({mine} or (profile_id is null and {IS_OWNER}))"
    op.execute("drop policy account_isolation on trainings")
    op.execute(
        f"create policy trainings_read on trainings for select using (profile_id is null or {mine})"
    )
    op.execute(f"create policy trainings_insert on trainings for insert with check {catalog}")
    op.execute(
        "create policy trainings_update on trainings for update "
        f"using {catalog} with check {catalog}"
    )
    op.execute(f"create policy trainings_delete on trainings for delete using {catalog}")


def downgrade() -> None:
    for name in ("trainings_read", "trainings_insert", "trainings_update", "trainings_delete"):
        op.execute(f"drop policy {name} on trainings")
    op.execute(
        "create policy account_isolation on trainings using "
        "(profile_id is null or profile_id in (select id from profiles)) with check "
        "(profile_id is null or profile_id in (select id from profiles))"
    )
    for table in SHARED:
        for name in ("shared_read", "owner_insert", "owner_update", "owner_delete", "worker_write"):
            op.execute(f"drop policy {name} on {table}")
        op.execute(f"alter table {table} disable row level security")
    op.execute("drop policy owner_only on account_links")
    op.execute("alter table account_links disable row level security")
    op.execute("drop policy account_isolation on sessions")
    op.execute("alter table sessions disable row level security")
    for name in (
        "account_read",
        "account_update",
        "account_delete",
        "account_create",
        "worker_read",
    ):
        op.execute(f"drop policy {name} on users")
    op.execute("alter table users disable row level security")

    for function in EXISTING_FUNCTIONS:
        op.execute(f"alter function {function} set search_path = public")
    op.execute(
        "create function news_source_followers(source bigint) returns bigint "
        "language sql stable security definer set search_path = public as $$ "
        "select count(*) from profile_sources where source_id = source $$"
    )
    op.execute("revoke all on function news_source_followers(bigint) from public")
    op.execute(f"grant execute on function news_source_followers(bigint) to {APP}")
    op.execute("drop function drop_unfollowed_news_source(bigint)")
    for name, _args, types, _result, _query in NEW_FUNCTIONS:
        op.execute(f"drop function {name}({types})")

    op.execute(f"grant all on all tables in schema public to {APP}")
    op.execute(f"grant all on all sequences in schema public to {APP}")
    op.execute(f"alter default privileges in schema public grant all on tables to {APP}")
    op.execute(f"alter default privileges in schema public grant all on sequences to {APP}")
