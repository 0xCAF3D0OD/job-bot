"""Captures de toutes les pages pour la migration des échelles (docs/135 §7) : chaque page des
audits, chaque repliable ouvert et chaque vue choisie (explore.py), à 1440 et 390 px, en clair
et en sombre. On les prend avant et après un changement, puis `compare.py` montre ce qui a bougé.

    make demo
    cd backend && uv run --with playwright python ../frontend/scripts/captures.py \
        http://localhost:5200 /chemin/avant
"""

import asyncio
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from explore import states
from playwright.async_api import async_playwright
from regles import PAGES

# Remonte en haut et attend que la page n'y bouge plus pendant 300 ms : ouvrir un repliable
# peut lancer un défilement qui finirait pendant la capture.
SETTLE_AT_TOP = """async () => {
  let still = 0;
  for (let i = 0; i < 100 && still < 6; i++) {
    window.scrollTo(0, 0);
    await new Promise((r) => setTimeout(r, 50));
    still = window.scrollY === 0 ? still + 1 : 0;
  }
}"""

SIZES = [{"width": 1440, "height": 900}, {"width": 390, "height": 844}]
# Les pages publiques et la page introuvable (1.6.11), en plus des pages des audits.
PUBLIC = ["connexion", "inscription", "la-plateforme", "conditions", "a-propos", "bienvenue", "page-introuvable"]
SCHEMES = ["light", "dark"]
# Un rendu stable d'une série à l'autre : sans ces options, l'anticrénelage du texte varie de
# quelques pixels entre deux captures identiques.
STABLE = [
    "--disable-gpu",
    "--disable-partial-raster",
    "--disable-lcd-text",
    "--force-color-profile=srgb",
    "--font-render-hinting=none",
    "--disable-skia-runtime-opts",
    "--disable-threaded-scrolling",
    "--num-raster-threads=1",
]


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "accueil"


async def main(base: str, out: Path) -> int:
    # L'horloge de la page est figée (« il y a 9 min ») : la même heure pour la série d'avant et
    # celle d'après, l'heure pleine en cours par défaut ou CAPTURES_TIME (ISO).
    now = os.environ.get("CAPTURES_TIME") or datetime.now().replace(minute=0, second=0).isoformat()
    count = 0
    async with async_playwright() as p:
        chrome = os.environ.get("CHROME")
        browser = await p.chromium.launch(
            args=STABLE, **({"executable_path": chrome} if chrome else {})
        )
        probe = await browser.new_page()
        found = await (await probe.request.get(f"{base}/api/offers?limit=1")).json()
        await probe.close()
        extra, offer = [], ""
        if found.get("items"):
            offer = str(found["items"][0]["id"])
            extra = [f"candidatures/offres?offre={offer}", f"candidatures/offres/{offer}/preparer"]
        for scheme in SCHEMES:
            for size in SIZES:
                context = await browser.new_context(
                    viewport=size, color_scheme=scheme, reduced_motion="reduce"
                )
                await context.clock.set_fixed_time(datetime.fromisoformat(now))
                page = await context.new_page()
                for path in PAGES + extra + PUBLIC:
                    await page.goto(f"{base}/{path}")
                    await page.wait_for_timeout(1700)
                    # La page est chargée : plus de requête en cours ni de voile de chargement.
                    await page.wait_for_load_state("networkidle")
                    await page.locator(".page-veil").wait_for(state="detached", timeout=15000)
                    name = slug(path.replace(offer, "offre") if offer else path)
                    async for state in states(page):
                        suffix = f"--{slug(state)}" if state else ""
                        file = f"{name}{suffix}-{size['width']}-{scheme}.png"
                        # Toujours depuis le haut : une rubrique fait défiler la page, et les
                        # en-têtes collants se placent selon le défilement du moment.
                        await page.wait_for_load_state("networkidle")
                        await page.evaluate(SETTLE_AT_TOP)
                        await page.screenshot(
                            path=out / file, full_page=True, animations="disabled", caret="hide"
                        )
                        count += 1
                await context.close()
        await browser.close()
    print(f"{count} captures dans {out}, horloge {now}")
    return 0


if __name__ == "__main__":
    target = Path(sys.argv[2])
    target.mkdir(parents=True, exist_ok=True)
    sys.exit(asyncio.run(main(sys.argv[1], target)))
