"""Le type de contrat d'une offre (issue #468, Kevin, 18.11.2026) : sans devinette."""

import importlib

import pytest

from jobbot.core.contract import CONTRACT_WORDS, Contract, classify_contract
from jobbot.db.models import Offer

# Des textes rencontrés dans le champ « employmentType » des sites (jobup, pages lues, offres
# ajoutées à la main) et leur catégorie attendue.
SAMPLES = [
    ("CDI", Contract.CDI),
    ("Durée indéterminée", Contract.CDI),
    ("Contrat à durée indéterminée", Contract.CDI),
    ("Contrat fixe", Contract.CDI),
    ("Festanstellung", Contract.CDI),
    ("Unbefristet", Contract.CDI),
    ("PERMANENT", Contract.CDI),
    ("Tempo indeterminato", Contract.CDI),
    ("CDD 12 mois", Contract.CDD),
    ("Durée déterminée", Contract.CDD),
    ("Befristet", Contract.CDD),
    ("Fixed-term", Contract.CDD),
    ("Stage", Contract.STAGE),
    ("Praktikum", Contract.STAGE),
    ("INTERN", Contract.STAGE),
    ("Internship", Contract.STAGE),
    ("Temporaire", Contract.TEMPORARY),
    ("Temporär", Contract.TEMPORARY),
    ("TEMPORARY", Contract.TEMPORARY),
    ("Intérim", Contract.TEMPORARY),
    # Pas de devinette : vide, temps de travail seul, mot inconnu ou deux catégories.
    (None, Contract.UNSPECIFIED),
    ("", Contract.UNSPECIFIED),
    ("Temps plein", Contract.UNSPECIFIED),
    ("FULL_TIME", Contract.UNSPECIFIED),
    ("Temps partiel", Contract.UNSPECIFIED),
    ("Apprentissage", Contract.UNSPECIFIED),
    ("Indépendant", Contract.UNSPECIFIED),
    ("CDI ou CDD", Contract.UNSPECIFIED),
    ("Internationale", Contract.UNSPECIFIED),
    ("Stagione", Contract.UNSPECIFIED),
]


@pytest.mark.parametrize(("text", "expected"), SAMPLES)
def test_classify_contract(text: str | None, expected: Contract) -> None:
    assert classify_contract(text) == expected


def test_the_migration_keeps_the_same_words() -> None:
    migration = importlib.import_module("jobbot.db.migrations.versions.0093_contrat_offre")
    assert {c.value: words for c, words in CONTRACT_WORDS.items()} == migration.CONTRACT_WORDS
    assert Contract.UNSPECIFIED.value == migration.UNSPECIFIED
    for text, expected in SAMPLES:
        assert migration.classify(text) == expected.value


def test_an_offer_keeps_its_category_up_to_date() -> None:
    offer = Offer(title="x", employment_type="CDD 6 mois")
    assert offer.contract == Contract.CDD
    offer.employment_type = None
    assert offer.contract == Contract.UNSPECIFIED
