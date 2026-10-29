"""Le jeu de lettres de référence du relecteur (décision de Kevin) : cinq lettres, bonnes et
mauvaises, plus une lettre avec un fait inventé, chacune avec ce que la relecture doit trouver.

- La longueur et le tiret cadratin se vérifient sans l'IA : testés à chaque CI.
- Les autres critères, c'est l'IA qui les juge : `JOBBOT_REVIEW_EVAL=1` avec une vraie clé
  (`JOBBOT_ANTHROPIC_API_KEY`) relance le relecteur sur les six lettres et vérifie son classement.
"""

import json
import os
from typing import Any

import pytest

from jobbot.llm import letter_review
from jobbot.llm.scoring import OfferData, ProfileChunkData
from jobbot.scoring import service
from tests.conftest import make_settings

PROFILE = [
    ProfileChunkData(
        id=1,
        kind="experience",
        title="Ingénieur plateforme, Démo SA (2021-2025)",
        content="Plateforme Kubernetes de 40 services ; déploiements de 2 jours à 20 minutes ; "
        "astreintes avec Prometheus et Grafana.",
    ),
    ProfileChunkData(
        id=2,
        kind="competence",
        title="Infrastructure as code",
        content="Terraform sur Azure et AWS, modules partagés par 3 équipes.",
    ),
]
OFFER = OfferData(
    id=1,
    title="Ingénieur DevOps",
    company="Prototype Fintech SA",
    location="Genève",
    rate=None,
    employment_type=None,
    text="Exigences : Kubernetes en production, Terraform, supervision (Prometheus). "
    "Équipe plateforme de 6 personnes.",
    partial=False,
)


def _letter(*paragraphs: str, salutation: str = "Madame, Monsieur,") -> dict[str, Any]:
    return {
        "subject": "Candidature au poste d'ingénieur DevOps",
        "salutation": salutation,
        "closing": "Je vous prie d'agréer, Madame, Monsieur, mes salutations distinguées.",
        "paragraphs": [{"text": p, "chunk_ids": []} for p in paragraphs],
    }


GOOD = (
    "Votre équipe plateforme de six personnes construit ce que je fais depuis quatre ans : "
    "une plateforme Kubernetes en production.",
    "Chez Démo SA, j'ai mené une plateforme de 40 services et ramené les déploiements de deux "
    "jours à vingt minutes.",
    "J'écris l'infrastructure en Terraform sur Azure et AWS, et j'assure les astreintes avec "
    "Prometheus et Grafana.",
    "Je serais heureux d'en parler lors d'un entretien.",
)

# Chaque cas : la lettre, puis ce que chaque critère doit donner (absent : pas vérifié).
CASES: dict[str, tuple[dict[str, Any], dict[str, bool]]] = {
    "bonne": (
        _letter(*GOOD),
        {
            "accroche": True,
            "pertinence": True,
            "precision": True,
            "longueur": True,
            "conclusion": True,
            "invention": True,
            "regles": True,
        },
    ),
    "creuse": (
        _letter(
            "Je suis une personne dynamique, motivée et passionnée depuis toujours.",
            "Je pense être le candidat idéal pour ce poste passionnant.",
            "Je serais heureux d'en parler lors d'un entretien.",
        ),
        {"accroche": False, "precision": False, "longueur": True, "regles": True},
    ),
    "trop-longue": (
        _letter(*GOOD, *(["Pour le reste, " + "mon parcours parle de lui-même. " * 20] * 4)),
        {"longueur": False, "regles": True},
    ),
    "sans-conclusion": (
        _letter(*GOOD[:3]),
        {"conclusion": False, "longueur": True, "regles": True},
    ),
    "tiret": (
        _letter(GOOD[0].replace(" : ", " — "), *GOOD[1:]),
        {"regles": False, "longueur": True},
    ),
    "inventee": (
        _letter(
            GOOD[0],
            "J'ai passé dix ans chez Google à diriger une équipe de 50 ingénieurs.",
            *GOOD[2:],
        ),
        {"invention": False, "longueur": True, "regles": True},
    ),
}


@pytest.mark.parametrize("name", list(CASES))
def test_reference_letters_code_checks(name: str) -> None:
    """La longueur et le tiret cadratin : sans l'IA, à chaque CI."""
    letter, expected = CASES[name]
    checks = letter_review.deterministic(letter)
    for key in ("longueur", "regles"):
        if key in expected:
            assert checks[key][0] is expected[key], (name, key, checks[key][1])


def test_reviewer_never_receives_coordinates() -> None:
    """Le relecteur reçoit la lettre, l'offre et le profil, jamais les coordonnées."""
    params = letter_review.request_params(
        "claude", "low", PROFILE, OFFER, CASES["bonne"][0], language="fr", instruction=None
    )
    sent = json.dumps(params, ensure_ascii=False)
    assert "<lettre>" in sent and "Prototype Fintech SA" in sent and "Terraform" in sent
    # Les coordonnées de l'en-tête (letters/document.py) ne sont jamais dans ses entrées.
    for absent in ("Camille Exemple", "Rue du Test 1", "1020 Renens", "+41 79", "camille@"):
        assert absent not in sent


@pytest.mark.skipif(
    os.environ.get("JOBBOT_REVIEW_EVAL") != "1", reason="relecture réelle : JOBBOT_REVIEW_EVAL=1"
)
@pytest.mark.parametrize("name", list(CASES))
async def test_reference_letters_with_ai(name: str) -> None:
    """Le relecteur classe correctement les six lettres (appel réel à l'IA)."""
    settings = make_settings(anthropic_api_key=os.environ["JOBBOT_ANTHROPIC_API_KEY"])
    client = service.make_client(settings)
    letter, expected = CASES[name]
    params = letter_review.request_params(
        settings.llm_model, "medium", PROFILE, OFFER, letter, language="fr", instruction=None
    )
    raw = await client.score(params)
    review = letter_review.parse_review(raw.text, letter)
    got = {c.key: c.ok for c in review.criteria}
    wrong = {k: (got[k], v) for k, v in expected.items() if got[k] is not v}
    assert not wrong, (name, wrong, [c.reason for c in review.criteria])
