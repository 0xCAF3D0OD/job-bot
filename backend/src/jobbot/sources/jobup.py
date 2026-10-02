"""Analyseur des e-mails jobup (expéditeur candidat@jobup.ch ou candidat@my.jobup.ch).

Construit sur de vrais e-mails « Suggestions d'offres d'emploi » (septembre 2026), des
recommandations basées sur les offres consultées. On lit la partie texte, dont les
entités HTML (&amp;, &#039;) doivent être décodées. Chaque offre tient sur deux lignes :

    IT System Engineer - https://www.jobup.ch/fr/emplois/detail/<uuid>/?utm_source=…
    Michael Page Switzerland, Genève

L'identifiant de l'offre est l'UUID du lien ; les paramètres (dont l'identifiant du compte)
sont abandonnés au profit d'un lien neutre.
"""

import html
import re

from jobbot.db.models import Source
from jobbot.mail.message import ParsedEmail
from jobbot.sources.base import ParsedAlert, RawOffer

_SENDER_DOMAINS = ("jobup.ch", "my.jobup.ch")
_OFFER_LINE = re.compile(
    r"^(?P<title>.+?)\s+-\s+(?P<url>https?://(?P<host>(?:www\.)?jobup\.ch)/(?P<lang>[a-z]{2})/"
    r"(?:emplois|jobs)/detail/(?P<id>[0-9a-f-]{36})/?\S*)$",
    re.IGNORECASE,
)
_RECOMMENDATIONS = re.compile(r"suggestions d'offres|recommandons", re.IGNORECASE)


def _company_location(line: str) -> tuple[str | None, str | None]:
    # « Michael Page Switzerland, Genève » ; le nom d'entreprise peut contenir une virgule.
    company, sep, location = line.rpartition(", ")
    if not sep:
        # Sans virgule : un lieu seul (« 1020 Renens VD ») ou une entreprise seule.
        if re.match(r"^\d{4}\s", line):
            return None, line.strip()
        return line.strip() or None, None
    return company.strip() or None, location.strip() or None


class JobupParser:
    source = Source.JOBUP
    version = "jobup-1"

    def matches(self, email: ParsedEmail) -> bool:
        return email.sender_domain in _SENDER_DOMAINS

    def parse(self, email: ParsedEmail) -> ParsedAlert:
        if not email.text:
            raise ValueError("e-mail jobup sans partie texte")
        lines = [
            html.unescape(line).strip() for line in email.text.replace("\r\n", "\n").split("\n")
        ]
        lines = [line for line in lines if line]

        offers: list[RawOffer] = []
        for index, line in enumerate(lines):
            match = _OFFER_LINE.match(line)
            if not match:
                continue
            following = lines[index + 1] if index + 1 < len(lines) else ""
            company, location = (
                _company_location(following) if not _OFFER_LINE.match(following) else (None, None)
            )
            job_id = match.group("id").lower()
            offers.append(
                RawOffer(
                    title=match.group("title").strip(),
                    company=company,
                    location=location,
                    url=f"https://www.jobup.ch/{match.group('lang')}/emplois/detail/{job_id}/",
                    external_id=job_id,
                )
            )

        text = " ".join(lines[:3])
        label = "Recommandations jobup" if _RECOMMENDATIONS.search(text) else email.subject
        return ParsedAlert(alert_label=label, offers=offers)
