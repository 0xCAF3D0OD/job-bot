"""Importer ce paquet enregistre toutes les tâches dans jobbot.worker.jobs.JOBS."""

from jobbot.worker.tasks import collect, enrich, filter, heartbeat, score

__all__ = ["collect", "enrich", "filter", "heartbeat", "score"]
