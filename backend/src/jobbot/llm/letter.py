"""Rédaction de la lettre de motivation par l'IA (docs/08-candidatures.md §3).

L'IA ne reçoit jamais les coordonnées de Kevin : elle écrit l'objet et le corps, la
plateforme assemble le reste (letters/document.py).
"""

import json
import re
from dataclasses import dataclass
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

# v3 (30.10.2026) : ne jamais grossir un fait présent (statut, public, client, échelle, rôle), et
# les affirmations marquées « Pas vrai » données comme interdites.
PROMPT_VERSION = "letter-v3"
INSTRUCTIONS = resources.files("jobbot.llm").joinpath("prompts/letter-v3.md").read_text("utf-8")
MAX_TOKENS = 16_000
Language = Literal["fr", "en", "de"]


class Paragraph(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    chunk_ids: list[int] = Field(default_factory=list)


class Employer(BaseModel):
    address: str | None = Field(default=None, max_length=300)
    contact_name: str | None = Field(default=None, max_length=300)
    contact_phone: str | None = Field(default=None, max_length=300)


class LetterOutput(BaseModel):
    language: Language
    subject: str = Field(min_length=1, max_length=200)
    # La formule d'appel et la formule de politesse : rédigées par l'IA, donc modifiables par une
    # consigne (« Dear Hiring Committee »). Absentes d'une ancienne version : celles de la langue.
    salutation: str | None = Field(default=None, max_length=200)
    paragraphs: list[Paragraph] = Field(min_length=1, max_length=6)
    closing: str | None = Field(default=None, max_length=300)
    employer: Employer = Field(default_factory=Employer)
    # Une consigne qui touche une partie que l'IA ne peut pas changer (coordonnées, date,
    # destinataire, signature) : une ligne qui le dit, et aucune version n'est créée.
    refusal: str | None = Field(default=None, max_length=200)


_NULLABLE = {"anyOf": [{"type": "string"}, {"type": "null"}]}
OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "language": {"type": "string", "enum": ["fr", "en", "de"]},
        "subject": {"type": "string"},
        "salutation": {"type": "string"},
        "closing": {"type": "string"},
        "refusal": _NULLABLE,
        "paragraphs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "chunk_ids": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["text", "chunk_ids"],
                "additionalProperties": False,
            },
        },
        "employer": {
            "type": "object",
            "properties": {
                "address": _NULLABLE,
                "contact_name": _NULLABLE,
                "contact_phone": _NULLABLE,
            },
            "required": ["address", "contact_name", "contact_phone"],
            "additionalProperties": False,
        },
    },
    "required": [
        "language",
        "subject",
        "salutation",
        "paragraphs",
        "closing",
        "employer",
        "refusal",
    ],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class Assessment:
    """La note déjà calculée (0.4), pour viser les exigences principales."""

    strengths: list[str]
    gaps: list[str]


def assessment_text(assessment: Assessment | None) -> str:
    if assessment is None or not (assessment.strengths or assessment.gaps):
        return ""
    lines = ["<evaluation>"]
    lines += [f"point fort : {s}" for s in assessment.strengths]
    lines += [f"manque : {g}" for g in assessment.gaps]
    lines.append("</evaluation>")
    return "\n".join(lines) + "\n\n"


def _previous_text(previous: dict[str, Any]) -> str:
    body = "\n\n".join(p["text"] for p in previous.get("paragraphs", []))
    lines = [f"objet : {previous.get('subject', '')}"]
    if previous.get("salutation"):
        lines.append(f"formule d'appel : {previous['salutation']}")
    if previous.get("closing"):
        lines.append(f"formule de politesse : {previous['closing']}")
    head = "\n".join(lines)
    return f"<version_precedente>\n{head}\n\n{body}\n</version_precedente>"


def request_params(
    model: str,
    effort: str,
    chunks: list[ProfileChunkData],
    offer: OfferData,
    *,
    language: Language | None,
    assessment: Assessment | None = None,
    previous: dict[str, Any] | None = None,
    instruction: str | None = None,
    forbidden: list[str] | None = None,
) -> dict[str, Any]:
    parts = [offer_message(offer), "\n\n", assessment_text(assessment)]
    parts.append(f"<langue>{language or 'auto'}</langue>")
    if forbidden:
        lines = "\n".join(f"- {claim}" for claim in forbidden)
        parts.append(f"\n\n<interdits>\n{lines}\n</interdits>")
    if previous is not None:
        parts.append("\n\n" + _previous_text(previous))
    if instruction:
        safe = instruction.replace("</consigne>", "</ consigne>")
        parts.append(f"\n\n<consigne>\n{safe}\n</consigne>")
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


_DASH = re.compile(r"\s*\u2014\s*|\s+\u2013\s+")
_DOUBLED = re.compile(r",\s*([,.;:!?])")


def no_dash(text: str) -> str:
    """Garde-fou de la lettre : le tiret cadratin (et le tiret en incise) devient une virgule.
    Un intervalle collé (« 80\u2013100 % ») reste tel quel."""
    return _DOUBLED.sub(r"\1", _DASH.sub(", ", text)).strip()


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip() or None


def parse_output(text: str, chunks: list[ProfileChunkData]) -> LetterOutput:
    """Valide la réponse ; les identifiants de blocs inconnus sont retirés."""
    try:
        output = LetterOutput.model_validate(json.loads(text))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise InvalidScore(f"réponse non conforme : {type(exc).__name__}") from exc
    valid = {c.id for c in chunks}
    paragraphs = [
        Paragraph(
            text=no_dash(p.text),
            chunk_ids=list(dict.fromkeys(i for i in p.chunk_ids if i in valid)),
        )
        for p in output.paragraphs
        if p.text.strip()
    ]
    if not paragraphs:
        raise InvalidScore("lettre vide")
    subject = no_dash(output.subject)
    for prefix in ("Objet :", "Objet:", "Subject:", "Betreff:"):
        subject = subject.removeprefix(prefix).strip()
    salutation = no_dash(output.salutation) if output.salutation else None
    closing = no_dash(output.closing) if output.closing else None
    employer = Employer(
        address=_clean(output.employer.address),
        contact_name=_clean(output.employer.contact_name),
        contact_phone=_clean(output.employer.contact_phone),
    )
    return LetterOutput(
        language=output.language,
        subject=subject,
        salutation=salutation or None,
        paragraphs=paragraphs,
        closing=closing or None,
        employer=employer,
        refusal=(output.refusal or "").strip() or None,
    )
