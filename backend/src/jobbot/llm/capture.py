"""Lire une capture d'écran d'annonce (Kevin, 17.11, Q1).

« Refaire la note » accepte un PDF, un PNG ou un JPG. Un PDF se lit sans IA
(manual_offers.pdf_text). Une image n'a pas de texte : l'IA le recopie. L'image n'est ni rangée
ni journalisée (E-5, J-1) ; elle ne part qu'à l'IA, comme donnée (I-2). L'IA ne recopie que
l'annonce, jamais ce qui entoure la page (nom de la personne connectée, menus, messages) ; le
nom de la personne est ensuite retiré du texte, comme d'un texte collé (I-1).
"""

import base64
import json
from importlib import resources
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from jobbot.llm.scoring import InvalidScore

PROMPT_VERSION = "capture-v1"
# Recopier un texte : le petit modèle des alertes suffit.
MODEL = "claude-haiku-4-5"
MAX_TOKENS = 4_000

ImageType = Literal["image/png", "image/jpeg"]

INSTRUCTIONS = (
    resources.files("jobbot.llm").joinpath(f"prompts/{PROMPT_VERSION}.md").read_text("utf-8")
)

OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"found": {"type": "boolean"}, "text": {"type": "string"}},
    "required": ["found", "text"],
    "additionalProperties": False,
}


class CaptureOutput(BaseModel):
    found: bool
    text: str = Field(max_length=40_000)


def image_type(data: bytes) -> ImageType | None:
    """Le type d'une image d'après son contenu (E-5), jamais d'après son nom."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    return None


def request_params(data: bytes, media_type: ImageType) -> dict[str, Any]:
    picture = base64.standard_b64encode(data).decode("ascii")
    return {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": [{"type": "text", "text": INSTRUCTIONS}],
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": picture},
                    },
                    {"type": "text", "text": "Recopie l'annonce de cette capture."},
                ],
            }
        ],
        "output_config": {"format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
    }


def parse_output(text: str) -> CaptureOutput:
    try:
        return CaptureOutput.model_validate(json.loads(text))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise InvalidScore(f"réponse non conforme : {type(exc).__name__}") from exc
