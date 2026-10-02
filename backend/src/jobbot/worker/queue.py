"""Mise en file d'une tâche depuis l'API (bouton « Collecter maintenant »)."""

import procrastinate
from procrastinate.exceptions import AlreadyEnqueued

from jobbot.settings import Settings

QUEUE = "default"


async def enqueue(settings: Settings, task_name: str) -> bool:
    """Met la tâche en file. Renvoie False si la même tâche attend déjà son tour.

    Une connexion courte est ouverte pour l'occasion : l'API n'a pas besoin de garder
    un pool procrastinate ouvert pour une action aussi rare.
    """
    app = procrastinate.App(
        connector=procrastinate.PsycopgConnector(
            conninfo=settings.libpq_url, min_size=1, max_size=1
        )
    )
    async with app.open_async():
        try:
            await app.configure_task(
                task_name, queue=QUEUE, queueing_lock=task_name, lock=task_name
            ).defer_async()
        except AlreadyEnqueued:
            return False
    return True
