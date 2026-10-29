"""Règles du filtre (core/filter.py), dont des titres réels tirés des alertes."""

import pytest

from jobbot.core.filter import (
    ContractType,
    Criteria,
    Language,
    OfferFacts,
    RemotePolicy,
    canton_of,
    evaluate,
)


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
        ("Biel/Bienne", True),  # canton connu (BE), refusé
        ("Ennetbürgen", False),  # canton inconnu : on n'écarte pas
        (None, False),  # lieu inconnu : on n'écarte pas
    ],
)
def test_locations(location: str | None, excluded: bool) -> None:
    criteria = Criteria(locations=("VD", "Genève"))
    assert ("locations" in rules(OfferFacts("Admin", location=location), criteria)) is excluded


def test_city_canton_learned_from_other_offers() -> None:
    criteria = Criteria(locations=("VD",))
    facts = OfferFacts("Admin", location="Prilly")
    assert rules(facts, criteria) == []  # canton inconnu
    assert rules(facts, criteria, {"prilly": "VD"}) == []
    assert rules(OfferFacts("Admin", location="Wil"), criteria, {"wil": "SG"}) == ["locations"]


def test_cities_only_excludes_other_known_cities() -> None:
    assert rules(OfferFacts("A", location="Zürich"), Criteria(locations=("Lausanne",))) == [
        "locations"
    ]


@pytest.mark.parametrize(
    ("policy", "excluded"),
    [
        (RemotePolicy.FROM_SWITZERLAND, False),
        (RemotePolicy.ANYWHERE, False),
        (RemotePolicy.REFUSE, True),
    ],
)
def test_full_remote(policy: RemotePolicy, excluded: bool) -> None:
    facts = OfferFacts("Cloud Consultant", location="Home Office")
    criteria = Criteria(locations=("VD",), remote_policy=policy)
    assert ("remote" in rules(facts, criteria)) is excluded
    # Sans lieux saisis, le télétravail n'est pas filtré.
    assert rules(facts, Criteria(remote_policy=policy)) == []


def test_remote_region_from_switzerland() -> None:
    """Télétravail complet réservé à d'autres pays : écarté seulement « depuis la Suisse »,
    même sans lieux saisis ; sans précision dans l'annonce, l'offre reste."""
    us_only = OfferFacts(
        "SRE", location="New York", remote="full", remote_region="US only",
        remote_from_switzerland=False,
    )  # fmt: skip
    swiss = Criteria(remote_policy=RemotePolicy.FROM_SWITZERLAND)
    assert rules(us_only, swiss) == ["remote_region"]
    assert rules(
        us_only, Criteria(locations=("VD",), remote_policy=RemotePolicy.FROM_SWITZERLAND)
    ) == ["remote_region"]
    assert rules(us_only, Criteria(remote_policy=RemotePolicy.ANYWHERE)) == []
    europe = OfferFacts("SRE", remote="full", remote_region="Europe", remote_from_switzerland=True)
    unknown = OfferFacts("SRE", location="Remote", remote_from_switzerland=None)
    hybrid = OfferFacts("SRE", location="Lausanne", remote="hybrid")
    assert rules(europe, swiss) == rules(unknown, swiss) == rules(hybrid, swiss) == []
    reason = evaluate(us_only, swiss).reasons[0].message
    assert "US only" in reason and "Suisse" in reason


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
    assert canton_of("Genève") == "GE"  # une ville connue
    assert canton_of("Sion, Valais") == "VS"
    assert canton_of("Ennetbürgen") is None
    assert canton_of("Home Office") is None


def test_digest_changes_with_criteria() -> None:
    assert Criteria().digest() == Criteria().digest()
    assert Criteria(min_rate=80).digest() != Criteria().digest()


# --- Bug du 2026-10-29 : 277 offres sur 576 écartées « pour lieu » (Effet des critères) ---


@pytest.mark.parametrize(
    ("wanted", "location"),
    [
        ("bern", "Berne"),
        ("bern", "Bern"),
        ("Berne", "Bern, BE"),
        ("BE", "Berne"),
        ("BE", "Thun"),
        ("BE", "Biel/Bienne"),
        ("zurich", "Zürich"),
        ("zurich", "Zuerich"),
        ("Zürich", "Zurich"),
        ("ZH", "Zürich"),
        ("ZH", "Winterthur"),
        ("zurich", "Zurich 80" + chr(0x2013) + "100 %"),  # tiret demi-cadratin
        ("zurich", "Zürich 80-100%"),
        ("bern", "Berne, Suisse 80-100%"),
        ("bern", "3011 Bern, Schweiz"),
        ("Genève", "Genf"),
        ("geneve", "Genève (GE)"),
        ("Bienne", "Biel"),
        ("Valais", "Sion"),
        ("Wallis", "Sierre, VS"),
        ("VS", "Sion, Valais"),
        ("GE", "Geneva, Switzerland"),
        ("Lausanne", "Lausanne, Vaud, Suisse"),
    ],
)
def test_location_variants_are_accepted(wanted: str, location: str) -> None:
    """Chaque variante de langue, d'abréviation et de texte parasite est reconnue."""
    assert rules(OfferFacts("Admin", location=location), Criteria(locations=(wanted,))) == []


@pytest.mark.parametrize(
    ("wanted", "location"),
    [("bern", "Zurich 80-100 %"), ("ZH", "Berne, Suisse"), ("Lausanne", "Genf")],
)
def test_other_places_stay_excluded(wanted: str, location: str) -> None:
    assert rules(OfferFacts("Admin", location=location), Criteria(locations=(wanted,))) == [
        "locations"
    ]


def test_full_remote_open_from_switzerland_is_never_excluded_for_place() -> None:
    """Télétravail complet ouvert depuis la Suisse : jamais écarté pour le lieu."""
    criteria = Criteria(locations=("bern",), remote_policy=RemotePolicy.FROM_SWITZERLAND)
    facts = OfferFacts("Admin", location="Zurich", remote="full", remote_from_switzerland=True)
    assert rules(facts, criteria) == []
    unknown = OfferFacts("Admin", location="Berlin", remote="full", remote_from_switzerland=None)
    assert rules(unknown, criteria) == []


@pytest.mark.parametrize(
    ("wanted", "location"),
    [
        ("geneve", "Meyrin, GE"),
        ("zurich", "Winterthur"),
        ("Berne", "Thun"),
        ("fribourg", "Bulle, FR"),
    ],
)
def test_capital_name_means_its_whole_canton(wanted: str, location: str) -> None:
    """Un chef-lieu qui nomme son canton vaut le canton entier : un canton comprend ses communes."""
    assert rules(OfferFacts("Admin", location=location), Criteria(locations=(wanted,))) == []
