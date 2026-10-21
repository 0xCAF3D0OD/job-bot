"""E-mail d'un site qui demande de confirmer l'alerte (docs/65 §3).

Avec une adresse de réception par compte, ces e-mails arrivent dans la boîte de la plateforme
et non chez la personne : on y repère le lien de confirmation. Pour un site connu, jobA1
l'ouvre lui-même (docs/112 §4) ; si la page demande une connexion ou une action, la page
Alertes le montre et la personne l'ouvre.
"""

import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

import httpx

from jobbot.log import get_logger
from jobbot.logos import service as logos
from jobbot.mail.message import ParsedEmail

log = get_logger(__name__)

# Les sites dont jobA1 ouvre lui-même le lien de confirmation (docs/112 §4).
KNOWN_HOSTS = ("jobup.ch", "jobs.ch", "indeed.com", "job-room.ch", "linkedin.com")
# Une page qui demande de se connecter : la confirmation n'est pas faite.
_LOGIN = re.compile(r"login|signin|sign-in|connexion|anmelden|/auth/|/u/", re.I)
_PASSWORD = re.compile(r"<input[^>]+type=[\"']?password", re.I)
# Jamais un lien qui supprime, change un mot de passe ou désinscrit.
_NEVER = re.compile(r"delete|supprim|lösch|password|passwort|mot-de-passe|reset", re.I)

# Français, allemand, anglais, italien : « confirmer », « bestätigen », « activer »…
WORDS = re.compile(r"confirm|conferm|bestätig|bestaetig|activ|aktivier|valid|verif|vérif", re.I)
# Jamais le lien de désabonnement, même s'il contient « confirmer ».
REFUSED = re.compile(r"unsubscribe|désabonn|desabonn|abmeld|abbestell|disiscriv|opt-?out", re.I)


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join("".join(self._text).split())))
            self._href = None


def confirmation_link(email: ParsedEmail) -> str | None:
    """Le lien à ouvrir pour confirmer l'alerte, si l'e-mail en demande une."""
    if not WORDS.search(email.subject or "") and not WORDS.search(email.text or ""):
        return None
    links: list[tuple[str, str]] = []
    if email.html:
        parser = _Links()
        parser.feed(email.html)
        links = parser.links
    elif email.text:
        links = [(url, "") for url in re.findall(r"https://\S+", email.text)]
    for href, text in links:
        if not href.startswith("https://") or REFUSED.search(href) or REFUSED.search(text):
            continue
        if WORDS.search(text) or WORDS.search(href):
            return href[:2000]
    return None


def known_site(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    return any(host == h or host.endswith("." + h) for h in KNOWN_HOSTS)


async def _open(url: str) -> bool:
    async with httpx.AsyncClient(
        timeout=10, follow_redirects=False, headers={"User-Agent": logos.USER_AGENT}
    ) as client:
        data, final = await logos._get(client, url, 2_000_000)
    page = data.decode("utf-8", errors="replace")
    return not _LOGIN.search(urlsplit(final).path + "?" + (urlsplit(final).query or "")) and not (
        _PASSWORD.search(page)
    )


async def open_confirmation(url: str) -> bool:
    """Ouvre le lien d'un site connu ; True si la page l'a accepté sans demander de connexion.
    Un lien d'un autre site, ou qui pourrait supprimer ou désinscrire, n'est jamais ouvert."""
    if not known_site(url) or REFUSED.search(url) or _NEVER.search(url):
        return False
    try:
        return await _open(url)
    except (httpx.HTTPError, logos.Refused) as exc:
        log.info("confirmation_not_opened", error=type(exc).__name__)
        return False
