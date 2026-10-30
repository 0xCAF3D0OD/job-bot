"""Relecture de la lettre avant son affichage : un rédacteur, puis un relecteur (décision de Kevin).

Sept critères, chacun réussi ou à revoir, avec une raison d'une ligne. Deux se vérifient sans l'IA
(la longueur et le tiret cadratin) ; les autres, l'IA les juge. Le relecteur ne
reçoit que le texte de la lettre, l'offre et le profil : jamais les coordonnées de la personne.

v2 (demande de Kevin du 30.10.2026) : chaque phrase est rapprochée de sa source. Une affirmation
plus forte que son bloc (en production, utilisateurs, chiffre, institution, rôle…) est listée dans
`claims`, avec la citation du bloc et la phrase réécrite au niveau de la source, ou rien (la phrase
est alors retirée). Le contrôle sans l'IA (llm/claims.py) lui signale les phrases suspectes, et les
affirmations marquées « Pas vrai » lui sont données comme interdites.
"""

import json
from dataclasses import asdict, dataclass
from importlib import resources
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from jobbot.llm import claims as claims_check
from jobbot.llm.letter import no_dash
from jobbot.llm.scoring import (
    InvalidScore,
    OfferData,
    ProfileChunkData,
    offer_message,
    profile_block,
)

PROMPT_VERSION = "letter-review-v2"
INSTRUCTIONS = (
    resources.files("jobbot.llm").joinpath("prompts/letter-review-v2.md").read_text("utf-8")
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


class AiClaim(BaseModel):
    """Une phrase plus forte que sa source : la citation du bloc, et la phrase à son niveau."""

    paragraph: int
    sentence: str = Field(min_length=1, max_length=2000)
    block: int | None = None
    quote: str = Field(default="", max_length=600)
    rewrite: str = Field(default="", max_length=2000)


class AiReview(BaseModel):
    criteria: list[AiCriterion] = Field(min_length=1, max_length=len(AI_KEYS))
    claims: list[AiClaim] = Field(default_factory=list, max_length=30)


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
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "paragraph": {"type": "integer"},
                    "sentence": {"type": "string"},
                    "block": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "quote": {"type": "string"},
                    "rewrite": {"type": "string"},
                },
                "required": ["paragraph", "sentence", "block", "quote", "rewrite"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["criteria", "claims"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class Criterion:
    key: str
    label: str
    ok: bool
    reason: str


@dataclass(frozen=True)
class Claim:
    paragraph: int
    sentence: str
    block: int | None
    quote: str
    rewrite: str


@dataclass(frozen=True)
class Review:
    criteria: list[Criterion]
    claims: list[Claim]
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
            "claims": [asdict(c) for c in self.claims],
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
    for i, paragraph in enumerate(letter.get("paragraphs", []), start=1):
        cited = ", ".join(str(c) for c in paragraph.get("chunk_ids", []))
        lines.append(f"[{i}] (blocs : {cited or 'aucun'}) {paragraph['text']}")
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
    flags: list[claims_check.Flag] | None = None,
    forbidden: list[str] | None = None,
) -> dict[str, Any]:
    """Le relecteur : le texte de la lettre, l'offre et le profil, jamais les coordonnées."""
    parts = [offer_message(offer), f"\n\n<langue>{language or 'auto'}</langue>"]
    if instruction:
        safe = instruction.replace("</consigne>", "</ consigne>")
        parts.append(f"\n\n<consigne>\n{safe}\n</consigne>")
    if forbidden:
        parts.append(claims_check.forbidden_block(forbidden))
    parts.append("\n\n" + _letter_text(letter))
    if flags:
        lines = "\n".join(f"[{f.paragraph}] {f.text()}" for f in flags)
        parts.append(f"\n\n<signalements>\n{lines}\n</signalements>")
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


def parse_review(
    text: str,
    letter: dict[str, Any],
    *,
    corrected: bool = False,
    flags: list[claims_check.Flag] | None = None,
) -> Review:
    """Les avis de l'IA, complétés par les vérifications du code, dans l'ordre de l'affichage.
    Une phrase signalée par le contrôle sans l'IA met « Aucune invention » à revoir, même si l'IA
    l'a laissée passer."""
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
        elif key == "invention" and flags and seen["invention"].ok:
            ok, reason = False, f"Plus fort que ton profil : {flags[0].text()}"
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
    stronger = [
        Claim(c.paragraph, c.sentence.strip(), c.block, c.quote.strip(), c.rewrite.strip())
        for c in ai.claims
        if 1 <= c.paragraph <= count
    ]
    return Review(criteria, stronger, corrected)


def correction_instruction(review: Review) -> str:
    """La consigne de l'unique correction automatique : ce qui est à revoir, et rien d'autre."""
    lines = [f"- {c.label} : {c.reason}" for c in review.criteria if not c.ok]
    return (
        "Corrige la lettre selon cette relecture, sans rien changer d'autre :\n"
        + "\n".join(lines)
        + "\nRetire tout fait absent des blocs du profil : ne le remplace jamais par un autre."
        + "\nRamène toute affirmation plus forte que son bloc au niveau exact du bloc (statut,"
        + " public, client, lieu, échelle, rôle), sans rien ajouter."
    )


def apply_claims(letter: dict[str, Any], review: Review) -> dict[str, Any]:
    """Chaque phrase plus forte que sa source est réécrite au niveau de la source, ou retirée.

    La phrase est cherchée mot pour mot dans son paragraphe ; une phrase introuvable est laissée (le
    contrôle sans l'IA la rattrape ensuite). Un paragraphe vidé disparaît, jamais la lettre entière.
    """
    if not review.claims:
        return letter
    paragraphs = [dict(p) for p in letter.get("paragraphs", [])]
    for claim in review.claims:
        paragraph = paragraphs[claim.paragraph - 1]
        if claim.sentence not in paragraph["text"]:
            continue
        replacement = no_dash(claim.rewrite) if claim.rewrite else ""
        text = paragraph["text"].replace(claim.sentence, replacement)
        paragraph["text"] = " ".join(text.split())
    kept = [p for p in paragraphs if p["text"].strip()]
    return {**letter, "paragraphs": kept} if kept else letter
