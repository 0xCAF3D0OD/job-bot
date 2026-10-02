"""Normalisation des offres et empreinte de dédoublonnage (docs/03-collecte-gmail.md §4).

Deux annonces dont le titre, l'entreprise et le lieu normalisés sont égaux ont la même
empreinte : elles sont considérées comme la même offre. Fonctions pures, sans base.
"""

import hashlib
import re
import unicodedata
from dataclasses import dataclass

# Mentions de genre : (h/f), (m/w/d), h/f, m/w/d, w/m/d, (f/h/x)…
_GENDER_GROUP = r"(?:h|f|m|w|d|x|e|i)(?:\s*/\s*(?:h|f|m|w|d|x|e|i)){1,3}"
_GENDER_PAREN = re.compile(rf"\(\s*{_GENDER_GROUP}\s*\)", re.IGNORECASE)
_GENDER_BARE = re.compile(rf"(?<![\w/]){_GENDER_GROUP}(?![\w/])", re.IGNORECASE)
# Formes inclusives collées au mot : Informatiker/-in, Informatiker/in, Informatiker:in,
# Informatiker*in, Ingénieur·e, Collaborateur(trice), Employé(e), administratif(ve).
_INCLUSIVE_SUFFIX = re.compile(
    r"(?<=\w)(?:/-?in(?:nen)?|[:*]in(?:nen)?|[·.](?:e|ne|se|ice|euse|rice)s?"
    r"|\((?:e|ne|se|ve|ice|euse|rice|trice|in)\))(?!\w)",
    re.IGNORECASE,
)

# Taux d'activité : « 80-100 % », « 80 % - 100 % », « 80 à 100% », « 100% », « 60 bis 80 % ».
_RATE_RANGE = re.compile(
    # \u2013 et \u2014 : tirets demi-cadratin et cadratin.
    r"(?<![\d,.])(\d{1,3})\s*%?\s*(?:-|\u2013|\u2014|à|a|bis|to)\s*(\d{1,3})\s*%",
    re.IGNORECASE,
)
# Taux décimal (« 26,25 % ») : ignoré, ce n'est pas un taux d'activité standard.
_RATE_SINGLE = re.compile(r"(?<![\d,.])(\d{1,3})\s*%")

# Formes juridiques retirées en fin de nom d'entreprise (après normalisation).
_LEGAL_SUFFIXES = (
    ("s", "a", "r", "l"),
    ("s", "a"),
    ("sarl",),
    ("sa",),
    ("ag",),
    ("gmbh",),
    ("ltd",),
    ("inc",),
    ("llc",),
    ("sas",),
    ("plc",),
    ("se",),
    ("kg",),
)

_CANTONS = {
    "ag", "ai", "ar", "be", "bl", "bs", "fr", "ge", "gl", "gr", "ju", "lu", "ne", "nw",
    "ow", "sg", "sh", "so", "sz", "tg", "ti", "ur", "vd", "vs", "zg", "zh",
}  # fmt: skip


def normalize_text(value: str) -> str:
    """Minuscules, sans accents, ponctuation remplacée par des espaces, espaces réduits."""
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    lowered = without_accents.casefold()
    return " ".join(re.sub(r"[^\w]+|_", " ", lowered).split())


def parse_rate(title: str) -> tuple[int | None, int | None]:
    """Taux d'activité (min, max) mentionné dans le titre, ou (None, None)."""
    if match := _RATE_RANGE.search(title):
        low, high = sorted((int(match.group(1)), int(match.group(2))))
        if 1 <= low <= high <= 100:
            return low, high
    if match := _RATE_SINGLE.search(title):
        rate = int(match.group(1))
        if 1 <= rate <= 100:
            return rate, rate
    return None, None


def normalize_title(title: str) -> str:
    cleaned = _RATE_RANGE.sub(" ", title)
    cleaned = _RATE_SINGLE.sub(" ", cleaned)
    cleaned = _GENDER_PAREN.sub(" ", cleaned)
    cleaned = _INCLUSIVE_SUFFIX.sub("", cleaned)
    cleaned = _GENDER_BARE.sub(" ", cleaned)
    return normalize_text(cleaned)


def normalize_company(company: str | None) -> str:
    if not company:
        return ""
    tokens = normalize_text(company).split()
    changed = True
    while changed and len(tokens) > 1:
        changed = False
        for suffix in _LEGAL_SUFFIXES:
            n = len(suffix)
            if len(tokens) > n and tuple(tokens[-n:]) == suffix:
                tokens = tokens[:-n]
                changed = True
                break
    return " ".join(tokens)


def normalize_location(location: str | None) -> str:
    """Ville seule : sans NPA, sans canton, sans ce qui suit une virgule."""
    if not location:
        return ""
    first = re.split(r"[,;/]| - ", location, maxsplit=1)[0]
    first = re.sub(r"\(.*?\)", " ", first)
    tokens = [t for t in normalize_text(first).split() if not re.fullmatch(r"\d{4,5}", t)]
    while len(tokens) > 1 and tokens[-1] in _CANTONS:
        tokens.pop()
    return " ".join(tokens)


@dataclass(frozen=True)
class NormalizedOffer:
    title_key: str
    company_key: str
    location_key: str
    rate_min: int | None
    rate_max: int | None
    fingerprint: str


def normalize_offer(title: str, company: str | None, location: str | None) -> NormalizedOffer:
    title_key = normalize_title(title)
    company_key = normalize_company(company)
    location_key = normalize_location(location)
    rate_min, rate_max = parse_rate(title)
    digest = hashlib.sha256(f"{title_key}|{company_key}|{location_key}".encode()).hexdigest()
    return NormalizedOffer(
        title_key=title_key,
        company_key=company_key,
        location_key=location_key,
        rate_min=rate_min,
        rate_max=rate_max,
        fingerprint=digest,
    )
