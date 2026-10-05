"""Filtre des prérequis (docs/04-profil-prerequis.md §4)."""

from jobbot.filtering.service import run_filter
from jobbot.runtime import Runtime
from jobbot.worker.jobs import RunContext, register

FILTER_JOB = "filter"


@register(FILTER_JOB)
async def filter_job(runtime: Runtime, ctx: RunContext) -> None:
    result = await run_filter(runtime)
    ctx.items_in = result.examined
    ctx.items_out = result.to_review
