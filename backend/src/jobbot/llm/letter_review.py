"""Relecture de la lettre avant son affichage : un rédacteur, puis un relecteur (décision de Kevin).

Sept critères, chacun réussi ou à revoir, avec une raison d'une ligne. Deux se vérifient sans l'IA
(la longueur et le tiret cadratin) ; les autres, l'IA les juge. Le relecteur ne
reçoit que le texte de la lettre, l'offre et le profil : jamais les coordonnées de la personne.
"""

import json
from dataclasses import asdict, dataclass
from importlib import resources
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from jobbot.llm.scoring import (
    InvalidScore,
    OfferData,
    ProfileChunkData,
    offer_message,
    profile_block,
)

PROMPT_VERSION = "letter-review-v1"
INSTRUCTIONS = (
    resources.files("jobbot.llm").joinpath("prompts/letter-review-v1.md").read_text("utf-8")
)
MAX_TOKENS = 4_000

# Les critères, dans l'ordre de l'affichage.
LABELS = {
    "accroche": "Accroche",
    "pertinence": "Pertinence",
    "precision": "Précision",
    "longueur": "Longueur",
    "conclusion": "Conclusion",
    "invention": "Aucune invention",
    "regles": "Règles",
}
AiKey = Literal["accroche", "pertinence", "precision", "conclusion", "invention", "consigne"]
AI_KEYS: tuple[AiKey, ...] = (
    "accroche",
    "pertinence",
    "precision",
    "conclusion",
    "invention",
    "consigne",
)

# Une page A4 : en-tête, objet et formules compris, le corps tient en 400 mots environ.
MAX_WORDS = 400


class AiCriterion(BaseModel):
    key: AiKey
    ok: bool
    reason: str = Field(min_length=1, max_length=200)


class AiReview(BaseModel):
    criteria: list[AiCriterion] = Field(min_length=1, max_length=len(AI_KEYS))
    invented_paragraphs: list[int] = Field(default_factory=list)


OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "criteria": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "enum": list(AI_KEYS)},
                    "ok": {"type": "boolean"},
                    "reason": {"type": "string"},
                },
                "required": ["key", "ok", "reason"],
                "additionalProperties": False,
            },
        },
        "invented_paragraphs": {"type": "array", "items": {"type": "integer"}},
    },
    "required": ["criteria", "invented_paragraphs"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class Criterion:
    key: str
    label: str
    ok: bool
    reason: str


@dataclass(frozen=True)
class Review:
    criteria: list[Criterion]
    invented_paragraphs: list[int]
    corrected: bool = False

    @property
    def passed(self) -> int:
        return sum(c.ok for c in self.criteria)

    @property
    def all_ok(self) -> bool:
        return all(c.ok for c in self.criteria)

    def failing(self, key: str) -> bool:
        return any(c.key == key and not c.ok for c in self.criteria)

    def as_dict(self) -> dict[str, Any]:
        return {
            "criteria": [asdict(c) for c in self.criteria],
            "invented_paragraphs": self.invented_paragraphs,
            "corrected": self.corrected,
        }


def _texts(letter: dict[str, Any]) -> list[str]:
    return [p["text"] for p in letter.get("paragraphs", [])]


def deterministic(letter: dict[str, Any]) -> dict[str, tuple[bool, str]]:
    """Ce que le code vérifie seul : la longueur et le tiret cadratin."""
    words = sum(len(t.split()) for t in _texts(letter))
    length = (
        (True, f"{words} mots : tient sur une page.")
        if words <= MAX_WORDS
        else (False, f"{words} mots : raccourcis sous {MAX_WORDS} pour tenir sur une page.")
    )
    whole = " ".join(
        [
            letter.get("subject") or "",
            letter.get("salutation") or "",
            letter.get("closing") or "",
            *_texts(letter),
        ]
    )
    # Sans formule enregistrée, la lettre prend celle de sa langue (letters/document.py).
    if "—" in whole:
        rules = (False, "Un tiret cadratin reste : remplace-le par une virgule.")
    else:
        rules = (True, "Sans tiret cadratin.")
    return {"longueur": length, "regles": rules}


def _letter_text(letter: dict[str, Any]) -> str:
    lines = [f"objet : {letter.get('subject', '')}"]
    if letter.get("salutation"):
        lines.append(f"formule d'appel : {letter['salutation']}")
    lines += [f"[{i}] {text}" for i, text in enumerate(_texts(letter), start=1)]
    if letter.get("closing"):
        lines.append(f"formule de politesse : {letter['closing']}")
    return "<lettre>\n" + "\n".join(lines) + "\n</lettre>"


def request_params(
    model: str,
    effort: str,
    chunks: list[ProfileChunkData],
    offer: OfferData,
    letter: dict[str, Any],
    *,
    language: str | None,
    instruction: str | None,
) -> dict[str, Any]:
    """Le relecteur : le texte de la lettre, l'offre et le profil, jamais les coordonnées."""
    parts = [offer_message(offer), f"\n\n<langue>{language or 'auto'}</langue>"]
    if instruction:
        safe = instruction.replace("</consigne>", "</ consigne>")
        parts.append(f"\n\n<consigne>\n{safe}\n</consigne>")
    parts.append("\n\n" + _letter_text(letter))
    return {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "system": [
            {"type": "text", "text": INSTRUCTIONS},
            {"type": "text", "text": profile_block(chunks), "cache_control": {"type": "ephemeral"}},
        ],
        "messages": [{"role": "user", "content": "".join(parts)}],
        "output_config": {
            "effort": effort,
            "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA},
        },
    }


def parse_review(text: str, letter: dict[str, Any], *, corrected: bool = False) -> Review:
    """Les avis de l'IA, complétés par les vérifications du code, dans l'ordre de l'affichage."""
    try:
        ai = AiReview.model_validate(json.loads(text))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise InvalidScore(f"relecture non conforme : {type(exc).__name__}") from exc
    seen = {c.key: c for c in ai.criteria}
    if set(AI_KEYS) - set(seen):
        raise InvalidScore("relecture incomplète")
    checks = deterministic(letter)
    criteria: list[Criterion] = []
    for key, label in LABELS.items():
        if key == "longueur":
            ok, reason = checks["longueur"]
        elif key == "regles":
            # Les règles : le tiret et la formule (le code), la langue et la consigne (l'IA).
            code_ok, code_reason = checks["regles"]
            ai_rule = seen["consigne"]
            ok = code_ok and ai_rule.ok
            reason = code_reason if not code_ok else ai_rule.reason
        else:
            found = seen[key]  # type: ignore[index]
            ok, reason = found.ok, found.reason
        criteria.append(Criterion(key, label, ok, reason.strip()))
    count = len(_texts(letter))
    invented = sorted({i for i in ai.invented_paragraphs if 1 <= i <= count})
    return Review(criteria, invented, corrected)


def correction_instruction(review: Review) -> str:
    """La consigne de l'unique correction automatique : ce qui est à revoir, et rien d'autre."""
    lines = [f"- {c.label} : {c.reason}" for c in review.criteria if not c.ok]
    return (
        "Corrige la lettre selon cette relecture, sans rien changer d'autre :\n"
        + "\n".join(lines)
        + "\nRetire tout fait absent des blocs du profil : ne le remplace jamais par un autre."
    )


def drop_invented(letter: dict[str, Any], review: Review) -> dict[str, Any]:
    """« Aucune invention » est bloquant : un paragraphe qui invente encore est retiré."""
    if not review.invented_paragraphs:
        return letter
    keep = [
        p
        for i, p in enumerate(letter.get("paragraphs", []), start=1)
        if i not in review.invented_paragraphs
    ]
    return {**letter, "paragraphs": keep} if keep else letter
