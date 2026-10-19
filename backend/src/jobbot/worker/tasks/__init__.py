"""Importer ce paquet enregistre toutes les tâches dans jobbot.worker.jobs.JOBS."""

from jobbot.worker.tasks import (
    backup,
    collect,
    employer,
    enrich,
    filter,
    heartbeat,
    news,
    reminders,
    rhythm,
    score,
)

__all__ = [
    "backup",
    "collect",
    "employer",
    "enrich",
    "filter",
    "heartbeat",
    "news",
    "reminders",
    "rhythm",
    "score",
]
