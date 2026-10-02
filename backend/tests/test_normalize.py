import pytest

from jobbot.core.normalize import (
    normalize_company,
    normalize_location,
    normalize_offer,
    normalize_text,
    normalize_title,
    parse_rate,
)


def test_normalize_text() -> None:
    assert normalize_text("  Ingénieur Système — Zürich!  ") == "ingenieur systeme zurich"


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Ingénieur système (h/f) 80-100%", "ingenieur systeme"),
        ("Ingénieur système H/F", "ingenieur systeme"),
        ("Systemtechniker (m/w/d) 100 %", "systemtechniker"),
        ("Systemtechniker w/m/d", "systemtechniker"),
        ("Informatiker/-in EFZ", "informatiker efz"),
        ("Informatiker/in EFZ", "informatiker efz"),
        ("Informatiker:in EFZ", "informatiker efz"),
        ("Informatiker*in EFZ", "informatiker efz"),
        ("Ingénieur·e DevOps", "ingenieur devops"),
        ("Collaborateur(trice) administratif(ve)", "collaborateur administratif"),
        ("Employé(e) de commerce 60 à 80%", "employe de commerce"),
        ("DevOps Engineer (f/m/x) \u2013 80% - 100%", "devops engineer"),
    ],
)
def test_normalize_title(title: str, expected: str) -> None:
    assert normalize_title(title) == expected


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Admin 80-100%", (80, 100)),
        ("Admin 80 % - 100 %", (80, 100)),
        ("Admin 80 à 100%", (80, 100)),
        ("Admin 60 bis 80 %", (60, 80)),
        ("Admin 100%", (100, 100)),
        ("Admin 100\u201380%", (80, 100)),
        ("Admin", (None, None)),
        ("Admin 150%", (None, None)),
        ("Admin 2024", (None, None)),
    ],
)
def test_parse_rate(title: str, expected: tuple[int | None, int | None]) -> None:
    assert parse_rate(title) == expected


@pytest.mark.parametrize(
    ("company", "expected"),
    [
        ("Swisscom (Suisse) SA", "swisscom suisse"),
        ("Acme S.A.", "acme"),
        ("Acme Sàrl", "acme"),
        ("Acme S.à r.l.", "acme"),
        ("Muster AG", "muster"),
        ("Muster GmbH", "muster"),
        ("SA", "sa"),
        (None, ""),
    ],
)
def test_normalize_company(company: str | None, expected: str) -> None:
    assert normalize_company(company) == expected


@pytest.mark.parametrize(
    ("location", "expected"),
    [
        ("1003 Lausanne", "lausanne"),
        ("Lausanne, VD", "lausanne"),
        ("Lausanne VD", "lausanne"),
        ("Zürich (ZH)", "zurich"),
        ("8005 Zürich", "zurich"),
        ("Genève / Télétravail", "geneve"),
        ("La Chaux-de-Fonds", "la chaux de fonds"),
        (None, ""),
    ],
)
def test_normalize_location(location: str | None, expected: str) -> None:
    assert normalize_location(location) == expected


SAME = [
    (
        ("Ingénieur système (h/f) 80-100%", "Acme SA", "1003 Lausanne"),
        ("Ingenieur Systeme H/F", "ACME", "Lausanne, VD"),
    ),
    (
        ("Systemtechniker (m/w/d) 100%", "Muster AG", "8005 Zürich"),
        ("Systemtechniker w/m/d", "Muster AG", "Zürich (ZH)"),
    ),
]
DIFFERENT = [
    (
        ("Ingénieur système", "Acme SA", "Lausanne"),
        ("Ingénieur réseau", "Acme SA", "Lausanne"),
    ),
    (
        ("Ingénieur système", "Acme SA", "Lausanne"),
        ("Ingénieur système", "Acme SA", "Genève"),
    ),
    (
        ("Ingénieur système", "Acme SA", "Lausanne"),
        ("Ingénieur système", "Globex SA", "Lausanne"),
    ),
]


@pytest.mark.parametrize(("a", "b"), SAME)
def test_same_offer_same_fingerprint(a: tuple[str, str, str], b: tuple[str, str, str]) -> None:
    assert normalize_offer(*a).fingerprint == normalize_offer(*b).fingerprint


@pytest.mark.parametrize(("a", "b"), DIFFERENT)
def test_different_offers_different_fingerprint(
    a: tuple[str, str, str], b: tuple[str, str, str]
) -> None:
    assert normalize_offer(*a).fingerprint != normalize_offer(*b).fingerprint


def test_normalized_offer_keeps_rate() -> None:
    offer = normalize_offer("Admin 80-100%", None, None)
    assert (offer.rate_min, offer.rate_max) == (80, 100)
