"""La boîte des invités (docs/113) : à part de celle de l'exploitant, vidée après copie."""

from collections.abc import AsyncIterator, Callable
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot import accounts
from jobbot.api.app import create_app
from jobbot.auth import passwords
from jobbot.collect import service
from jobbot.db.models import Search, User
from jobbot.mail import addresses, site_codes
from jobbot.mail.imap import MailboxError
from jobbot.runtime import Runtime
from jobbot.worker import tasks as _tasks  # noqa: F401  (enregistre les tâches)
from jobbot.worker.jobs import execute

from .conftest import admin_engine, make_settings
from .emails import make_email
from .test_collect import FakeMailbox
from .test_site_codes import Clock

NOW = datetime.now(UTC)


class FakeGuestBox(FakeMailbox):
    """La boîte des invités en mémoire : `clean` retire ce que jobA1 a déjà copié."""

    def __init__(self) -> None:
        super().__init__()
        self.cleaned: list[str] = []

    def clean(self, *, known: Callable[[set[str]], set[str]], before: date) -> int:
        copied = known({mid for mid, _ in self.emails})
        self.cleaned += sorted(copied)
        self.emails = [(mid, raw) for mid, raw in self.emails if mid not in copied]
        return len(copied)


@pytest.fixture
async def rt(tmp_path: Path) -> AsyncIterator[Runtime]:
    settings = make_settings(
        imap_user="kevin@example.com",
        imap_password="secret-de-test",
        guest_imap_user="alertes@example.ch",
        guest_imap_password="secret-invites",
        alert_domain="alertes@example.ch",
        storage_path=tmp_path,
    )
    runtime = Runtime.create(settings, "worker")
    async with admin_engine().begin() as conn:
        await conn.execute(text("TRUNCATE searches, offers, job_runs CASCADE"))
    yield runtime
    async with admin_engine().begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE username = 'amy-boite'"))
    await runtime.dispose()


@pytest.fixture
def boxes(monkeypatch: pytest.MonkeyPatch) -> tuple[FakeMailbox, FakeGuestBox]:
    owner, guest = FakeMailbox(), FakeGuestBox()
    monkeypatch.setattr(service, "mailbox_factory", lambda _settings: owner)
    monkeypatch.setattr(service, "guest_mailbox_factory", lambda _settings: guest)
    return owner, guest


async def _amy(rt: Runtime) -> int:
    async with rt.sessionmaker.begin() as session:
        user = User(
            username="amy-boite",
            password_hash=passwords.hash_password("un-mot-de-passe-solide"),
            mail_code="fictif02",
        )
        session.add(user)
        await session.flush()
        return user.id


def _mail(message_id: str, to: str) -> bytes:
    return make_email(
        message_id=message_id,
        sender="noreply@jobs.example",
        received_at=NOW,
        subject="Bienvenue",
        to=to,
    )


async def _messages(rt: Runtime, account: int) -> list[str]:
    with accounts.use(account):
        async with rt.sessionmaker() as session:
            return list(await session.scalars(select(Search.message_id).order_by(Search.id)))


async def test_guest_box_is_separate_and_emptied(
    rt: Runtime, boxes: tuple[FakeMailbox, FakeGuestBox], account: int
) -> None:
    owner_box, guest_box = boxes
    amy = await _amy(rt)
    owner_box.add(_mail("<kevin@x>", "kevin@example.com"), "<kevin@x>")
    guest_box.add(_mail("<amy@x>", "alertes+amy-fictif02@example.ch"), "<amy@x>")
    # Dans la boîte des invités, un e-mail sans code d'invité n'est à personne, pas à
    # l'exploitant.
    guest_box.add(_mail("<perdu@x>", "alertes@example.ch"), "<perdu@x>")
    with accounts.use(None):
        result = await service.collect(rt)
    assert (result.fetched, result.new_searches, result.unrouted) == (3, 2, 1)
    assert await _messages(rt, amy) == ["<amy@x>"]
    assert await _messages(rt, account) == ["<kevin@x>"]
    # La boîte des invités est vidée de ce qui est copié ; l'e-mail sans compte attend
    # (supprimé après 7 jours). La boîte de l'exploitant, elle, n'a pas de « clean ».
    assert guest_box.cleaned == ["<amy@x>"]
    assert [mid for mid, _ in guest_box.emails] == ["<perdu@x>"]
    assert [mid for mid, _ in owner_box.emails] == ["<kevin@x>"]


async def test_guest_box_read_when_gmail_fails(
    rt: Runtime, boxes: tuple[FakeMailbox, FakeGuestBox], account: int
) -> None:
    """Décision de Kevin du 15.11 : une boîte illisible (mot de passe Gmail refusé) n'empêche
    pas de lire l'autre ; l'erreur est relancée après, ou gardée dans le résultat."""
    owner_box, guest_box = boxes
    amy = await _amy(rt)
    owner_box.error = MailboxError("auth", "authentification IMAP refusée")
    guest_box.add(_mail("<amy@x>", "alertes+amy-fictif02@example.ch"), "<amy@x>")
    with accounts.use(None), pytest.raises(MailboxError):
        await service.collect(rt)
    assert await _messages(rt, amy) == ["<amy@x>"]
    assert guest_box.cleaned == ["<amy@x>"]
    with accounts.use(None):
        result = await service.collect(rt, raise_errors=False)
    assert [e.kind for e in result.errors] == ["auth"]
    # Et dans l'autre sens : la boîte des invités en panne, celle de l'exploitant est lue.
    owner_box.error = None
    guest_box.error = MailboxError("connection", "connexion IMAP impossible")
    owner_box.add(_mail("<kevin@x>", "kevin@example.com"), "<kevin@x>")
    with accounts.use(None):
        result = await service.collect(rt, raise_errors=False)
    assert [e.kind for e in result.errors] == ["connection"]
    assert await _messages(rt, account) == ["<kevin@x>"]


async def test_three_waits_one_shared_reading(
    rt: Runtime,
    boxes: tuple[FakeMailbox, FakeGuestBox],
    account: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Décision de Kevin du 15.11 : trois pages attendent en même temps ; un seul relevé lit la
    boîte des invités toutes les 15 s, et chaque code arrive sur la page de son compte."""
    _owner_box, guest_box = boxes
    clock = Clock(monkeypatch)
    monkeypatch.setattr(site_codes, "enqueue", _no_enqueue)
    names = {"lea-trois": "trois001", "max-trois": "trois002", "zoe-trois": "trois003"}
    ids: dict[str, int] = {}
    async with rt.sessionmaker.begin() as session:
        for name, code in names.items():
            user = User(username=name, password_hash="!", mail_code=code)
            session.add(user)
            await session.flush()
            ids[name] = user.id
    # Le code de chacun arrive à son tour : Léa au 2e relevé, Max au 4e, Zoé au 7e.
    arrivals = {2: ("lea-trois", "111111"), 4: ("max-trois", "222222"), 7: ("zoe-trois", "333333")}
    fetches = guest_box.since_calls
    real_fetch = guest_box.fetch_since

    def fetch_since(*args: object, **kwargs: object) -> object:
        arrival = arrivals.get(len(fetches) + 1)
        if arrival:
            name, code = arrival
            mid = f"<{name}@x>"
            guest_box.add(_code(mid, f"alertes+{name}-{names[name]}@example.ch", code), mid)
        return real_fetch(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(guest_box, "fetch_since", fetch_since)
    try:
        for user_id in ids.values():
            with accounts.use(user_id):
                await site_codes.expect(rt)
        with accounts.use(None):
            assert await execute(rt, site_codes.FAST_COLLECT_JOB)
        # Sept relevés, un toutes les 15 s, un seul relevé pour les trois attentes ; le dernier
        # code reçu, plus personne n'attend : le relevé s'arrête.
        assert len(fetches) == 7
        assert clock.sleeps == 7
        for name, code in [
            ("lea-trois", "111111"),
            ("max-trois", "222222"),
            ("zoe-trois", "333333"),
        ]:
            with accounts.use(ids[name]):
                found = await site_codes.last(rt, "jobup")
            assert found is not None and found.code == code
    finally:
        async with admin_engine().begin() as conn:
            await conn.execute(text("DELETE FROM users WHERE username LIKE '%-trois'"))


async def _no_enqueue(_settings: object, _name: str) -> bool:
    return True


def _code(message_id: str, to: str, code: str) -> bytes:
    return make_email(
        message_id=message_id,
        sender="no-reply@jobup.ch",
        received_at=NOW,
        subject="Votre code de vérification",
        html=f"<p>Votre code de vérification est <b>{code}</b>. Il expire dans 10 minutes.</p>",
        to=to,
    )


async def test_guest_address_without_owner_box(tmp_path: Path) -> None:
    """La boîte des invités suffit pour donner une adresse à un invité."""
    settings = make_settings(
        guest_imap_user="alertes@example.ch",
        guest_imap_password="secret-invites",
        alert_domain="alertes@example.ch",
        storage_path=tmp_path,
    )
    assert settings.guest_imap_configured and not settings.imap_configured
    rt = Runtime.create(settings)
    amy = await _amy(rt)
    try:
        with accounts.use(amy):
            async with rt.sessionmaker.begin() as session:
                address = await addresses.account_address(session, settings)
        assert address == "alertes+amy-boite-fictif02@example.ch"
        app = create_app(settings, rt)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
            assert (await api.get("/api/privacy")).json()["guest_mailbox"] is True
    finally:
        async with admin_engine().begin() as conn:
            await conn.execute(text("DELETE FROM users WHERE username = 'amy-boite'"))
        await rt.dispose()
