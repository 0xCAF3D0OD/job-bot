"""Contrat commun des analyseurs d'alertes."""

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
    # Logo de l'entreprise, quand l'alerte en montre un (docs/14 §4).
    logo_url: str | None = None


@dataclass(frozen=True)
class ParsedAlert:
    alert_label: str | None
    offers: list[RawOffer]


class Parser(Protocol):
    source: Source
    version: str

    def matches(self, email: ParsedEmail) -> bool: ...

    def parse(self, email: ParsedEmail) -> ParsedAlert: ...
