"""Reprise des tâches restées « en cours » après l'arrêt brutal d'un worker (A1 du 13 novembre).

Chaque tâche porte un verrou à son nom : jamais deux exécutions simultanées. Mais un worker tué
pendant une tâche (coupure, `docker stop` trop court) la laisse marquée « en cours » ; procrastinate
ne prend alors plus aucune tâche du même nom, pour toujours. Ici, une tâche dont le worker ne donne
plus signe de vie est reprise :

- remise en file, une fois : elle repart du début. Nos tâches ne refont que ce qui reste à faire
  (une offre notée ne l'est plus, un CV lu ne l'est plus, une alerte relevée ne l'est plus) : pas de
  double note ni de double appel à l'IA pour ce qui a été enregistré ;
- si la même tâche attend déjà son tour (le planificateur l'a remise en file), l'ancienne est close
  en échec : la suivante fera le travail, une seule fois.

Le contrôle tourne au démarrage du worker, puis toutes les minutes, à côté de la file.
"""

import asyncio
import contextlib

import procrastinate
from procrastinate import jobs

from jobbot.log import get_logger

log = get_logger(__name__)

# Un worker sans signe de vie depuis ce délai est tenu pour mort (procrastinate en envoie un
# toutes les 10 s par défaut).
STALLED_AFTER_SECONDS = 60
CHECK_EVERY_SECONDS = 60


async def recover_stalled(app: procrastinate.App) -> tuple[int, int]:
    """Reprend les tâches des workers morts. Renvoie (remises en file, closes)."""
    manager = app.job_manager
    retried = closed = 0
    stalled = list(await manager.get_stalled_jobs(seconds_since_heartbeat=STALLED_AFTER_SECONDS))
    for job in stalled:
        try:
            await manager.retry_job(job)
            retried += 1
            log.warning("stalled_job_retried", job_id=job.id, task=job.task_name)
        except Exception as exc:
            # Déjà en attente sous le même verrou de file : la nouvelle suffit.
            await manager.finish_job(job, status=jobs.Status.FAILED, delete_job=False)
            closed += 1
            log.warning(
                "stalled_job_closed", job_id=job.id, task=job.task_name, reason=type(exc).__name__
            )
    return retried, closed


async def watch_stalled(app: procrastinate.App, stop: asyncio.Event) -> None:
    """Le contrôle, au démarrage puis toutes les minutes, jusqu'à l'arrêt du worker."""
    while not stop.is_set():
        try:
            await recover_stalled(app)
        except Exception as exc:
            log.warning("stalled_check_failed", error=type(exc).__name__)
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop.wait(), timeout=CHECK_EVERY_SECONDS)
