"""Les schémas de sortie envoyés à l'IA restent dans ce que l'API accepte.

Le 10.11.2026, la lecture du CV échouait à chaque fois (« erreur de l'API (400) ») : le schéma
`understood` écrivait un champ facultatif avec deux types (`["integer", "null"]`) et mettait
`null` dans un `enum`. Ce test lit tous les schémas et refuse ces formes.
"""

from typing import Any

import pytest

from jobbot.llm import alert, cv, letter, letter_review, proposals, scoring
from jobbot.scoring import remote

SCHEMAS = {
    "alert": alert.OUTPUT_SCHEMA,
    "cv": cv.OUTPUT_SCHEMA,
    "letter": letter.OUTPUT_SCHEMA,
    "letter_review": letter_review.OUTPUT_SCHEMA,
    "proposals": proposals.OUTPUT_SCHEMA,
    "understand": proposals.UNDERSTAND_SCHEMA,
    "scoring": scoring.OUTPUT_SCHEMA,
    "remote": remote.SCHEMA,
}

# Contraintes que les sorties structurées ne prennent pas (docs de l'API).
UNSUPPORTED = {"minimum", "maximum", "multipleOf", "minLength", "maxLength", "minItems", "maxItems"}


def problems(node: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(node, list):
        for i, item in enumerate(node):
            found += problems(item, f"{path}[{i}]")
        return found
    if not isinstance(node, dict):
        return found
    if isinstance(node.get("type"), list):
        found.append(f"{path} : plusieurs types, écrire anyOf")
    if "enum" in node and any(v is None for v in node["enum"]):
        found.append(f"{path} : null dans un enum, écrire anyOf avec {{'type': 'null'}}")
    if "enum" in node and "type" in node:
        kinds = {type(v) for v in node["enum"]}
        if node["type"] == "string" and kinds != {str}:
            found.append(f"{path} : enum de type string avec d'autres valeurs")
    found += [f"{path} : contrainte {key} non prise en charge" for key in UNSUPPORTED & node.keys()]
    if node.get("type") == "object":
        if node.get("additionalProperties") is not False:
            found.append(f"{path} : additionalProperties doit valoir false")
        properties = set(node.get("properties", {}))
        if set(node.get("required", [])) != properties:
            found.append(f"{path} : required doit lister toutes les propriétés")
    for key, value in node.items():
        found += problems(value, f"{path}.{key}")
    return found


@pytest.mark.parametrize("name", sorted(SCHEMAS))
def test_schema_uses_supported_forms(name: str) -> None:
    assert problems(SCHEMAS[name]) == []


def test_checker_catches_the_cv_bug() -> None:
    bad = {
        "type": "object",
        "properties": {
            "min_rate": {"type": ["integer", "null"]},
            "remote": {"type": ["string", "null"], "enum": ["remote", "onsite", None]},
        },
        "required": ["min_rate", "remote"],
        "additionalProperties": False,
    }
    assert len(problems(bad)) == 3


def test_understand_request_uses_the_fixed_schema() -> None:
    params = proposals.request_params("claude-opus-5-5", "low", [], "CV", understand=True)
    schema = params["output_config"]["format"]["schema"]
    understood = schema["properties"]["understood"]["properties"]
    assert understood["remote"] == {
        "anyOf": [{"type": "string", "enum": ["remote", "onsite"]}, {"type": "null"}]
    }
    assert problems(schema) == []
