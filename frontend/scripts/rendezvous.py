"""« Nouveau rendez-vous », étape du choix de la date (défaut du 13 novembre) : sur la démo, le sélecteur tient dans
le volet à 1440, 1280 et 1024 px, et dans la feuille du bas à 390 et 320 px. Aucun défilement horizontal (WCAG
1.4.10) : `scrollWidth` égal à `clientWidth` sur le volet et sur tout ce qu'il contient ; chaque heure tient dans la
largeur du volet et s'atteint en défilant de haut en bas ; « Valider » est dans la zone visible sans défiler.

Sur téléphone, la démo a déjà un rendez-vous ORP : la page reçue est modifiée ici (aucun rendez-vous à venir), pour
passer par « Ajouter ».

    make audit-rendez-vous DEMO_URL=http://localhost:5200
"""

import asyncio
import json
import os
import sys

from playwright.async_api import BrowserContext, Route, async_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5200").rstrip("/")
SHEET = "[data-test=new-meeting]"
SIZES = ((1440, 900), (1280, 800), (1024, 768), (390, 844), (320, 640))

# Ce qui déborde de côté dans le volet : lui-même, ou n'importe lequel de ses blocs qui défile (hors textes réservés
# aux lecteurs d'écran, d'un pixel de large).
OVERFLOW = """(sheet) => [sheet, ...sheet.querySelectorAll('*')]
  .filter((el) => el.clientWidth > 1 && el.scrollWidth > el.clientWidth + 1 && getComputedStyle(el).overflowX !== 'visible')
  .map((el) => `${el.className || el.tagName} (${el.scrollWidth} pour ${el.clientWidth})`)"""
# Dans la zone visible : dans le volet et dans la fenêtre, sur les quatre côtés.
VISIBLE = """([el, sheet]) => {
  const a = el.getBoundingClientRect(), b = sheet.getBoundingClientRect();
  return a.width > 0 && a.left >= b.left - 1 && a.right <= b.right + 1 && a.top >= b.top - 1
    && a.bottom <= Math.min(b.bottom, innerHeight) + 1;
}"""
INSIDE_WIDTH = """([el, sheet]) => {
  const a = el.getBoundingClientRect(), b = sheet.getBoundingClientRect();
  return a.width > 0 && a.left >= b.left - 1 && a.right <= b.right + 1;
}"""


async def date_step(context: BrowserContext, width: int) -> list[str]:
    faults: list[str] = []
    page = await context.new_page()

    def check(ok: bool, what: str) -> None:
        if not ok:
            faults.append(f"{width} px : {what}")

    if width < 1024:

        async def no_meeting(route: Route) -> None:
            if route.request.method != "GET":
                await route.continue_()
                return
            response = await route.fetch()
            body = await response.json()
            body["meeting"] = None
            await route.fulfill(response=response, json=body)

        await page.route("**/api/orp-meeting", no_meeting)
    await page.goto(f"{BASE}/candidatures/rendez-vous-orp")
    opener = page.locator("[data-test=rdv-add]" if width >= 1024 else "[data-test=meeting-add]")
    await opener.first.wait_for(timeout=15000)
    await opener.first.click()
    await page.wait_for_selector("[data-test=new-meeting-form]", timeout=5000)
    await page.locator(f"{SHEET} [data-test=dt-date]").click()
    confirm = page.locator(f"{SHEET} [data-test=dt-confirm]")
    await confirm.wait_for(timeout=5000)
    await page.wait_for_timeout(400)  # le sélecteur a fini de glisser
    sheet = await page.locator(SHEET).element_handle()
    assert sheet

    wide = await page.evaluate(OVERFLOW, sheet)
    check(not wide, f"défilement horizontal dans le volet : {', '.join(wide)}")
    check(await page.evaluate(VISIBLE, [await confirm.element_handle(), sheet]), "« Valider » n'est pas dans la zone visible")

    slots = page.locator(f"{SHEET} [data-test^=dt-slot-]")
    count = await slots.count()
    check(count >= 9, f"{count} heures proposées, 9 attendues au moins")
    for index in range(count):
        slot = slots.nth(index)
        name = (await slot.text_content() or "").strip()
        handle = await slot.element_handle()
        check(await page.evaluate(INSIDE_WIDTH, [handle, sheet]), f"l'heure {name} dépasse du volet")
        await slot.scroll_into_view_if_needed()
        check(await page.evaluate(VISIBLE, [handle, sheet]), f"l'heure {name} n'est pas atteignable en défilant de haut en bas")
        box = await slot.bounding_box()
        check(bool(box and box["height"] >= 44 and box["width"] >= 44), f"l'heure {name} fait moins de 44 px")
    other = page.locator(f"{SHEET} [data-test=dt-typed-time]")
    await other.scroll_into_view_if_needed()
    check(await page.evaluate(VISIBLE, [await other.element_handle(), sheet]), "« Autre heure » n'est pas atteignable")
    # Après avoir défilé jusqu'en bas, « Valider » est toujours là, et rien ne défile de côté.
    check(await page.evaluate(VISIBLE, [await confirm.element_handle(), sheet]), "« Valider » sort de la vue quand on défile")
    wide = await page.evaluate(OVERFLOW, sheet)
    check(not wide, f"défilement horizontal après défilement : {', '.join(wide)}")

    # Choisir « Demain » puis 10 h, valider : retour au formulaire, la date et l'heure sont reprises.
    await page.locator(f"{SHEET} [data-test='dt-shortcut-Demain']").click()
    await page.locator(f"{SHEET} [data-test='dt-slot-10:00']").click()
    await confirm.click()
    await page.wait_for_selector("[data-test=new-meeting-form]", timeout=5000)
    time = " ".join((await page.locator(f"{SHEET} [data-test=dt-time]").text_content() or "").split())
    check("10" in time, f"l'heure choisie n'est pas reprise dans le formulaire (« {time} »)")
    save = page.locator(f"{SHEET} [data-test=meeting-save]")
    check(await page.evaluate(VISIBLE, [await save.element_handle(), sheet]), "« Ajouter le rendez-vous » n'est pas dans la zone visible")
    await page.close()
    return faults


async def main() -> int:
    faults: list[str] = []
    async with async_playwright() as p:
        chrome = os.environ.get("CHROME")
        browser = await p.chromium.launch(**({"executable_path": chrome} if chrome else {}))
        for width, height in SIZES:
            context = await browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce")
            faults += await date_step(context, width)
            await context.close()
        await browser.close()
    for fault in faults:
        print(fault)
    print(json.dumps({"défauts": len(faults)}, ensure_ascii=False))
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
