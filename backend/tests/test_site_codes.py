"""Les codes et les messages des sites (docs/112)."""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot import accounts
from jobbot.api.app import create_app
from jobbot.collect import service
from jobbot.db.models import Notification, Search
from jobbot.mail import confirm, site_codes
from jobbot.mail.codes import find_code
from jobbot.mail.message import ParsedEmail
from jobbot.notify import service as notify
from jobbot.runtime import Runtime
from jobbot.worker.jobs import RunContext
from jobbot.worker.tasks import site_codes as fast_task

from . import test_collect
from .conftest import admin_engine
from .emails import make_email
from .test_collect import FakeMailbox

collect_runtime = test_collect.collect_runtime
imap_settings = test_collect.imap_settings
mailbox = test_collect.mailbox

NOW = datetime.now(UTC)


def email(subject: str, text_body: str) -> ParsedEmail:
    return ParsedEmail("m", subject, "no-reply@jobup.ch", "jobup.ch", NOW, None, text_body)


@pytest.mark.parametrize(
    ("subject", "body", "code"),
    [
        (
            "Votre code de vérification",
            "Voici votre code : 482913. Il expire dans 10 minutes. Rue X 12, 1003 Lausanne, "
            "tél. 021 123 45 67",
            "482913",
        ),
        ("Ihr Bestätigungscode", "Ihr Code lautet 482 913", "482913"),
        ("Your verification code", "Use 4829 to verify your email. Copyright 2026", "4829"),
        ("Bienvenue sur jobup", "Service client : +41 21 123 45 67. Code postal 1003.", None),
        ("Alerte modifiée", "Votre alerte a été modifiée le 21.10.2026.", None),
        ("Code promo", "Votre code promo vaut 20 CHF", None),
    ],
)
def test_find_code(subject: str, body: str, code: str | None) -> None:
    found = find_code(email(subject, body))
    assert (found.code if found else None) == code


@pytest.fixture
def phone(monkeypatch: pytest.MonkeyPatch) -> list[notify.Message]:
    sent: list[notify.Message] = []

    async def send(_settings: object, message: notify.Message) -> None:
        sent.append(message)

    async def phone_settings(_session: object, settings: object) -> object:
        return settings

    monkeypatch.setattr(notify, "send", send)
    monkeypatch.setattr(notify, "phone_settings", phone_settings)
    return sent


@pytest.fixture
async def clean(collect_runtime: Runtime) -> Runtime:
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE notifications"))
        await conn.execute(text("DELETE FROM settings WHERE key = 'code_expected'"))
    return collect_runtime


def _code_email(message_id: str, received: datetime) -> bytes:
    return make_email(
        message_id=message_id,
        sender="no-reply@jobup.ch",
        received_at=received,
        subject="Votre code de vérification",
        html="<p>Votre code de vérification est <b>482913</b>. Il expire dans 10 minutes.</p>",
    )


async def test_code_shown_then_erased(
    clean: Runtime, mailbox: FakeMailbox, phone: list[notify.Message]
) -> None:
    mailbox.add(_code_email("<code@x>", datetime.now(UTC)), "<code@x>")
    with accounts.use(None):
        result = await service.collect(clean)
    assert result.codes == 1
    async with clean.sessionmaker() as session:
        search = (await session.scalars(select(Search))).one()
        assert (search.kind, search.code) == ("code", "482913")
        bell = (await session.scalars(select(Notification))).one()
        assert (bell.kind, bell.message) == ("site_code", "jobup : 482 913")
    # Dans la notification du téléphone, le code lui-même.
    assert [m.message for m in phone] == ["jobup : 482 913"]

    app = create_app(clean.settings, clean)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        page = (await api.get("/api/alert-searches")).json()
        assert [(c["site"], c["code"]) for c in page["codes"]] == [("jobup", "482913")]
        # Ni preuve de recherche ORP, ni alerte reçue du site.
        orp = (await api.get("/api/orp", params={"month": f"{NOW:%Y-%m}"})).json()
        assert orp["searches"] == []

    later = datetime.now(UTC) + timedelta(minutes=31)
    raw_key = search.raw_key
    assert clean.storage.exists(raw_key)
    await site_codes.purge(clean, later)
    # La copie de l'e-mail du code s'en va avec lui (docs/113).
    assert not clean.storage.exists(raw_key)
    async with clean.sessionmaker() as session:
        assert (await session.scalars(select(Search.code))).one() is None
        assert (await session.scalars(select(Notification.message))).one() == "Code expiré"
    assert await site_codes.current(clean) == []
    # Au bout de 30 jours, l'e-mail lui-même s'en va.
    assert await site_codes.purge(clean, datetime.now(UTC) + timedelta(days=31)) == 1
    async with clean.sessionmaker() as session:
        assert (await session.scalars(select(Search))).first() is None


async def test_extension_reads_a_fresh_code(
    clean: Runtime, mailbox: FakeMailbox, phone: Any
) -> None:
    mailbox.add(_code_email("<old@x>", datetime.now(UTC) - timedelta(minutes=12)), "<old@x>")
    with accounts.use(None):
        await service.collect(clean)
    # Reçu il y a 12 minutes : montré sur la page, mais trop vieux pour être rempli.
    assert len(await site_codes.current(clean)) == 1
    assert await site_codes.latest(clean, "jobup") is None
    mailbox.add(_code_email("<new@x>", datetime.now(UTC)), "<new@x>")
    with accounts.use(None):
        await service.collect(clean)
    found = await site_codes.latest(clean, "jobup")
    assert found is not None and found.code == "482913"
    assert await site_codes.latest(clean, "indeed") is None


async def test_site_messages(clean: Runtime, mailbox: FakeMailbox) -> None:
    mailbox.add(
        make_email(
            message_id="<hello@x>",
            sender="info@jobs.example",
            received_at=datetime.now(UTC),
            subject="Bienvenue sur jobs.example",
            html="<p>Bienvenue !</p><img src='https://x/y.png'><p>Ton compte est prêt.</p>",
        ),
        "<hello@x>",
    )
    with accounts.use(None):
        await service.collect(clean)
    app = create_app(clean.settings, clean)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        [message] = (await api.get("/api/alert-searches/messages")).json()
        assert message["subject"] == "Bienvenue sur jobs.example"
        body = (await api.get(f"/api/alert-searches/messages/{message['id']}")).json()
        assert body["text"] == "aucune offre"
        assert (await api.get("/api/alert-searches/messages/999999")).status_code == 404


async def test_confirmation_opened_for_known_sites(
    clean: Runtime, mailbox: FakeMailbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened: list[str] = []
    accepted = {"https://www.jobup.ch/fr/alerte/confirmer?t=1": True}

    async def fake_open(url: str) -> bool:
        opened.append(url)
        return accepted.get(url, False)

    monkeypatch.setattr(confirm, "_open", fake_open)
    links = {
        "<ok@x>": "https://www.jobup.ch/fr/alerte/confirmer?t=1",
        "<login@x>": "https://www.jobup.ch/fr/alerte/confirmer?t=2",
        "<other@x>": "https://jobs.example/alert/confirm?t=3",
    }
    for message_id, url in links.items():
        mailbox.add(
            make_email(
                message_id=message_id,
                sender="noreply@jobs.example",
                received_at=datetime.now(UTC),
                subject="Merci de confirmer votre alerte",
                html=f'<a href="{url}">Confirmer mon alerte</a>',
            ),
            message_id,
        )
    with accounts.use(None):
        await service.collect(clean)
    # Seuls les sites connus sont ouverts ; une page qui demande une connexion reste à faire.
    assert sorted(opened) == sorted(links[k] for k in ("<ok@x>", "<login@x>"))
    app = create_app(clean.settings, clean)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        pending = (await api.get("/api/alert-searches")).json()["to_confirm"]
    assert sorted(p["url"] for p in pending) == sorted(links[k] for k in ("<login@x>", "<other@x>"))
    # Jamais un lien qui désinscrit ou change un mot de passe, ni un site inconnu.
    assert not await confirm.open_confirmation("https://www.jobup.ch/unsubscribe?confirm=1")
    assert not await confirm.open_confirmation("https://www.jobup.ch/password/reset?t=1")
    assert len(opened) == 2


async def test_expect_code_is_limited(clean: Runtime, monkeypatch: pytest.MonkeyPatch) -> None:
    queued: list[str] = []

    async def enqueue(_settings: object, name: str) -> bool:
        queued.append(name)
        return True

    monkeypatch.setattr(site_codes, "enqueue", enqueue)
    app = create_app(clean.settings, clean)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        answers = [
            (await api.post("/api/alert-searches/expect-code")).json()["queued"] for _ in range(7)
        ]
    assert answers == [True] * 6 + [False]
    assert queued == ["collect_fast"] * 6


async def test_fast_collect_stops_at_the_first_code(
    clean: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    rounds: list[int] = []

    async def collect(_runtime: Runtime, _run_id: object = None) -> service.CollectResult:
        rounds.append(1)
        return service.CollectResult(fetched=1, codes=1 if len(rounds) == 3 else 0)

    async def no_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(fast_task, "collect", collect)
    monkeypatch.setattr(asyncio, "sleep", no_sleep)
    await fast_task.collect_fast_job(clean, RunContext(job="collect_fast"))
    assert len(rounds) == 3
