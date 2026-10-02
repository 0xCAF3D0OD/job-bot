"""Analyseur des alertes Indeed (expéditeur donotreply@jobalert.indeed.com).

Construit sur de vraies alertes (octobre 2026). On lit la partie texte de l'e-mail, plus
stable que le HTML : un en-tête, puis un bloc par offre séparé par une ligne vide :

    Ingénieur DevOps/Ingénieure DevOps
    Qim Info - Genève, GE
    Participer à la gestion et à l'évolution des environnements Cloud…
    il y a 1 jour
    https://ch.indeed.com/rc/clk/dl?jk=d90d9c1278a832a9&from=ja&…

Le lien de l'e-mail contient des jetons de suivi propres au compte : on ne garde que
l'identifiant de l'offre (`jk`) et on reconstruit un lien neutre.
"""

import re
from urllib.parse import parse_qs, urlparse

from jobbot.db.models import Source
from jobbot.mail.message import ParsedEmail
from jobbot.sources.base import ParsedAlert, RawOffer

_SENDER_DOMAIN = "jobalert.indeed.com"
_JOB_LINK = re.compile(r"^https?://[\w.-]*indeed\.[a-z.]+/(?:rc/clk|pagead/clk|viewjob)\S*$")
_SEARCH_LINK = re.compile(r"https?://[\w.-]*indeed\.[a-z.]+/jobs\?\S+")
# Lignes d'ancienneté ou de mise en avant, qui ne font pas partie de l'extrait.
_META_LINE = re.compile(
    r"^(il y a .+|aujourd'hui|publiée? .+|nouveau|nouvelle|just posted|today|"
    r"vor .+|heute|neu|\d+\+? ?(jours?|days?|tage?n?) ?.*|"
    r"candidature simplifiée|easily apply|einfach bewerben|employeur réactif|"
    r"responsive employer|recrutement urgent|urgently hiring)$",
    re.IGNORECASE,
)


def _offer_url(link: str) -> tuple[str, str | None]:
    """(lien neutre, identifiant jk). Sans jk, le lien d'origine est gardé."""
    parsed = urlparse(link)
    jk = parse_qs(parsed.query).get("jk", [None])[0]
    if not jk:
        return link, None
    return f"https://{parsed.netloc}/viewjob?jk={jk}", jk


def _company_location(line: str) -> tuple[str | None, str | None]:
    # « Swisscom AG - Bern, BE » ; le nom d'entreprise peut lui-même contenir « - ».
    company, sep, location = line.rpartition(" - ")
    if not sep:
        return line.strip() or None, None
    return company.strip() or None, location.strip() or None


def _alert_label(text: str) -> str | None:
    match = _SEARCH_LINK.search(text)
    if not match:
        return None
    query = parse_qs(urlparse(match.group(0)).query)
    what = (query.get("q") or [""])[0].strip()
    where = (query.get("l") or [""])[0].strip()
    label = " · ".join(part for part in (what, where) if part)
    return label or None


class IndeedParser:
    source = Source.INDEED
    version = "indeed-1"

    def matches(self, email: ParsedEmail) -> bool:
        return email.sender_domain == _SENDER_DOMAIN

    def parse(self, email: ParsedEmail) -> ParsedAlert:
        if not email.text:
            raise ValueError("alerte Indeed sans partie texte")
        text = email.text.replace("\r\n", "\n")
        offers: list[RawOffer] = []
        for block in re.split(r"\n\s*\n", text):
            lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
            if len(lines) < 3 or not _JOB_LINK.match(lines[-1]):
                continue
            title, details, link = lines[0], lines[1:-1], lines[-1]
            company, location = _company_location(details[0])
            snippet_lines = [line for line in details[1:] if not _META_LINE.match(line)]
            url, jk = _offer_url(link)
            offers.append(
                RawOffer(
                    title=title,
                    company=company,
                    location=location,
                    snippet=" ".join(snippet_lines) or None,
                    url=url,
                    external_id=jk,
                )
            )
        return ParsedAlert(alert_label=_alert_label(text), offers=offers)
