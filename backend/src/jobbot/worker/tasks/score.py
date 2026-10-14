"""Note et résumé des offres par l'IA (docs/06-note-ia.md)."""

from jobbot.filtering.service import run_filter
from jobbot.log import get_logger
from jobbot.notify.service import notify_new_scores
from jobbot.runtime import Runtime
from jobbot.scoring.remote import run_remote
from jobbot.scoring.service import ScoringResult, run_scoring
from jobbot.worker.jobs import RunContext, register

log = get_logger(__name__)

SCORE_JOB = "score"


async def _notify(runtime: Runtime) -> None:
    """Notifications après la notation ; un échec d'envoi n'annule pas les notes."""
    try:
        await notify_new_scores(runtime)
    except Exception as exc:
        log.warning("notification_failed", error=type(exc).__name__)


RESCORE_JOB = "rescore"
REMOTE_JOB = "remote"


async def _refilter(runtime: Runtime, result: ScoringResult) -> None:
    """Le télétravail est relevé à la notation : une offre réservée à d'autres pays est
    écartée si tu ne l'acceptes qu'ouverte depuis la Suisse (docs/26 §3)."""
    if result.scored or result.batch_collected:
        await run_filter(runtime)


# Toutes les 10 minutes : relève des lots terminés et notes manquantes. Sans rien à faire,
# la tâche ne fait que deux requêtes en base.
@register(SCORE_JOB, cron="*/10 * * * *")
async def score_job(runtime: Runtime, ctx: RunContext) -> None:
    result = await run_scoring(runtime)
    ctx.items_in = result.scored + result.failed + result.batch_submitted
    ctx.items_out = result.scored + result.batch_collected
    await _refilter(runtime, result)
    await _notify(runtime)


@register(RESCORE_JOB)
async def rescore_job(runtime: Runtime, ctx: RunContext) -> None:
    """Renotation après un changement de profil, sur clic de Kevin (en lot)."""
    result = await run_scoring(runtime, rescore_profile=True)
    ctx.items_in = result.batch_submitted
    ctx.items_out = result.batch_collected
    await _refilter(runtime, result)
    await _notify(runtime)


@register(REMOTE_JOB)
async def remote_job(runtime: Runtime, ctx: RunContext) -> None:
    """Relecture du télétravail des offres déjà notées, sur clic de Kevin (docs/26 §2)."""
    result = await run_remote(runtime)
    ctx.items_in = result.read + result.failed
    ctx.items_out = result.read
