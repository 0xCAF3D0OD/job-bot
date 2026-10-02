"""Analyseur Indeed, sur de vraies alertes anonymisées (tests/fixtures/emails)."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from jobbot.mail.anonymize import anonymize_url
from jobbot.mail.message import ParsedEmail, parse_email
from jobbot.sources.indeed import IndeedParser
from jobbot.sources.registry import detect_source, find_parser

FIXTURES = Path(__file__).parent / "fixtures" / "emails"


def load(name: str) -> ParsedEmail:
    raw = (FIXTURES / name).read_bytes()
    return parse_email(raw, fallback_received=datetime.now(UTC))


@pytest.mark.parametrize(
    ("name", "count", "label"),
    [
        ("indeed-1.eml", 6, "platform engineer · Lausanne, VD"),
        ("indeed-2.eml", 1, "platform engineer · Lausanne, VD"),
        ("indeed-3.eml", 21, "devops"),
    ],
)
def test_counts_and_label(name: str, count: int, label: str) -> None:
    email = load(name)
    assert isinstance(find_parser(email), IndeedParser)
    assert detect_source(email).value == "indeed"
    alert = IndeedParser().parse(email)
    assert len(alert.offers) == count
    assert alert.alert_label == label


def test_offer_fields() -> None:
    first = IndeedParser().parse(load("indeed-1.eml")).offers[0]
    assert first.title == "Technical Customer Support Engineer"
    assert (first.company, first.location) == ("Flybotix", "Renens, VD")
    assert first.external_id == "321791861a57b58e"
    assert first.url == "https://ch.indeed.com/viewjob?jk=321791861a57b58e"
    assert first.snippet and "il y a" not in first.snippet


def test_every_offer_is_complete_and_links_are_neutral() -> None:
    for name in ("indeed-1.eml", "indeed-2.eml", "indeed-3.eml"):
        for offer in IndeedParser().parse(load(name)).offers:
            assert offer.title and offer.company and offer.location
            if offer.external_id:
                # Lien reconstruit : aucun jeton de suivi du compte.
                assert offer.url == f"https://ch.indeed.com/viewjob?jk={offer.external_id}"


def test_sponsored_offers_have_no_job_key() -> None:
    offers = IndeedParser().parse(load("indeed-3.eml")).offers
    sponsored = [o for o in offers if o.external_id is None]
    assert [o.title for o in sponsored] == [
        "Sr. Delivery Consultant \u2013 AI ML, Professional Services, AWSI HCLS",
        "Senior Python Full Stack Developer",
        "Senior Software & Platform Engineer \u2013 Risk Modeling Platform",
    ]
    assert all("/pagead/" in o.url for o in sponsored)


def test_company_with_dash_keeps_location() -> None:
    from jobbot.sources.indeed import _company_location

    assert _company_location("Hewlett-Packard - Meyrin - Genève, GE") == (
        "Hewlett-Packard - Meyrin",
        "Genève, GE",
    )
    assert _company_location("Sans lieu") == ("Sans lieu", None)


def test_anonymize_url_keeps_only_useful_parameters() -> None:
    url = "https://ch.indeed.com/rc/clk/dl?jk=abc&tk=SECRET&alid=ID123&q=devops"
    assert anonymize_url(url) == "https://ch.indeed.com/rc/clk/dl?jk=abc&tk=x&alid=x&q=devops"
    assert anonymize_url("https://x.indeed.com/v3/H4sIAAAAAAAA_z2MQQ6DIBBF7z") == (
        "https://x.indeed.com/v3/x"
    )


def test_fixtures_contain_no_personal_data() -> None:
    for path in FIXTURES.glob("*.eml"):
        text = path.read_text(errors="replace")
        assert "Delivered-To" not in text and "Received:" not in text
        assert "To: alertes@example.com" in text
