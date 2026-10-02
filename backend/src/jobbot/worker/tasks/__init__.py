"""Importer ce paquet enregistre toutes les tâches dans jobbot.worker.jobs.JOBS."""

from jobbot.worker.tasks import heartbeat

__all__ = ["heartbeat"]
