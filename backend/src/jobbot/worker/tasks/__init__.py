"""Importer ce paquet enregistre toutes les tâches dans jobbot.worker.jobs.JOBS."""

from jobbot.worker.tasks import (
    backup,
    collect,
    cv_read,
    employer,
    enrich,
    filter,
    first_offers,
    heartbeat,
    reminders,
    rhythm,
    score,
    site_codes,
)

__all__ = [
    "backup",
    "collect",
    "cv_read",
    "employer",
    "enrich",
    "filter",
    "first_offers",
    "heartbeat",
    "reminders",
    "rhythm",
    "score",
    "site_codes",
]
