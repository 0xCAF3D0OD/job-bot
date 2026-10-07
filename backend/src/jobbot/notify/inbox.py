"""Alertes de la cloche (docs/15 §1) : collecte en échec, nettoyage, lecture."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select

from jobbot.db.models import Notification
from jobbot.mail.imap import MailboxError
from jobbot.notify import service as notify
from jobbot.runtime import Runtime

KEEP_FOR = timedelta(days=90)
# Une collecte qui échoue toutes les 2 heures ne doit pas remplir la cloche.
COLLECT_ALERT_EVERY = timedelta(hours=6)
_REASONS = {
    "auth": "Gmail refuse la connexion : vérifie l'adresse et le mot de passe d'application.",
    "connection": "Gmail est injoignable (réseau), ou le libellé configuré est introuvable.",
}


async def collect_failed(runtime: Runtime, exc: BaseException) -> bool:
    """Alerte « collecte en échec », au plus une toutes les 6 heures. Jamais de secret."""
    since = datetime.now(UTC) - COLLECT_ALERT_EVERY
    async with runtime.sessionmaker() as session:
        recent = await session.scalar(
            select(Notification.id).where(
                Notification.kind == "collect_failed", Notification.created_at > since
            )
        )
    if recent:
        return False
    kind = getattr(exc, "kind", "") if isinstance(exc, MailboxError) else ""
    reason = _REASONS.get(
        kind, f"Erreur inattendue ({type(exc).__name__}) : voir l'état technique."
    )
    await notify.deliver(
        runtime,
        notify.Message(
            title="La collecte des alertes a échoué",
            message=reason,
            priority=4,
            tags=["warning"],
            click=f"{runtime.settings.public_url.rstrip('/')}/reglages/diagnostic",
        ),
        kind="collect_failed",
        link="/reglages/diagnostic",
    )
    return True


async def purge(runtime: Runtime) -> int:
    async with runtime.sessionmaker.begin() as session:
        result = await session.execute(
            delete(Notification).where(Notification.created_at < datetime.now(UTC) - KEEP_FOR)
        )
        return int(getattr(result, "rowcount", 0) or 0)
