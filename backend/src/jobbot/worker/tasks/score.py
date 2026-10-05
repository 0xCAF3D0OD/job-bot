"""Note et résumé des offres par l'IA (docs/06-note-ia.md)."""

from jobbot.runtime import Runtime
from jobbot.scoring.service import run_scoring
from jobbot.worker.jobs import RunContext, register

SCORE_JOB = "score"
RESCORE_JOB = "rescore"


# Toutes les 10 minutes : relève des lots terminés et notes manquantes. Sans rien à faire,
# la tâche ne fait que deux requêtes en base.
@register(SCORE_JOB, cron="*/10 * * * *")
async def score_job(runtime: Runtime, ctx: RunContext) -> None:
    result = await run_scoring(runtime)
    ctx.items_in = result.scored + result.failed + result.batch_submitted
    ctx.items_out = result.scored + result.batch_collected


@register(RESCORE_JOB)
async def rescore_job(runtime: Runtime, ctx: RunContext) -> None:
    """Renotation après un changement de profil, sur clic de Kevin (en lot)."""
    result = await run_scoring(runtime, rescore_profile=True)
    ctx.items_in = result.batch_submitted
    ctx.items_out = result.batch_collected
