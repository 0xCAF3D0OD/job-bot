"""Ce qui ne part jamais à l'IA (docs/121 §A.3) : les coordonnées de la personne.

Avant d'envoyer un document (CV, certificat) à l'IA, jobA1 retire :
- l'e-mail, le téléphone, les liens ;
- le nom et le prénom, l'adresse (rue, NPA, localité) tels qu'ils sont dans les coordonnées ;
- en tête du document (les premières lignes), une ligne qui ressemble à un nom seul, à une
  rue ou à « NPA Localité », même si les coordonnées ne sont pas encore saisies (à l'accueil) ;
- toute ligne qui donne la date de naissance.
Les dates d'une expérience (« 2019 à 2023 », « mars 2021 ») restent : l'IA en a besoin.
"""

import re
from collections.abc import Iterable

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# Numéro international (+41…, 0041…) ou suisse (0xx xxx xx xx) ; pas les années « 2021-2023 ».
PHONE = re.compile(
    r"(?:\+|\b00)\d{2}[\d ().-]{7,}\d(?!\d)|\b0\d{1,2}[ .-]?\d{3}[ .-]?\d{2}[ .-]?\d{2}\b"
)
URL = re.compile(r"\b(?:https?://|www\.)\S+|\b(?:linkedin\.com|github\.com)/\S+", re.IGNORECASE)
# « 1003 Lausanne », « CH-1003 Lausanne », « 8001 Zürich ».
LOCALITY = re.compile(r"^(?:CH[- ]?)?\d{4}\s+[A-ZÀ-Ýa-zà-ÿ][\w'\u2019 .-]*$")
# « Rue du Test 1 », « Chemin des Vignes 4b », « Bahnhofstrasse 12 », « Via Nassa 5 ».
STREET = re.compile(
    r"^(?:(?:rue|chemin|ch\.|avenue|av\.|route|rte|place|pl\.|boulevard|bd|quai|impasse|allée|"
    r"sentier|via|piazza|corso)\b.*\d|[\wÀ-ÿ-]*(?:strasse|straße|weg|gasse|platz|allee)\s+\d)",
    re.IGNORECASE,
)
# La date de naissance, avec ce qui l'annonce : seulement ce morceau, pas toute la phrase
# (« Monsieur X, né le 3 mai 1990, a travaillé chez Acme SA… » garde l'employeur).
_DATE = r"\d{1,2}(?:[./-]\d{1,2}[./-]|\s*(?:er)?\s+[A-Za-zÀ-ÿ]+\.?\s+)(?:19|20)\d{2}"
BIRTH = re.compile(
    r"(?:n[ée]e?\s+le|date\s+de\s+naissance|geburtsdatum|geboren\s+am|born(?:\s+on)?|"
    r"date\s+of\s+birth|data\s+di\s+nascita|nat[oa]\s+il)\s*:?\s*" + _DATE,
    re.IGNORECASE,
)
# Un nom seul : 2 à 4 mots qui commencent par une capitale, sans chiffre ni deux-points.
NAME_LINE = re.compile(r"^[A-ZÀ-Ý][\wÀ-ÿ'\u2019-]+(?:\s+[A-ZÀ-Ý][\wÀ-ÿ'\u2019-]+){1,3}$")
# Les titres d'un CV ne sont pas des noms.
HEADINGS = re.compile(
    r"^(curriculum|cv|lebenslauf|profil|expériences?|formations?|compétences|langues|"
    r"centres?\s+d'intérêt|skills|education|experience|résumé|contact)\b",
    re.IGNORECASE,
)
HEAD_LINES = 8


def _names(name: str | None) -> list[str]:
    parts = (name or "").split()
    return sorted({p for p in [name or "", *parts] if len(p) > 2}, key=len, reverse=True)


def redact(text: str, identity: object | None = None) -> str:
    """Le texte pour l'IA, sans les coordonnées de la personne. `identity` : ses coordonnées
    (nom, rue, NPA, localité), quand elles sont connues."""
    text = EMAIL.sub("[e-mail retiré]", text)
    text = URL.sub("[lien retiré]", text)
    text = PHONE.sub("[téléphone retiré]", text)
    known: Iterable[str] = ()
    if identity is not None:
        street = getattr(identity, "street", None)
        postcode = getattr(identity, "postcode", None)
        city = getattr(identity, "city", None)
        place = " ".join(p for p in (postcode, city) if p)
        known = [v for v in (street, place) if v and len(v) > 2]
        for name in _names(getattr(identity, "name", None)):
            text = re.sub(rf"\b{re.escape(name)}\b", "[nom retiré]", text, flags=re.IGNORECASE)
    for value in known:
        text = re.sub(re.escape(value), "[adresse retirée]", text, flags=re.IGNORECASE)
    lines = text.splitlines()
    seen = 0
    for i, line in enumerate(lines):
        line = BIRTH.sub("[date de naissance retirée]", line)
        lines[i] = line
        stripped = line.strip()
        if not stripped or stripped == "[date de naissance retirée]":
            continue
        seen += 1
        if seen > HEAD_LINES:
            continue
        if LOCALITY.match(stripped) or STREET.match(stripped):
            lines[i] = "[adresse retirée]"
        elif NAME_LINE.match(stripped) and not HEADINGS.match(stripped):
            lines[i] = "[nom retiré]"
    return "\n".join(lines)
