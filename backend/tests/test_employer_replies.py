"""Les réponses d'employeurs transférées à la main (docs/146) : rattachées à la candidature,
rangées par mots-clés, annoncées par une notification ; le statut ne change pas tout seul et
rien du message n'est gardé."""

from datetime import UTC, date, datetime, timedelta
from email.message import EmailMessage
from email.utils import format_datetime

import pytest
from sqlalchemy import select
from structlog.testing import capture_logs

from jobbot import accounts
from jobbot.collect import service
from jobbot.db.models import IGNORED_KIND, Application, Search
from jobbot.mail import replies
from jobbot.mail.message import ParsedEmail, parse_email
from jobbot.notify import service as notify
from jobbot.rhythm import service as rhythm
from jobbot.runtime import Runtime

from . import test_site_codes
from .test_collect import FakeMailbox
from .test_gmail_transfer import FORWARDED, owner_rows

collect_runtime = test_site_codes.collect_runtime
imap_settings = test_site_codes.imap_settings
mailbox = test_site_codes.mailbox
clean = test_site_codes.clean
phone = test_site_codes.phone

IVY_BODY = """Super nouvelle !

---------- Forwarded message ---------
De : Claire Exemple <claire.exemple@ivypartners.ch>
Date: lun. 16 nov. 2026 à 10:02
Subject: Votre candidature DevOps
To: <kevin@exemple.ch>

Bonjour,

Nous avons le plaisir de vous inviter à un entretien. Merci de nous indiquer vos disponibilités.
Tél. +41 79 000 00 00
"""


def manual_forward(
    message_id: str, body: str, subject: str = "Fwd: Votre candidature DevOps"
) -> bytes:
    msg = EmailMessage()
    msg["From"] = "Kevin <kevin@exemple.ch>"
    msg["To"] = "alertes@example.com"
    msg["Subject"] = subject
    msg["Message-ID"] = message_id
    msg["Date"] = format_datetime(datetime.now(UTC))
    msg.set_content(body)
    return msg.as_bytes()


def parsed(body: str, subject: str = "Fwd: Votre candidature") -> ParsedEmail:
    return parse_email(manual_forward("<x@x>", body, subject), fallback_received=datetime.now(UTC))


def application(company: str, **fields: object) -> Application:
    values: dict[str, object] = {
        "id": 1,
        "sent_at": date(2026, 11, 2),
        "method": "electronique",
        "company": company,
        "job_title": "DevOps",
        "orp_month": "2026-11",
        "application_url": None,
        "contact_email": None,
    }
    values.update(fields)
    return Application(**values)


def test_manual_forward_gives_original_sender() -> None:
    forward = replies.read_forward(parsed(IVY_BODY))
    assert forward is not None and forward.sender_domain == "ivypartners.ch"
    assert "Super nouvelle" not in forward.text  # la note de la personne n'est pas lue


@pytest.mark.parametrize(
    "header",
    [
        # Outlook en français, sans ligne de tirets.
        "De : RH Exemple <rh@exemple-sa.ch>\nEnvoyé : lundi 16 novembre 2026 10:02\nÀ : Kevin",
        # Apple Mail.
        "Début du message réexpédié :\n\nDe: RH <rh@exemple-sa.ch>\nObjet: Candidature",
        # Outlook en allemand.
        "Von: RH <rh@exemple-sa.ch>\nGesendet: Montag, 16. November 2026\nAn: Kevin",
    ],
)
def test_forward_headers_of_common_clients(header: str) -> None:
    forward = replies.read_forward(parsed(f"{header}\n\nBonjour"))
    assert forward is not None and forward.sender_domain == "exemple-sa.ch"


def test_not_a_forward() -> None:
    # Un message écrit directement, et un transfert de filtre Gmail (une alerte) : pas lus.
    assert replies.read_forward(parsed("De : rien\nJuste un mot.", "Coucou")) is None
    filtered = FORWARDED + manual_forward("<f@x>", IVY_BODY)
    email = parse_email(filtered, fallback_received=datetime.now(UTC))
    assert email.forwarded and replies.read_forward(email) is None


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("Nous avons le plaisir de vous inviter à un entretien.", "entretien"),
        ("Suite à notre entretien, nous sommes malheureusement au regret…", "refus"),
        ("Leider müssen wir Ihnen mitteilen, dass wir Sie nicht berücksichtigen.", "refus"),
        ("Gerne laden wir Sie zu einem Vorstellungsgespräch ein.", "entretien"),
        ("Unfortunately we decided to move on with other candidates.", "refus"),
        ("We would like to schedule an interview with you.", "entretien"),
        ("Nous avons bien reçu votre candidature ; un entretien pourrait suivre.", "autre"),
        ("Pouvez-vous nous envoyer vos certificats ?", "autre"),
    ],
)
def test_classify(text: str, kind: str) -> None:
    assert replies.classify(text) == kind


def test_match_by_domain_then_by_name() -> None:
    ivy = application("Ivy Partners SA", id=1)
    other = application("Exemple AG", id=2, application_url="https://jobs.exemple.ch/42")
    forward = replies.Forward("ivypartners.ch", "Bonjour")
    assert replies.match([ivy, other], forward) is ivy  # le domaine colle au nom
    forward = replies.Forward("careers.exemple.ch", "Bonjour")
    assert replies.match([ivy, other], forward) is other  # le lien de la candidature
    # Un logiciel de recrutement : le nom de l'entreprise dans le message décide.
    forward = replies.Forward("myworkday.com", "Merci pour votre intérêt pour Exemple.")
    assert replies.match([ivy, other], forward) is other


def test_no_match_when_unsure() -> None:
    ivy = application("Ivy Partners SA", id=1)
    other = application("Exemple AG", id=2)
    both = replies.Forward("myworkday.com", "Ivy Partners et Exemple vous remercient")
    assert replies.match([ivy, other], both) is None
    assert replies.match([ivy, other], replies.Forward(None, "Bonjour")) is None
    # Deux candidatures dans la même entreprise : la plus récente.
    newer = application("Ivy Partners", id=3, sent_at=date(2026, 11, 10))
    assert replies.match([ivy, newer], replies.Forward("ivypartners.ch", "")) is newer


async def _add_application(rt: Runtime, **fields: object) -> int:
    with accounts.use(None):
        async with rt.sessionmaker() as session:
            owner = await accounts.owner_id(session)
    today = datetime.now(UTC).date()
    with accounts.use(owner):
        async with rt.sessionmaker.begin() as session:
            row = Application(
                sent_at=today - timedelta(days=5),
                method="electronique",
                orp_month=f"{today:%Y-%m}",
                job_title="DevOps Engineer",
                **fields,
            )
            session.add(row)
            await session.flush()
            return row.id


async def _application(rt: Runtime, application_id: int) -> Application:
    with accounts.use(None):
        async with rt.sessionmaker() as session:
            owner = await accounts.owner_id(session)
    with accounts.use(owner):
        async with rt.sessionmaker() as session:
            return await session.get_one(Application, application_id)


async def test_reply_is_attached_and_announced_without_keeping_it(
    clean: Runtime,
    mailbox: FakeMailbox,
    phone: list[notify.Message],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Un jour de repos : l'invitation part quand même sur le téléphone (Kevin, 16.11, 13 h 08).
    async def rest_day(*_: object) -> bool:
        return False

    monkeypatch.setattr(rhythm, "is_research_day", rest_day)
    application_id = await _add_application(clean, company="Ivy Partners SA")
    mailbox.add(manual_forward("<ivy@x>", IVY_BODY), "<ivy@x>")
    with capture_logs() as logs, accounts.use(None):
        await service.collect(clean)

    searches, bell = await owner_rows(clean)
    [search] = searches
    # L'e-mail n'est ni stocké ni dans le journal : seul son Message-ID reste.
    assert search.kind == IGNORED_KIND and search.subject is None
    assert not clean.storage.exists(search.raw_key)
    stored = await _application(clean, application_id)
    # Le statut ne change pas tout seul ; le type de réponse est gardé.
    assert (stored.status, stored.reply_kind) == ("en_attente", "entretien")
    assert stored.reply_at is not None
    link = f"/candidatures/suivi?candidature={application_id}"
    assert [(n.kind, n.title, n.link) for n in bell] == [
        ("employer_reply", "Ivy Partners SA t'a répondu : entretien ?", link)
    ]
    assert [m.title for m in phone] == ["Ivy Partners SA t'a répondu : entretien ?"]
    assert phone[0].click is not None and phone[0].click.endswith(link)
    # Ni expéditeur, ni texte, ni coordonnée dans les journaux ou la notification (J-1, X-5).
    text = repr(logs) + repr([(n.title, n.message) for n in bell])
    for secret in ("claire", "ivypartners.ch", "+41 79", "disponibilit", "kevin@"):
        assert secret not in text.lower()
    assert any(e["event"] == "employer_reply" and e["matched"] for e in logs)
    assert not any(e["event"] == "gmail_filter_warning" for e in logs)

    # Relue à la collecte suivante : ni nouvelle notification ni changement.
    with accounts.use(None):
        await service.collect(clean)
    _, bell = await owner_rows(clean)
    assert len(bell) == 1

    # La même invitation transférée une deuxième fois : la cloche, pas de rappel au téléphone.
    mailbox.add(manual_forward("<ivy2@x>", IVY_BODY), "<ivy2@x>")
    with accounts.use(None):
        await service.collect(clean)
    _, bell = await owner_rows(clean)
    assert len(bell) == 2 and len(phone) == 1


async def test_unmatched_reply_still_announced(
    clean: Runtime, mailbox: FakeMailbox, phone: list[notify.Message]
) -> None:
    mailbox.add(
        manual_forward(
            "<inconnu@x>",
            "De : RH <rh@inconnue.ch>\nObjet : Candidature\n\nMalheureusement, c'est non.",
        ),
        "<inconnu@x>",
    )
    with accounts.use(None):
        await service.collect(clean)
    _, bell = await owner_rows(clean)
    assert [(n.title, n.link) for n in bell] == [
        ("Réponse d'entreprise reçue", "/candidatures/suivi")
    ]
    # Un refus reste dans la cloche, jamais sur le téléphone, même un jour de recherche.
    assert phone == []


async def test_refusal_and_receipt_stay_in_the_bell(
    clean: Runtime,
    mailbox: FakeMailbox,
    phone: list[notify.Message],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def research_day(*_: object) -> bool:
        return True

    monkeypatch.setattr(rhythm, "is_research_day", research_day)
    await _add_application(clean, company="Ivy Partners SA")
    header = "De : RH <rh@ivypartners.ch>\nObjet : Candidature\n\n"
    mailbox.add(manual_forward("<non@x>", header + "Malheureusement, c'est non."), "<non@x>")
    mailbox.add(
        manual_forward("<recu@x>", header + "Nous avons bien reçu votre candidature."), "<recu@x>"
    )
    with accounts.use(None):
        await service.collect(clean)
    _, bell = await owner_rows(clean)
    assert sorted(n.title for n in bell) == [
        "Ivy Partners SA t'a répondu",
        "Ivy Partners SA t'a répondu : refus ?",
    ]
    assert phone == []


async def test_personal_email_without_forward_header_stays_silent(
    clean: Runtime, mailbox: FakeMailbox, phone: list[notify.Message]
) -> None:
    mailbox.add(manual_forward("<perso@x>", "On se voit samedi ?", "Samedi"), "<perso@x>")
    with accounts.use(None):
        await service.collect(clean)
    searches, bell = await owner_rows(clean)
    assert [s.kind for s in searches] == [IGNORED_KIND] and bell == []
    with accounts.use(None):
        async with clean.sessionmaker() as session:
            assert await session.scalar(select(Search.subject)) is None
