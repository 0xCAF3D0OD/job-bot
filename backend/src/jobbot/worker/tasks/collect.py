"""Collecte des alertes e-mail (docs/03-collecte-gmail.md)."""

from datetime import UTC, datetime, timedelta

from jobbot import accounts
from jobbot.collect.service import collect
from jobbot.notify.inbox import collect_failed, collect_recovered
from jobbot.runtime import Runtime
from jobbot.worker.jobs import LOCAL_TZ, RunContext, execute, register
from jobbot.worker.tasks.enrich import ENRICH_JOB
from jobbot.worker.tasks.filter import FILTER_JOB
from jobbot.worker.tasks.score import SCORE_JOB

COLLECT_JOB = "collect"
# Toutes les 2 heures (UTC), utile de 7 h à 21 h, heure suisse.
COLLECT_EVERY_HOURS = 2
COLLECT_CRON = f"0 */{COLLECT_EVERY_HOURS} * * *"
COLLECT_ACTIVE_HOURS = (7, 21)


def next_collect(after: datetime) -> datetime:
    """La prochaine collecte planifiée après `after` : une heure pleine UTC multiple de 2, dans
    les heures utiles (heure suisse). Lue par Candidatures vide, « prochaine vérification ce soir
    vers 18 h » (§41 du 16.11)."""
    start, end = COLLECT_ACTIVE_HOURS
    moment = after.astimezone(UTC).replace(minute=0, second=0, microsecond=0)
    for _ in range(48):
        moment += timedelta(hours=1)
        if (
            moment.hour % COLLECT_EVERY_HOURS == 0
            and start <= moment.astimezone(LOCAL_TZ).hour <= end
        ):
            return moment
    raise ValueError("aucune collecte planifiée dans les 48 heures")


# Une boîte pour la plateforme ; chaque e-mail est rangé dans le compte de son adresse de
# destination (docs/65 §3). L'état de la boîte, lui, regarde l'exploitant.
@register(COLLECT_JOB, cron=COLLECT_CRON, active_hours=COLLECT_ACTIVE_HOURS, scope="platform")
async def collect_job(runtime: Runtime, ctx: RunContext) -> None:
    async with runtime.sessionmaker.begin() as session:
        owner = await accounts.owner_id(session)
    try:
        result = await collect(runtime, ctx.run_id)
    except Exception as exc:
        # Visible dans la cloche (docs/15 §1) ; l'échec reste enregistré dans le journal.
        with accounts.use(owner):
            await collect_failed(runtime, exc)
        raise
    with accounts.use(owner):
        await collect_recovered(runtime)
    ctx.items_in = result.fetched
    ctx.items_out = result.new_offers
    # Les nouvelles offres passent aussitôt par le filtre de leur compte ; puis, pour chaque
    # compte, les offres jobup retenues sont lues sur le site et l'IA les note (exécutions
    # tracées à part ; elles reprennent aussi ce qui attendait).
    for account in sorted(result.accounts):
        with accounts.use(account):
            await execute(runtime, FILTER_JOB)
    if runtime.settings.enrich_enabled:
        await execute(runtime, ENRICH_JOB)
    if runtime.settings.llm_configured:
        await execute(runtime, SCORE_JOB)
