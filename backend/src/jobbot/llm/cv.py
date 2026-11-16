"""CV adapté : sélection et ordre des blocs, titre et résumé (docs/08-candidatures.md §4).

L'IA ne réécrit pas les blocs : le texte des expériences reste celui de Kevin.
"""

import json
from importlib import resources
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from jobbot.llm import cv_reasons
from jobbot.llm.letter import Assessment, Language, assessment_text
from jobbot.llm.scoring import (
    InvalidScore,
    OfferData,
    ProfileChunkData,
    offer_message,
    profile_block,
)

PROMPT_VERSION = "cv-v1"
_PROMPTS = resources.files("jobbot.llm").joinpath("prompts")
INSTRUCTIONS = _PROMPTS.joinpath(f"{PROMPT_VERSION}.md").read_text("utf-8")
# Le prompt suivant (ligne « Pourquoi », §32 et §37 du 16.11) : il ne sert qu'à `jobbot
# mesure-pourquoi` ; cv-v1 reste en service jusqu'à la bascule, après la mesure de Kevin.
NEXT_VERSION = "cv-v2"
NEXT_INSTRUCTIONS = _PROMPTS.joinpath(f"{NEXT_VERSION}.md").read_text("utf-8")
MAX_TOKENS = 8_000
# Types de blocs qui ont leur place dans un CV ; préférences, rédhibitoires et ton n'y vont pas.
CV_KINDS = ("experience", "competence", "formation")


class CvOutput(BaseModel):
    language: Language
    headline: str = Field(max_length=120)
    summary: str = Field(max_length=800)
    chunk_ids: list[int] = Field(max_length=40)
    keywords: list[str] = Field(default_factory=list, max_length=30)


OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "language": {"type": "string", "enum": ["fr", "en", "de"]},
        "headline": {"type": "string"},
        "summary": {"type": "string"},
        "chunk_ids": {"type": "array", "items": {"type": "integer"}},
        "keywords": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["language", "headline", "summary", "chunk_ids", "keywords"],
    "additionalProperties": False,
}
NEXT_OUTPUT_SCHEMA: dict[str, Any] = {
    **OUTPUT_SCHEMA,
    "properties": {
        **OUTPUT_SCHEMA["properties"],
        "reasons": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"target": {"type": "string"}, "reason": {"type": "string"}},
                "required": ["target", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": [*OUTPUT_SCHEMA["required"], "reasons"],
}


def is_language_block(chunk: ProfileChunkData) -> bool:
    """Le bloc « Langues » (type compétence) a sa propre rubrique, en fin de CV."""
    return chunk.title.strip().lower().startswith(("langue", "language", "sprache"))


def _previous_text(previous: dict[str, Any]) -> str:
    return (
        "<version_precedente>\n"
        f"titre : {previous.get('headline', '')}\n"
        f"résumé : {previous.get('summary', '')}\n"
        f"blocs : {', '.join(str(i) for i in previous.get('chunk_ids', []))}\n"
        "</version_precedente>"
    )


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
    next_prompt: bool = False,
) -> dict[str, Any]:
    """`next_prompt` : le prompt suivant (NEXT_VERSION), pour la mesure avant sa mise en service."""
    instructions, schema = (
        (NEXT_INSTRUCTIONS, NEXT_OUTPUT_SCHEMA) if next_prompt else (INSTRUCTIONS, OUTPUT_SCHEMA)
    )
    parts = [offer_message(offer), "\n\n", assessment_text(assessment)]
    parts.append(f"<langue>{language or 'auto'}</langue>")
    if previous is not None:
        parts.append("\n\n" + _previous_text(previous))
    if instruction:
        parts.append(
            f"\n\n<consigne>\n{instruction.replace('</consigne>', '</ consigne>')}\n</consigne>"
        )
    return {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "system": [
            {"type": "text", "text": instructions},
            # Même bloc de profil que la note et la lettre : il profite du même cache.
            {"type": "text", "text": profile_block(chunks), "cache_control": {"type": "ephemeral"}},
        ],
        "messages": [{"role": "user", "content": "".join(parts)}],
        "output_config": {
            "effort": effort,
            "format": {"type": "json_schema", "schema": schema},
        },
    }


def parse_output(text: str, chunks: list[ProfileChunkData]) -> CvOutput:
    """Valide la réponse ; garde seulement des blocs de CV existants, ajoute formation et
    langues si l'IA les a omises, et ne retient que les mots-clés présents dans les blocs."""
    try:
        output = CvOutput.model_validate(json.loads(text))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise InvalidScore(f"réponse non conforme : {type(exc).__name__}") from exc
    eligible = {c.id: c for c in chunks if c.kind in CV_KINDS}
    ids = list(dict.fromkeys(i for i in output.chunk_ids if i in eligible))
    if not ids and eligible:
        raise InvalidScore("aucun bloc choisi")
    for chunk in eligible.values():
        if chunk.id not in ids and (chunk.kind == "formation" or is_language_block(chunk)):
            ids.append(chunk.id)
    corpus = " ".join(f"{eligible[i].title} {eligible[i].content}" for i in ids).lower()
    keywords = list(
        dict.fromkeys(
            k.strip() for k in output.keywords if k.strip() and k.strip().lower() in corpus
        )
    )[:12]
    return CvOutput(
        language=output.language,
        headline=output.headline.strip()[:80],
        summary=output.summary.strip(),
        chunk_ids=ids,
        keywords=keywords,
    )


def parse_reasons(
    text: str, output: CvOutput, chunks: list[ProfileChunkData], offer_text: str | None
) -> list[cv_reasons.Reason]:
    """Les raisons de la réponse cv-v2 qui passent la vérification (cv_reasons) ; une réponse
    sans raisons, ou des raisons mal formées, n'en donnent aucune : le CV reste valable."""
    try:
        raw = json.loads(text).get("reasons")
    except (json.JSONDecodeError, AttributeError):
        return []
    if not isinstance(raw, list):
        return []
    pairs = [
        (str(r.get("target", "")), str(r.get("reason", "")))
        for r in raw[:40]
        if isinstance(r, dict)
    ]
    return cv_reasons.validate(
        pairs,
        offer_text or "",
        summary=output.summary,
        kept=output.chunk_ids,
        eligible={c.id for c in chunks if c.kind in CV_KINDS},
    )
