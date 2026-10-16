"""E-mail d'un site qui demande de confirmer l'alerte (docs/65 §3).

Avec une adresse de réception par compte, ces e-mails arrivent dans la boîte de la plateforme
et non chez la personne : on y repère le lien de confirmation, que la page Alertes lui montre.
La plateforme ne l'ouvre jamais elle-même : c'est la personne qui clique.
"""

import re
from html.parser import HTMLParser

from jobbot.mail.message import ParsedEmail

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
