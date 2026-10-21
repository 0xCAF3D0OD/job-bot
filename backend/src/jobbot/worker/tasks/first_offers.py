"""Les premières offres d'un compte (docs/104, 0.80.0) : la recherche publique de jobup."""

from jobbot.collect.public_search import run_first_offers
from jobbot.runtime import Runtime
from jobbot.worker.jobs import RunContext, execute, register
from jobbot.worker.tasks.enrich import ENRICH_JOB
from jobbot.worker.tasks.filter import FILTER_JOB
from jobbot.worker.tasks.score import SCORE_JOB

FIRST_OFFERS_JOB = "first_offers"


# Jamais planifiée : demandée à la fin de l'accueil, ou depuis la page Alertes.
@register(FIRST_OFFERS_JOB)
async def first_offers_job(runtime: Runtime, ctx: RunContext) -> None:
    result = await run_first_offers(runtime)
    ctx.items_in = result.found
    ctx.items_out = result.new_offers
    if not result.new_offers:
        return
    # Comme après une alerte : le filtre, la page de chaque offre, puis la note.
    await execute(runtime, FILTER_JOB)
    if runtime.settings.enrich_enabled:
        await execute(runtime, ENRICH_JOB)
    if runtime.settings.llm_configured:
        await execute(runtime, SCORE_JOB)
