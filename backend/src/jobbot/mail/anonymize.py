"""Anonymisation d'e-mails réels pour en faire des jeux de test (docs/03-collecte-gmail.md §5).

L'e-mail est reconstruit de zéro avec le strict nécessaire aux analyseurs :
- en-têtes : seulement From, Subject et Date ; destinataire et Message-ID fictifs ;
  tous les autres (Received, DKIM, Delivered-To…) sont abandonnés ;
- corps : la partie texte seule, où les liens ne gardent que les paramètres utiles
  (identifiant d'offre, termes de recherche) ; jetons de suivi et identifiants de compte
  sont remplacés par « x » ;
- toute adresse e-mail restante est remplacée.

Le résultat doit quand même être relu avant d'être commité : le dépôt est public.
"""

import re
from email import message_from_bytes, policy
from email.message import EmailMessage
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

# Paramètres d'URL conservés : ils décrivent l'offre ou la recherche, pas la personne.
KEPT_PARAMS = frozenset({"jk", "q", "l", "radius", "hl", "from", "lang"})
_URL = re.compile(r"https?://[^\s<>\"')]+")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# Segment de chemin qui ressemble à un identifiant ou à un jeton (long, sans voyelles lisibles).
_TOKEN_SEGMENT = re.compile(r"^[A-Za-z0-9_-]{16,}$")


def anonymize_url(url: str) -> str:
    parsed = urlparse(url)
    query = [(k, v if k in KEPT_PARAMS else "x") for k, v in parse_qsl(parsed.query)]
    path = "/".join(
        "x" if _TOKEN_SEGMENT.match(segment) else segment for segment in parsed.path.split("/")
    )
    return urlunparse(parsed._replace(path=path, query=urlencode(query), fragment=""))


def anonymize_text(text: str) -> str:
    text = _URL.sub(lambda m: anonymize_url(m.group(0)), text)
    return _EMAIL.sub("adresse@example.com", text)


def anonymize(raw: bytes, *, index: int) -> bytes:
    original = message_from_bytes(raw, policy=policy.default)
    assert isinstance(original, EmailMessage)
    body = original.get_body(preferencelist=("plain",))
    if body is None:
        raise ValueError("e-mail sans partie texte")

    msg = EmailMessage()
    msg["From"] = str(original["From"])
    msg["To"] = "alertes@example.com"
    msg["Subject"] = str(original["Subject"] or "")
    msg["Date"] = str(original["Date"])
    msg["Message-ID"] = f"<fixture-{index}@example.invalid>"
    msg.set_content(anonymize_text(body.get_content()))
    return msg.as_bytes(policy=policy.SMTP)
