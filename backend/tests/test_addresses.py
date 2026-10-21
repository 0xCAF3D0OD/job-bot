"""Une adresse de réception par compte (docs/65 §3) : l'aiguillage, la collecte rangée par
destinataire, les e-mails de confirmation, les sites en pause pour un compte."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot import accounts
from jobbot.api.app import create_app
from jobbot.auth import passwords
from jobbot.collect import service
from jobbot.db.models import Search, User
from jobbot.mail.addresses import (
    alert_box,
    alert_domain,
    domain_address,
    name_slug,
    plus_address,
    route,
)
from jobbot.mail.confirm import confirmation_link
from jobbot.mail.message import parse_email
from jobbot.runtime import Runtime
from jobbot.sources.sites import load_sites

from . import test_collect
from .conftest import make_settings
from .emails import make_email
from .test_collect import FakeMailbox

# Les fixtures de la collecte (boîte en mémoire, analyseurs de test, réglages IMAP).
collect_runtime = test_collect.collect_runtime
imap_settings = test_collect.imap_settings
mailbox = test_collect.mailbox
parsers = test_collect.parsers

BASE = "alertes@example.com"
NOW = datetime(2026, 10, 16, 9, tzinfo=UTC)


def test_route_by_recipient() -> None:
    codes = {"k7f3q9ab": 2}
    assert route(("alertes@example.com",), BASE, codes, owner=1) == 1
    assert route(("Alertes+K7F3Q9AB@Example.com",), BASE, codes, owner=1) == 2
    # Un code inconnu (compte supprimé) : personne.
    assert route(("alertes+inconnu@example.com",), BASE, codes, owner=1) is None
    # Une autre adresse (transfert, copie cachée) : l'exploitant, comme avant.
    assert route(("kevin+x@autre.ch",), BASE, codes, owner=1) == 1
    assert plus_address("alertes@example.com", "abc") == "alertes+abc@example.com"


def test_route_by_alert_domain() -> None:
    """docs/104 (0.79.0) : « nom-code@domaine » désigne le compte ; « +code » marche encore."""
    codes = {"k7f3q9ab": 2}
    domain = "alertes.joba1.ch"
    expected = "eliot-muller-k7f3q9ab@alertes.joba1.ch"
    assert domain_address(domain, "Éliot Müller", "k7f3q9ab") == expected
    assert name_slug("!!!") == "compte"
    upper = ("Eliot-Muller-K7F3Q9AB@Alertes.Joba1.ch",)
    assert route(upper, BASE, codes, owner=1, domain=domain) == 2
    assert route(("eliot-inconnu1@alertes.joba1.ch",), BASE, codes, owner=1, domain=domain) is None
    assert route(("alertes+k7f3q9ab@example.com",), BASE, codes, owner=1, domain=domain) == 2
    assert route(("alertes@example.com",), BASE, codes, owner=1, domain=domain) == 1


def test_forwarded_by_gmail_reaches_its_account() -> None:
    """docs/116 §1 : une alerte jobup transférée par la boîte Gmail de la personne garde son
    destinataire d'origine ; l'adresse jobA1 est dans X-Forwarded-To."""
    raw = (
        b"From: jobup <candidat@jobup.ch>\r\n"
        b"To: amy.exemple@gmail.com\r\n"
        b"X-Forwarded-To: alertes+amy-32e6krri@joba1.ch\r\n"
        b"X-Forwarded-For: amy.exemple@gmail.com alertes+amy-32e6krri@joba1.ch\r\n"
        b"Subject: Nouvelles offres\r\n"
        b"Message-ID: <fwd@x>\r\n"
        b"Date: Wed, 21 Oct 2026 08:00:00 +0000\r\n\r\nTexte\r\n"
    )
    email = parse_email(raw, fallback_received=NOW)
    assert email.sender_domain == "jobup.ch"
    assert route(email.recipients, BASE, {"32e6krri": 5}, owner=1, domain="joba1.ch") == 5


def test_alert_address_without_catch_all() -> None:
    """0.82.3 : le réglage est une adresse entière ; « alertes+nom-code@domaine » désigne le
    compte, et passe par la seule redirection de « alertes@ »."""
    settings = make_settings(alert_domain="Alertes@Joba1.ch")
    assert (alert_domain(settings), alert_box(settings)) == ("joba1.ch", "alertes")
    assert alert_box(make_settings(alert_domain="alertes.joba1.ch")) is None
    address = domain_address("joba1.ch", "Amy", "32e6krri", "alertes")
    assert address == "alertes+amy-32e6krri@joba1.ch"
    codes = {"32e6krri": 5}
    assert route((address,), BASE, codes, owner=1, domain="joba1.ch") == 5
    # La boîte seule, sans code : à personne (l'exploitant a sa propre adresse).
    assert route(("alertes@joba1.ch",), BASE, codes, owner=1, domain="joba1.ch") is None


def test_recipients_read_from_headers() -> None:
    raw = make_email(
        message_id="<r@x>", sender="a@jobup.ch", received_at=NOW, to="Moi <alertes+abc@example.com>"
    )
    assert parse_email(raw, fallback_received=NOW).recipients == ("alertes+abc@example.com",)


def test_confirmation_link() -> None:
    html = (
        '<p><a href="https://site.example/se-desabonner?id=1">Confirmer le désabonnement</a></p>'
        '<p><a href="http://site.example/confirm">Confirmer</a></p>'
        '<p><a href="https://site.example/alert/activate?t=9">Activer mon alerte</a></p>'
    )
    raw = make_email(
        message_id="<c@x>",
        sender="noreply@site.example",
        received_at=NOW,
        subject="Confirmez votre alerte",
        html=html,
    )
    assert (
        confirmation_link(parse_email(raw, fallback_received=NOW))
        == "https://site.example/alert/activate?t=9"
    )
    plain = make_email(
        message_id="<n@x>",
        sender="noreply@site.example",
        received_at=NOW,
        subject="Nouvelles offres",
    )
    assert confirmation_link(parse_email(plain, fallback_received=NOW)) is None


@pytest.fixture
async def camille(collect_runtime: Runtime) -> AsyncIterator[int]:
    async with collect_runtime.sessionmaker.begin() as session:
        user = User(
            username="camille-adresse",
            password_hash=passwords.hash_password("un-mot-de-passe-solide"),
            mail_code="k7f3q9ab",
        )
        session.add(user)
        await session.flush()
        account = user.id
    yield account
    async with collect_runtime.engine.begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE username = 'camille-adresse'"))


async def _searches(runtime: Runtime, account: int) -> list[str]:
    with accounts.use(account):
        async with runtime.sessionmaker() as session:
            return list(
                await session.scalars(select(Search.message_id).order_by(Search.message_id))
            )


@pytest.mark.usefixtures("parsers")
async def test_collect_routes_each_email_to_its_account(
    collect_runtime: Runtime, mailbox: FakeMailbox, camille: int, account: int
) -> None:
    offer = ("SRE", "Exemple SA", "Lausanne", "https://jobup.ch/1", "1")
    mailbox.add(
        make_email(message_id="<a@x>", sender="a@jobup.ch", received_at=NOW, offers=[offer]),
        "<a@x>",
    )
    mailbox.add(
        make_email(
            message_id="<b@x>",
            sender="a@jobup.ch",
            received_at=NOW,
            offers=[offer],
            to="alertes+k7f3q9ab@example.com",
        ),
        "<b@x>",
    )
    mailbox.add(
        make_email(
            message_id="<c@x>",
            sender="a@jobup.ch",
            received_at=NOW,
            to="alertes+supprime@example.com",
        ),
        "<c@x>",
    )
    with accounts.use(None):
        result = await service.collect(collect_runtime)
    assert (result.fetched, result.new_searches, result.unrouted) == (3, 2, 1)
    assert result.accounts == {account, camille}
    assert await _searches(collect_runtime, account) == ["<a@x>"]
    assert await _searches(collect_runtime, camille) == ["<b@x>"]
    # Chaque compte a sa propre offre, même identique ; un e-mail rangé n'est pas relu.
    with accounts.use(camille):
        async with collect_runtime.sessionmaker() as session:
            assert await session.scalar(text("select count(*) from offers")) == 1
    with accounts.use(None):
        again = await service.collect(collect_runtime)
    assert (again.fetched, again.new_searches) == (1, 0)  # seul l'e-mail sans compte revient


@pytest.mark.usefixtures("parsers")
async def test_alerts_page_address_and_confirmations(
    collect_runtime: Runtime, mailbox: FakeMailbox, camille: int, account: int
) -> None:
    html = '<a href="https://jobs.example/alert/confirm?t=1">Confirmer mon alerte</a>'
    mailbox.add(
        make_email(
            message_id="<conf@x>",
            sender="noreply@jobs.example",
            received_at=NOW,
            subject="Merci de confirmer votre alerte",
            to="alertes+k7f3q9ab@example.com",
            html=html,
        ),
        "<conf@x>",
    )
    with accounts.use(None):
        await service.collect(collect_runtime)
    app = create_app(collect_runtime.settings, collect_runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        mine = (await api.get("/api/alert-searches")).json()
    assert (mine["mailbox"], mine["folder"], mine["personal_address"]) == (BASE, "INBOX", False)
    assert mine["to_confirm"] == []

    # Le compte invité : son adresse, et le lien de confirmation reçu pour lui.
    secured = Runtime.create(collect_runtime.settings.model_copy(update={"auth_enabled": True}))
    app = create_app(secured.settings, secured)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as api:
        login = await api.post(
            "/api/auth/login",
            json={"username": "camille-adresse", "password": "un-mot-de-passe-solide"},
        )
        assert login.status_code == 204
        page = (await api.get("/api/alert-searches")).json()
        assert (page["mailbox"], page["folder"], page["personal_address"]) == (
            "alertes+k7f3q9ab@example.com",
            None,
            True,
        )
        [pending] = page["to_confirm"]
        assert pending["url"] == "https://jobs.example/alert/confirm?t=1"
        done = await api.post(f"/api/alert-searches/confirmations/{pending['search_id']}")
        assert done.json()["to_confirm"] == []
    await secured.dispose()

    # Avec le domaine des alertes (docs/104, 0.79.0) : son adresse ne montre plus la boîte.
    update = {"auth_enabled": True, "alert_domain": "alertes.joba1.ch"}
    domained = Runtime.create(collect_runtime.settings.model_copy(update=update))
    app = create_app(domained.settings, domained)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as api:
        login = await api.post(
            "/api/auth/login",
            json={"username": "camille-adresse", "password": "un-mot-de-passe-solide"},
        )
        assert login.status_code == 204
        page = (await api.get("/api/alert-searches")).json()
        assert page["mailbox"] == "camille-adresse-k7f3q9ab@alertes.joba1.ch"
        assert page["personal_address"] is True
    await domained.dispose()


async def test_site_pause_is_per_account(runtime: Runtime, camille: int, account: int) -> None:
    app = create_app(runtime.settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        sites = (await api.get("/api/sites")).json()
        linkedin = next(s for s in sites if s["slug"] == "linkedin")
        paused = (await api.patch(f"/api/sites/{linkedin['id']}", json={"active": False})).json()
        assert not next(s for s in paused if s["slug"] == "linkedin")["active"]
    with accounts.use(camille):
        async with runtime.sessionmaker() as session:
            assert next(s for s in await load_sites(session) if s.slug == "linkedin").active
    async with runtime.engine.begin() as conn:
        await conn.execute(text("DELETE FROM account_sites"))
