"""Adresse cherchée sur Internet par l'IA, en dernier recours (docs/12, 0.7.2). Sans réseau."""

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text, update

from jobbot.api.app import create_app
from jobbot.db.models import Company, LlmCall, Offer, OfferStatus, Setting
from jobbot.llm.client import RawResult
from jobbot.llm.pricing import Usage, cost_usd
from jobbot.registry import web
from jobbot.registry.service import lookup_addresses
from jobbot.runtime import Runtime
from jobbot.scoring import service as scoring

from .conftest import make_settings

NOW = datetime(2026, 10, 5, 8, 0, tzinfo=UTC)
FOUND = (
    "D'après la page contact :\n<reponse>"
    + json.dumps(
        {
            "found": True,
            "street": "Rue de l'Exemple 3",
            "postcode": "1003",
            "town": "Lausanne",
            "source_url": "https://exemple.ch/contact",
        }
    )
    + "</reponse>"
)


def test_parse_answer() -> None:
    found = web.parse_answer(FOUND)
    assert found is not None and found.address == "Rue de l'Exemple 3\n1003 Lausanne"
    assert web.parse_answer('<reponse>{"found": false}</reponse>') is None
    assert web.parse_answer("pas de balise") is None
    bad_postcode = FOUND.replace('"1003"', '"75008"')
    assert web.parse_answer(bad_postcode) is None
    assert web.parse_answer(FOUND.replace("https://", "http://")) is None


def test_request_params_and_cost() -> None:
    params = web.request_params("Exemple <SA>", "Lausanne")
    assert params["model"] == "claude-haiku-4-5"
    assert params["messages"][0]["content"] == (
        "<entreprise>Exemple SA</entreprise>\n<ville>Lausanne</ville>"
    )
    assert params["tools"][0]["type"] == "web_search_20250305"
    assert params["tools"][0]["max_uses"] == 2
    assert "output_config" not in params
    base = cost_usd("claude-opus-5", Usage(1000, 0, 0, 100))
    assert cost_usd("claude-opus-5", Usage(1000, 0, 0, 100, web_searches=2)) == base + Decimal(
        "0.02"
    )


class FakeClient:
    def __init__(self, text: str) -> None:
        self.text = text
        self.calls: list[dict[str, Any]] = []

    async def score(self, params: dict[str, Any]) -> RawResult:
        self.calls.append(params)
        return RawResult(
            self.text, "claude-opus-5", Usage(2000, 0, 0, 300, web_searches=1), "end_turn"
        )


@pytest.fixture
async def rt() -> AsyncIterator[Runtime]:
    runtime = Runtime.create(make_settings(anthropic_api_key="sk-test"))
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE offers, companies, llm_calls CASCADE"))
    yield runtime
    async with runtime.sessionmaker.begin() as session:
        await session.execute(
            update(Setting).where(Setting.key == "llm_monthly_budget_chf").values(value=10)
        )
    await runtime.dispose()


async def add(rt: Runtime, n: int, company: str, **extra: object) -> int:
    async with rt.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint=f"w{n}",
            title="DevOps",
            company=company,
            location="Lausanne, VD",
            canton="VD",
            first_seen_at=NOW,
            last_seen_at=NOW,
            status=OfferStatus.TO_REVIEW,
            **extra,
        )
        session.add(offer)
        await session.flush()
        return offer.id


async def test_web_fallback_in_lookup(rt: Runtime, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeClient(FOUND)
    monkeypatch.setattr(scoring, "make_client", lambda _settings: fake)
    first = await add(rt, 1, "Exemple Group")
    letter = await add(
        rt,
        2,
        "Exemple Group",
        company_address="Ancienne 1\n1000 Lausanne",
        company_address_source="letter",
    )
    result = await lookup_addresses(rt)
    assert (result.web_searched, result.web_found) == (1, 1)
    assert len(fake.calls) == 1  # une seule fois pour l'entreprise
    async with rt.sessionmaker() as session:
        for offer_id in (first, letter):
            offer = await session.get_one(Offer, offer_id)
            assert offer.company_address == "Rue de l'Exemple 3\n1003 Lausanne"
            assert (offer.company_address_source, offer.company_address_url) == (
                "web",
                "https://exemple.ch/contact",
            )
        assert list(await session.scalars(select(LlmCall.purpose))) == ["address"]
        company = await session.get_one(Company, "exemple group")
        assert company.chosen_by == "web"

    await lookup_addresses(rt)
    assert len(fake.calls) == 1  # en cache


async def test_web_nothing_found_and_budget(rt: Runtime, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeClient('<reponse>{"found": false}</reponse>')
    monkeypatch.setattr(scoring, "make_client", lambda _settings: fake)
    offer_id = await add(rt, 1, "Inconnue SA")
    await lookup_addresses(rt)
    async with rt.sessionmaker() as session:
        assert (await session.get_one(Offer, offer_id)).company_address is None
        assert (await session.get_one(Company, "inconnue")).web_looked_up_at is not None

    async with rt.sessionmaker.begin() as session:
        await session.execute(
            update(Setting).where(Setting.key == "llm_monthly_budget_chf").values(value=0)
        )
    await add(rt, 2, "Autre SA")
    result = await lookup_addresses(rt)
    assert result.web_searched == 0 and len(fake.calls) == 1  # plafond atteint : rien


async def test_endpoint_returns_web_address(rt: Runtime, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scoring, "make_client", lambda _settings: FakeClient(FOUND))
    offer_id = await add(rt, 1, "Exemple Group")
    app = create_app(rt.settings, rt)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
        body = (await api.get(f"/api/offers/{offer_id}/address-candidates")).json()
        assert body["web_address"] == "Rue de l'Exemple 3\n1003 Lausanne"
        assert body["web_source_url"] == "https://exemple.ch/contact"
        offer = (await api.get(f"/api/offers/{offer_id}")).json()
        assert offer["company_address_source"] == "web"
