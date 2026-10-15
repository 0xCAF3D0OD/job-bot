"""Rappels quotidiens : relance des candidatures sans réponse (docs/08 §5) et preuves ORP
(objectif, remise, veille de la date limite ; docs/09 §5)."""

from jobbot.assistant import service as assistant
from jobbot.contacts.service import notify_contacts
from jobbot.notify.inbox import purge
from jobbot.notify.interviews import notify_interviews
from jobbot.notify.orp import notify_orp
from jobbot.notify.service import notify_reminders
from jobbot.runtime import Runtime
from jobbot.trainings.funding import notify_funding
from jobbot.worker.jobs import RunContext, register

REMINDERS_JOB = "reminders"


# Planifiée chaque heure (UTC), exécutée seulement à 9 h, heure suisse : un rappel par jour.
@register(REMINDERS_JOB, cron="0 * * * *", active_hours=(9, 9))
async def reminders_job(runtime: Runtime, ctx: RunContext) -> None:
    ctx.items_out = (
        await notify_reminders(runtime)
        + await notify_orp(runtime)
        + await notify_interviews(runtime)  # « fais le point » le lendemain (docs/23)
        + await notify_contacts(runtime)  # contact sans réponse depuis 7 jours (docs/31)
        + await notify_funding(runtime)  # financement ORP sans réponse depuis 14 jours (docs/37)
    )
    await purge(runtime)  # alertes de la cloche de plus de 90 jours
    await assistant.purge(runtime)  # discussions de l'assistant de plus de 30 jours
