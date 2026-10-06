"""Relevé des actualités (docs/15 §2)."""

from jobbot.news.service import fetch_news
from jobbot.runtime import Runtime
from jobbot.worker.jobs import RunContext, register

NEWS_JOB = "news"


# Toutes les 6 heures (UTC), à toute heure : les flux sont légers.
@register(NEWS_JOB, cron="0 */6 * * *")
async def news_job(runtime: Runtime, ctx: RunContext) -> None:
    result = await fetch_news(runtime)
    ctx.items_in = result.sources
    ctx.items_out = result.new_items
