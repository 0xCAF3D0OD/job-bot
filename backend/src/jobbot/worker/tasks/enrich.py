"""Lecture des pages d'offres jobup (docs/05-candidature-externe.md)."""

from jobbot.enrich.service import enrich
from jobbot.registry.service import lookup_addresses
from jobbot.runtime import Runtime
from jobbot.worker.jobs import RunContext, execute, register
from jobbot.worker.tasks.filter import FILTER_JOB

ENRICH_JOB = "enrich"


@register(ENRICH_JOB)
async def enrich_job(runtime: Runtime, ctx: RunContext) -> None:
    result = await enrich(runtime)
    ctx.items_in = result.fetched
    ctx.items_out = result.ok
    # Le texte complet peut révéler un type d'emploi ou une langue exigée : on refiltre.
    if result.ok:
        await execute(runtime, FILTER_JOB)
    # Adresse des entreprises sans page lisible (Indeed, LinkedIn) : registre IDE (docs/12).
    await lookup_addresses(runtime)
