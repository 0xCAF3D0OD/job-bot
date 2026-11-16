"""La ligne « Pourquoi » du CV adapté (§32 et §37 du 16.11.2026) : cv-v2, vérification des
citations, `origin: "user"`, mesure du coût sur 5 CV fictifs."""

import json
import re
from typing import Any

from jobbot.llm import cv as cv_llm
from jobbot.llm import cv_measure, cv_reasons
from jobbot.llm.client import RawResult
from jobbot.llm.pricing import Usage
from jobbot.llm.scoring import ProfileChunkData

OFFER = (
    "Ingénieur DevOps. Exigences : Kubernetes, Terraform et Google Cloud. "
    "JavaScript est un plus. Teamfähigkeit, sehr gute Französischkenntnisse."
)
CHUNKS = [
    ProfileChunkData(1, "experience", "Stage DevOps", "Terraform sur AWS."),
    ProfileChunkData(2, "experience", "Stage web", "Vue.js et PHP."),
    ProfileChunkData(3, "competence", "Programmation", "Go, Java, Python."),
    ProfileChunkData(4, "formation", "École 42", "Projets système."),
    ProfileChunkData(5, "preference", "Postes", "DevOps"),
]


def check(text: str, removed: bool = False) -> cv_reasons.Reason | None:
    return cv_reasons.check(text, cv_reasons.fold(OFFER), removed=removed)


def test_valid_citation_without_accents_or_case() -> None:
    reason = check("L'annonce demande « kubernetes » et « TERRAFORM ».")
    assert reason is not None and reason.quotes == ("kubernetes", "TERRAFORM")
    # Les mots cités restent dans la langue de l'annonce, la phrase est en français.
    assert check("L'annonce demande « Teamfähigkeit ».") is not None
    assert check("L\u2019annonce cite « google cloud ».") is not None


def test_absent_word_drops_the_reason() -> None:
    assert check("L'annonce demande « Ansible ».") is None
    # Une seule citation inventée suffit à écarter la raison.
    assert check("L'annonce demande « Kubernetes » et « Ansible ».") is None
    # Sans citation, pas de raison (sauf la contrainte de place d'un retrait).
    assert check("Ce bloc est plus pertinent pour ce poste.") is None


def test_empty_field_gives_no_line() -> None:
    assert check("") is None
    assert check("   ") is None
    assert check("« »") is None


def test_whole_words_only() -> None:
    # « Go » ne valide pas « Google », « Java » ne valide pas « JavaScript ».
    assert check("L'annonce demande « Go ».") is None
    assert check("L'annonce demande « Java ».") is None
    assert check("L'annonce demande « JavaScript ».") is not None
    assert check("L'annonce demande « Kube ».") is None


def test_removal_may_give_the_place_constraint() -> None:
    assert check("Retiré pour tenir sur une page.", removed=True) is not None
    assert check("Retiré pour tenir sur une page.", removed=False) is None
    assert check("Retiré pour tenir sur une page ; « Ansible » absent.", removed=True) is None


def test_parse_reasons_targets() -> None:
    body = {
        "language": "fr",
        "headline": "DevOps",
        "summary": "Terraform sur AWS.",
        "chunk_ids": [3, 1, 4],
        "keywords": [],
        "reasons": [
            {"target": "profil", "reason": "L'annonce demande « Terraform »."},
            {"target": "3", "reason": "L'annonce cite « JavaScript »."},
            {"target": "3", "reason": "Doublon « Kubernetes »."},
            {"target": "2", "reason": "Retiré pour tenir sur une page."},
            {"target": "1", "reason": ""},
            {"target": "5", "reason": "L'annonce demande « Kubernetes »."},
            {"target": "999", "reason": "L'annonce demande « Kubernetes »."},
        ],
    }
    text = json.dumps(body)
    output = cv_llm.parse_output(text, CHUNKS)
    reasons = cv_llm.parse_reasons(text, output, CHUNKS, OFFER)
    assert [(r.target, r.quotes) for r in reasons] == [
        ("summary", ("Terraform",)),
        (3, ("JavaScript",)),
        (2, ()),
    ]
    # cv-v1 sans « reasons » : aucune raison, le CV reste valable.
    assert cv_llm.parse_reasons(json.dumps({**body, "reasons": None}), output, CHUNKS, OFFER) == []


def test_next_prompt_only_for_the_measure() -> None:
    offer = cv_measure.CASES[0].offer
    v1 = cv_llm.request_params("m", "low", CHUNKS, offer, language=None)
    v2 = cv_llm.request_params("m", "low", CHUNKS, offer, language=None, next_prompt=True)
    assert cv_llm.PROMPT_VERSION == "cv-v1" and cv_llm.NEXT_VERSION == "cv-v2"
    assert "reasons" not in v1["output_config"]["format"]["schema"]["properties"]
    assert "reasons" in v2["output_config"]["format"]["schema"]["required"]
    assert "pour tenir sur une page" in v2["system"][0]["text"]
    assert "reasons" not in v1["system"][0]["text"]


def test_changed_targets() -> None:
    before = {"summary": "A", "chunk_ids": [1, 2, 3, 4]}
    assert cv_reasons.changed_targets(before, before) == []
    after = {"summary": "B", "chunk_ids": [2, 1, 3, 5]}
    assert cv_reasons.changed_targets(before, after) == ["summary", 4, 5, 2, 1]


class MeasureClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def score(self, params: dict[str, Any]) -> RawResult:
        self.calls.append(params)
        schema = params["output_config"]["format"]["schema"]
        ids = [int(i) for i in re.findall(r'id="(\d+)"', params["system"][1]["text"])]
        body: dict[str, Any] = {
            "language": "fr",
            "headline": "Titre",
            "summary": "Résumé.",
            "chunk_ids": ids,
            "keywords": [],
        }
        out = 300
        if "reasons" in schema["properties"]:
            body["reasons"] = [
                {"target": "profil", "reason": "L'annonce demande « Kubernetes »."},
                {"target": str(ids[1]), "reason": "L'annonce demande « Ansible »."},
            ]
            out = 360
        return RawResult(json.dumps(body), "claude-opus-5", Usage(2000, 0, 0, out), "end_turn")


async def test_measure_prints_numbers_only() -> None:
    client = MeasureClient()
    rows = await cv_measure.measure(client, "claude-opus-5", "medium")
    assert len(client.calls) == 10 and len(rows) == 5
    lines = cv_measure.report(rows)
    text = "\n".join(lines)
    assert "Total (5 CV)" in text and "Raisons valables :" in text
    # Aucun texte de CV, d'offre ou de raison dans le compte rendu.
    for case in cv_measure.CASES:
        assert case.offer.title not in text
        assert all(c.title not in text for c in case.chunks)
    assert "Kubernetes" not in text and "Ansible" not in text
