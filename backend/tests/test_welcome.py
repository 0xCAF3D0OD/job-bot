"""L'accueil après la première connexion (docs/66 §4) : seulement les nouveaux comptes, reprise
là où on s'est arrêté, le métier dans « Mon domaine »."""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from jobbot import accounts, welcome
from jobbot.api.app import create_app
from jobbot.auth import passwords
from jobbot.collect import public_search
from jobbot.db.models import User
from jobbot.news import domain
from jobbot.runtime import Runtime

from .conftest import make_settings

PASSWORD = "un-mot-de-passe-solide"


@pytest.fixture
async def secured() -> AsyncIterator[Runtime]:
    runtime = Runtime.create(make_settings(auth_enabled=True, public_search_enabled=True))
    yield runtime
    async with runtime.engine.begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE username = 'camille-accueil'"))
    await runtime.dispose()


async def test_new_account_goes_through_welcome(
    secured: Runtime, runtime: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    queued: list[str] = []

    async def enqueue(_settings: object, name: str) -> bool:
        queued.append(name)
        return True

    monkeypatch.setattr(public_search, "enqueue", enqueue)
    async with secured.sessionmaker.begin() as session:
        user = User(username="camille-accueil", password_hash=passwords.hash_password(PASSWORD))
        session.add(user)
        await session.flush()
        camille = user.id
    app = create_app(secured.settings, secured)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as api:
        await api.post(
            "/api/auth/login", json={"username": "camille-accueil", "password": PASSWORD}
        )
        assert (await api.get("/api/auth/me")).json()["welcome"] == "pending"
        assert (await api.get("/api/welcome")).json() == {
            "status": "pending",
            "step": 1,
            "goal": None,
            "trade": None,
            "roles": [],
        }
        saved = await api.put(
            "/api/welcome", json={"goal": "orp", "trade": "Infirmière", "step": 3}
        )
        assert saved.json() == {
            "status": "pending",
            "step": 3,
            "goal": "orp",
            "trade": "Infirmière",
            "roles": [],
        }
        # « Plus tard » : plus d'envoi forcé vers l'accueil, mais pas fini.
        later = (await api.put("/api/welcome", json={"postponed": True})).json()
        assert later["status"] == "postponed" and later["step"] == 3
        assert (await api.get("/api/auth/me")).json()["welcome"] == "postponed"
        done = (await api.put("/api/welcome", json={"done": True})).json()
        assert done["status"] == "done"
        # Les premières offres (docs/104, 0.80.0) : la recherche publique, une seule fois.
        assert queued == ["first_offers"]
        first = (await api.get("/api/alert-searches/first-offers")).json()
        assert first["status"] == "queued"
        await api.put("/api/welcome", json={"done": True})
        assert queued == ["first_offers"]
    # Le métier est le premier mot de « Mon domaine » (Actualités, alertes proposées).
    with accounts.use(camille):
        async with secured.sessionmaker() as session:
            assert (await domain.keywords(session))[0] == "Infirmière"
    # Changer de métier à l'accueil remplace l'ancien, sans toucher aux mots ajoutés ailleurs
    # (docs/69 §1).
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as api:
        await api.post(
            "/api/auth/login", json={"username": "camille-accueil", "password": PASSWORD}
        )
        current = (await api.get("/api/news/preferences")).json()
        words = current["domain_keywords"] + ["soins palliatifs"]
        await api.put("/api/news/preferences", json={**current, "domain_keywords": words})
        await api.put("/api/welcome", json={"trade": "Aide-soignante"})
    with accounts.use(camille):
        async with secured.sessionmaker() as session:
            kept = await domain.keywords(session)
    assert kept[0] == "Aide-soignante" and "Infirmière" not in kept
    assert "soins palliatifs" in kept
    # L'exploitant ne le voit jamais.
    async with AsyncClient(
        transport=ASGITransport(app=create_app(runtime.settings, runtime)), base_url="http://test"
    ) as owner:
        assert (await owner.get("/api/welcome")).json()["status"] == "done"


async def test_first_offers_caught_up_for_older_accounts(
    secured: Runtime, runtime: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0.80.1 : un accueil fini avant la 0.80.0 ; la recherche part à la première visite."""
    queued: list[str] = []

    async def enqueue(_settings: object, name: str) -> bool:
        queued.append(name)
        return True

    monkeypatch.setattr(public_search, "enqueue", enqueue)
    async with secured.sessionmaker.begin() as session:
        user = User(username="camille-accueil", password_hash=passwords.hash_password(PASSWORD))
        session.add(user)
        await session.flush()
        camille = user.id
    app = create_app(secured.settings, secured)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as api:
        await api.post(
            "/api/auth/login", json={"username": "camille-accueil", "password": PASSWORD}
        )
        await api.put("/api/welcome", json={"trade": "Pâtissier"})
        # Fini avant la 0.80.0 : l'accueil est « done », sans recherche faite.
        with accounts.use(camille):
            async with secured.sessionmaker.begin() as session:
                await welcome.save(session, {"done": True})
        first = (await api.get("/api/alert-searches/first-offers")).json()
        assert first["status"] == "queued" and queued == ["first_offers"]
        await api.get("/api/alert-searches/first-offers")
        assert queued == ["first_offers"]
    # L'exploitant n'est pas concerné.
    async with AsyncClient(
        transport=ASGITransport(app=create_app(runtime.settings, runtime)), base_url="http://test"
    ) as owner:
        assert (await owner.get("/api/alert-searches/first-offers")).json()["status"] in (
            "none",
            "done",
            "failed",
            "no_trade",
            "disabled",
        )
    assert queued == ["first_offers"]
