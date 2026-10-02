"""Contrat commun des analyseurs d'alertes et choix de l'analyseur pour un e-mail."""

from dataclasses import dataclass
from typing import Protocol

from jobbot.db.models import Source
from jobbot.mail.message import ParsedEmail


@dataclass(frozen=True)
class RawOffer:
    """Une offre telle qu'elle apparaît dans l'e-mail, avant normalisation."""

    title: str
    url: str
    company: str | None = None
    location: str | None = None
    snippet: str | None = None
    external_id: str | None = None


@dataclass(frozen=True)
class ParsedAlert:
    alert_label: str | None
    offers: list[RawOffer]


class Parser(Protocol):
    source: Source
    version: str

    def matches(self, email: ParsedEmail) -> bool: ...

    def parse(self, email: ParsedEmail) -> ParsedAlert: ...


# Enregistrés en 0.2.0-b. Tant que la liste est vide, tous les e-mails sont « non reconnus ».
PARSERS: list[Parser] = []

# Domaines d'expéditeur supposés, à confirmer sur les vrais e-mails (0.2.0-b).
_SENDER_DOMAINS: tuple[tuple[str, Source], ...] = (
    ("jobup.ch", Source.JOBUP),
    ("indeed.com", Source.INDEED),
    ("indeed.ch", Source.INDEED),
    ("job-room.ch", Source.JOBROOM),
    ("arbeit.swiss", Source.JOBROOM),
)


def detect_source(email: ParsedEmail) -> Source:
    domain = email.sender_domain
    for suffix, source in _SENDER_DOMAINS:
        if domain == suffix or domain.endswith("." + suffix):
            return source
    return Source.UNKNOWN


def find_parser(email: ParsedEmail) -> Parser | None:
    return next((parser for parser in PARSERS if parser.matches(email)), None)
