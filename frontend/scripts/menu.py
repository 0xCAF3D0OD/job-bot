"""Le menu « Candidatures » depuis Mes alertes, Préparer et Relances (Kevin, 13.11.2026) : sur la démo, un clic
sur « Candidatures » dans le menu mène à la liste des offres. Avant, ces pages étaient retenues comme dernière page
de Candidatures et le clic ramenait sur la page déjà ouverte.

Parcours, sur ordinateur (menu du haut, 1440 px) et sur téléphone (barre du bas, 390 px) :
1. Candidatures (les offres), Mes alertes, clic sur « Candidatures » : la liste des offres.
2. Envoyées, Préparer une offre, clic sur « Candidatures » : la liste des offres (ordinateur seulement : le téléphone
   cache la barre du bas sur Préparer).
3. Envoyées, Relances, clic sur « Candidatures » : la liste des offres.

    make audit-menu DEMO_URL=http://localhost:5200
    CAPTURES=dossier make audit-menu   (une capture après chaque clic, clair et sombre)
"""

import asyncio
import os
import sys

from playwright.async_api import Page, async_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5200").rstrip("/")
CAPTURES = os.environ.get("CAPTURES")
OFFERS = "/candidatures/offres"

DESK = {"name": "ordinateur", "viewport": {"width": 1440, "height": 900}, "link": "nav.main-nav a:has-text('Candidatures')"}
PHONE = {"name": "telephone", "viewport": {"width": 390, "height": 844}, "link": "[data-test=tab-jobs]"}


async def offer_id(page: Page) -> int:
    data = await page.evaluate("() => fetch('/api/offers?limit=1').then((r) => r.json())")
    return int(data["items"][0]["id"])


async def path(page: Page) -> str:
    return await page.evaluate("() => location.pathname")


async def walk(page: Page, device: dict, steps: list[str], name: str, scheme: str) -> list[str]:
    """Ouvre chaque adresse dans l'ordre, puis clique sur « Candidatures » dans le menu."""
    for step in steps:
        await page.goto(BASE + step)
        await page.wait_for_load_state("networkidle")
    link = page.locator(device["link"]).first
    if not await link.count():
        return [f"{device['name']}, {name} : pas de lien « Candidatures » dans le menu"]
    await link.click()
    await page.wait_for_timeout(600)
    await page.wait_for_load_state("networkidle")
    if CAPTURES:
        os.makedirs(CAPTURES, exist_ok=True)
        await page.screenshot(path=f"{CAPTURES}/{name}-{device['name']}-{scheme}.png")
    got = await path(page)
    if got != OFFERS:
        return [f"{device['name']}, {name} : le menu mène à {got}, pas à {OFFERS}"]
    return []


async def main() -> int:
    faults: list[str] = []
    async with async_playwright() as p:
        chrome = os.environ.get("CHROME")
        browser = await p.chromium.launch(**({"executable_path": chrome} if chrome else {}))
        for scheme in ("clair", "sombre") if CAPTURES else ("clair",):
            for device in (DESK, PHONE):
                context = await browser.new_context(
                    viewport=device["viewport"],
                    reduced_motion="reduce",
                    color_scheme="dark" if scheme == "sombre" else "light",
                    device_scale_factor=2 if CAPTURES else 1,
                )
                page = await context.new_page()
                await page.goto(BASE + OFFERS)
                oid = await offer_id(page)
                faults += await walk(page, device, [OFFERS, "/candidatures/alertes"], "mes-alertes", scheme)
                if device is DESK:
                    steps = ["/candidatures/suivi", f"/candidatures/offres/{oid}/preparer"]
                    faults += await walk(page, device, steps, "preparer", scheme)
                faults += await walk(page, device, ["/candidatures/suivi", "/candidatures/relances"], "relances", scheme)
                await context.close()
        await browser.close()
    for fault in faults:
        print(f"  ✗ {fault}")
    print("Menu « Candidatures » : " + ("rien à signaler." if not faults else f"{len(faults)} défaut(s)."))
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
