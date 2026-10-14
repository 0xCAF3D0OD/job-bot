"""Alertes de la cloche (docs/15 §1) : collecte en échec, nettoyage, lecture."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, update

from jobbot.db.models import JobRun, JobRunStatus, Notification
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


COLLECT_JOB = "collect"


async def _previous_failed(runtime: Runtime) -> bool:
    """La collecte terminée juste avant celle-ci a-t-elle aussi échoué ?"""
    async with runtime.sessionmaker() as session:
        status = await session.scalar(
            select(JobRun.status)
            .where(JobRun.job == COLLECT_JOB, JobRun.status != JobRunStatus.RUNNING)
            .order_by(JobRun.started_at.desc(), JobRun.id.desc())
            .limit(1)
        )
    return status == JobRunStatus.FAILURE


async def collect_failed(runtime: Runtime, exc: BaseException) -> bool:
    """Alerte « collecte en échec », au plus une toutes les 6 heures. Jamais de secret.

    Une coupure réseau isolée (veille, changement de Wi-Fi) se rattrape au passage suivant :
    l'alerte n'arrive qu'au deuxième échec de suite. Un refus de connexion (mot de passe,
    adresse) ne se répare pas tout seul : alerte dès le premier échec.
    """
    kind = getattr(exc, "kind", "") if isinstance(exc, MailboxError) else ""
    if kind == "connection" and not await _previous_failed(runtime):
        return False
    since = datetime.now(UTC) - COLLECT_ALERT_EVERY
    async with runtime.sessionmaker() as session:
        recent = await session.scalar(
            select(Notification.id).where(
                Notification.kind == "collect_failed", Notification.created_at > since
            )
        )
    if recent:
        return False
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


async def collect_recovered(runtime: Runtime) -> int:
    """Collecte rétablie : les alertes « collecte en échec » encore non lues sont marquées
    lues, la cloche ne signale plus un problème réglé."""
    async with runtime.sessionmaker.begin() as session:
        result = await session.execute(
            update(Notification)
            .where(Notification.kind == "collect_failed", Notification.read_at.is_(None))
            .values(read_at=datetime.now(UTC))
        )
        return int(getattr(result, "rowcount", 0) or 0)


async def purge(runtime: Runtime) -> int:
    async with runtime.sessionmaker.begin() as session:
        result = await session.execute(
            delete(Notification).where(Notification.created_at < datetime.now(UTC) - KEEP_FOR)
        )
        return int(getattr(result, "rowcount", 0) or 0)
