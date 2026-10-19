"""Le signal de la semaine (docs/86, 0.68.1) : planifiée chaque heure, exécutée seulement à
17 h, heure suisse ; le message ne part que le dernier jour de recherche de la semaine."""

from jobbot.notify.rhythm import notify_week
from jobbot.rhythm.service import SIGNAL_HOUR
from jobbot.runtime import Runtime
from jobbot.worker.jobs import RunContext, register

RHYTHM_JOB = "rhythm"


@register(RHYTHM_JOB, cron="0 * * * *", active_hours=(SIGNAL_HOUR, SIGNAL_HOUR))
async def rhythm_job(runtime: Runtime, ctx: RunContext) -> None:
    ctx.items_out = await notify_week(runtime)
