"""Règles du filtre (core/filter.py), dont des titres réels tirés des alertes."""

import pytest

from jobbot.core.filter import ContractType, Criteria, Language, OfferFacts, canton_of, evaluate


def rules(
    facts: OfferFacts, criteria: Criteria, cantons: dict[str, str] | None = None
) -> list[str]:
    return [r.rule for r in evaluate(facts, criteria, cantons).reasons]


def test_no_criteria_lets_everything_pass() -> None:
    assert evaluate(OfferFacts("Stage vente Zürich", location="Zürich, ZH"), Criteria()).passed


@pytest.mark.parametrize(
    ("location", "excluded"),
    [
        ("Pully, VD", False),  # canton accepté
        ("1020 Renens VD", False),
        ("Genève", False),  # commune acceptée
        ("Geneve", False),  # sans accent
        ("Zürich, ZH", True),  # canton connu, refusé
        ("Biel/Bienne", False),  # canton inconnu : on n'écarte pas
        (None, False),  # lieu inconnu : on n'écarte pas
    ],
)
def test_locations(location: str | None, excluded: bool) -> None:
    criteria = Criteria(locations=("VD", "Genève"))
    assert ("locations" in rules(OfferFacts("Admin", location=location), criteria)) is excluded


def test_city_canton_learned_from_other_offers() -> None:
    criteria = Criteria(locations=("VD",))
    facts = OfferFacts("Admin", location="Zürich")
    assert rules(facts, criteria) == []  # canton inconnu
    assert rules(facts, criteria, {"zurich": "ZH"}) == ["locations"]


def test_cities_only_excludes_other_known_cities() -> None:
    assert rules(OfferFacts("A", location="Zürich"), Criteria(locations=("Lausanne",))) == [
        "locations"
    ]


@pytest.mark.parametrize(("remote_ok", "excluded"), [(True, False), (False, True)])
def test_full_remote(remote_ok: bool, excluded: bool) -> None:
    facts = OfferFacts("Cloud Consultant", location="Home Office")
    criteria = Criteria(locations=("VD",), remote_ok=remote_ok)
    assert ("remote" in rules(facts, criteria)) is excluded
    # Sans lieux saisis, le télétravail n'est pas filtré.
    assert rules(facts, Criteria(remote_ok=remote_ok)) == []


@pytest.mark.parametrize(
    ("rate_min", "rate_max", "excluded"),
    [(60, 80, False), (50, 60, True), (100, 100, False), (None, None, False)],
)
def test_min_rate(rate_min: int | None, rate_max: int | None, excluded: bool) -> None:
    facts = OfferFacts("Admin", rate_min=rate_min, rate_max=rate_max)
    assert ("min_rate" in rules(facts, Criteria(min_rate=80))) is excluded


@pytest.mark.parametrize(
    ("title", "contract"),
    [
        ("Internship / Master Thesis: Quality Gate for AI-Assisted Delivery", "stage"),
        ("Wireless Software Engineer_ Intern", "stage"),
        ("Stagiaire en informatique", "stage"),
        ("Praktikum Systemtechnik", "stage"),
        ("Apprenti(e) informaticien(ne)", "apprentissage"),
        ("Ingénieur système (CDD 12 mois)", "temporaire"),
        ("Administrateur Linux \u2013 mission temporaire", "temporaire"),
    ],
)
def test_contract_types(title: str, contract: str) -> None:
    criteria = Criteria(excluded_types=tuple(ContractType))
    reasons = evaluate(OfferFacts(title), criteria).reasons
    assert [r.rule for r in reasons] == ["contract"]
    assert contract in reasons[0].message


@pytest.mark.parametrize(
    "title",
    ["Ingénieur DevOps (H/F)", "Internal Tools Engineer", "International Support Analyst"],
)
def test_contract_keywords_need_whole_words(title: str) -> None:
    assert evaluate(OfferFacts(title), Criteria(excluded_types=tuple(ContractType))).passed


def test_banned_words_ignore_case_and_accents() -> None:
    criteria = Criteria(banned_words=("Vente",))
    assert rules(OfferFacts("Conseiller de VENTE"), criteria) == ["banned_word"]
    assert rules(OfferFacts("Inventaire"), criteria) == []


@pytest.mark.parametrize(
    ("snippet", "excluded"),
    [
        ("Fliessend Deutsch und Englisch zwingend.", True),
        ("Allemand courant indispensable.", True),
        ("Fluent German (C1) required.", True),
        ("German or French is a plus.", False),
        ("Connaissances d'allemand un atout.", False),
    ],
)
def test_language_requirements(snippet: str, excluded: bool) -> None:
    facts = OfferFacts("DevOps", snippet=snippet)
    assert ("language" in rules(facts, Criteria(unspoken_languages=(Language.GERMAN,)))) is excluded


def test_several_reasons_are_all_reported() -> None:
    criteria = Criteria(locations=("VD",), excluded_types=(ContractType.INTERNSHIP,))
    reasons = evaluate(OfferFacts("Internship", location="Zürich, ZH"), criteria).reasons
    assert [r.rule for r in reasons] == ["locations", "contract"]


def test_canton_of() -> None:
    assert canton_of("Lausanne, VD") == "VD"
    assert canton_of("Zürich (ZH)") == "ZH"
    assert canton_of("Genève") is None
    assert canton_of("Home Office") is None


def test_digest_changes_with_criteria() -> None:
    assert Criteria().digest() == Criteria().digest()
    assert Criteria(min_rate=80).digest() != Criteria().digest()
