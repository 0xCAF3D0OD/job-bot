"""Le transfert Gmail (docs/142 §5) : seules les alertes des sites sont lues. Un e-mail d'un
autre expéditeur est supprimé sans être lu ni stocké, sauf le code de Gmail qui confirme le
transfert ; un e-mail transféré qui n'est pas une alerte fait prévenir la personne."""

from datetime import UTC, datetime

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from structlog.testing import capture_logs

from jobbot import accounts
from jobbot.api.app import create_app
from jobbot.collect import service
from jobbot.db.models import IGNORED_KIND, Notification, Search
from jobbot.notify import service as notify
from jobbot.runtime import Runtime

from . import test_site_codes
from .emails import make_email
from .test_collect import FakeMailbox

collect_runtime = test_site_codes.collect_runtime
imap_settings = test_site_codes.imap_settings
mailbox = test_site_codes.mailbox
clean = test_site_codes.clean
phone = test_site_codes.phone

FORWARDED = b"X-Forwarded-For: amy.exemple@gmail.com alertes@example.com\r\n"
FORWARDED += b"X-Forwarded-To: alertes@example.com\r\n"


def forwarded(message_id: str, sender: str, subject: str, html: str) -> bytes:
    raw = make_email(
        message_id=message_id,
        sender=sender,
        received_at=datetime.now(UTC),
        subject=subject,
        html=html,
    )
    return FORWARDED + raw


async def owner_rows(rt: Runtime) -> tuple[list[Search], list[Notification]]:
    with accounts.use(None):
        async with rt.sessionmaker() as session:
            owner = await accounts.owner_id(session)
    with accounts.use(owner):
        async with rt.sessionmaker() as session:
            searches = list(await session.scalars(select(Search).order_by(Search.id)))
            bell = list(await session.scalars(select(Notification).order_by(Notification.id)))
    return searches, bell


async def test_unknown_sender_deleted_unread_and_person_warned(
    clean: Runtime, mailbox: FakeMailbox, phone: list[notify.Message]
) -> None:
    # Un e-mail personnel transféré par un filtre trop large, avec un « code » dedans.
    mailbox.add(
        forwarded(
            "<banque@x>",
            "noreply@banque.example",
            "Votre code de vérification",
            "<p>Votre code de vérification est <b>482913</b>. Solde : 1200 CHF.</p>",
        ),
        "<banque@x>",
    )
    with capture_logs() as logs, accounts.use(None):
        result = await service.collect(clean)

    assert result.codes == 0
    searches, bell = await owner_rows(clean)
    [search] = searches
    # Ni objet, ni code, ni copie : seul le Message-ID reste, pour ne pas le relire.
    assert search.kind == IGNORED_KIND
    assert (search.subject, search.code, search.confirm_url) == (None, None, None)
    assert search.raw_purged_at is not None and not clean.storage.exists(search.raw_key)
    # La personne est prévenue, sans l'expéditeur ni l'objet.
    assert [(n.kind, n.title, n.message) for n in bell] == [
        (
            "gmail_filter",
            "Vérifie ton filtre Gmail",
            "Un e-mail qui n'est pas une alerte est arrivé : vérifie ton filtre Gmail.",
        )
    ]
    assert [m.title for m in phone] == ["Vérifie ton filtre Gmail"]
    text = repr(logs)
    assert "banque" not in text and "482913" not in text and "vérification" not in text
    assert any(e["event"] == "gmail_filter_warning" for e in logs)

    # Un deuxième le même jour : supprimé de même, sans nouvel avertissement.
    mailbox.add(
        forwarded("<perso@x>", "ami@exemple.ch", "Samedi ?", "<p>On se voit samedi ?</p>"),
        "<perso@x>",
    )
    with accounts.use(None):
        await service.collect(clean)
    searches, bell = await owner_rows(clean)
    assert [s.kind for s in searches] == [IGNORED_KIND, IGNORED_KIND]
    assert len(bell) == 1

    # L'extension le montre (GET /api/extension/alerts).
    app = create_app(clean.settings, clean)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = (await client.post("/api/extension-tokens", json={"name": "Firefox"})).json()
        auth = {"Authorization": f"Bearer {token['token']}"}
        body = (await client.get("/api/extension/alerts", headers=auth)).json()
    assert body["filter_warning_at"] is not None


async def test_only_gmail_forwarding_code_is_read(
    clean: Runtime, mailbox: FakeMailbox, phone: list[notify.Message]
) -> None:
    # Le code de confirmation du transfert : lu et affiché.
    mailbox.add(
        make_email(
            message_id="<fwd@x>",
            sender="forwarding-noreply@google.com",
            received_at=datetime.now(UTC),
            subject="(#123456789) Confirmation de transfert Gmail",
            html="<p>Code de confirmation : 123456789</p>",
        ),
        "<fwd@x>",
    )
    # Un autre e-mail de Google avec un code : pas une source d'alerte, donc pas lu.
    mailbox.add(
        make_email(
            message_id="<google@x>",
            sender="no-reply@accounts.google.com",
            received_at=datetime.now(UTC),
            subject="Votre code de validation Google",
            html="<p>Votre code de validation est 654321.</p>",
        ),
        "<google@x>",
    )
    with accounts.use(None):
        result = await service.collect(clean)

    assert result.codes == 1
    searches, bell = await owner_rows(clean)
    by_id = {s.message_id: s for s in searches}
    assert (by_id["<fwd@x>"].source, by_id["<fwd@x>"].code) == ("gmail", "123456789")
    assert by_id["<google@x>"].kind == IGNORED_KIND and by_id["<google@x>"].code is None
    # Non transféré : pas d'avertissement (le filtre n'y est pour rien).
    assert [n.kind for n in bell] == ["site_code"]


async def test_forwarded_alert_from_a_site_is_kept_without_warning(
    clean: Runtime, mailbox: FakeMailbox, phone: list[notify.Message]
) -> None:
    mailbox.add(
        forwarded(
            "<jobup@x>",
            "no-reply@jobup.ch",
            "Votre code de vérification",
            "<p>Votre code de vérification est <b>482913</b>.</p>",
        ),
        "<jobup@x>",
    )
    with accounts.use(None):
        await service.collect(clean)
    searches, bell = await owner_rows(clean)
    assert [(s.source, s.code) for s in searches] == [("jobup", "482913")]
    assert [n.kind for n in bell] == ["site_code"]
