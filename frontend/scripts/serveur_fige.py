"""Le serveur à heure figée, pour les captures (docs/135 §7) : `jobbot` lancé avec l'horloge
arrêtée à CAPTURES_TIME, la même que celle de la page dans `captures.py`. Les dates de la démo
(« Relevé il y a … », « il y a 3 jours ») ne bougent plus d'une série à l'autre, même si la base
est remplie à nouveau entre les deux.

    cd backend
    CAPTURES_TIME=2026-10-22T23:00:00 uv run --with time-machine python \
        ../frontend/scripts/serveur_fige.py demo-seed
    CAPTURES_TIME=2026-10-22T23:00:00 uv run --with time-machine python \
        ../frontend/scripts/serveur_fige.py api
"""

import os
import sys
from datetime import datetime

import time_machine

from jobbot.__main__ import main

if __name__ == "__main__":
    moment = datetime.fromisoformat(os.environ["CAPTURES_TIME"]).astimezone()
    # tick=False : l'heure ne bouge pas du tout pendant la série.
    time_machine.travel(moment, tick=False).start()
    sys.argv = ["jobbot", *sys.argv[1:]]
    sys.exit(main())
