"""Mise en file d'une tâche depuis l'API (bouton « Collecter maintenant », « Renoter »…).

La tâche emporte le compte qui l'a demandée : le worker ne la fait que pour lui (docs/78
§3.4). Deux comptes peuvent la mettre en file en même temps ; un même compte, une fois.
"""

import procrastinate
from procrastinate.exceptions import AlreadyEnqueued

from jobbot import accounts
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
    account = accounts.current()
    waiting = task_name if account is None else f"{task_name}:{account}"
    async with app.open_async():
        try:
            await app.configure_task(
                task_name, queue=QUEUE, queueing_lock=waiting, lock=task_name
            ).defer_async(account=account)
        except AlreadyEnqueued:
            return False
    return True
