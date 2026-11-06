"""Faire tenir la lettre sur une page A4 (demande de Kevin du 6.11.2026).

Le PDF est construit avec le modèle choisi et ses pages comptées. S'il déborde, la mise en page
se resserre, sans l'IA, dans cet ordre et seulement jusqu'à ce que la lettre tienne :
l'espacement entre les paragraphes, l'interligne (jamais sous 1,25), les marges (jamais sous
2 cm), la taille du texte (jamais sous 10,5 pt). Si la mise en page la plus serrée déborde
encore, `excess_words` dit combien de mots retirer, d'après le débordement mesuré : la route
demande alors à l'IA une cible chiffrée.

Le Word reprend la mise en page choisie ici (letters/document.py), pour un rendu identique.
"""

import math
import re
from dataclasses import dataclass, replace

from jobbot.letters.document import DEFAULT_LAYOUT, Layout, LetterDocument
from jobbot.letters.pdf import Placement, Template, render_letter

MIN_LEADING = 1.25
MIN_SIDE = 2.0
MIN_SIZE = 10.5


def _steps() -> list[Layout]:
    """Les mises en page essayées, de la plus aérée à la plus serrée, chacune gardant les
    resserrements d'avant."""
    steps = [DEFAULT_LAYOUT]
    current = DEFAULT_LAYOUT
    # 1. L'espacement entre les paragraphes (et entre les blocs de l'en-tête).
    for gap, blocks in ((8, 0.85), (6, 0.7), (4, 0.55)):
        current = replace(current, gap=gap, blocks=blocks)
        steps.append(current)
    # 2. L'interligne, jamais sous 1,25.
    for ratio in (1.28, MIN_LEADING):
        current = replace(current, leading=round(current.size * ratio, 2))
        steps.append(current)
    # 3. Les marges, jamais sous 2 cm.
    for side in (2.25, MIN_SIDE):
        current = replace(current, side=side)
        steps.append(current)
    # 4. La taille du texte, jamais sous 10,5 pt (l'interligne suit, à 1,25).
    for size in (10.75, MIN_SIZE):
        current = replace(current, size=size, leading=round(size * MIN_LEADING, 2))
        steps.append(current)
    return steps


STEPS = _steps()
TIGHTEST = STEPS[-1]


@dataclass(frozen=True)
class Fit:
    """La mise en page retenue et ce que le PDF construit avec elle a mesuré."""

    layout: Layout
    placement: Placement
    words: int  # les mots du corps

    @property
    def fits(self) -> bool:
        return self.placement.pages <= 1

    @property
    def overflow_lines(self) -> int:
        """Le débordement, en lignes de texte de cette mise en page."""
        if self.fits:
            return 0
        return max(1, math.ceil(self.placement.overflow / self.layout.leading - 0.05))

    @property
    def adjusted(self) -> bool:
        return self.layout != DEFAULT_LAYOUT


def body_words(letter: LetterDocument) -> int:
    return sum(len(text.split()) for text in letter.paragraphs)


def measure(letter: LetterDocument, template: Template, layout: Layout = DEFAULT_LAYOUT) -> Fit:
    _pdf, placement = render_letter(letter, template=template, layout=layout)
    return Fit(layout, placement, body_words(letter))


def fit(letter: LetterDocument, template: Template) -> Fit:
    """La première mise en page qui tient sur une page ; sinon la plus serrée, qui déborde."""
    result = measure(letter, template)
    for layout in STEPS[1:]:
        if result.fits:
            return result
        result = measure(letter, template, layout)
    return result


def excess_words(result: Fit) -> int:
    """Les mots à retirer pour que le débordement mesuré disparaisse, avec une ligne de marge
    (une phrase raccourcie ne libère pas toujours une ligne entière)."""
    if result.fits:
        return 0
    per_line = result.words / max(result.placement.body_lines, 1)
    return math.ceil((result.overflow_lines + 1) * per_line)


def target_words(letter: LetterDocument, template: Template) -> int | None:
    """La cible chiffrée pour l'IA quand même la mise en page la plus serrée déborde."""
    result = fit(letter, template)
    if result.fits:
        return None
    return max(80, result.words - excess_words(result))


# Une consigne qui demande une lettre plus courte (fr, en, de).
LENGTH_REQUEST = re.compile(
    r"plus court|raccourci|trop long|moins long|une (seule )?page|tien[st]? pas|tenir sur"
    r"|déborde|shorter|too long|one page|single page|kürzer|zu lang|eine seite",
    re.IGNORECASE,
)


def is_length_request(instruction: str | None) -> bool:
    return bool(instruction and LENGTH_REQUEST.search(instruction))


def requested_target(letter: LetterDocument, template: Template) -> int:
    """La cible d'une consigne de longueur : au moins 15 % de moins, et assez pour tenir sur une
    page sans resserrer la mise en page."""
    result = measure(letter, template)
    shorter = math.floor(result.words * 0.85)
    if result.fits:
        return max(80, shorter)
    return max(80, min(shorter, result.words - excess_words(result)))


def shorten_instruction(target: int) -> str:
    return (
        f"Raccourcis le corps à {target} mots au plus, garde les 2 exigences principales et la "
        "conclusion. La lettre doit tenir sur une page A4."
    )
