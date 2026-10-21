"""Les codes des sites (docs/112) : le relevé rapide, et l'effacement des codes."""

import asyncio

from jobbot import accounts
from jobbot.collect.service import collect
from jobbot.mail import site_codes
from jobbot.runtime import Runtime
from jobbot.worker.jobs import RunContext, execute, register
from jobbot.worker.tasks.enrich import ENRICH_JOB
from jobbot.worker.tasks.filter import FILTER_JOB
from jobbot.worker.tasks.score import SCORE_JOB

# 20 relevés, un toutes les 15 secondes : 5 minutes.
FAST_ROUNDS = 20
FAST_EVERY_SECONDS = 15.0
PURGE_JOB = "site_codes_purge"


# Demandé par « J'attends un code » ou par l'extension ; une seule boîte pour la plateforme.
@register(site_codes.FAST_COLLECT_JOB, scope="platform")
async def collect_fast_job(runtime: Runtime, ctx: RunContext) -> None:
    fetched = new_offers = 0
    offer_accounts: set[int] = set()
    for round_ in range(FAST_ROUNDS):
        if round_:
            await asyncio.sleep(FAST_EVERY_SECONDS)
        result = await collect(runtime, ctx.run_id)
        fetched += result.fetched
        new_offers += result.new_offers
        offer_accounts |= result.accounts
        # Le code est arrivé : le relevé rapide s'arrête là.
        if result.codes:
            break
    ctx.items_in, ctx.items_out = fetched, new_offers
    # Une alerte arrivée entre-temps suit son chemin habituel.
    for account in sorted(offer_accounts):
        with accounts.use(account):
            await execute(runtime, FILTER_JOB)
    if offer_accounts and runtime.settings.enrich_enabled:
        await execute(runtime, ENRICH_JOB)
    if offer_accounts and runtime.settings.llm_configured:
        await execute(runtime, SCORE_JOB)


@register(PURGE_JOB, cron="*/15 * * * *")
async def purge_job(runtime: Runtime, ctx: RunContext) -> None:
    ctx.items_out = await site_codes.purge(runtime)
