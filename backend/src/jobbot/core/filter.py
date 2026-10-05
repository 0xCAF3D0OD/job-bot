"""Filtre des prérequis non négociables (docs/04-profil-prerequis.md §3).

Fonctions pures, sans base. Règle d'or : une information inconnue n'exclut jamais une
offre ; seule une information présente et contraire à un prérequis l'écarte.
"""

import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import StrEnum

from jobbot.core.normalize import normalize_location, normalize_text

# --- Prérequis ------------------------------------------------------------------------


class ContractType(StrEnum):
    INTERNSHIP = "stage"
    APPRENTICESHIP = "apprentissage"
    TEMPORARY = "temporaire"
    FREELANCE = "freelance"


class Language(StrEnum):
    GERMAN = "allemand"
    ITALIAN = "italien"
    ENGLISH = "anglais"


@dataclass(frozen=True)
class Criteria:
    # Communes et/ou cantons acceptés (« Lausanne », « VD »). Vide : pas de règle de lieu.
    locations: tuple[str, ...] = ()
    remote_ok: bool = False
    min_rate: int | None = None
    excluded_types: tuple[ContractType, ...] = ()
    banned_words: tuple[str, ...] = ()
    unspoken_languages: tuple[Language, ...] = ()

    def digest(self) -> str:
        """Empreinte des prérequis : une évaluation faite avec d'autres prérequis est périmée."""
        payload = json.dumps(
            {
                "locations": sorted(self.locations),
                "remote_ok": self.remote_ok,
                "min_rate": self.min_rate,
                "excluded_types": sorted(self.excluded_types),
                "banned_words": sorted(self.banned_words),
                "unspoken_languages": sorted(self.unspoken_languages),
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


# --- Mots-clés (affichés dans le formulaire) ------------------------------------------

CONTRACT_KEYWORDS: dict[ContractType, tuple[str, ...]] = {
    ContractType.INTERNSHIP: (
        "stage", "stagiaire", "internship", "intern", "praktikum", "praktikant",
        "trainee", "master thesis", "travail de master",
    ),
    ContractType.APPRENTICESHIP: (
        "apprenti", "apprentie", "apprentissage", "apprentice", "lehrstelle", "lernende",
        "lernender",
    ),
    ContractType.TEMPORARY: (
        "temporaire", "interim", "interimaire", "cdd", "duree determinee", "fixed term",
        "fixed-term", "temporary", "befristet", "temporar",
    ),
    ContractType.FREELANCE: ("freelance", "freelancer", "independant", "auto-entrepreneur"),
}  # fmt: skip

LANGUAGE_NAMES: dict[Language, tuple[str, ...]] = {
    Language.GERMAN: ("allemand", "german", "deutsch", "deutschkenntnisse"),
    Language.ITALIAN: ("italien", "italian", "italienisch", "italiano"),
    Language.ENGLISH: ("anglais", "english", "englisch", "englischkenntnisse"),
}
# Mots qui, à moins de trois mots du nom de la langue, en font une exigence.
REQUIREMENT_WORDS = (
    "courant", "couramment", "indispensable", "requis", "obligatoire", "exige", "parfait",
    "maternelle", "fluent", "fluency", "native", "mandatory", "required", "fliessend",
    "fliessende", "zwingend", "verhandlungssicher", "muttersprache", "sehr gute", "c1", "c2",
)  # fmt: skip

_REMOTE = re.compile(r"\b(home office|teletravail|remote|full remote|homeoffice)\b")
# « Lausanne, VD », « 1003 Lausanne VD », « Zürich (ZH) ».
_CANTON_IN_LOCATION = re.compile(r"(?:,\s*|\s|\()([A-Z]{2})\)?\s*$")
_CANTONS = {
    "AG", "AI", "AR", "BE", "BL", "BS", "FR", "GE", "GL", "GR", "JU", "LU", "NE", "NW",
    "OW", "SG", "SH", "SO", "SZ", "TG", "TI", "UR", "VD", "VS", "ZG", "ZH",
}  # fmt: skip


# --- Évaluation -----------------------------------------------------------------------


@dataclass(frozen=True)
class Reason:
    rule: str  # locations | remote | min_rate | contract | banned_word | language
    message: str


@dataclass(frozen=True)
class OfferFacts:
    title: str
    company: str | None = None
    location: str | None = None
    snippet: str | None = None
    rate_min: int | None = None
    rate_max: int | None = None


@dataclass
class Evaluation:
    passed: bool
    reasons: list[Reason] = field(default_factory=list)


def canton_of(location: str | None) -> str | None:
    if not location:
        return None
    match = _CANTON_IN_LOCATION.search(location.strip())
    if match and match.group(1) in _CANTONS:
        return match.group(1)
    return None


def _contains(text: str, phrase: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text) is not None


def _check_location(
    facts: OfferFacts, criteria: Criteria, city_cantons: dict[str, str]
) -> Reason | None:
    # Sans lieux saisis, aucune règle de lieu, télétravail compris.
    if not facts.location or not criteria.locations:
        return None
    normalized = normalize_text(facts.location)
    if _REMOTE.search(normalized):
        if criteria.remote_ok:
            return None
        return Reason("remote", f"Lieu : télétravail complet ({facts.location}), non accepté")

    entries = [loc.strip() for loc in criteria.locations if loc.strip()]
    wanted_cantons = {loc.upper() for loc in entries if loc.upper() in _CANTONS}
    wanted_cities = {normalize_location(loc) for loc in entries if loc.upper() not in _CANTONS}
    city = normalize_location(facts.location)
    if city in wanted_cities:
        return None
    canton = canton_of(facts.location) or city_cantons.get(city)
    if canton in wanted_cantons:
        return None
    if canton is None and wanted_cantons:
        # Canton inconnu alors que tu acceptes des cantons : on ne sait pas, on n'écarte pas.
        return None
    return Reason("locations", f"Lieu : {facts.location} n'est pas dans tes lieux acceptés")


def _check_rate(facts: OfferFacts, criteria: Criteria) -> Reason | None:
    if criteria.min_rate is None or facts.rate_max is None:
        return None
    if facts.rate_max >= criteria.min_rate:
        return None
    rate = (
        f"{facts.rate_max} %"
        if facts.rate_min in (None, facts.rate_max)
        else f"{facts.rate_min}-{facts.rate_max} %"
    )
    return Reason("min_rate", f"Taux : {rate}, sous ton minimum de {criteria.min_rate} %")


def evaluate(
    facts: OfferFacts, criteria: Criteria, city_cantons: dict[str, str] | None = None
) -> Evaluation:
    """Applique tous les prérequis. `city_cantons` : canton connu de villes sans canton."""
    reasons: list[Reason] = []
    title = normalize_text(facts.title)
    text = normalize_text(f"{facts.title} {facts.snippet or ''}")

    if reason := _check_location(facts, criteria, city_cantons or {}):
        reasons.append(reason)
    if reason := _check_rate(facts, criteria):
        reasons.append(reason)

    for contract in criteria.excluded_types:
        hit = next(
            (k for k in CONTRACT_KEYWORDS[contract] if _contains(text, normalize_text(k))), None
        )
        if hit:
            reasons.append(Reason("contract", f"Type : {contract.value} (« {hit} »)"))

    for word in criteria.banned_words:
        normalized = normalize_text(word)
        if normalized and _contains(title, normalized):
            reasons.append(Reason("banned_word", f"Mot interdit dans le titre : « {word} »"))

    for language in criteria.unspoken_languages:
        if phrase := _language_requirement(text, language):
            reasons.append(Reason("language", f"Langue : {language.value} exigé (« {phrase} »)"))

    return Evaluation(passed=not reasons, reasons=reasons)


def _language_requirement(text: str, language: Language) -> str | None:
    """Phrase qui exige la langue, si le texte en contient une : le nom de la langue et un
    mot d'exigence à moins de trois mots l'un de l'autre."""
    words = text.split()
    names = {normalize_text(n) for n in LANGUAGE_NAMES[language]}
    requirements = [normalize_text(w).split() for w in REQUIREMENT_WORDS]
    for index, word in enumerate(words):
        if word not in names:
            continue
        window_start = max(0, index - 3)
        window = words[window_start : index + 4]
        for requirement in requirements:
            for pos in range(len(window) - len(requirement) + 1):
                if window[pos : pos + len(requirement)] == requirement:
                    return " ".join(window)
    return None
