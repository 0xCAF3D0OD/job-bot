"""Vérification des liens du catalogue des formations, chaque heure (Kevin, 16.11.2026)."""

import httpx

from jobbot.runtime import Runtime
from jobbot.trainings.links import HEADERS, TIMEOUT, check_due
from jobbot.worker.jobs import RunContext, register

TRAINING_LINKS_JOB = "liens-formations"


# Le catalogue est commun et s'écrit au nom de l'exploitant (docs/78 §3.2).
@register(TRAINING_LINKS_JOB, cron="35 * * * *", scope="owner")
async def training_links(runtime: Runtime, ctx: RunContext) -> None:
    async with (
        httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, headers=HEADERS) as client,
        runtime.sessionmaker.begin() as session,
    ):
        ctx.items_out = await check_due(session, client)
