"""Objectif du mois (lot du 11 novembre au soir, PR 50) : sur la démo, à 390 et à 1440 px, ouvrir le Profil, toucher
« Suivi ORP », appuyer deux fois sur « plus », enregistrer ; la ligne dit « {objectif + 2} recherches par mois », puis
l'Accueil (ou Aujourd'hui) et le Suivi ORP montrent le nouvel objectif, sans rechargement de la page.

Le panneau est une fenêtre modale nommée « Objectif du mois » ; le compteur est un `spinbutton` (flèches haut et bas) ;
les deux boutons ronds font 56 px et portent leur nom ; « Annuler » ferme sans rien envoyer et rend le focus à la ligne.

La démo refuse d'écrire : l'enregistrement des réglages est intercepté et vérifié (seul l'objectif change), puis les
lectures suivantes (réglages, Aujourd'hui, mois ORP, résumé du mois) répondent avec le nouvel objectif, comme le
ferait le serveur.

    make audit-objectif DEMO_URL=http://localhost:5200
"""

import asyncio
import json
import os
import sys

from playwright.async_api import BrowserContext, Route, async_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5200").rstrip("/")
ROW = "[data-test=criteria-row-orp]"
VALUE = "[data-test=goal-value]"


async def run(context: BrowserContext, width: int) -> list[str]:
    faults: list[str] = []
    saved: dict[str, object] = {}
    sent: list[dict[str, object]] = []
    page = await context.new_page()

    def check(ok: bool, what: str) -> None:
        if not ok:
            faults.append(f"{width} px : {what}")

    async def settings(route: Route) -> None:
        if route.request.method == "PUT":
            body = json.loads(route.request.post_data or "{}")
            sent.append(body)
            saved.update(body)
            await route.fulfill(json=body)
        elif saved:
            await route.fulfill(json=saved)
        else:
            await route.continue_()

    def patched(key: str):
        async def handler(route: Route) -> None:
            if not saved or route.request.method != "GET":
                await route.continue_()
                return
            response = await route.fetch()
            body = await response.json()
            body[key] = saved["orp_monthly_target"]
            await route.fulfill(response=response, json=body)

        return handler

    await page.route("**/api/settings", settings)
    await page.route("**/api/today", patched("month_target"))
    await page.route("**/api/orp?*", patched("target"))
    await page.route("**/api/orp", patched("target"))
    await page.route("**/api/applications/summary*", patched("target"))

    await page.goto(f"{BASE}/profil")
    row = page.locator(ROW)
    await row.wait_for(timeout=15000)
    await page.evaluate("window.__sansRechargement = true")
    before_text = (await row.locator(".criteria-row-value").text_content() or "").strip()
    before = int(before_text.split()[0])
    check(before_text == f"{before} recherches par mois", f"la ligne dit « {before_text} »")
    check((await row.locator(".criteria-row-label").text_content() or "").strip() == "Suivi ORP", "la ligne ne s'appelle pas « Suivi ORP »")
    labels = [((await e.text_content()) or "").strip() for e in await page.locator("[data-test=criteria-summary] .criteria-row-label").all()]
    check(labels[-2:] == ["Langues", "Suivi ORP"], f"« Suivi ORP » ne suit pas « Langues » : {labels}")

    # « Annuler » : rien n'est envoyé, le focus revient à la ligne.
    await row.click()
    dialog = page.locator("dialog[data-test=goal-sheet]")
    await page.locator(VALUE).wait_for()
    check(await dialog.evaluate("(e) => e.matches(':modal')"), "le panneau n'est pas une fenêtre modale")
    title = await dialog.evaluate("(e) => document.getElementById(e.getAttribute('aria-labelledby'))?.textContent.trim()")
    check(title == "Objectif du mois", f"le panneau s'appelle « {title} »")
    await page.locator("[data-test=goal-more]").click()
    await page.locator("[data-test=goal-cancel]").click()
    await page.wait_for_timeout(400)
    check(not sent, "« Annuler » a envoyé un enregistrement")
    check(await row.evaluate("(e) => e === document.activeElement"), "après « Annuler », le focus n'est pas rendu à la ligne")

    await row.click()
    value = page.locator(VALUE)
    await value.wait_for()
    attributes = await value.evaluate("(e) => Object.fromEntries(['role','aria-label','aria-valuenow','aria-valuemin','aria-valuemax','tabindex'].map((n) => [n, e.getAttribute(n)]))")
    wanted = {"role": "spinbutton", "aria-label": "Recherches par mois", "aria-valuenow": str(before), "aria-valuemin": "1", "aria-valuemax": "99", "tabindex": "0"}
    check(attributes == wanted, f"le compteur : {attributes}")
    for selector, name in (("[data-test=goal-less]", "Une recherche de moins"), ("[data-test=goal-more]", "Une recherche de plus")):
        button = page.locator(selector)
        check(await button.get_attribute("aria-label") == name, f"le bouton ne s'appelle pas « {name} »")
        box = await button.bounding_box()
        check(bool(box and round(box["width"]) == 56 and round(box["height"]) == 56), f"« {name} » ne fait pas 56 px")
    # Au clavier : flèche haut, flèche bas.
    await value.focus()
    await page.keyboard.press("ArrowUp")
    check(await value.get_attribute("aria-valuenow") == str(before + 1), "la flèche haut n'ajoute pas une recherche")
    await page.keyboard.press("ArrowDown")
    check(await value.get_attribute("aria-valuenow") == str(before), "la flèche bas n'enlève pas une recherche")

    await page.locator("[data-test=goal-more]").click()
    await page.locator("[data-test=goal-more]").click()
    await page.locator("[data-test=goal-save]").click()
    await page.wait_for_function(f"document.querySelector('{ROW} .criteria-row-value')?.textContent.trim() === '{before + 2} recherches par mois'", timeout=5000)
    check(len(sent) == 1 and sent[0].get("orp_monthly_target") == before + 2, f"l'enregistrement : {[s.get('orp_monthly_target') for s in sent]}")
    check(not await dialog.evaluate("(e) => e.open"), "le panneau reste ouvert après « Enregistrer »")

    # L'Accueil (téléphone) ou Aujourd'hui (ordinateur), puis le Suivi ORP, par les liens de l'application.
    await page.locator('a[href="/aujourdhui"]:visible').first.click()
    home = page.locator("[data-test=orp-bar] [data-test=month-count]").first
    await home.wait_for(timeout=15000)
    text = (await home.text_content() or "").strip()
    check(text.endswith(f" sur {before + 2}"), f"l'Accueil dit « {text} »")
    await page.locator("[data-test=home-orp], [data-test=orp-month-link]").first.click()
    await page.wait_for_url("**/bilan**")
    bar = page.locator("[data-test=orp-bar] [data-test=month-count]").first
    await bar.wait_for(timeout=15000)
    text = (await bar.text_content() or "").strip()
    check(text.endswith(f" sur {before + 2}"), f"le Suivi ORP dit « {text} »")
    check(await page.evaluate("window.__sansRechargement === true"), "la page a été rechargée en chemin")
    await page.close()
    return faults


async def main() -> int:
    faults: list[str] = []
    async with async_playwright() as p:
        chrome = os.environ.get("CHROME")
        browser = await p.chromium.launch(**({"executable_path": chrome} if chrome else {}))
        for width, height in ((390, 844), (1440, 900)):
            phone = width < 821
            context = await browser.new_context(viewport={"width": width, "height": height}, has_touch=phone, is_mobile=phone)
            faults += await run(context, width)
            await context.close()
        await browser.close()
    for fault in faults:
        print(fault)
    print(json.dumps({"défauts": len(faults)}, ensure_ascii=False))
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
