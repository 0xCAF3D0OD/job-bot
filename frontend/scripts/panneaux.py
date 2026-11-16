"""Panneaux à formulaire (paquet du 11 novembre, PR 37) : sur la démo, le panneau « Ajouter » s'ouvre en
fenêtre modale, garde le focus, se ferme par Échap et par un clic à l'extérieur, et rend le focus au bouton
d'origine (WCAG 2.1.2, 2.4.3). Puis le panneau « Alerte <site> » des Alertes (planche AlertesOrdinateurSite) :
modal, nommé par son titre, 440 px, focus gardé, Échap rend le focus à la carte ; bouton de copie de 44 × 44 px.

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


ALERT_CARD = "[data-test=alerts-family-todo] [data-test^=alert-card-]"
ALERT_PANEL = ".side-panel.alert-site-panel"


async def alert_panel(page: Page) -> list[str]:
    """Le panneau « Alerte <site> », ouvert depuis la première carte « À créer » de la page Alertes."""
    faults: list[str] = []
    await page.goto(f"{BASE}/candidatures/alertes")
    try:
        await page.wait_for_selector(ALERT_CARD, timeout=15000)
    except Exception:  # noqa: BLE001 - la démo n'a pas de carte « À créer » : le dire, pas planter
        return ["Alertes : aucune carte « À créer » sur la démo"]
    card = page.locator(ALERT_CARD).first
    card_test = await card.get_attribute("data-test")
    await card.focus()
    await page.keyboard.press("Enter")
    await page.wait_for_selector(ALERT_PANEL, timeout=5000)
    info = await page.evaluate(
        """(sel) => { const d = document.querySelector(sel); const r = d.getBoundingClientRect();
        const copy = d.querySelector('.alert-site-address .copy-button')?.getBoundingClientRect();
        return { role: d.getAttribute('role'), modal: d.getAttribute('aria-modal'), label: d.getAttribute('aria-label') ?? '',
          title: d.querySelector('h2')?.textContent?.trim() ?? '', width: Math.round(r.width),
          inside: d.contains(document.activeElement), copy: copy ? [Math.round(copy.width), Math.round(copy.height)] : null }; }""",
        ALERT_PANEL,
    )
    if info["role"] != "dialog" or info["modal"] != "true":
        faults.append("Alertes : le panneau n'est pas une fenêtre modale")
    if not info["label"].startswith("Alerte ") or info["label"] != info["title"]:
        faults.append(f"Alertes : le panneau n'est pas nommé par son titre (« {info['label']} »)")
    if info["width"] != 440:
        faults.append(f"Alertes : le panneau fait {info['width']} px, pas 440")
    if not info["inside"]:
        faults.append("Alertes : le focus n'est pas dans le panneau à l'ouverture")
    if info["copy"] is not None and info["copy"] != [44, 44]:
        faults.append(f"Alertes : le bouton de copie fait {info['copy'][0]} × {info['copy'][1]} px, pas 44 × 44")
    for _ in range(20):
        await page.keyboard.press("Tab")
    if not await page.evaluate("(sel) => document.querySelector(sel).contains(document.activeElement)", ALERT_PANEL):
        faults.append("Alertes : la tabulation sort du panneau")
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(300)
    if await page.locator(ALERT_PANEL).count():
        faults.append("Alertes, Échap : le panneau reste ouvert")
    elif await page.evaluate("() => document.activeElement?.dataset?.test ?? ''") != card_test:
        faults.append("Alertes, Échap : le focus ne revient pas à la carte")
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

        faults += await alert_panel(page)

        await browser.close()
    for fault in faults:
        print(fault)
    print(json.dumps({"défauts": len(faults)}, ensure_ascii=False))
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
