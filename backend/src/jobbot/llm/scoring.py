"""Construction de la demande de note, format imposé de la réponse et validation.

Docs/06 §2 : l'IA ne reçoit que les blocs de profil actifs et le texte de l'offre ; elle
n'a aucun outil ; sa réponse suit un schéma JSON imposé, puis elle est revalidée ici.
"""

import hashlib
import json
from dataclasses import dataclass
from html import escape
from importlib import resources
from typing import Any

from pydantic import BaseModel, Field, ValidationError

PROMPT_VERSION = "score-v1"
INSTRUCTIONS = resources.files("jobbot.llm").joinpath("prompts/score-v1.md").read_text("utf-8")
MAX_OFFER_CHARS = 12_000
MAX_TOKENS = 4_000


class Point(BaseModel):
    text: str = Field(max_length=300)
    chunk_ids: list[int] = Field(default_factory=list)


class ScoreOutput(BaseModel):
    summary_role: str = Field(max_length=400)
    summary_asks: str = Field(max_length=400)
    summary_offers: str = Field(max_length=400)
    score: int | None = Field(default=None, ge=0, le=100)
    strengths: list[Point] = Field(default_factory=list, max_length=6)
    gaps: list[Point] = Field(default_factory=list, max_length=6)


# Schéma envoyé à l'API (sorties structurées) : seulement des types simples, les bornes
# sont vérifiées par ScoreOutput à la réception.
_POINT_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "chunk_ids": {"type": "array", "items": {"type": "integer"}},
    },
    "required": ["text", "chunk_ids"],
    "additionalProperties": False,
}
OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary_role": {"type": "string"},
        "summary_asks": {"type": "string"},
        "summary_offers": {"type": "string"},
        "score": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
        "strengths": {"type": "array", "items": _POINT_SCHEMA},
        "gaps": {"type": "array", "items": _POINT_SCHEMA},
    },
    "required": ["summary_role", "summary_asks", "summary_offers", "score", "strengths", "gaps"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class ProfileChunkData:
    id: int
    kind: str
    title: str
    content: str


@dataclass(frozen=True)
class OfferData:
    id: int
    title: str
    company: str | None
    location: str | None
    rate: str | None
    employment_type: str | None
    text: str | None
    # Vrai si `text` n'est que l'extrait de l'alerte (pas le texte complet de l'annonce).
    partial: bool


def profile_block(chunks: list[ProfileChunkData]) -> str:
    """Bloc de profil, stable d'un appel à l'autre (mis en cache) : ordre fixe par id."""
    if not chunks:
        return "<profil>\n(aucun bloc de profil : ne donne pas de note)\n</profil>"
    parts = [
        f'<bloc id="{c.id}" type="{c.kind}" titre="{escape(c.title)}">\n{c.content}\n</bloc>'
        for c in sorted(chunks, key=lambda c: c.id)
    ]
    return "<profil>\n" + "\n".join(parts) + "\n</profil>"


def profile_hash(chunks: list[ProfileChunkData]) -> str:
    return hashlib.sha256(profile_block(chunks).encode()).hexdigest()[:16]


def offer_message(offer: OfferData) -> str:
    fields = {
        "titre": offer.title,
        "entreprise": offer.company,
        "lieu": offer.location,
        "taux": offer.rate,
        "type": offer.employment_type,
    }
    header = "\n".join(f"{k} : {v}" for k, v in fields.items() if v)
    text = (offer.text or "").strip()[:MAX_OFFER_CHARS] or "(aucun texte)"
    nature = "extrait de l'alerte seulement" if offer.partial else "texte complet de l'annonce"
    # Les balises de fin éventuellement présentes dans l'annonce sont neutralisées.
    text = text.replace("</offre>", "</ offre>")
    return f"<offre>\n{header}\n\n[{nature}]\n{text}\n</offre>"


def request_params(
    model: str, effort: str, chunks: list[ProfileChunkData], offer: OfferData
) -> dict[str, Any]:
    """Paramètres communs aux appels directs et aux lots."""
    return {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "system": [
            {"type": "text", "text": INSTRUCTIONS},
            # Consignes + profil : préfixe stable, mis en cache entre les offres.
            {"type": "text", "text": profile_block(chunks), "cache_control": {"type": "ephemeral"}},
        ],
        "messages": [{"role": "user", "content": offer_message(offer)}],
        "output_config": {
            "effort": effort,
            "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA},
        },
    }


class InvalidScore(ValueError):
    pass


def parse_output(text: str, chunks: list[ProfileChunkData]) -> ScoreOutput:
    """Valide la réponse et retire ce qui n'est pas prouvé par un bloc actif."""
    try:
        output = ScoreOutput.model_validate(json.loads(text))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise InvalidScore(f"réponse non conforme : {type(exc).__name__}") from exc
    valid = {c.id for c in chunks}
    if not valid:
        return output.model_copy(update={"score": None, "strengths": [], "gaps": []})

    strengths = []
    for point in output.strengths:
        ids = [i for i in point.chunk_ids if i in valid]
        if ids:  # un point fort sans bloc qui le prouve est retiré (docs/06 §2)
            strengths.append(point.model_copy(update={"chunk_ids": ids}))
    gaps = [
        point.model_copy(update={"chunk_ids": [i for i in point.chunk_ids if i in valid]})
        for point in output.gaps
    ]
    return output.model_copy(update={"strengths": strengths[:4], "gaps": gaps[:4]})
