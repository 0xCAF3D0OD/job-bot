"""Le paiement de Plus par Payrexx (docs/125 §6). La personne accepte les conditions, passe par la
page de paiement de Payrexx, revient ; jobA1 vérifie auprès de Payrexx avant de donner Plus. Le
webhook est public (Payrexx n'a pas de session) mais signé, et ne fait que déclencher une
relecture de la transaction."""

import json
from datetime import date
from typing import Any
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from jobbot import accounts
from jobbot.billing import payrexx, service
from jobbot.db.models import User
from jobbot.log import get_logger
from jobbot.runtime import Runtime

router = APIRouter(prefix="/api/billing", tags=["billing"])
log = get_logger(__name__)


def _runtime(request: Request) -> Runtime:
    runtime: Runtime = request.app.state.runtime
    return runtime


class CheckoutIn(BaseModel):
    # La case « J'accepte les conditions d'utilisation » (docs/125 §7).
    accept_terms: bool


class CheckoutOut(BaseModel):
    link: str


class BillingState(BaseModel):
    confirmed: bool = False
    plan_until: date | None = None


async def _guest(runtime: Runtime) -> User:
    if not runtime.settings.billing_ready:
        raise HTTPException(status.HTTP_409_CONFLICT, "le paiement n'est pas encore ouvert")
    async with runtime.sessionmaker() as session:
        if await accounts.is_owner(session):
            raise HTTPException(status.HTTP_409_CONFLICT, "l'exploitant n'a pas de formule")
        user = await session.get_one(User, accounts.current())
        session.expunge(user)
        return user


@router.post("/checkout", operation_id="startCheckout")
async def start_checkout(request: Request, body: CheckoutIn) -> CheckoutOut:
    runtime = _runtime(request)
    user = await _guest(runtime)
    if not body.accept_terms:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "accepte d'abord les conditions d'utilisation"
        )
    if user.plan == "plus" and user.plan_until is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Plus t'est déjà offert")
    if (
        user.plan_until is not None
        and user.plan_until >= date.today()
        and not user.plan_cancelled_at
    ):
        raise HTTPException(status.HTTP_409_CONFLICT, "Plus est déjà payé")
    try:
        result = await service.checkout(runtime, user.id)
    except payrexx.PayrexxError as exc:
        log.warning("billing_checkout_failed", problem=str(exc))
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "la page de paiement ne s'ouvre pas, réessaie plus tard"
        ) from exc
    return CheckoutOut(link=result.link)


@router.post("/sync", operation_id="syncBilling")
async def sync_billing(request: Request) -> BillingState:
    """Au retour de la page de paiement."""
    runtime = _runtime(request)
    user = await _guest(runtime)
    try:
        confirmed = await service.sync(runtime, user.id)
    except payrexx.PayrexxError as exc:
        log.warning("billing_sync_failed", problem=str(exc))
        confirmed = False
    async with runtime.sessionmaker() as session:
        refreshed = await session.get_one(User, user.id)
        return BillingState(confirmed=confirmed, plan_until=refreshed.plan_until)


@router.post("/cancel", operation_id="cancelBilling")
async def cancel_billing(request: Request) -> BillingState:
    runtime = _runtime(request)
    user = await _guest(runtime)
    if user.plan_until is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "aucun abonnement à résilier")
    try:
        until = await service.cancel(runtime, user.id)
    except payrexx.PayrexxError as exc:
        log.warning("billing_cancel_failed", problem=str(exc))
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "la résiliation n'a pas abouti, réessaie plus tard"
        ) from exc
    return BillingState(plan_until=until)


def _transaction_id(raw: bytes, content_type: str) -> str | None:
    payload: Any
    if "json" in content_type:
        payload = json.loads(raw or b"{}")
        transaction = payload.get("transaction") if isinstance(payload, dict) else None
        tid = transaction.get("id") if isinstance(transaction, dict) else None
        return str(tid) if tid else None
    form = parse_qs(raw.decode("utf-8", "replace"))
    values = form.get("transaction[id]")
    return values[0] if values else None


@router.post("/webhook", operation_id="billingWebhook", include_in_schema=False)
async def billing_webhook(request: Request) -> dict[str, str]:
    runtime = _runtime(request)
    raw = await request.body()
    if not runtime.settings.billing_ready or not payrexx.signed(
        runtime.settings, raw, request.headers.get("x-webhook-signature")
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "signature invalide")
    try:
        transaction_id = _transaction_id(raw, request.headers.get("content-type", ""))
    except (ValueError, AttributeError):
        transaction_id = None
    # Un abonnement (résilié, échoué) n'a rien à faire ici : sans paiement, Plus s'arrête seul à
    # la fin de la période payée.
    if transaction_id:
        try:
            await service.on_transaction(runtime, transaction_id)
        except payrexx.PayrexxError as exc:
            log.warning("billing_webhook_failed", problem=str(exc))
            # Payrexx réessaiera.
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "réessayer") from exc
    return {"status": "ok"}
