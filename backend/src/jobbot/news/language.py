"""Langue d'un texte court (titre et résumé), par ses mots les plus courants.

Assez pour filtrer des actualités ; sans dépendance ni appel extérieur.
"""

import re

from jobbot.core.normalize import normalize_text

LANGUAGES = ("fr", "de", "en", "it", "es")
_WORDS = {
    "fr": "le la les des est et un une du pour dans que sur au aux avec pas plus ce qui par son",
    "de": "der die das und ist nicht mit fur den von zu ein eine auf im dem sich wird bei auch",
    "en": "the and is of to in for with on how what you your this are from it be by at",
    "it": "il di che per con una della del non sono gli nel alla dei da si piu",
    "es": "el los las del que con por una para es en como mas su al lo",
}
STOPWORDS = {lang: set(words.split()) for lang, words in _WORDS.items()}
_FEED_LANG = re.compile(r"^([a-z]{2})(?:[-_].*)?$", re.I)


def detect(text: str) -> str | None:
    """Langue la plus probable, ou None si le texte ne permet pas de trancher."""
    words = normalize_text(text).split()
    scores = {lang: sum(w in stop for w in words) for lang, stop in STOPWORDS.items()}
    best = max(scores, key=lambda lang: scores[lang])
    ranked = sorted(scores.values(), reverse=True)
    if ranked[0] < 2 or ranked[0] == ranked[1]:
        return None
    return best


def from_feed(value: str | None) -> str | None:
    """« fr-CH » → « fr » ; None si la valeur n'est pas une langue reconnue."""
    match = _FEED_LANG.match((value or "").strip())
    language = match.group(1).lower() if match else None
    return language if language in LANGUAGES else None
