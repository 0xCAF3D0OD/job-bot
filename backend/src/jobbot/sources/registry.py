"""Analyseurs actifs et choix de l'analyseur pour un e-mail."""

from jobbot.db.models import Source
from jobbot.mail.message import ParsedEmail
from jobbot.sources.base import Parser
from jobbot.sources.indeed import IndeedParser

# Un e-mail qu'aucun analyseur ne reconnaît est enregistré « non reconnu ».
PARSERS: list[Parser] = [IndeedParser()]

# Domaines d'expéditeur. Confirmés : jobalert.indeed.com, my.jobup.ch. Job-Room à confirmer.
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
