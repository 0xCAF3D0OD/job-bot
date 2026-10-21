"""Les recommandations hors métier écartées (docs/116 §3)."""

from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from sqlalchemy import select, text

from jobbot import accounts
from jobbot.collect import service, topic
from jobbot.db.models import AlertSearch, Offer, Search
from jobbot.runtime import Runtime

from . import test_collect
from .conftest import admin_engine
from .test_collect import FakeMailbox

collect_runtime = test_collect.collect_runtime
imap_settings = test_collect.imap_settings
mailbox = test_collect.mailbox

FIXTURES = Path(__file__).parent / "fixtures" / "emails"


@pytest.mark.parametrize(
    ("title", "kept"),
    [
        ("Chargé·e de communication 80 %", True),
        ("Communicante digitale", True),
        ("Menuisier poseur H/F", False),
        ("Responsable de la communication interne", True),
        ("Assistante de direction", False),
    ],
)
def test_on_topic(title: str, kept: bool) -> None:
    stems = topic._stems("communicante") | topic._stems("relations presse")
    assert topic.on_topic(title, stems) is kept


def test_without_trade_everything_passes() -> None:
    assert topic.on_topic("Menuisier poseur H/F", set())


@pytest.fixture
async def alert(collect_runtime: Runtime) -> AsyncIterator[Runtime]:
    with accounts.use(None):
        async with collect_runtime.sessionmaker() as session:
            owner = await accounts.owner_id(session)
    with accounts.use(owner):
        async with collect_runtime.sessionmaker.begin() as session:
            session.add(AlertSearch(terms="ingénieur système", location=None))
    yield collect_runtime
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE alert_searches CASCADE"))


async def test_recommendations_keep_the_trade(alert: Runtime, mailbox: FakeMailbox) -> None:
    mailbox.add((FIXTURES / "jobup-1.eml").read_bytes(), "<jobup-1>")
    with accounts.use(None):
        await service.collect(alert)
    async with alert.sessionmaker() as session:
        search = (await session.scalars(select(Search))).one()
        titles = list(await session.scalars(select(Offer.title)))
    # Cinq recommandations ; une seule parle d'ingénieur système.
    assert titles == ["Ingénieur système infrastructure (f/m/d) - 80% ou 100%"]
    assert (search.results_count, search.off_topic_count) == (1, 4)
