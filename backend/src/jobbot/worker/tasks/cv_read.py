"""La lecture du CV demandée depuis le Profil (PR 21 du 10 novembre) : elle continue quand la
personne quitte la page, et la cloche prévient à la fin."""

from jobbot.profile.reading import read_pending
from jobbot.runtime import Runtime
from jobbot.worker.jobs import RunContext, register

CV_READ_JOB = "cv_read"


@register(CV_READ_JOB)
async def cv_read_job(runtime: Runtime, ctx: RunContext) -> None:
    ctx.items_out = await read_pending(runtime)
