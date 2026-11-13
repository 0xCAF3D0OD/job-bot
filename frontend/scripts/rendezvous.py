"""« Nouveau rendez-vous », étape du choix de la date (défaut du 13 novembre) : sur la démo, le sélecteur tient dans
le volet à 1440, 1280 et 1024 px, et dans la feuille du bas à 390 et 320 px. Aucun défilement horizontal (WCAG
1.4.10) : `scrollWidth` égal à `clientWidth` sur le volet et sur tout ce qu'il contient ; chaque heure tient dans la
largeur du volet et s'atteint en défilant de haut en bas ; « Valider » est dans la zone visible sans défiler.

Sur téléphone, la démo a déjà un rendez-vous ORP : la page reçue est modifiée ici (aucun rendez-vous à venir), pour
passer par « Ajouter ».

Ajout (défaut 2 du 13 novembre), à 1440 px : un rendez-vous ORP pour « Demain » à 10 h, depuis « Nouveau
rendez-vous » puis depuis « Ajouter » de « Prochain rendez-vous » d'une fiche passée ; il est annoncé (rôle
« status »), sous « À venir », sélectionné, repris dans la fiche passée, et encore là après rechargement. Si
l'enregistrement échoue, le volet reste ouvert, garde la saisie et le dit.

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


async def add_meeting(context: BrowserContext, opener: str) -> list[str]:
    """Défaut 2 du 13 novembre : ajouter un rendez-vous ORP pour « Demain » à 10 h, depuis « Nouveau rendez-vous »
    (`rdv-add`) ou depuis « Ajouter » de « Prochain rendez-vous » d'une fiche passée (`outcome-next-add`). Le volet se
    ferme, un message de statut l'annonce, le rendez-vous est sous « À venir » et sélectionné, la fiche passée affiche
    sa date sans rechargement, et il est encore là après rechargement.

    La démo refuse d'écrire et a déjà un rendez-vous prévu : la page reçue est modifiée ici (aucun rendez-vous à
    venir), et l'enregistrement est simulé, puis rendu par les lectures suivantes."""
    faults: list[str] = []
    saved: dict[str, object] = {}
    page = await context.new_page()

    def check(ok: bool, what: str) -> None:
        if not ok:
            faults.append(f"1440 px, depuis {opener} : {what}")

    async def meeting(route: Route) -> None:
        method = route.request.method
        if method not in ("GET", "PUT"):
            await route.continue_()
            return
        response = await context.request.get(f"{BASE}/api/orp-meeting")
        body = await response.json()
        if method == "PUT":
            sent = json.loads(route.request.post_data or "{}")
            saved.update(id=99, starts_at=sent["starts_at"], place=sent.get("place") or None, advisor=None, outcome_at=None,
                         agreed_target=None, measures=[], assignments=None, note=None, asked=[], next_starts_at=None, sheet_text=None)
        body["meeting"] = dict(saved) if saved else None
        for past in body["past"]:
            past["next_starts_at"] = saved.get("starts_at")
        await route.fulfill(json=body)

    await page.route("**/api/orp-meeting", meeting)
    await page.goto(f"{BASE}/candidatures/rendez-vous-orp")
    await page.locator("[data-test=rdv-add]").wait_for(timeout=15000)
    past = page.locator("[data-test^=rdv-item-passe-]").first
    await past.click()
    next_line = page.locator("[data-test=outcome-inline] [data-test=outcome-next]")
    check("Pas encore noté" in (await next_line.text_content() or ""), "la fiche passée ne dit pas « Pas encore noté » avant l'ajout")

    await page.locator(f"[data-test={opener}]").first.click()
    await page.wait_for_selector("[data-test=new-meeting-form]", timeout=5000)
    orp = page.locator(f"{SHEET} [data-test=meeting-kind-orp]")
    if opener == "outcome-next-add":
        check(await orp.get_attribute("aria-checked") == "true",
              "depuis une fiche ORP, le volet ne s'ouvre pas sur « L’ORP »")
    else:
        await orp.click()
    await page.locator(f"{SHEET} [data-test=dt-date]").click()
    await page.locator(f"{SHEET} [data-test='dt-shortcut-Demain']").click()
    await page.locator(f"{SHEET} [data-test='dt-slot-10:00']").click()
    await page.locator(f"{SHEET} [data-test=dt-confirm]").click()
    await page.locator(f"{SHEET} [data-test=meeting-save]").click()

    try:
        await page.locator(f"dialog{SHEET}[open]").wait_for(state="detached", timeout=4000)
    except Exception:
        check(not await page.locator(f"dialog{SHEET}[open]").count(), "le volet ne se ferme pas après l'ajout")
    check(bool(saved), "aucun enregistrement n'est parti")
    toast = page.locator("[data-test=meeting-added]")
    try:
        await toast.wait_for(timeout=3000)
        check(await toast.get_attribute("role") == "status", "le message d'ajout n'a pas le rôle « status »")
        text = " ".join((await toast.text_content() or "").split())
        check(text.startswith("Rendez-vous ajouté") and "10 h" in text, f"le message d'ajout dit « {text} »")
    except Exception:
        check(False, "aucun message de statut n'annonce l'ajout")
    item = page.locator("[data-test=rdv-item-orp]")
    check(await item.count() == 1, "le rendez-vous n'est pas sous « À venir »")
    if await item.count():
        try:
            await page.wait_for_url("**rdv=orp*", timeout=3000)
        except Exception:
            pass
        check(await item.get_attribute("aria-current") == "true", "le rendez-vous ajouté n'est pas sélectionné")
        check("10 h" in (await item.text_content() or ""), "la ligne « À venir » ne montre pas 10 h")
    check("Aucun rendez-vous à venir" not in (await page.locator("[data-test=rdv-desktop]").text_content() or ""), "« Aucun rendez-vous à venir » est encore affiché")
    # La fiche passée, sans rechargement : « Prochain rendez-vous » affiche la date.
    await past.click()
    line = " ".join((await next_line.text_content() or "").split())
    check("Pas encore noté" not in line and "10 h" in line, f"« Prochain rendez-vous » de la fiche passée dit « {line} »")
    # Après rechargement : toujours là.
    await page.reload()
    await page.locator("[data-test=rdv-add]").wait_for(timeout=15000)
    check(await page.locator("[data-test=rdv-item-orp]").count() == 1, "après rechargement, le rendez-vous n'est plus sous « À venir »")
    await page.locator("[data-test^=rdv-item-passe-]").first.click()
    line = " ".join((await next_line.text_content() or "").split())
    check("10 h" in line, f"après rechargement, « Prochain rendez-vous » dit « {line} »")
    await page.close()
    return faults


async def failed_save(context: BrowserContext) -> list[str]:
    """Jamais d'échec silencieux : si l'enregistrement échoue (serveur en erreur, puis connexion coupée), le volet
    reste ouvert, la saisie est gardée et un message le dit."""
    faults: list[str] = []
    page = await context.new_page()
    mode = {"abort": False}

    async def refuse(route: Route) -> None:
        if route.request.method != "PUT":
            await route.continue_()
        elif mode["abort"]:
            await route.abort()
        else:
            await route.fulfill(status=500, json={"detail": [{"msg": "erreur"}]})

    await page.route("**/api/orp-meeting", refuse)
    await page.goto(f"{BASE}/candidatures/rendez-vous-orp")
    await page.locator("[data-test=rdv-add]").click()
    await page.wait_for_selector("[data-test=new-meeting-form]", timeout=5000)
    await page.locator(f"{SHEET} [data-test=meeting-kind-orp]").click()
    await page.locator(f"{SHEET} [data-test=dt-date]").click()
    await page.locator(f"{SHEET} [data-test='dt-shortcut-Demain']").click()
    await page.locator(f"{SHEET} [data-test='dt-slot-10:00']").click()
    await page.locator(f"{SHEET} [data-test=dt-confirm]").click()
    for what in ("le serveur répond par une erreur", "la connexion est coupée"):
        await page.locator(f"{SHEET} [data-test=meeting-save]").click()
        alert = page.locator(f"{SHEET} [role=alert]")
        try:
            await alert.first.wait_for(timeout=4000)
            text = " ".join((await alert.first.text_content() or "").split())
            if "n’est pas enregistré" not in text:
                faults.append(f"1440 px, {what} : le message dit « {text} »")
        except Exception:
            faults.append(f"1440 px, {what} : aucun message, l'échec est silencieux")
        if not await page.locator(f"dialog{SHEET}[open]").count():
            faults.append(f"1440 px, {what} : le volet s'est fermé")
        time = " ".join((await page.locator(f"{SHEET} [data-test=dt-time]").text_content() or "").split())
        if "10" not in time:
            faults.append(f"1440 px, {what} : la saisie n'est pas gardée (« {time} »)")
        mode["abort"] = True
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
        for opener in ("rdv-add", "outcome-next-add"):
            # L'heure s'affiche à l'heure suisse : le navigateur du test aussi.
            context = await browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce", timezone_id="Europe/Zurich")
            faults += await add_meeting(context, opener)
            await context.close()
        context = await browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        faults += await failed_save(context)
        await context.close()
        await browser.close()
    for fault in faults:
        print(fault)
    print(json.dumps({"défauts": len(faults)}, ensure_ascii=False))
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
