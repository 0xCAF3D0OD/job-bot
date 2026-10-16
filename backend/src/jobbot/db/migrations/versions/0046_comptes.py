"""Chaque ligne appartient à un compte, séparé par la base (docs/65 §1 et §7)

Revision ID: 0046
Revises: 0045
Create Date: 2026-10-16

- Les tables propres à une personne reçoivent `user_id`, rempli avec le premier compte
  (l'exploitant) pour les données déjà là, puis tiré du compte en cours (`app.user_id`).
- Les clés uniques qui valaient pour toute la plateforme valent désormais par compte.
- Sécurité au niveau des lignes : le rôle `jobbot_app`, que l'application endosse à chaque
  connexion, ne voit et n'écrit que les lignes du compte en cours. Sans compte : rien.
- Deux fonctions retrouvent le compte d'un jeton (extension, agenda) avant que le compte
  soit connu ; elles ne rendent que ce numéro. Une troisième compte les abonnés d'une source
  d'actualités dans tous les comptes, avant de l'effacer.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0046"
down_revision: str | None = "0045"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ROLE = "jobbot_app"
CURRENT = "nullif(current_setting('app.user_id', true), '')::bigint"

ACCOUNT_TABLES = (
    "settings",
    "searches",
    "offers",
    "offer_links",
    "offer_sightings",
    "criteria",
    "evaluations",
    "documents",
    "profile_chunks",
    "llm_calls",
    "llm_batches",
    "applications",
    "drafts",
    "orp_months",
    "notifications",
    "training_marks",
    "profiles",
    "profile_sources",
    "alert_searches",
    "alert_setups",
    "interviews",
    "chat_conversations",
    "chat_messages",
    "chat_actions",
    "calendar_tokens",
    "extension_tokens",
    "contacts",
)

# (table, ancienne contrainte ou index, nouvelle définition)
PRIMARY_KEYS = (
    ("settings", "settings_pkey", "(user_id, key)"),
    ("criteria", "criteria_pkey", "(user_id, kind)"),
    ("orp_months", "orp_months_pkey", "(user_id, month)"),
)
UNIQUES = (
    ("searches", "searches_message_id_key", "(user_id, message_id)"),
    ("offers", "offers_fingerprint_key", "(user_id, fingerprint)"),
    ("documents", "documents_sha256_key", "(user_id, sha256)"),
)


def upgrade() -> None:
    op.execute(
        f"""
        do $$ begin
          if not exists (select 1 from pg_roles where rolname = '{ROLE}') then
            create role {ROLE} nologin;
          end if;
        end $$;
        """
    )
    op.execute(f"grant {ROLE} to current_user")
    op.execute(f"grant usage on schema public to {ROLE}")
    op.execute(f"grant all on all tables in schema public to {ROLE}")
    op.execute(f"grant all on all sequences in schema public to {ROLE}")
    op.execute(f"alter default privileges in schema public grant all on tables to {ROLE}")
    op.execute(f"alter default privileges in schema public grant all on sequences to {ROLE}")

    # Le premier compte reçoit les données déjà là ; s'il n'y en a aucun, on le crée.
    op.execute(
        "insert into users (username, password_hash) "
        "select 'proprietaire', '!' where not exists (select 1 from users)"
    )
    for table in ACCOUNT_TABLES:
        op.execute(f"alter table {table} add column user_id bigint")
        op.execute(f"update {table} set user_id = (select min(id) from users)")
        op.execute(f"alter table {table} alter column user_id set not null")
        op.execute(f"alter table {table} alter column user_id set default {CURRENT}")
        op.execute(
            f"alter table {table} add constraint {table}_user_id_fkey "
            "foreign key (user_id) references users (id) on delete cascade"
        )
        op.execute(f"create index ix_{table}_user_id on {table} (user_id)")

    for table, name, columns in PRIMARY_KEYS:
        op.execute(f"alter table {table} drop constraint {name}")
        op.execute(f"alter table {table} add constraint {name} primary key {columns}")
    for table, name, columns in UNIQUES:
        op.execute(f"alter table {table} drop constraint {name}")
        op.execute(f"alter table {table} add constraint {name} unique {columns}")
    op.execute("drop index profiles_one_main")
    op.execute("create unique index profiles_one_main on profiles (user_id) where is_main")
    op.execute("drop index uq_offer_links_source_external_id")
    op.execute(
        "create unique index uq_offer_links_source_external_id "
        "on offer_links (user_id, source, external_id) where external_id is not null"
    )

    for table in ACCOUNT_TABLES:
        op.execute(f"alter table {table} enable row level security")
        op.execute(
            f"create policy account_isolation on {table} "
            f"using (user_id = {CURRENT}) with check (user_id = {CURRENT})"
        )
    # Le catalogue des formations est commun ; les suggestions faites pour un profil
    # n'appartiennent qu'au compte de ce profil.
    op.execute("alter table trainings enable row level security")
    op.execute(
        "create policy account_isolation on trainings using "
        "(profile_id is null or profile_id in (select id from profiles)) with check "
        "(profile_id is null or profile_id in (select id from profiles))"
    )

    for table, function in (
        ("extension_tokens", "account_of_extension_token"),
        ("calendar_tokens", "account_of_calendar_token"),
    ):
        op.execute(
            f"create function {function}(hash text) returns bigint "
            "language sql stable security definer set search_path = public as $$ "
            f"select user_id from {table} where token_hash = hash and revoked_at is null $$"
        )
        op.execute(f"revoke all on function {function}(text) from public")
        op.execute(f"grant execute on function {function}(text) to {ROLE}")
    # Une source d'actualités n'est effacée que si plus aucun compte ne la suit.
    op.execute(
        "create function news_source_followers(source bigint) returns bigint "
        "language sql stable security definer set search_path = public as $$ "
        "select count(*) from profile_sources where source_id = source $$"
    )
    op.execute("revoke all on function news_source_followers(bigint) from public")
    op.execute(f"grant execute on function news_source_followers(bigint) to {ROLE}")


def downgrade() -> None:
    op.execute("drop function news_source_followers(bigint)")
    for function in ("account_of_extension_token", "account_of_calendar_token"):
        op.execute(f"drop function {function}(text)")
    op.execute("drop policy account_isolation on trainings")
    op.execute("alter table trainings disable row level security")
    for table in ACCOUNT_TABLES:
        op.execute(f"drop policy account_isolation on {table}")
        op.execute(f"alter table {table} disable row level security")
    op.execute("drop index uq_offer_links_source_external_id")
    op.execute(
        "create unique index uq_offer_links_source_external_id "
        "on offer_links (source, external_id) where external_id is not null"
    )
    op.execute("drop index profiles_one_main")
    op.execute("create unique index profiles_one_main on profiles (is_main) where is_main")
    # Retour à un seul compte : seules les données de l'exploitant sont gardées.
    for table in ACCOUNT_TABLES:
        op.execute(f"delete from {table} where user_id <> (select min(id) from users)")
    for table, name, _columns in UNIQUES:
        column = name.removeprefix(f"{table}_").removesuffix("_key")
        op.execute(f"alter table {table} drop constraint {name}")
        op.execute(f"alter table {table} add constraint {name} unique ({column})")
    for table, name, columns in PRIMARY_KEYS:
        op.execute(f"alter table {table} drop constraint {name}")
        op.execute(
            f"alter table {table} add constraint {name} primary key "
            f"({columns.removeprefix('(user_id, ')}"
        )
    for table in ACCOUNT_TABLES:
        op.execute(f"alter table {table} drop column user_id")
