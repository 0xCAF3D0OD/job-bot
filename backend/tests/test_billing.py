"""Le paiement de Plus (docs/125 §6) : la page de paiement, la confirmation au retour, le webhook
signé qui ne fait que relire la transaction, le renouvellement, la résiliation."""

import hashlib
import hmac
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from jobbot import accounts, plans
from jobbot.api.app import create_app
from jobbot.auth import passwords
from jobbot.billing import payrexx, service
from jobbot.db.models import Payment, User
from jobbot.runtime import Runtime

from .conftest import admin_engine, make_settings

PASSWORD = "un-mot-de-passe-solide"
NAME = "noa-plus"
KEY = "cle-de-signature"


@pytest.fixture
async def guest() -> AsyncIterator[tuple[Runtime, int]]:
    runtime = Runtime.create(
        make_settings(
            auth_enabled=True,
            billing_enabled=True,
            payrexx_instance="jobA1",
            payrexx_api_secret="secret",
            payrexx_webhook_key=KEY,
        )
    )
    async with runtime.sessionmaker.begin() as session:
        user = User(username=NAME, password_hash=passwords.hash_password(PASSWORD))
        session.add(user)
        await session.flush()
        user_id = user.id
    yield runtime, user_id
    async with admin_engine().begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE id = :u"), {"u": user_id})
    await runtime.dispose()


@asynccontextmanager
async def logged_in(runtime: Runtime) -> AsyncIterator[AsyncClient]:
    app = create_app(runtime.settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as api:
        await api.post("/api/auth/login", json={"username": NAME, "password": PASSWORD})
        yield api


def test_next_month() -> None:
    assert service.next_month(date(2026, 1, 31)) == date(2026, 2, 28)
    assert service.next_month(date(2026, 12, 15)) == date(2027, 1, 15)
    assert service.account_of("jobA1-plus-42") == 42
    assert service.account_of("ORDER-42") is None


async def test_checkout_then_confirmed_on_return(
    guest: tuple[Runtime, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime, user_id = guest
    seen: dict[str, Any] = {}

    async def create_gateway(_s: Any, *, reference: str, back: str) -> tuple[str, str]:
        seen.update(reference=reference, back=back)
        return "77", "https://jobA1.payrexx.com/?payment=abc"

    async def gateway_status(_s: Any, gateway_id: str) -> str:
        return "confirmed" if gateway_id == "77" else "waiting"

    monkeypatch.setattr(payrexx, "create_gateway", create_gateway)
    monkeypatch.setattr(payrexx, "gateway_status", gateway_status)
    async with logged_in(runtime) as api:
        # Les conditions d'abord.
        refused = await api.post("/api/billing/checkout", json={"accept_terms": False})
        assert refused.status_code == 422
        started = await api.post("/api/billing/checkout", json={"accept_terms": True})
        assert started.json() == {"link": "https://jobA1.payrexx.com/?payment=abc"}
        assert seen["reference"] == f"jobA1-plus-{user_id}"
        assert seen["back"].endswith("/reglages?rubrique=compte")
        back = (await api.post("/api/billing/sync")).json()
        assert back["confirmed"] is True
        expected = service.next_month(datetime.now(UTC).date()) + service.GRACE
        assert back["plan_until"] == expected.isoformat()
        seen_plan = (await api.get("/api/plan")).json()
        assert seen_plan["plan"] == "plus" and seen_plan["billing_available"] is True
        # Déjà payé : pas de seconde page de paiement.
        again = await api.post("/api/billing/checkout", json={"accept_terms": True})
        assert again.status_code == 409


async def test_webhook_is_signed_and_only_triggers_a_reread(
    guest: tuple[Runtime, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime, user_id = guest
    asked: list[str] = []

    async def transaction(_s: Any, transaction_id: str) -> dict[str, Any]:
        asked.append(transaction_id)
        reference = f"jobA1-plus-{user_id}" if transaction_id == "55" else "AUTRE-1"
        return {
            "id": transaction_id,
            "status": "confirmed",
            "referenceId": reference,
            "amount": 700,
            "time": "2026-10-22 10:00:00",
            "subscription": {"id": 9},
            "invoice": {"currencyAlpha3": "CHF"},
        }

    cancelled: list[str] = []

    async def cancel_subscription(_s: Any, subscription_id: str) -> None:
        cancelled.append(subscription_id)

    monkeypatch.setattr(payrexx, "transaction", transaction)
    monkeypatch.setattr(payrexx, "cancel_subscription", cancel_subscription)
    app = create_app(runtime.settings, runtime)
    # Le contenu d'un webhook n'est jamais cru : seul l'identifiant sert, puis l'API est relue.
    body = json.dumps({"transaction": {"id": 55, "status": "confirmed"}}).encode()
    good = hmac.new(KEY.encode(), body, hashlib.sha256).hexdigest()
    headers = {"content-type": "application/json"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as hook:
        forged = await hook.post(
            "/api/billing/webhook",
            content=body,
            headers={**headers, "x-webhook-signature": "0" * 64},
        )
        assert forged.status_code == 401 and asked == []
        for _ in range(2):
            ok = await hook.post(
                "/api/billing/webhook",
                content=body,
                headers={**headers, "x-webhook-signature": good},
            )
            assert ok.status_code == 200
        other = json.dumps({"transaction": {"id": 56}}).encode()
        sign = hmac.new(KEY.encode(), other, hashlib.sha256).hexdigest()
        await hook.post(
            "/api/billing/webhook", content=other, headers={**headers, "x-webhook-signature": sign}
        )
    assert asked == ["55", "55", "56"]
    with accounts.use(user_id):
        async with runtime.sessionmaker() as session:
            payments = list(await session.scalars(select(Payment)))
            user = await session.get_one(User, user_id)
            assert [(p.amount_cents, p.paid_on) for p in payments] == [(700, date(2026, 10, 22))]
            assert user.billing_subscription_id == "9"
            assert user.plan_until == date(2026, 11, 25)
            # Après la période payée et sans renouvellement : Essentiel.
            assert await plans.plan_of(session, date(2026, 11, 25)) == plans.PLUS
            assert await plans.plan_of(session, date(2026, 11, 26)) == plans.ESSENTIEL
    # Résilier : plus de renouvellement chez Payrexx, Plus jusqu'au bout de la période.
    async with logged_in(runtime) as api:
        result = (await api.post("/api/billing/cancel")).json()
        assert result["plan_until"] == "2026-11-25"
        state = (await api.get("/api/plan")).json()
        assert state["cancelled"] is True and state["payments"][0]["amount_cents"] == 700
    assert cancelled == ["9"]


async def test_no_payment_until_enabled() -> None:
    runtime = Runtime.create(make_settings())
    app = create_app(runtime.settings, runtime)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as api:
        assert (
            await api.post("/api/billing/checkout", json={"accept_terms": True})
        ).status_code == 409
        assert (await api.get("/api/plan")).json()["billing_available"] is False
        assert (await api.post("/api/billing/webhook", content=b"{}")).status_code == 401
    await runtime.dispose()
