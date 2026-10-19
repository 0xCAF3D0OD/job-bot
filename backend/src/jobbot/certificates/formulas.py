"""Les formules codées des certificats de travail suisses (docs/87 §3), en français et en
allemand. Une liste écrite, visible et testée : jobA1 repère ces passages sans IA.

Niveaux de prestation : 4 très bon, 3 bon, 2 suffisant, 1 à revoir. Les formules sont
essayées dans l'ordre : la plus précise d'abord, et un passage déjà repéré ne l'est pas deux
fois (« dans l'ensemble à notre satisfaction » n'est pas aussi « à notre satisfaction »).
"""

import re
from dataclasses import dataclass
from typing import Literal

VERSION = "formules-v1"

Category = Literal["performance", "behaviour", "closing", "departure", "effort"]
Tone = Literal["good", "neutral", "bad"]

A = r"(?:à|a)"
APOS = r"['\u2019]"


@dataclass(frozen=True)
class Formula:
    pattern: re.Pattern[str]
    language: Literal["fr", "de"]
    category: Category
    meaning: str
    tone: Tone
    level: int | None = None


def _f(
    pattern: str,
    language: Literal["fr", "de"],
    category: Category,
    meaning: str,
    tone: Tone,
    level: int | None = None,
) -> Formula:
    return Formula(re.compile(pattern, re.IGNORECASE), language, category, meaning, tone, level)


FORMULAS: tuple[Formula, ...] = (
    # --- Prestations, en français -----------------------------------------------------
    _f(
        rf"toujours\s+{A}\s+notre\s+(?:plus\s+grande|pleine\s+et\s+entière)\s+satisfaction",
        "fr",
        "performance",
        "Très bon : la meilleure formule.",
        "good",
        4,
    ),
    _f(
        rf"{A}\s+notre\s+pleine\s+et\s+entière\s+satisfaction",
        "fr",
        "performance",
        "Très bon.",
        "good",
        4,
    ),
    _f(
        rf"(?:dans\s+l{APOS}ensemble|en\s+général|globalement)\s+{A}\s+notre\s+satisfaction",
        "fr",
        "performance",
        "À revoir : « dans l'ensemble » retire presque tout le compliment.",
        "bad",
        1,
    ),
    _f(
        rf"(?:toujours\s+)?{A}\s+notre\s+(?:plus\s+grande|entière)\s+satisfaction",
        "fr",
        "performance",
        "Bon, sans être la meilleure formule.",
        "good",
        3,
    ),
    _f(
        rf"{A}\s+notre\s+satisfaction",
        "fr",
        "performance",
        "Suffisant : sans « entière » ni « plus grande », la formule est tiède.",
        "neutral",
        2,
    ),
    # --- Prestations, en allemand -----------------------------------------------------
    _f(
        r"stets\s+zu\s+unserer\s+vollsten\s+zufriedenheit",
        "de",
        "performance",
        "Très bon (« sehr gut ») : la meilleure formule.",
        "good",
        4,
    ),
    _f(
        r"(?:zu\s+unserer\s+vollsten|stets\s+zu\s+unserer\s+vollen)\s+zufriedenheit",
        "de",
        "performance",
        "Bon (« gut »).",
        "good",
        3,
    ),
    _f(
        r"im\s+gro(?:ss|ß)en\s+und\s+ganzen\s+zu\s+unserer\s+zufriedenheit",
        "de",
        "performance",
        "À revoir (« mangelhaft ») : « im Grossen und Ganzen ».",
        "bad",
        1,
    ),
    _f(
        r"zu\s+unserer\s+vollen\s+zufriedenheit",
        "de",
        "performance",
        "Suffisant (« befriedigend »).",
        "neutral",
        2,
    ),
    _f(
        r"(?:stets\s+)?zu\s+unserer\s+zufriedenheit",
        "de",
        "performance",
        "Suffisant, à la limite (« ausreichend »).",
        "neutral",
        2,
    ),
    # --- Les efforts sans résultat --------------------------------------------------
    _f(
        rf"s{APOS}est\s+(?:toujours\s+)?efforcée?\s+de",
        "fr",
        "effort",
        "À revoir : « s'est efforcé » dit qu'il n'y est pas arrivé.",
        "bad",
        1,
    ),
    _f(
        r"dans\s+la\s+mesure\s+de\s+ses\s+(?:moyens|possibilités|capacités)",
        "fr",
        "effort",
        "À revoir : sous-entend des moyens limités.",
        "bad",
        1,
    ),
    _f(
        r"a\s+fait\s+preuve\s+de\s+bonne\s+volonté",
        "fr",
        "effort",
        "À revoir : la bonne volonté plutôt que le résultat.",
        "bad",
        1,
    ),
    _f(
        r"(?:war\s+stets\s+bemüht|bemühte\s+sich|hat\s+sich\s+bemüht)",
        "de",
        "effort",
        "À revoir : « bemüht » veut dire sans succès.",
        "bad",
        1,
    ),
    # --- Le départ ---------------------------------------------------------------------
    _f(
        rf"{A}\s+sa\s+(?:propre\s+)?demande|de\s+son\s+propre\s+(?:chef|gré)",
        "fr",
        "departure",
        "Départ voulu par toi : un bon signal.",
        "good",
    ),
    _f(
        rf"d{APOS}un\s+commun\s+accord",
        "fr",
        "departure",
        "« D'un commun accord » : souvent lu comme un départ négocié.",
        "neutral",
    ),
    _f(
        r"nous\s+nous\s+sommes\s+séparés|nous\s+avons\s+(?:dû\s+)?mettre?\s+fin",
        "fr",
        "departure",
        "Départ décidé par l'employeur, dit ouvertement.",
        "bad",
    ),
    _f(
        r"auf\s+(?:seinen|ihren|eigenen)\s+(?:eigenen\s+)?wunsch",
        "de",
        "departure",
        "Départ voulu par toi : un bon signal.",
        "good",
    ),
    _f(
        r"im\s+gegenseitigen\s+einvernehmen",
        "de",
        "departure",
        "Départ d'un commun accord : souvent négocié.",
        "neutral",
    ),
)

# La formule de fin : regrets, remerciements, vœux. Ce qui manque compte autant.
CLOSING = {
    "fr": {
        "regrets": re.compile(r"regrett\w*[^.]{0,60}départ|départ[^.]{0,40}regrett", re.I),
        "thanks": re.compile(r"remerci\w*", re.I),
        "wishes": re.compile(
            r"(?:souhait\w*|vœux|voeux)[^.]{0,80}(?:succès|réussite|meilleur|bonne\s+suite)", re.I
        ),
    },
    "de": {
        "regrets": re.compile(r"bedauern[^.]{0,60}(?:ausscheiden|weggang|austritt)", re.I),
        "thanks": re.compile(r"\bdanken\b|\bdank\b", re.I),
        "wishes": re.compile(r"wünschen[^.]{0,80}(?:erfolg|alles\s+gute)", re.I),
    },
}
CLOSING_NAMES = {"regrets": "les regrets", "thanks": "les remerciements", "wishes": "les vœux"}

# Le comportement : supérieurs d'abord, puis collègues.
BEHAVIOUR = {
    "fr": (
        re.compile(r"comportement[^.]*", re.I),
        re.compile(r"supérieur", re.I),
        re.compile(r"collègue", re.I),
    ),
    "de": (
        re.compile(r"verhalten[^.]*", re.I),
        re.compile(r"vorgesetzten", re.I),
        re.compile(r"kolleg", re.I),
    ),
}
