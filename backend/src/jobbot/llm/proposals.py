"""Proposition de blocs de profil à partir d'un document (docs/07-propositions-blocs.md).

Rien n'est enregistré ici : la plateforme montre les propositions, Kevin les relit,
les modifie et choisit lesquelles ajouter.
"""

import json
from html import escape
from importlib import resources
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from jobbot.llm.redact import redact
from jobbot.llm.scoring import InvalidScore, ProfileChunkData

PROMPT_VERSION = "propose-chunks-v1"
INSTRUCTIONS = (
    resources.files("jobbot.llm").joinpath("prompts/propose-chunks-v1.md").read_text("utf-8")
)
# Le CV lu à l'accueil (docs/121 §A) : les blocs, et ce que le CV dit de la recherche.
UNDERSTAND_VERSION = "cv-understand-v1"
UNDERSTAND_INSTRUCTIONS = INSTRUCTIONS + (
    resources.files("jobbot.llm").joinpath("prompts/cv-understand-v1.md").read_text("utf-8")
)
MAX_DOCUMENT_CHARS = 30_000
MAX_TOKENS = 8_000


def scrub(text: str, identity: object | None = None, *, head: bool = True) -> str:
    """Les coordonnées retirées avant l'envoi à l'IA (docs/121 §A.3, `llm/redact.py`)."""
    return redact(text, identity, head=head)


class Proposal(BaseModel):
    kind: Literal["experience", "competence", "formation", "preference"]
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=2000)
    tags: list[str] = Field(default_factory=list, max_length=8)
    duplicate_of: int | None = None


class ProposalOutput(BaseModel):
    chunks: list[Proposal] = Field(max_length=20)


OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "chunks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": ["experience", "competence", "formation", "preference"],
                    },
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "duplicate_of": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                },
                "required": ["kind", "title", "content", "tags", "duplicate_of"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["chunks"],
    "additionalProperties": False,
}


LANGUAGES = ("allemand", "italien", "anglais")

UNDERSTOOD_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "roles": {"type": "array", "items": {"type": "string"}},
        "min_rate": {"type": ["integer", "null"]},
        "languages": {"type": "array", "items": {"type": "string", "enum": list(LANGUAGES)}},
        "remote": {"type": ["string", "null"], "enum": ["remote", "onsite", None]},
    },
    "required": ["roles", "min_rate", "languages", "remote"],
    "additionalProperties": False,
}
UNDERSTAND_SCHEMA: dict[str, Any] = {
    **OUTPUT_SCHEMA,
    "properties": {**OUTPUT_SCHEMA["properties"], "understood": UNDERSTOOD_SCHEMA},
    "required": ["chunks", "understood"],
}


class Understood(BaseModel):
    """Ce que le CV dit de la recherche, seulement s'il le dit (docs/121 §A)."""

    roles: list[str] = Field(default_factory=list)
    min_rate: int | None = None
    languages: list[str] = Field(default_factory=list)
    remote: Literal["remote", "onsite"] | None = None


def request_params(
    model: str,
    effort: str,
    existing: list[ProfileChunkData],
    document_text: str,
    identity: object | None = None,
    *,
    understand: bool = False,
) -> dict[str, Any]:
    blocks = (
        "\n".join(
            f'<bloc id="{c.id}" type="{c.kind}" titre="{escape(c.title)}">\n{c.content}\n</bloc>'
            for c in sorted(existing, key=lambda c: c.id)
        )
        or "(aucun bloc existant)"
    )
    text = scrub(document_text, identity)[:MAX_DOCUMENT_CHARS].replace(
        "</document>", "</ document>"
    )
    return {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "system": [
            {"type": "text", "text": UNDERSTAND_INSTRUCTIONS if understand else INSTRUCTIONS}
        ],
        "messages": [
            {
                "role": "user",
                "content": f"<blocs_existants>\n{blocks}\n</blocs_existants>\n\n"
                f"<document>\n{text}\n</document>",
            }
        ],
        "output_config": {
            "effort": effort,
            "format": {
                "type": "json_schema",
                "schema": UNDERSTAND_SCHEMA if understand else OUTPUT_SCHEMA,
            },
        },
    }


def parse_output(text: str, existing: list[ProfileChunkData]) -> list[Proposal]:
    try:
        output = ProposalOutput.model_validate(json.loads(text))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise InvalidScore(f"réponse non conforme : {type(exc).__name__}") from exc
    known = {c.id for c in existing}
    cleaned = []
    for proposal in output.chunks[:15]:
        tags = list(dict.fromkeys(t.strip().lower()[:40] for t in proposal.tags if t.strip()))[:4]
        cleaned.append(
            proposal.model_copy(
                update={
                    "title": scrub(proposal.title.strip(), head=False)[:200],
                    "content": scrub(proposal.content.strip(), head=False)[:2000],
                    "tags": tags,
                    # Un doublon qui désigne un bloc inexistant est ignoré.
                    "duplicate_of": proposal.duplicate_of
                    if proposal.duplicate_of in known
                    else None,
                }
            )
        )
    return cleaned


def parse_understood(text: str) -> Understood:
    """La partie « understood » de la réponse, nettoyée ; vide si elle manque ou déraille."""
    try:
        raw = json.loads(text).get("understood") or {}
        found = Understood.model_validate(raw)
    except (json.JSONDecodeError, ValidationError, AttributeError):
        return Understood()
    roles = [scrub(r.strip(), head=False)[:80] for r in found.roles if r.strip()]
    roles = list(dict.fromkeys(roles))[:3]
    rate = found.min_rate if found.min_rate is not None and 10 <= found.min_rate <= 100 else None
    languages = [lang for lang in LANGUAGES if lang in found.languages]
    return Understood(roles=roles, min_rate=rate, languages=languages, remote=found.remote)
