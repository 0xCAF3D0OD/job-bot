"""Collecte des alertes e-mail (docs/03-collecte-gmail.md)."""

from jobbot.collect.service import collect
from jobbot.runtime import Runtime
from jobbot.worker.jobs import RunContext, execute, register
from jobbot.worker.tasks.enrich import ENRICH_JOB
from jobbot.worker.tasks.filter import FILTER_JOB
from jobbot.worker.tasks.score import SCORE_JOB

COLLECT_JOB = "collect"
# Toutes les 2 heures (UTC), utile de 7 h à 21 h, heure suisse.
COLLECT_CRON = "0 */2 * * *"
COLLECT_ACTIVE_HOURS = (7, 21)


@register(COLLECT_JOB, cron=COLLECT_CRON, active_hours=COLLECT_ACTIVE_HOURS)
async def collect_job(runtime: Runtime, ctx: RunContext) -> None:
    result = await collect(runtime, ctx.run_id)
    ctx.items_in = result.fetched
    ctx.items_out = result.new_offers
    # Les nouvelles offres passent aussitôt par le filtre, puis les offres jobup retenues
    # sont lues sur le site (exécutions tracées à part).
    if result.new_offers:
        await execute(runtime, FILTER_JOB)
    if runtime.settings.enrich_enabled:
        await execute(runtime, ENRICH_JOB)
    # Puis l'IA note les offres retenues (appels directs si elles sont peu nombreuses).
    if runtime.settings.llm_configured:
        await execute(runtime, SCORE_JOB)
