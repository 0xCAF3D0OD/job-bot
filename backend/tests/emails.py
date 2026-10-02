"""Construction d'e-mails et faux analyseurs pour les tests de collecte."""

from dataclasses import dataclass, field
from datetime import datetime
from email.message import EmailMessage
from email.utils import format_datetime

from jobbot.db.models import Source
from jobbot.mail.message import ParsedEmail
from jobbot.sources.base import ParsedAlert, RawOffer


def make_email(
    *,
    message_id: str,
    sender: str,
    received_at: datetime,
    offers: list[tuple[str, ...]] = (),  # type: ignore[assignment]
    subject: str = "Nouvelles offres",
) -> bytes:
    """E-mail dont le corps texte liste les offres, une par ligne :
    titre|entreprise|lieu|url|identifiant (identifiant facultatif)."""
    msg = EmailMessage()
    msg["From"] = f"Alertes <{sender}>"
    msg["To"] = "alertes@example.com"
    msg["Subject"] = subject
    msg["Message-ID"] = message_id
    msg["Date"] = format_datetime(received_at)
    msg.set_content("\n".join("|".join(offer) for offer in offers) or "aucune offre")
    msg.add_alternative("<html><body><p>alerte</p></body></html>", subtype="html")
    return msg.as_bytes()


@dataclass
class LineParser:
    """Analyseur de test : lit le format de make_email."""

    source: Source
    domain: str
    version: str = "test-1"
    fail: bool = False
    seen: list[str] = field(default_factory=list)

    def matches(self, email: ParsedEmail) -> bool:
        return email.sender_domain == self.domain

    def parse(self, email: ParsedEmail) -> ParsedAlert:
        self.seen.append(email.message_id)
        if self.fail:
            raise ValueError("format inattendu")
        offers = []
        for line in (email.text or "").splitlines():
            parts = line.strip().split("|")
            if len(parts) < 4:
                continue
            title, company, location, url, *rest = parts
            offers.append(
                RawOffer(
                    title=title,
                    company=company or None,
                    location=location or None,
                    url=url,
                    external_id=rest[0] if rest else None,
                )
            )
        return ParsedAlert(alert_label=email.subject, offers=offers)
