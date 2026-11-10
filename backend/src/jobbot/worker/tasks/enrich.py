"""Lecture des pages d'offres jobup (docs/05-candidature-externe.md)."""

from jobbot.enrich.service import enrich
from jobbot.logos.service import fetch_logos
from jobbot.manual_offers import read_pending_texts
from jobbot.registry.service import lookup_addresses
from jobbot.runtime import Runtime
from jobbot.worker.jobs import RunContext, execute, register
from jobbot.worker.tasks.filter import FILTER_JOB

ENRICH_JOB = "enrich"


@register(ENRICH_JOB)
async def enrich_job(runtime: Runtime, ctx: RunContext) -> None:
    result = await enrich(runtime)
    # Les annonces complètes des autres sites, lues en arrière-plan (prompt du 10 novembre,
    # PR 13) ; chaque texte lu repasse par le filtre, la notation qui suit la collecte
    # refait la note.
    texts = await read_pending_texts(runtime)
    ctx.items_in = result.fetched + texts.tried
    ctx.items_out = result.ok + texts.done
    # Le texte complet peut révéler un type d'emploi ou une langue exigée : on refiltre.
    if result.ok:
        await execute(runtime, FILTER_JOB)
    # Adresse des entreprises sans page lisible (Indeed, LinkedIn) : registre IDE (docs/12).
    await lookup_addresses(runtime)
    # Logos des entreprises (docs/14 §4), téléchargés une fois par entreprise.
    await fetch_logos(runtime)
