"""Rappel de relance des candidatures sans réponse (docs/08 §5)."""

from jobbot.notify.service import notify_reminders
from jobbot.runtime import Runtime
from jobbot.worker.jobs import RunContext, register

REMINDERS_JOB = "reminders"


# Planifiée chaque heure (UTC), exécutée seulement à 9 h, heure suisse : un rappel par jour.
@register(REMINDERS_JOB, cron="0 * * * *", active_hours=(9, 9))
async def reminders_job(runtime: Runtime, ctx: RunContext) -> None:
    ctx.items_out = await notify_reminders(runtime)
