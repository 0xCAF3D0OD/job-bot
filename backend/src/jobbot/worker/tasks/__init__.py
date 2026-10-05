"""Importer ce paquet enregistre toutes les tâches dans jobbot.worker.jobs.JOBS."""

from jobbot.worker.tasks import collect, filter, heartbeat

__all__ = ["collect", "filter", "heartbeat"]
