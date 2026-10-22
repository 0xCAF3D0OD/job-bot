"""Les coordonnées ne partent jamais à l'IA (docs/121 §A.3)."""

from jobbot.letters.document import Identity
from jobbot.llm import proposals
from jobbot.llm.redact import redact

CV = """Camille Exemple
Rue du Test 1
CH-1020 Renens
+41 79 000 00 00
camille@exemple.ch
www.camille-exemple.ch
Née le 12.03.1990
Nationalité : suisse

Expériences
Ingénieure DevOps, Exemple Logistique SA (2021 - 2026)
Bahnhofstrasse 12 : un client à Zurich
Mars 2019 : stage, 6 mois"""


def test_head_of_cv_without_known_identity() -> None:
    """À l'accueil, les coordonnées ne sont pas encore saisies : l'en-tête suffit."""
    text = redact(CV)
    for secret in (
        "Camille Exemple",
        "Rue du Test",
        "1020 Renens",
        "079",
        "+41",
        "camille@",
        "12.03.1990",
        "camille-exemple.ch",
    ):
        assert secret not in text, secret
    # Le parcours reste : l'IA en a besoin.
    assert "Ingénieure DevOps, Exemple Logistique SA (2021 - 2026)" in text
    assert "Mars 2019 : stage, 6 mois" in text
    # Une rue plus bas, dans le texte d'une expérience, n'est pas une adresse de la personne.
    assert "Bahnhofstrasse 12" in text


def test_known_identity_removed_everywhere() -> None:
    identity = Identity(
        name="Camille Exemple", street="Rue du Test 1", postcode="1020", city="Renens"
    )
    text = redact(
        "Lettre de Camille Exemple, Rue du Test 1, 1020 Renens. Camille a dirigé…", identity
    )
    assert "Camille" not in text and "Exemple" not in text
    assert "Rue du Test 1" not in text and "1020 Renens" not in text


def test_proposal_request_carries_no_contact_details() -> None:
    identity = Identity(name="Camille Exemple", city="Renens", postcode="1020")
    params = proposals.request_params("modele", "low", [], CV, identity)
    sent = params["messages"][0]["content"]
    assert "Camille" not in sent and "Renens" not in sent and "1990" not in sent
