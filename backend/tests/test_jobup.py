"""Analyseur jobup, sur de vrais e-mails anonymisés (tests/fixtures/emails)."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from jobbot.mail.anonymize import anonymize_url
from jobbot.mail.message import ParsedEmail, parse_email
from jobbot.sources.jobup import JobupParser
from jobbot.sources.registry import detect_source, find_parser

FIXTURES = Path(__file__).parent / "fixtures" / "emails"


def load(name: str) -> ParsedEmail:
    return parse_email((FIXTURES / name).read_bytes(), fallback_received=datetime.now(UTC))


@pytest.mark.parametrize(("name", "count"), [("jobup-1.eml", 5), ("jobup-2.eml", 6)])
def test_counts_and_label(name: str, count: int) -> None:
    email = load(name)
    assert isinstance(find_parser(email), JobupParser)
    assert detect_source(email).value == "jobup"
    alert = JobupParser().parse(email)
    assert len(alert.offers) == count
    assert alert.alert_label == "Recommandations jobup"


def test_offer_fields_and_neutral_link() -> None:
    first = JobupParser().parse(load("jobup-1.eml")).offers[0]
    assert first.title == "Comptable de caisse de pension (100%)"
    assert first.company == "Aon Schweiz AG, Zweigniederlassung Neuchâtel"
    assert first.location == "Neuchatel"
    assert first.external_id == "0425259b-0281-430e-aa5c-8e6ab78425d8"
    assert first.url == (
        "https://www.jobup.ch/fr/emplois/detail/0425259b-0281-430e-aa5c-8e6ab78425d8/"
    )


def test_html_entities_are_decoded() -> None:
    titles = [o.company for o in JobupParser().parse(load("jobup-1.eml")).offers]
    assert "GIAP - Groupement Intercommunal pour l'Animation Parascolaire" in titles


def test_location_without_company() -> None:
    offers = JobupParser().parse(load("jobup-2.eml")).offers
    phone = next(o for o in offers if o.title.startswith("Téléphoniste"))
    assert (phone.company, phone.location) == (None, "1020 Renens VD")


def test_company_containing_separator() -> None:
    offers = JobupParser().parse(load("jobup-2.eml")).offers
    core = next(o for o in offers if "Core DevOps" in o.title)
    assert (core.company, core.location) == ("infomaniak | The Ethical Cloud", "Geneve")


def test_anonymize_masks_jwt_but_keeps_offer_uuid() -> None:
    offer = "https://www.jobup.ch/fr/emplois/detail/0425259b-0281-430e-aa5c-8e6ab78425d8/?uid=abc"
    assert anonymize_url(offer) == (
        "https://www.jobup.ch/fr/emplois/detail/0425259b-0281-430e-aa5c-8e6ab78425d8/?uid=x"
    )
    jwt = "https://www.jobup.ch/fr/desabonner/eyJ0eXAiOiJKV1Qi.eyJ1c2VyX2lkIjoi.acx1N9sDc6wE0Sn"
    assert anonymize_url(jwt) == "https://www.jobup.ch/fr/desabonner/x"
