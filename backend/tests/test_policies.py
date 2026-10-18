"""Une règle pour chaque table, et des rôles sans privilège (docs/78 §3.1 et §3.2).

La liste des familles (`jobbot.db.policies`) est comparée à la base elle-même : une table
oubliée, ou sans la règle de sa famille, fait échouer ces tests.
"""

import re
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import psycopg
import pytest
from sqlalchemy import func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ProgrammingError

from jobbot import accounts
from jobbot.auth import passwords
from jobbot.db import policies
from jobbot.db.base import APP_ROLE, WORKER_ROLE
from jobbot.db.models import Company, NewsSource, ProfileSource, User
from jobbot.profiles.service import main_profile
from jobbot.runtime import Runtime

from .conftest import TEST_DATABASE_URL, admin_engine

GUEST = "compte-regles"
NOW = datetime.now(UTC)


async def catalog(sql: str, **params: object) -> list[tuple[object, ...]]:
    async with admin_engine().connect() as conn:
        return [tuple(row) for row in await conn.execute(text(sql), params)]


@pytest.fixture
async def guest(runtime: Runtime) -> AsyncIterator[int]:
    async with admin_engine().begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE username = :u"), {"u": GUEST})
    async with runtime.sessionmaker.begin() as session:
        user = User(username=GUEST, password_hash=passwords.hash_password("x" * 12))
        session.add(user)
        await session.flush()
        guest_id = user.id
    yield guest_id
    async with admin_engine().begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE username = :u"), {"u": GUEST})
        await conn.execute(text("DELETE FROM companies WHERE name_key LIKE 'regles-%'"))
        await conn.execute(text("DELETE FROM news_sources WHERE name LIKE 'Règles %'"))


async def test_every_table_has_a_family() -> None:
    tables = {
        str(name)
        for (name,) in await catalog(
            "select relname from pg_class where relkind = 'r' "
            "and relnamespace = 'public'::regnamespace"
        )
    }
    assert tables - set(policies.FAMILIES) == set(), "table sans famille dans db/policies.py"
    assert set(policies.FAMILIES) - tables == set(), "famille d'une table qui n'existe plus"


async def test_each_family_has_its_rules() -> None:
    rls = {
        str(name): bool(enabled)
        for name, enabled in await catalog(
            "select relname, relrowsecurity from pg_class where relkind = 'r' "
            "and relnamespace = 'public'::regnamespace"
        )
    }
    names = {
        (str(table), str(policy))
        for table, policy in await catalog("select tablename, policyname from pg_policies")
    }
    not_null = {
        str(table)
        for (table,) in await catalog(
            "select table_name from information_schema.columns where table_schema = 'public' "
            "and column_name = 'user_id' and is_nullable = 'NO'"
        )
    }
    for table, family in policies.FAMILIES.items():
        if family == "technical":
            assert not rls[table], table
            continue
        assert rls[table], f"{table} : pas de séparation dans la base"
        if family == "personal":
            assert (table, "account_isolation") in names, table
            assert table in not_null, f"{table} : user_id peut rester vide"
        elif family == "shared" and table != "trainings":
            assert {(table, "shared_read"), (table, "worker_write")} <= names, table
    assert ("trainings", "trainings_insert") in names


async def test_roles_have_no_privilege() -> None:
    roles = {
        str(name): (bool(superuser), bool(bypass), bool(login))
        for name, superuser, bypass, login in await catalog(
            "select rolname, rolsuper, rolbypassrls, rolcanlogin from pg_roles "
            "where rolname in (:a, :w)",
            a=APP_ROLE,
            w=WORKER_ROLE,
        )
    }
    assert roles == {APP_ROLE: (False, False, True), WORKER_ROLE: (False, False, True)}
    # Ni vider une table d'un coup (TRUNCATE passe outre la séparation), ni déclencheur, ni
    # référence ; la version des migrations en lecture seule.
    risky = await catalog(
        "select relname, p from pg_class, unnest(array['TRUNCATE', 'REFERENCES', 'TRIGGER']) p "
        "where relkind = 'r' and relnamespace = 'public'::regnamespace "
        "and has_table_privilege(:a, oid, p)",
        a=APP_ROLE,
    )
    assert risky == []
    writes = await catalog(
        "select has_table_privilege(:a, 'alembic_version', 'UPDATE')", a=APP_ROLE
    )
    assert writes == [(False,)]


async def test_special_functions_are_guarded() -> None:
    functions = await catalog(
        "select proname, proconfig, coalesce(proacl::text, '') from pg_proc "
        "where prosecdef and pronamespace = 'public'::regnamespace"
    )
    assert len(functions) == 11
    for name, config, acl in functions:
        assert config == ["search_path=public, pg_temp"], name
        # Pas d'exécution pour tout le monde (« =X/ » : PUBLIC), seulement pour l'API.
        assert not re.search(r"[{,]=X/", str(acl)) and f"{APP_ROLE}=X/" in str(acl), name


async def test_direct_login_cannot_climb_back() -> None:
    """Connecté en jobbot_app, il n'y a rien à « défaire » : ni RESET ROLE, ni un autre rôle,
    ni TRUNCATE (docs/78 §3.1)."""
    url = make_url(TEST_DATABASE_URL).set(drivername="postgresql", username=APP_ROLE)
    try:
        conn = await psycopg.AsyncConnection.connect(
            url.render_as_string(hide_password=False), connect_timeout=3
        )
    except psycopg.OperationalError:
        pytest.skip("connexion locale en jobbot_app impossible (mot de passe exigé)")
    async with conn:
        await conn.execute("reset role")
        row = await (
            await conn.execute(
                "select current_user, rolsuper from pg_roles where rolname = current_user"
            )
        ).fetchone()
        assert row == (APP_ROLE, False)
        for statement in (f"set role {WORKER_ROLE}", "truncate offers", "select * from pg_authid"):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                await conn.execute(statement)
            await conn.rollback()
        # Sans compte : ni comptes, ni sessions, ni offres.
        for table in ("users", "sessions", "account_links", "offers"):
            count = await (await conn.execute(f"select count(*) from {table}")).fetchone()
            assert count == (0,), table


async def test_connection_tables_show_only_ones_own(
    runtime: Runtime, account: int, guest: int
) -> None:
    with accounts.use(guest):
        async with runtime.sessionmaker() as session:
            seen = set(await session.scalars(select(User.id)))
            hashes = await session.scalar(text("select count(*) from sessions"))
            links = await session.scalar(text("select count(*) from account_links"))
            owner = await accounts.owner_id(session)
    assert seen == {guest}
    assert hashes == 0 and links == 0
    assert owner == account  # connu de tous, sans montrer la liste des comptes
    async with runtime.sessionmaker() as session:
        everyone = set(await session.scalars(select(User.id)))
    assert {account, guest} <= everyone  # l'exploitant voit les comptes
    # Un invité ne crée pas de compte.
    with accounts.use(guest), pytest.raises(ProgrammingError, match="row-level security"):
        async with runtime.sessionmaker.begin() as session:
            session.add(User(username="regles-intrus", password_hash="!"))


async def test_shared_tables_written_by_worker_and_owner_only(
    runtime: Runtime, account: int, guest: int
) -> None:
    with accounts.use(guest):
        assert not await _writes(runtime)
        with pytest.raises(ProgrammingError, match="row-level security"):
            async with runtime.sessionmaker.begin() as session:
                session.add(Company(name_key="regles-invite", candidates=[], looked_up_at=NOW))
        async with runtime.sessionmaker.begin() as session:
            # Lire reste permis ; modifier une ligne commune ne touche rien.
            assert await session.scalar(select(func.count()).select_from(Company)) is not None
            changed = await session.execute(text("update sites set name = name"))
            assert getattr(changed, "rowcount", 0) == 0
    assert await _writes(runtime)  # l'exploitant
    async with runtime.sessionmaker.begin() as session:
        session.add(Company(name_key="regles-exploitant", candidates=[], looked_up_at=NOW))
    worker = Runtime.create(runtime.settings, "worker")
    try:
        with accounts.use(guest):
            assert await _writes(worker)
            async with worker.sessionmaker.begin() as session:
                session.add(Company(name_key="regles-worker", candidates=[], looked_up_at=NOW))
    finally:
        await worker.dispose()


async def _writes(rt: Runtime) -> bool:
    async with rt.sessionmaker() as session:
        return await accounts.writes_shared(session)


async def test_followed_source_survives_an_unfollow(
    runtime: Runtime, account: int, guest: int
) -> None:
    """Un invité qui ne suit plus une source ne l'efface pas si un autre compte la suit, et
    n'apprend pas qui la suit (migration 0054)."""
    async with runtime.sessionmaker.begin() as session:
        source = NewsSource(
            name="Règles source",
            kind="articles",
            url="https://regles.example",
            feed_url="https://regles.example/flux",
        )
        session.add(source)
        await session.flush()
        source_id = source.id
        profile = await main_profile(session)
        session.add(ProfileSource(profile_id=profile.id, source_id=source_id))
    with accounts.use(guest):
        async with runtime.sessionmaker.begin() as session:
            result = await session.scalar(select(func.drop_unfollowed_news_source(source_id)))
    assert result is None
    async with runtime.sessionmaker() as session:
        assert await session.get(NewsSource, source_id) is not None
    async with admin_engine().begin() as conn:
        await conn.execute(
            text("DELETE FROM profile_sources WHERE source_id = :s"), {"s": source_id}
        )
    async with runtime.sessionmaker.begin() as session:
        await session.execute(select(func.drop_unfollowed_news_source(source_id)))
    async with runtime.sessionmaker() as session:
        assert await session.get(NewsSource, source_id) is None


async def test_personal_uniques_are_per_account() -> None:
    """Une unicité qui vaudrait pour toute la plateforme dirait à un compte, par un refus,
    qu'une ligne existe chez un autre (migration 0055). Seules exceptions : les empreintes
    de jetons et le numéro de lot de l'IA, tirés au hasard."""
    rows = await catalog(
        "select conrelid::regclass::text, pg_get_constraintdef(oid) from pg_constraint "
        "where contype = 'u'"
    )
    allowed = {"UNIQUE (token_hash)", "UNIQUE (provider_batch_id)"}
    global_ = [
        (table, definition)
        for table, definition in rows
        if table in policies.PERSONAL
        and "user_id" not in str(definition)
        and definition not in allowed
    ]
    assert global_ == []
