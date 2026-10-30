"""Les affirmations fortes d'une lettre, comparées à leur source (demande de Kevin du 30.10.2026).

Une lettre disait « alloremplacant.ch … runs in production for compulsory schooling in the canton
of Vaud ». Le relecteur vérifiait qu'un fait existe dans un bloc, pas qu'il n'y est pas grossi.
Ici, sans l'IA : chaque phrase est rapprochée des blocs qu'elle cite, et une affirmation plus forte
que sa source est signalée : mise en production, utilisateurs ou clients, chiffres, échelle,
institution (canton, école, État), rôle de direction, « seul » ou « de bout en bout ». Une phrase
signalée est réécrite au niveau de la source par la correction, sinon retirée
(api/routes/letters.py).

Les catégories se comparent entre langues (un bloc en français, une lettre en anglais) ; un chiffre
se compare exactement. L'échelle, l'institution et les chiffres peuvent aussi venir de l'offre :
une phrase sur l'employeur (« votre infrastructure à grande échelle ») n'affirme rien sur la
personne.
"""

import re
from dataclasses import dataclass
from datetime import date

from jobbot.core.normalize import normalize_text
from jobbot.llm.scoring import ProfileChunkData

# Chaque catégorie : ce que dit la lettre, et ce qui, dans la source, l'autorise (par défaut, les
# mêmes mots).
_CATEGORIES: dict[str, tuple[str, ...]] = {
    "production": (
        r"production",
        r"prod",
        r"produktiv\w*",
        r"live",
        r"in betrieb",
        r"mise? en service",
    ),
    "utilisateurs": (
        r"utilisateur\w*",
        r"users?",
        r"clients?",
        r"customers?",
        r"nutzer\w*",
        r"kunden?",
        r"abonne\w*",
        r"used by",
        r"utilisee? par",
        r"utilises? par",
        r"genutzt",
    ),
    "echelle": (
        r"milliers?",
        r"centaines",
        r"dizaines",
        r"millions?",
        r"thousands",
        r"hundreds",
        r"dozens",
        r"tausende\w*",
        r"hunderte\w*",
        r"grande echelle",
        r"large scale",
        r"at scale",
    ),
    "institution": (
        r"canton\w*",
        r"kanton\w*",
        r"etat de",
        r"state of",
        r"dgeo",
        r"ministere\w*",
        r"ministry",
        r"gouvernement\w*",
        r"government\w*",
        r"communes?",
        r"municipal\w*",
        r"vaud\w*",
        r"ecoles?",
        r"scolaire\w*",
        r"schools?",
        r"schooling",
        r"schul\w*",
        r"enseignement",
        r"education",
        r"bildung\w*",
    ),
    "direction": (
        r"dirig\w*",
        r"led",
        r"headed",
        r"team lead\w*",
        r"lead developer",
        r"chef d equipe",
        r"chef de projet",
        r"a la tete",
        r"responsable d une equipe",
        r"leitete\w*",
        r"teamleit\w*",
        r"encadr\w*",
        r"manage[ds]? (?:a |an |the |my |une |l )?(?:team|equipe)",
    ),
    "seul": (
        r"seule?",
        r"a moi seul",
        r"alone",
        r"single handed\w*",
        r"on my own",
        r"end to end",
        r"de bout en bout",
        r"allein\w*",
        r"im alleingang",
        r"by myself",
    ),
}
# Ce qui, dans une source, autorise « seul » ou « de bout en bout » sans ces mots-là.
_SOLO_SOURCES = (
    r"projet personnel",
    r"personal project",
    r"complet",
    r"complete",
    r"from scratch",
    r"de l infrastructure au code",
    r"de a a z",
    r"full stack",
    r"eigenes projekt",
)
_FROM_OFFER = {"echelle", "institution"}

_NUMBERS = {
    "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7, "huit": 8, "neuf": 9,
    "dix": 10, "onze": 11, "douze": 12, "quinze": 15, "vingt": 20, "trente": 30, "quarante": 40,
    "cinquante": 50, "cent": 100, "mille": 1000,
    "two": 2, "three": 3, "four": 4, "five": 5, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "twelve": 12, "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "hundred": 100, "thousand": 1000,
    "zwei": 2, "drei": 3, "vier": 4, "funf": 5, "sechs": 6, "sieben": 7, "acht": 8, "neun": 9,
    "zehn": 10, "zwolf": 12, "zwanzig": 20, "dreissig": 30, "vierzig": 40, "funfzig": 50,
    "hundert": 100, "tausend": 1000,
}  # fmt: skip


def _compile(patterns: tuple[str, ...]) -> re.Pattern[str]:
    return re.compile(r"(?<![a-z0-9])(?:" + "|".join(patterns) + r")(?![a-z0-9])")


_PATTERNS = {name: _compile(patterns) for name, patterns in _CATEGORIES.items()}
_SOLO = _compile(_SOLO_SOURCES)
_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-Ý«\"(])")


@dataclass(frozen=True)
class Flag:
    """Une phrase plus forte que sa source : le paragraphe (1, 2…), la phrase, ce qui manque."""

    paragraph: int
    sentence: str
    reasons: tuple[str, ...]

    def text(self) -> str:
        return f"« {self.sentence} » ({', '.join(self.reasons)} absent de la source)"


def sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE.split(text) if s.strip()]


def _numbers(normalized: str) -> set[int]:
    # « 2 000 » ou « 2'000 » : un seul nombre (l'apostrophe devient une espace à la normalisation).
    found = {
        int(n.replace(" ", "")) for n in re.findall(r"\b\d{1,3}(?: \d{3})+\b|\b\d+\b", normalized)
    }
    found |= {value for word, value in _NUMBERS.items() if re.search(rf"\b{word}\b", normalized)}
    return found


def _durations(normalized: str) -> set[int]:
    """Les durées que les années d'une source permettent d'écrire : « depuis cinq ans » avec
    « 2021-2025 » ou « depuis 2021 » (écart entre deux années, ou jusqu'à cette année)."""
    years = {int(y) for y in re.findall(r"\b(?:19|20)\d\d\b", normalized)}
    if not years:
        return set()
    years.add(date.today().year)
    return {abs(a - b) + extra for a in years for b in years for extra in (0, 1) if a != b}


def _categories(normalized: str) -> set[str]:
    return {name for name, pattern in _PATTERNS.items() if pattern.search(normalized)}


def _supports(source: str) -> set[str]:
    found = _categories(source)
    if _SOLO.search(source):
        found.add("seul")
    return found


def _forbidden(sentence: str, forbidden: list[str]) -> bool:
    """Une phrase marquée « Pas vrai » : la même, ou presque (les trois quarts de ses mots)."""
    words = set(normalize_text(sentence).split())
    for claim in forbidden:
        claim_words = set(normalize_text(claim).split())
        if claim_words and len(words & claim_words) >= 0.75 * len(claim_words):
            return True
    return False


def check(
    letter: dict[str, object],
    chunks: list[ProfileChunkData],
    *,
    offer_text: str = "",
    forbidden: list[str] | None = None,
) -> list[Flag]:
    """Les phrases de la lettre plus fortes que les blocs qu'elles citent (ou que le profil entier,
    sans bloc cité), et celles marquées « Pas vrai »."""
    by_id = {c.id: normalize_text(f"{c.title} {c.content}") for c in chunks}
    whole = " ".join(by_id.values())
    offer = normalize_text(offer_text)
    flags: list[Flag] = []
    paragraphs = letter.get("paragraphs") or []
    assert isinstance(paragraphs, list)
    for index, paragraph in enumerate(paragraphs, start=1):
        cited = [by_id[i] for i in paragraph.get("chunk_ids", []) if i in by_id]
        source = " ".join(cited) if cited else whole
        supported = _supports(source)
        offer_supported = _supports(offer) & _FROM_OFFER
        source_numbers = _numbers(source) | _numbers(offer) | _durations(source)
        for sentence in sentences(paragraph.get("text", "")):
            normalized = normalize_text(sentence)
            reasons = [
                name
                for name in sorted(_categories(normalized))
                if name not in supported and name not in offer_supported
            ]
            missing = sorted(_numbers(normalized) - source_numbers)
            if missing:
                reasons.append("chiffre " + ", ".join(str(n) for n in missing))
            if forbidden and _forbidden(sentence, forbidden):
                reasons.append("marquée « Pas vrai »")
            if reasons:
                flags.append(Flag(index, sentence, tuple(reasons)))
    return flags


def forbidden_block(forbidden: list[str]) -> str:
    """Les affirmations marquées « Pas vrai », pour la rédaction et la relecture."""
    lines = "\n".join(f"- {claim}" for claim in forbidden)
    return f"\n\n<interdits>\n{lines}\n</interdits>"


def drop(letter: dict[str, object], flags: list[Flag]) -> dict[str, object]:
    """Retire les phrases signalées ; un paragraphe vidé disparaît (jamais la lettre entière)."""
    if not flags:
        return letter
    by_paragraph: dict[int, set[str]] = {}
    for flag in flags:
        by_paragraph.setdefault(flag.paragraph, set()).add(flag.sentence)
    kept = []
    paragraphs = letter.get("paragraphs") or []
    assert isinstance(paragraphs, list)
    for index, paragraph in enumerate(paragraphs, start=1):
        removed = by_paragraph.get(index, set())
        text = " ".join(s for s in sentences(paragraph.get("text", "")) if s not in removed)
        if text:
            kept.append({**paragraph, "text": text})
    return {**letter, "paragraphs": kept} if kept else letter
