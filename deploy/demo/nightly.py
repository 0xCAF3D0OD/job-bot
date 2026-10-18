"""Remet la démo à neuf chaque nuit à 4 h (heure suisse) : `jobbot demo-seed` (docs/77 §3).

Tourne en boucle dans son propre conteneur ; un échec est écrit dans le journal et la nuit
suivante réessaie.
"""

import subprocess
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

ZURICH = ZoneInfo("Europe/Zurich")
HOUR = 4


def seconds_until_next_run(now: datetime) -> float:
    target = now.replace(hour=HOUR, minute=0, second=0, microsecond=0)
    if target <= now:
        target = (now + timedelta(days=1)).replace(hour=HOUR, minute=0, second=0, microsecond=0)
    return (target - now).total_seconds()


def main() -> None:
    while True:
        wait = seconds_until_next_run(datetime.now(ZURICH))
        print(f"Prochaine remise à neuf dans {wait / 3600:.1f} h.", flush=True)
        time.sleep(wait)
        result = subprocess.run(["jobbot", "demo-seed"], check=False)
        print(f"Remise à neuf terminée (code {result.returncode}).", flush=True)


if __name__ == "__main__":
    main()
