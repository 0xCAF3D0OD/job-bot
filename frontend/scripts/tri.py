"""Trier les offres (lot du 11 novembre au soir, PR 45) : sur la démo, à 390 et à 1440 px, trier les 3 offres du
jour (garder, écarter, garder) mène à « C’est trié ! » et à « 2 offres gardées, 1 écartée. », avec les deux offres
gardées et leur lien « Préparer ». « Écarter » et « Garder » sont de vrais boutons atteints au clavier ; ← et →
trient sur ordinateur ; « Annuler » remet l'offre sans rien envoyer ; le focus suit l'offre.

La démo refuse d'écrire : les changements d'état sont interceptés et vérifiés (« later » pour gardée, « ignored »
pour écartée), dans l'ordre.

    make audit-tri DEMO_URL=http://localhost:5200
"""

import asyncio
import json
import os
import sys

from playwright.async_api import BrowserContext, Route, async_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5200").rstrip("/")
KEEP, DISMISS = "[data-test=triage-keep]", "[data-test=triage-dismiss]"
TITLE = "[data-test=triage-title]"


async def run(context: BrowserContext, width: int) -> list[str]:
    faults: list[str] = []
    sent: list[str] = []
    page = await context.new_page()

    async def status(route: Route) -> None:
        if route.request.method != "PATCH":
            await route.continue_()
            return
        sent.append(json.loads(route.request.post_data or "{}").get("status", ""))
        await route.fulfill(json={})

    await page.route("**/api/offers/*/status", status)
    await page.goto(f"{BASE}/candidatures/trier")
    await page.wait_for_selector(KEEP, timeout=15000)

    def check(ok: bool, what: str) -> None:
        if not ok:
            faults.append(f"{width} px : {what}")

    check((await page.locator("h1").first.text_content() or "").strip() == "Trier les offres", "le titre n'est pas « Trier les offres »")
    count = (await page.locator("[data-test=triage-count]").text_content() or "").strip()
    check(count == "3 offres pour toi", f"l'accroche est « {count} »")
    check(await page.locator("[data-test=triage-offer]").get_attribute("aria-label") == "Offre 1 sur 3", "la région n'est pas nommée « Offre 1 sur 3 »")
    for selector, name in ((DISMISS, "Écarter"), (KEEP, "Garder")):
        button = page.locator(selector)
        check(await button.evaluate("(e) => e.tagName") == "BUTTON", f"« {name} » n'est pas un bouton")
        check((await button.text_content() or "").strip() == name, f"le bouton ne dit pas « {name} »")
        box = await button.bounding_box()
        check(bool(box and box["height"] >= 44 and box["width"] >= 44), f"« {name} » fait moins de 44 px")

    # Au clavier : la tabulation atteint « Écarter » puis « Garder », dans cet ordre.
    await page.locator(TITLE).focus()
    reached: list[str] = []
    for _ in range(12):
        await page.keyboard.press("Tab")
        test = await page.evaluate("() => document.activeElement?.getAttribute('data-test') ?? ''")
        if test in ("triage-dismiss", "triage-keep"):
            reached.append(test)
    check(reached[:2] == ["triage-dismiss", "triage-keep"], f"ordre de tabulation : {reached}")

    # « Annuler » : l'offre revient, rien n'est envoyé.
    first = (await page.locator(TITLE).text_content() or "").strip()
    await page.locator(KEEP).click()
    toast = page.locator("[data-test=triage-toast]")
    await toast.wait_for(timeout=3000)
    check(await toast.get_attribute("role") == "status", "le message n'a pas le rôle « status »")
    check("Offre gardée dans tes candidatures" in (await toast.text_content() or ""), "le message ne dit pas « Offre gardée dans tes candidatures »")
    await page.wait_for_timeout(500)  # la carte précédente a fini de partir
    check(await page.evaluate("(s) => document.activeElement === document.querySelector(s)", TITLE), "le focus ne va pas au titre de l'offre suivante")
    await toast.locator("[data-test=undo]").click()
    await page.wait_for_timeout(500)
    check((await page.locator(TITLE).text_content() or "").strip() == first, "« Annuler » ne remet pas l'offre")
    check(not sent, "« Annuler » a envoyé un changement d'état")

    # Garder, écarter, garder : au clic sur téléphone, aux flèches sur ordinateur.
    kept: list[str] = []
    for choice in ("keep", "dismiss", "keep"):
        if choice == "keep":
            kept.append((await page.locator(TITLE).text_content() or "").strip())
        if width >= 1024:
            await page.locator(TITLE).focus()
            await page.keyboard.press("ArrowRight" if choice == "keep" else "ArrowLeft")
        else:
            await page.locator(KEEP if choice == "keep" else DISMISS).click()
        await page.wait_for_timeout(500)

    done = page.locator("[data-test=triage-done]")
    try:
        # Sur téléphone, la fin du tri est un écran poussé (position fixe) : c'est son titre qu'on attend.
        await done.locator("h1").wait_for(timeout=3000)
    except Exception:
        return [*faults, f"{width} px : « C’est trié ! » n'apparaît pas après 3 choix"]
    heading = " ".join((await done.locator("h1").text_content() or "").split())
    check(heading == "C’est trié !", f"le titre de fin est « {heading} »")
    summary = (await done.locator("[data-test=triage-summary]").text_content() or "").strip()
    check(summary.startswith("2 offres gardées, 1 écartée."), f"le compte est « {summary} »")
    names = [(t or "").strip() for t in await done.locator("[data-test=triage-kept] li b").all_text_contents()]
    check(names == kept, f"les offres gardées affichées sont {names}, attendu {kept}")
    check(await done.locator("[data-test=triage-kept] a").count() == 2, "il n'y a pas un lien « Préparer » par offre gardée")
    check(await page.evaluate("() => document.activeElement === document.querySelector('[data-test=triage-done]')"), "le focus ne va pas à la fin du tri")

    # Quitter la page envoie le dernier choix : trois états, dans l'ordre.
    await done.locator("[data-test=triage-home]").click()
    await page.wait_for_timeout(1000)
    check(sent == ["later", "ignored", "later"], f"états envoyés : {sent}")
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
