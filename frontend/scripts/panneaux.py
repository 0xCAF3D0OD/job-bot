"""Panneaux à formulaire (paquet du 11 novembre, PR 37) : sur la démo, le panneau « Ajouter » s'ouvre en
fenêtre modale, garde le focus, se ferme par Échap et par un clic à l'extérieur, et rend le focus au bouton
d'origine (WCAG 2.1.2, 2.4.3).

    make audit-panneaux DEMO_URL=http://localhost:5200
"""

import asyncio
import json
import os
import sys

from playwright.async_api import Page, async_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5200").rstrip("/")
OPENER = "[data-test=manual-open]"
PANEL = "dialog.sheet-panel[open]"


async def opened(page: Page) -> list[str]:
    """Ouvre le panneau et rend les défauts de l'état ouvert."""
    faults: list[str] = []
    await page.locator(OPENER).click()
    await page.wait_for_selector(PANEL, timeout=5000)
    if not await page.evaluate("() => document.querySelector('dialog.sheet-panel').matches(':modal')"):
        faults.append("le panneau n'est pas une fenêtre modale")
    labelled = await page.evaluate(
        "() => { const d = document.querySelector('dialog.sheet-panel'); return document.getElementById(d.getAttribute('aria-labelledby') ?? '')?.textContent?.trim() ?? ''; }"
    )
    if labelled != "Ajouter":
        faults.append(f"aria-labelledby ne nomme pas le panneau (« {labelled} »)")
    if not await page.evaluate("() => document.querySelector('dialog.sheet-panel').contains(document.activeElement)"):
        faults.append("le focus n'est pas dans le panneau à l'ouverture")
    # Le focus reste dans le panneau : vingt tabulations ne le font pas sortir.
    for _ in range(20):
        await page.keyboard.press("Tab")
    if not await page.evaluate("() => document.querySelector('dialog.sheet-panel').contains(document.activeElement)"):
        faults.append("la tabulation sort du panneau")
    if await page.locator(f"{PANEL} button", has_text="Annuler").count():
        faults.append("un bouton « Annuler » dans le panneau")
    return faults


async def closed(page: Page, how: str) -> list[str]:
    faults: list[str] = []
    await page.wait_for_timeout(300)
    if await page.locator(PANEL).count():
        faults.append(f"{how} : le panneau reste ouvert")
    elif not await page.evaluate("(sel) => document.activeElement === document.querySelector(sel)", OPENER):
        faults.append(f"{how} : le focus ne revient pas au bouton « Ajouter »")
    return faults


async def main() -> int:
    faults: list[str] = []
    async with async_playwright() as p:
        chrome = os.environ.get("CHROME")
        browser = await p.chromium.launch(**({"executable_path": chrome} if chrome else {}))
        context = await browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        page = await context.new_page()
        await page.goto(f"{BASE}/candidatures/offres")
        await page.wait_for_selector(OPENER, timeout=15000)

        faults += await opened(page)
        await page.keyboard.press("Escape")
        faults += await closed(page, "Échap")

        faults += await opened(page)
        await page.mouse.click(200, 500)  # dans la page, à gauche du panneau
        faults += await closed(page, "clic à l'extérieur")

        await browser.close()
    for fault in faults:
        print(fault)
    print(json.dumps({"défauts": len(faults)}, ensure_ascii=False))
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
