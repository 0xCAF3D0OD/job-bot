"""Les codes des sites (docs/112) : le relevé rapide, et l'effacement des codes."""

import asyncio
from datetime import UTC, datetime

from jobbot import accounts
from jobbot.collect.service import collect
from jobbot.log import get_logger
from jobbot.mail import site_codes
from jobbot.mail.imap import MailboxError
from jobbot.runtime import Runtime
from jobbot.worker.jobs import RunContext, execute, register
from jobbot.worker.tasks.enrich import ENRICH_JOB
from jobbot.worker.tasks.filter import FILTER_JOB
from jobbot.worker.tasks.score import SCORE_JOB

# Un relevé toutes les 15 secondes, tant que le compte attend son code (5 minutes pour « J'attends
# un code » et l'extension ; tant que l'étape du code relance, 10 minutes au plus), sous le
# plafond de la plateforme.
FAST_EVERY_SECONDS = 15.0
MAX_ROUNDS = 41
PURGE_JOB = "site_codes_purge"
log = get_logger(__name__)


# Demandé par « J'attends un code », par l'étape du code ou par l'extension ; une seule boîte.
@register(site_codes.FAST_COLLECT_JOB, scope="platform")
async def collect_fast_job(runtime: Runtime, ctx: RunContext) -> None:
    fetched = new_offers = 0
    offer_accounts: set[int] = set()
    errors: list[MailboxError] = []
    me = accounts.current()
    for round_ in range(MAX_ROUNDS):
        if round_:
            await asyncio.sleep(FAST_EVERY_SECONDS)
            until = await site_codes.fast_until(runtime)
            if until is None or datetime.now(UTC) >= until:
                break
        if not await site_codes.take_fast_read(runtime):
            log.warning("collect_fast_capped")
            break
        # Une boîte illisible n'arrête pas le relevé : l'autre reste lue à chaque tour.
        result = await collect(runtime, ctx.run_id, raise_errors=False)
        errors += result.errors
        fetched += result.fetched
        new_offers += result.new_offers
        offer_accounts |= result.accounts
        # Le code du compte est arrivé : le relevé rapide s'arrête là.
        if result.code_accounts and (me is None or me in result.code_accounts):
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
    if errors:
        raise errors[0]


@register(PURGE_JOB, cron="*/15 * * * *")
async def purge_job(runtime: Runtime, ctx: RunContext) -> None:
    ctx.items_out = await site_codes.purge(runtime)
