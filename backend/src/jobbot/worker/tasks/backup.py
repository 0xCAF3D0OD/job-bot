"""La sauvegarde de chaque nuit, son essai du dimanche et l'alerte (docs/82).

Vérifiée toutes les heures : une sauvegarde à 3 h (heure suisse), ou dès que la dernière date de
plus de 24 heures (l'ordinateur dormait à 3 h). Le dimanche, la dernière sauvegarde est
restaurée dans une base à part, puis effacée. Si une sauvegarde échoue, ou si la dernière date de
plus de 36 heures, une alerte part vers l'exploitant, au plus une par jour.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

from jobbot import accounts, backup, platform
from jobbot.log import get_logger
from jobbot.notify import service as notify
from jobbot.runtime import Runtime
from jobbot.worker.jobs import LOCAL_TZ, RunContext, register

log = get_logger(__name__)

BACKUP_JOB = "backup"
BACKUP_CRON = "17 * * * *"
NIGHT_HOUR = 3
ALERT_EVERY = timedelta(hours=24)
TEST_EVERY = timedelta(days=6)


async def read_status(runtime: Runtime) -> dict[str, Any]:
    async with runtime.sessionmaker() as session:
        value = await platform.get(session, backup.STATUS_KEY, {})
    return dict(value) if isinstance(value, dict) else {}


async def write_status(runtime: Runtime, **changes: object) -> dict[str, Any]:
    async with runtime.sessionmaker.begin() as session:
        current = await platform.get(session, backup.STATUS_KEY, {})
        merged = {**(current if isinstance(current, dict) else {}), **changes}
        await platform.put(session, backup.STATUS_KEY, merged)
    return merged


def due(status: dict[str, Any], now: datetime) -> bool:
    last = backup._when(status.get("last_at"))
    if last is None:
        return True
    age = now - last
    return age > timedelta(hours=24) or (
        age > timedelta(hours=20) and now.astimezone(LOCAL_TZ).hour == NIGHT_HOUR
    )


def test_due(status: dict[str, Any], now: datetime) -> bool:
    tested = backup._when(status.get("test_at"))
    sunday = now.astimezone(LOCAL_TZ).weekday() == 6
    return sunday and (tested is None or now - tested > TEST_EVERY)


async def save_now(runtime: Runtime, *, label: str | None = None) -> backup.Saved:
    """Une sauvegarde, notée dans l'état ; les anciennes sont triées. Lève BackupError."""
    now = datetime.now(UTC)
    try:
        made = await asyncio.to_thread(backup.make_backup, runtime.settings, label=label, now=now)
    except Exception as exc:
        reason = str(exc) if isinstance(exc, backup.BackupError) else type(exc).__name__
        await write_status(runtime, error_at=now.isoformat(), last_error=reason)
        raise
    await asyncio.to_thread(backup.prune, runtime.settings, now)
    await write_status(
        runtime,
        last_at=made.at.isoformat(),
        last_file=made.path.name,
        last_size=made.size,
        last_error=None,
        error_at=None,
    )
    return made


async def test_now(runtime: Runtime) -> dict[str, int]:
    present = backup.saved(runtime.settings)
    if not present:
        raise backup.BackupError("aucune sauvegarde à essayer")
    now = datetime.now(UTC).isoformat()
    try:
        result = await asyncio.to_thread(backup.restore_test, runtime.settings, present[0].path)
    except Exception as exc:
        reason = str(exc) if isinstance(exc, backup.BackupError) else type(exc).__name__
        await write_status(runtime, test_at=now, test_ok=False, test_error=reason)
        raise
    await write_status(
        runtime, test_at=now, test_ok=True, test_error=None, test_file=present[0].path.name
    )
    return result


async def _alert(runtime: Runtime, status: dict[str, Any], now: datetime) -> None:
    alerted = backup._when(status.get("alerted_at"))
    if not backup.late(status, now) or (alerted and now - alerted < ALERT_EVERY):
        return
    reason = status.get("last_error") or "aucune sauvegarde depuis plus de 36 heures"
    async with runtime.sessionmaker.begin() as session:
        owner = await accounts.owner_id(session)
    # L'alerte va à l'exploitant : la cloche de son compte, et son téléphone.
    with accounts.use(owner):
        await notify.deliver(
            runtime,
            notify.Message(
                title="La sauvegarde de jobA1 a échoué",
                message=f"{reason}. Voir les Réglages, rubrique Plateforme.",
                priority=4,
                tags=["warning"],
                click=f"{runtime.settings.public_url.rstrip('/')}/reglages?rubrique=plateforme",
            ),
            kind="backup_failed",
            link="/reglages?rubrique=plateforme",
        )
    await write_status(runtime, alerted_at=now.isoformat())


@register(BACKUP_JOB, cron=BACKUP_CRON, scope="platform")
async def nightly_backup(runtime: Runtime, ctx: RunContext) -> None:
    if not runtime.settings.backup_configured:
        return  # Les Réglages (Plateforme) disent qu'il manque la phrase secrète
    now = datetime.now(UTC)
    status = await read_status(runtime)
    ctx.items_in = ctx.items_out = 0
    try:
        if due(status, now):
            made = await save_now(runtime)
            ctx.items_out += 1
            log.info("backup_saved", file=made.path.name, size=made.size)
        status = await read_status(runtime)
        if backup.saved(runtime.settings) and test_due(status, now):
            result = await test_now(runtime)
            log.info("backup_tested", **result)
    finally:
        await _alert(runtime, await read_status(runtime), now)
