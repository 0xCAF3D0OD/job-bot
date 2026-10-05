"""Rédaction de la lettre de motivation par l'IA (docs/08-candidatures.md §3).

L'IA ne reçoit jamais les coordonnées de Kevin : elle écrit l'objet et le corps, la
plateforme assemble le reste (letters/document.py).
"""

import json
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

PROMPT_VERSION = "letter-v1"
INSTRUCTIONS = resources.files("jobbot.llm").joinpath("prompts/letter-v1.md").read_text("utf-8")
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
    paragraphs: list[Paragraph] = Field(min_length=1, max_length=6)
    employer: Employer = Field(default_factory=Employer)


_NULLABLE = {"anyOf": [{"type": "string"}, {"type": "null"}]}
OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "language": {"type": "string", "enum": ["fr", "en", "de"]},
        "subject": {"type": "string"},
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
    "required": ["language", "subject", "paragraphs", "employer"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class Assessment:
    """La note déjà calculée (0.4), pour viser les exigences principales."""

    strengths: list[str]
    gaps: list[str]


def _assessment_text(assessment: Assessment | None) -> str:
    if assessment is None or not (assessment.strengths or assessment.gaps):
        return ""
    lines = ["<evaluation>"]
    lines += [f"point fort : {s}" for s in assessment.strengths]
    lines += [f"manque : {g}" for g in assessment.gaps]
    lines.append("</evaluation>")
    return "\n".join(lines) + "\n\n"


def _previous_text(previous: dict[str, Any]) -> str:
    body = "\n\n".join(p["text"] for p in previous.get("paragraphs", []))
    subject = previous.get("subject", "")
    return f"<version_precedente>\nobjet : {subject}\n\n{body}\n</version_precedente>"


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
) -> dict[str, Any]:
    parts = [offer_message(offer), "\n\n", _assessment_text(assessment)]
    parts.append(f"<langue>{language or 'auto'}</langue>")
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
            text=p.text.strip(),
            chunk_ids=list(dict.fromkeys(i for i in p.chunk_ids if i in valid)),
        )
        for p in output.paragraphs
        if p.text.strip()
    ]
    if not paragraphs:
        raise InvalidScore("lettre vide")
    subject = output.subject.strip()
    for prefix in ("Objet :", "Objet:", "Subject:", "Betreff:"):
        subject = subject.removeprefix(prefix).strip()
    employer = Employer(
        address=_clean(output.employer.address),
        contact_name=_clean(output.employer.contact_name),
        contact_phone=_clean(output.employer.contact_phone),
    )
    return LetterOutput(
        language=output.language, subject=subject, paragraphs=paragraphs, employer=employer
    )
