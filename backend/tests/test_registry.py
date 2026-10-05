"""Adresse des entreprises par le registre IDE (docs/12 §2.2), sans réseau."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from jobbot.api.app import create_app
from jobbot.db.models import Offer, OfferStatus
from jobbot.registry import uid
from jobbot.registry.service import Place, choose, lookup_addresses, name_key
from jobbot.registry.uid import RegistryCompany, parse_response
from jobbot.runtime import Runtime
from jobbot.settings import Settings

NOW = datetime(2026, 10, 5, 8, 0, tzinfo=UTC)


def company(
    name: str, town: str = "Genève", canton: str = "GE", active: bool = True
) -> RegistryCompany:
    return RegistryCompany(
        f"CHE{abs(hash((name, town))) % 10**9:09d}",
        name,
        "chemin de l'Exemple 10",
        "1206",
        town,
        canton,
        active,
    )


# Réponse fictive, au format du service public (une entreprise radiée).
RESPONSE = (Path(__file__).parent / "fixtures" / "registry" / "search.xml").read_text("utf-8")


def test_parse_response() -> None:
    [found] = parse_response(RESPONSE)
    assert (found.uid, found.name, found.canton) == ("CHE100000001", "Exemple & Cie SA", "GE")
    assert found.address == "Chemin de l'Exemple 10\n1206 Genève"
    assert found.active is False  # radiée du registre du commerce


def test_name_key_and_choose() -> None:
    assert name_key("Exemple & Cie SA") == name_key("EXEMPLE et Cie") == "exemple"
    holding = company("Exemple Holding SA")
    main = company("Exemple SA")
    assert choose("Exemple & Cie", [holding, main], Place("GE", "geneve")) == main
    # Deux homonymes : départagés par le canton de l'offre, sinon rien d'office.
    vaud = company("Exemple Sàrl", town="Lausanne", canton="VD")
    assert choose("Exemple", [main, vaud], Place("VD", "lausanne")) == vaud
    assert choose("Exemple", [main, vaud], Place(None, "")) is None
    assert choose("Exemple", [company("Exemple SA", active=False)], Place(None, "")) is None


@pytest.fixture
async def fresh(runtime: Runtime) -> AsyncIterator[Runtime]:
    async with runtime.engine.begin() as conn:
        await conn.execute(text("TRUNCATE offers, companies CASCADE"))
    yield runtime


async def add(rt: Runtime, n: int, name: str, **extra: object) -> int:
    async with rt.sessionmaker.begin() as session:
        offer = Offer(
            fingerprint=f"r{n}",
            title="DevOps",
            company=name,
            canton="GE",
            location="Genève",
            first_seen_at=NOW,
            last_seen_at=NOW,
            status=extra.pop("status", OfferStatus.TO_REVIEW),
            **extra,
        )
        session.add(offer)
        await session.flush()
        return offer.id


async def test_lookup_fills_and_caches(
    fresh: Runtime, monkeypatch: pytest.MonkeyPatch, no_registry_network: list[str]
) -> None:
    results = {
        "Exemple SA": [company("Exemple SA")],
        "Homonyme": [company("Homonyme SA"), company("Homonyme Sàrl")],
    }

    async def fake(name: str) -> list[RegistryCompany]:
        no_registry_network.append(name)
        return results.get(name, [])

    monkeypatch.setattr(uid, "search", fake)
    found = await add(fresh, 1, "Exemple SA")
    same = await add(fresh, 2, "Exemple sa")
    manual = await add(
        fresh, 3, "Exemple SA", company_address="Rue saisie 1", company_address_source="manual"
    )
    twins = await add(fresh, 4, "Homonyme")

    result = await lookup_addresses(fresh)
    assert (result.searched, result.found, result.ambiguous) == (2, 1, 1)
    async with fresh.sessionmaker() as session:
        offers = {i: await session.get_one(Offer, i) for i in (found, same, manual, twins)}
    assert offers[found].company_address == "Chemin de l'Exemple 10\n1206 Genève"
    assert offers[same].company_address_source == "registry"
    assert offers[manual].company_address == "Rue saisie 1"
    assert offers[twins].company_address is None

    no_registry_network.clear()
    await lookup_addresses(fresh)
    assert no_registry_network == []  # en cache


@pytest.fixture
async def api(fresh: Runtime, settings: Settings) -> AsyncIterator[AsyncClient]:
    app = create_app(settings, fresh)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


async def test_api_candidates_and_choice(
    api: AsyncClient, fresh: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Même nom, même canton, même ville : impossible à départager d'office.
    twins = [company("Homonyme SA"), company("Homonyme Sàrl")]

    async def fake(_name: str) -> list[RegistryCompany]:
        return twins

    monkeypatch.setattr(uid, "search", fake)
    first = await add(fresh, 1, "Homonyme")
    other = await add(fresh, 2, "Homonyme")
    proposals = (await api.get(f"/api/offers/{first}/address-candidates")).json()
    assert proposals["chosen_uid"] is None and len(proposals["candidates"]) == 2

    chosen = twins[1]
    response = await api.post(
        f"/api/offers/{first}/address-candidates/choose", json={"uid": chosen.uid}
    )
    assert response.json() == {
        "company_address": chosen.address,
        "company_address_source": "registry",
    }
    # Le choix vaut pour les autres offres de la même entreprise.
    assert (await api.get(f"/api/offers/{other}")).json()["company_address"] == chosen.address
    bad = await api.post(f"/api/offers/{first}/address-candidates/choose", json={"uid": "CHE0"})
    assert bad.status_code == 404
