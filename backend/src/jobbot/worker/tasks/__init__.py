"""Importer ce paquet enregistre toutes les tâches dans jobbot.worker.jobs.JOBS."""

from jobbot.worker.tasks import (
    collect,
    employer,
    enrich,
    filter,
    heartbeat,
    news,
    reminders,
    score,
)

__all__ = ["collect", "employer", "enrich", "filter", "heartbeat", "news", "reminders", "score"]
