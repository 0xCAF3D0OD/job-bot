"""Annonces chez l'employeur (docs/20 §2) : offres bien notées, puis revérification."""

from sqlalchemy import select

from jobbot.db.models import Setting
from jobbot.employer import service
from jobbot.log import get_logger
from jobbot.runtime import Runtime
from jobbot.worker.jobs import RunContext, register

EMPLOYER_JOB = "employer"
PER_RUN = 6
RECHECK_PER_RUN = 20
DEFAULT_THRESHOLD = 70

log = get_logger(__name__)


# Chaque heure en journée : quelques offres à la fois, une requête après l'autre.
@register(EMPLOYER_JOB, cron="20 * * * *", active_hours=(7, 21))
async def employer_job(runtime: Runtime, ctx: RunContext) -> None:
    async with runtime.sessionmaker() as session:
        value = await session.scalar(
            select(Setting.value).where(Setting.key == "employer_search_threshold")
        )
        threshold = int(value) if isinstance(value, int | float) else DEFAULT_THRESHOLD
        offer_ids = await service.candidates(session, threshold, PER_RUN)
        stale = await service.stale(session, RECHECK_PER_RUN)
    use_web = True
    found = 0
    for offer_id in offer_ids:
        try:
            result = await service.find(runtime, offer_id, use_web=use_web)
        except service.EmployerUnavailable as exc:
            # Plafond ou compte : on continue sans IA (site et outil de recrutement seulement).
            log.info("employer_web_unavailable", reason=str(exc))
            use_web = False
            result = await service.find(runtime, offer_id, use_web=False)
        found += bool(result and result.url)
    for offer in stale:
        await service.recheck(runtime, offer)
    ctx.items_in = len(offer_ids) + len(stale)
    ctx.items_out = found
