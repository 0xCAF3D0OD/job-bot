"""Plus payé (docs/125 §6) : la page de paiement, la confirmation, le renouvellement, la
résiliation. Un paiement confirmé donne Plus jusqu'au même jour du mois suivant, plus 3 jours
de grâce (un renouvellement peut arriver un peu après) ; résilier garde Plus jusqu'à cette date.
On ne croit que l'API de Payrexx : un webhook déclenche une relecture, jamais une décision."""

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobbot import accounts, plans
from jobbot.billing import payrexx
from jobbot.db.models import Payment, User
from jobbot.log import get_logger
from jobbot.runtime import Runtime

log = get_logger(__name__)

GRACE = timedelta(days=3)
REFERENCE = re.compile(r"^jobA1-plus-(\d+)$")


def reference(user_id: int) -> str:
    return f"jobA1-plus-{user_id}"


def account_of(ref: str | None) -> int | None:
    match = REFERENCE.match(ref or "")
    return int(match.group(1)) if match else None


def next_month(day: date) -> date:
    """Le même jour du mois suivant (le 31 janvier donne le 28 ou 29 février)."""
    year, month = (day.year + 1, 1) if day.month == 12 else (day.year, day.month + 1)
    for last in (day.day, 30, 29, 28):
        try:
            return date(year, month, last)
        except ValueError:
            continue
    raise AssertionError("jour impossible")


async def grant(session: AsyncSession, user: User, paid_on: date) -> None:
    """Plus, jusqu'au mois suivant (et la grâce) ; une date plus lointaine reste."""
    until = next_month(paid_on) + GRACE
    user.plan = plans.PLUS
    user.plan_until = max(until, user.plan_until) if user.plan_until else until


@dataclass(frozen=True)
class Checkout:
    link: str


async def checkout(runtime: Runtime, user_id: int) -> Checkout:
    settings = runtime.settings
    back = f"{settings.public_url.rstrip('/')}/reglages?rubrique=compte"
    gateway_id, link = await payrexx.create_gateway(
        settings, reference=reference(user_id), back=back
    )
    async with runtime.sessionmaker.begin() as session:
        user = await session.get_one(User, user_id)
        user.billing_gateway_id = gateway_id
    log.info("billing_checkout", account=user_id, gateway=gateway_id)
    return Checkout(link=link)


async def sync(runtime: Runtime, user_id: int) -> bool:
    """Au retour de la page de paiement : si Payrexx confirme, Plus tout de suite (sans attendre
    le webhook). Vrai si le paiement est confirmé."""
    async with runtime.sessionmaker() as session:
        gateway_id = await session.scalar(select(User.billing_gateway_id).where(User.id == user_id))
    if not gateway_id:
        return False
    status = await payrexx.gateway_status(runtime.settings, gateway_id)
    if status != "confirmed":
        return False
    async with runtime.sessionmaker.begin() as session:
        user = await session.get_one(User, user_id)
        await grant(session, user, datetime.now(UTC).date())
        user.plan_cancelled_at = None
    log.info("billing_confirmed", account=user_id, gateway=gateway_id)
    return True


def _subscription_id(data: dict[str, object]) -> str | None:
    sub = data.get("subscription")
    if isinstance(sub, dict) and sub.get("id"):
        return str(sub["id"])
    if isinstance(sub, (int, str)) and str(sub):
        return str(sub)
    return None


async def on_transaction(runtime: Runtime, transaction_id: str) -> int | None:
    """Une transaction annoncée par un webhook : relue auprès de Payrexx ; confirmée et à nous,
    elle donne (ou prolonge) Plus et s'inscrit dans les paiements. Rend le compte concerné."""
    data = await payrexx.transaction(runtime.settings, transaction_id)
    user_id = account_of(str(data.get("referenceId") or ""))
    if user_id is None or data.get("status") != "confirmed":
        log.info(
            "billing_transaction_ignored", transaction=transaction_id, status=data.get("status")
        )
        return None
    amount = int(data.get("amount") or 0)
    raw_time = str(data.get("time") or "")
    try:
        paid_on = datetime.strptime(raw_time[:10], "%Y-%m-%d").date()
    except ValueError:
        paid_on = datetime.now(UTC).date()
    with accounts.use(user_id):
        async with runtime.sessionmaker.begin() as session:
            user = await session.get(User, user_id)
            if user is None:
                return None
            await grant(session, user, paid_on)
            if sub := _subscription_id(data):
                user.billing_subscription_id = sub
            await session.execute(
                insert(Payment)
                .values(
                    provider_ref=f"transaction-{transaction_id}",
                    amount_cents=amount,
                    currency=str((data.get("invoice") or {}).get("currencyAlpha3") or "CHF")
                    if isinstance(data.get("invoice"), dict)
                    else "CHF",
                    paid_on=paid_on,
                )
                .on_conflict_do_nothing(index_elements=["user_id", "provider_ref"])
            )
    log.info("billing_paid", account=user_id, transaction=transaction_id)
    return user_id


async def cancel(runtime: Runtime, user_id: int) -> date | None:
    """Résilier : plus de renouvellement ; Plus jusqu'à la fin de la période payée."""
    async with runtime.sessionmaker() as session:
        user = await session.get_one(User, user_id)
        subscription_id = user.billing_subscription_id
    if subscription_id:
        await payrexx.cancel_subscription(runtime.settings, subscription_id)
    async with runtime.sessionmaker.begin() as session:
        user = await session.get_one(User, user_id)
        user.plan_cancelled_at = datetime.now(UTC)
        until = user.plan_until
    log.info("billing_cancelled", account=user_id, subscription=subscription_id)
    return until
