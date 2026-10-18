"""Un lien d'invitation ne sert qu'une fois, même envoyé deux fois en même temps ; un identifiant
est unique sans tenir compte des majuscules (docs/69 §1)."""

from collections.abc import AsyncIterator

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from jobbot.auth import links, passwords
from jobbot.db.models import User
from jobbot.runtime import Runtime

PASSWORD = "un-mot-de-passe-solide"


@pytest.fixture
async def cleanup(runtime: Runtime) -> AsyncIterator[None]:
    yield
    async with runtime.engine.begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE lower(username) LIKE 'invite-%'"))
        await conn.execute(text("DELETE FROM account_links"))


async def test_link_is_locked_while_used(runtime: Runtime, cleanup: None) -> None:
    """Pendant qu'une demande utilise le lien, une seconde attend : elle ne peut pas le lire
    « encore valable » en même temps. Ensuite, elle le trouve utilisé."""
    async with runtime.sessionmaker.begin() as session:
        created = await links.create(session, "invite")
    async with runtime.sessionmaker() as first, first.begin():
        await links.find(first, created.token, lock=True)
        async with runtime.sessionmaker() as second, second.begin():
            await second.execute(text("set local lock_timeout = '300ms'"))
            with pytest.raises(DBAPIError, match="lock timeout"):
                await links.use(second, created.token, "invite-deux", PASSWORD)
        await links.use(first, created.token, "invite-un", PASSWORD)
    with pytest.raises(links.LinkError) as gone:
        async with runtime.sessionmaker.begin() as session:
            await links.use(session, created.token, "invite-trois", PASSWORD)
    assert gone.value.reason == "gone"
    async with runtime.sessionmaker() as session:
        names = list(
            await session.scalars(select(User.username).where(User.username.like("invite-%")))
        )
    assert names == ["invite-un"]


async def test_username_unique_whatever_the_case(runtime: Runtime, cleanup: None) -> None:
    async with runtime.sessionmaker.begin() as session:
        session.add(User(username="invite-Bob", password_hash=passwords.hash_password(PASSWORD)))
    with pytest.raises(IntegrityError):
        async with runtime.sessionmaker.begin() as session:
            session.add(
                User(username="invite-bob", password_hash=passwords.hash_password(PASSWORD))
            )
