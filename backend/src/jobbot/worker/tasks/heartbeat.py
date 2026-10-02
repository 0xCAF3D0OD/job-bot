"""Tâche de démonstration : prouve que le worker tourne et atteint la base.

La page État considère le worker en panne si aucun heartbeat n'a réussi depuis 10 minutes.
"""

from sqlalchemy import text

from jobbot.runtime import Runtime
from jobbot.worker.jobs import RunContext, register

HEARTBEAT_JOB = "heartbeat"
HEARTBEAT_CRON = "*/5 * * * *"
HEARTBEAT_STALE_AFTER_SECONDS = 600


@register(HEARTBEAT_JOB, cron=HEARTBEAT_CRON)
async def heartbeat(runtime: Runtime, ctx: RunContext) -> None:
    async with runtime.engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    ctx.items_in = 0
    ctx.items_out = 0
