"""Les recherches préparées par métier (docs/121 §B, docs/122) et la première alerte d'un site."""

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot import accounts
from jobbot.alerts import trades
from jobbot.api.app import create_app
from jobbot.auth import passwords
from jobbot.collect import service
from jobbot.db.models import Notification, User
from jobbot.llm.client import RawResult
from jobbot.llm.pricing import Usage
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring_service

from . import test_collect
from .conftest import admin_engine, make_settings
from .test_collect import FakeMailbox

collect_runtime = test_collect.collect_runtime
imap_settings = test_collect.imap_settings
mailbox = test_collect.mailbox

PASSWORD = "un-mot-de-passe-solide"
FIXTURES = Path(__file__).parent / "fixtures" / "emails"


@pytest.mark.parametrize(
    ("typed", "name"),
    [
        ("Communicante", "Chargé·e de communication"),
        ("Employée de commerce", "Employé·e de commerce"),
        ("aide-soignante", "Aide-soignant·e"),
        ("Menuisier poseur", "Menuisier·ère"),
        ("DevOps", "Ingénieur·e DevOps"),
        ("Astronaute", None),
        ("ab", None),
    ],
)
def test_match(typed: str, name: str | None) -> None:
    found = trades.match(typed)
    assert (found.name if found else None) == name


def test_the_list_is_the_one_validated() -> None:
    """docs/122 : 63 métiers, 1 à 3 recherches chacun."""
    assert len(trades.TRADES) == 63
    assert all(1 <= len(t.searches) <= 3 for t in trades.TRADES)


def test_parse_ai_searches() -> None:
    text_ = 'Voici : {"searches": ["astronaute", " ingénieur spatial ", "astronaute", "x"]}'
    assert trades.parse_searches(text_) == ["astronaute", "ingénieur spatial", "x"]
    assert trades.parse_searches("pas de json") == []


class FakeClient:
    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.params: list[dict[str, Any]] = []

    async def score(self, params: dict[str, Any]) -> RawResult:
        self.params.append(params)
        return RawResult(self.answer, "claude-haiku-4-5", Usage(100, 0, 0, 30), "end_turn")


@pytest.fixture
async def guest() -> AsyncIterator[Runtime]:
    runtime = Runtime.create(make_settings(auth_enabled=True, anthropic_api_key="sk-test"))
    async with runtime.sessionmaker.begin() as session:
        session.add(User(username="lea-metier", password_hash=passwords.hash_password(PASSWORD)))
    yield runtime
    async with admin_engine().begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE username = 'lea-metier'"))
    await runtime.dispose()


async def _terms(runtime: Runtime, trade: str, roles: list[str]) -> list[str]:
    app = create_app(runtime.settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as api:
        await api.post("/api/auth/login", json={"username": "lea-metier", "password": PASSWORD})
        await api.put("/api/welcome", json={"trade": trade, "roles": roles})
        page = (await api.get("/api/alert-searches")).json()
    return [s["terms"] for s in page["searches"]]


async def test_searches_from_the_trade_and_the_cv(guest: Runtime) -> None:
    """Le métier de la liste donne ses recherches, puis les postes gardés depuis le CV."""
    terms = await _terms(guest, "Communicante", ["Responsable communication", "Communication"])
    assert terms == [
        "chargé de communication",
        "communication",
        "relations publiques",
        "Responsable communication",
    ]


async def test_unknown_trade_asks_the_ai_once(
    guest: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeClient(json.dumps({"searches": ["astronaute", "ingénieur spatial"]}))
    monkeypatch.setattr(scoring_service, "make_client", lambda _settings: fake)
    assert await _terms(guest, "Astronaute", []) == ["astronaute", "ingénieur spatial"]
    # Seul le nom du métier part à l'IA.
    assert fake.params[0]["messages"][0]["content"] == "<metier>Astronaute</metier>"
    await _terms(guest, "Astronaute", [])
    assert len(fake.params) == 1


async def test_first_alert_of_a_site_is_announced(
    collect_runtime: Runtime, mailbox: FakeMailbox
) -> None:
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE notifications"))
    mailbox.add((FIXTURES / "jobup-1.eml").read_bytes(), "<jobup-1>")
    with accounts.use(None):
        await service.collect(collect_runtime)
    mailbox.add((FIXTURES / "jobup-2.eml").read_bytes(), "<jobup-2>")
    with accounts.use(None):
        await service.collect(collect_runtime)
    async with collect_runtime.sessionmaker() as session:
        notes = list(
            await session.scalars(select(Notification).where(Notification.kind == "first_alert"))
        )
    assert [n.message for n in notes] == ["jobup t'a envoyé ses premières offres : 5."]
