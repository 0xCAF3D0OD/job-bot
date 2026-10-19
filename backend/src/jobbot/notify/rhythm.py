"""Le signal de la semaine (docs/86 §2, 0.68.1) : un message, le dernier jour de recherche de
la semaine, à 17 h. À jour, en retard ou trop, sans reproche ; une fois par semaine."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from jobbot.db.models import Setting
from jobbot.notify.service import Message, deliver
from jobbot.rhythm import service as rhythm
from jobbot.runtime import Runtime

TAGS = {"done": ["tada"], "late": ["seedling"], "too_much": ["leaves"]}


async def notify_week(runtime: Runtime, today: date | None = None) -> int:
    today = today or rhythm.local_today()
    week = f"{today:%G-W%V}"
    async with runtime.sessionmaker() as session:
        sent = await session.scalar(select(Setting.value).where(Setting.key == rhythm.SIGNAL_KEY))
        found = await rhythm.signal(session, today)
    if found is None or sent == week:
        return 0
    base = runtime.settings.public_url.rstrip("/")
    await deliver(
        runtime,
        Message(title=found.title, message=found.message, tags=TAGS[found.kind], click=f"{base}/"),
        kind="rhythm_week",
        link="/",
    )
    async with runtime.sessionmaker.begin() as session:
        await session.execute(
            insert(Setting)
            .values(key=rhythm.SIGNAL_KEY, value=week)
            .on_conflict_do_update(index_elements=["user_id", "key"], set_={"value": week})
        )
    return 1
