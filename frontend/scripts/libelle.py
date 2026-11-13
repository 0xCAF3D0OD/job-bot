"""Libellé flottant des champs (FormField ; défaut du 13 novembre) : sur la démo, en clair et en sombre, le libellé
posé sur la bordure du haut l'interrompt, et aucun trait ne passe derrière ses lettres, au repos (champ rempli), au
focus, en erreur et en erreur avec le focus.

Deux champs : « Lien ou texte de l'annonce » du volet « Ajouter une offre » (1440 px) et le lieu du volet « Nouveau
rendez-vous » (390 px, où le fond de la feuille n'est pas celui du champ).

Le contrôle lit les pixels d'une capture du champ, plutôt que de la comparer à une image de référence, qui changerait
avec le rendu des polices d'une machine à l'autre :

- au-dessus du champ, sur la largeur du libellé, aucune rangée de pixels n'est un trait (une rangée dont plus de
  90 % des pixels ne sont pas le fond ; une ligne de texte a des blancs entre ses lettres, un trait n'en a pas) ;
- sous le libellé, la bordure du champ est interrompue, marge de 4 px comprise de chaque côté du texte ;
- rien n'est dessiné à l'extérieur du champ : pas de contour, et toute ombre est intérieure (`inset`).

    make audit-libelle DEMO_URL=http://localhost:5200
"""

import asyncio
import io
import json
import os
import sys

from PIL import Image
from playwright.async_api import Page, Route, async_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5200").rstrip("/")
SCALE = 2
STATES = ("repos", "focus", "erreur", "erreur et focus")

GEOMETRY = """(field) => {
  const box = field.closest('.form-field-box'), label = box.querySelector('.form-field-label');
  const text = label.querySelector('.form-field-text') ?? label;
  const a = label.getBoundingClientRect(), b = field.getBoundingClientRect(), c = text.getBoundingClientRect();
  const style = getComputedStyle(field);
  return { label: [a.left, a.top, a.right, a.bottom], field: [b.left, b.top, b.right, b.bottom], text: [c.left, c.right],
    shadow: style.boxShadow, outline: style.outlineStyle, border: parseFloat(style.borderTopWidth) };
}"""


def far(a: tuple[int, ...], b: tuple[int, ...]) -> bool:
    return sum(abs(x - y) for x, y in zip(a[:3], b[:3], strict=False)) > 36


async def audit(page: Page, selector: str, where: str) -> list[str]:
    faults: list[str] = []
    field = page.locator(selector).first
    await field.wait_for(timeout=15000)
    await page.wait_for_timeout(500)  # le volet a fini de glisser
    for state in STATES:
        await field.fill("Rue du Test 1")
        await field.evaluate("(e, bad) => bad ? e.setAttribute('aria-invalid', 'true') : e.removeAttribute('aria-invalid')", "erreur" in state)
        if "focus" in state:
            await field.focus()
        else:
            await field.evaluate("(e) => e.blur()")
        await page.wait_for_timeout(300)
        g = await field.evaluate(GEOMETRY)
        left, top, right, _ = g["label"]
        f_top = g["field"][1]
        name = f"{where}, {state}"

        layers = [layer for layer in g["shadow"].replace("), ", ")|").split("|") if layer and layer != "none"]
        if any("inset" not in layer for layer in layers):
            faults.append(f"{name} : une ombre est dessinée à l'extérieur du champ ({g['shadow']})")
        if g["outline"] != "none":
            faults.append(f"{name} : un contour est dessiné à l'extérieur du champ")
        if g["text"][0] - left < 4 - 0.5 or right - g["text"][1] < 4 - 0.5:
            faults.append(f"{name} : moins de 4 px de marge autour du texte du libellé")

        # La capture : du haut du libellé (2 px de plus) au bas de la bordure du champ (3 px de plus), sur sa largeur.
        clip = {"x": left, "y": top - 2, "width": right - left, "height": (f_top - top) + 2 + g["border"] + 3}
        image = Image.open(io.BytesIO(await page.screenshot(clip=clip))).convert("RGB")
        width, height = image.size
        outside = image.getpixel((1, 0))  # le fond du conteneur, au-dessus du libellé
        above = round((f_top - top + 2) * SCALE)  # les rangées au-dessus du champ
        for y in range(min(above, height)):
            drawn = sum(far(image.getpixel((x, y)), outside) for x in range(width))
            if drawn > 0.9 * width:
                faults.append(f"{name} : un trait passe derrière le libellé, {round(y / SCALE - 2, 1)} px sous son bord haut")
                break
        # La bordure interrompue : dans les marges de 4 px, à gauche et à droite du texte, sur la hauteur de la bordure.
        inside = image.getpixel((1, height - 1))  # le fond du champ, sous la bordure
        for side, x0 in (("gauche", 1), ("droite", width - round(3 * SCALE))):
            cut = all(
                not far(image.getpixel((x, y)), inside)
                for x in range(x0, x0 + round(2 * SCALE))
                for y in range(above, min(above + round(g["border"] * SCALE), height))
            )
            if not cut:
                faults.append(f"{name} : la bordure n'est pas interrompue à {side} du libellé")
    return faults


async def main() -> int:
    faults: list[str] = []
    async with async_playwright() as p:
        chrome = os.environ.get("CHROME")
        browser = await p.chromium.launch(**({"executable_path": chrome} if chrome else {}))
        for scheme, tone in (("light", "clair"), ("dark", "sombre")):
            context = await browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme=scheme, device_scale_factor=SCALE, reduced_motion="reduce")
            page = await context.new_page()
            await page.goto(f"{BASE}/candidatures/offres")
            await page.locator("[data-test=manual-open]").first.click()
            faults += await audit(page, "dialog[open] [data-test=manual-entry]", f"1440 px, {tone}, « Lien ou texte de l’annonce »")
            await context.close()

            context = await browser.new_context(viewport={"width": 390, "height": 844}, color_scheme=scheme, device_scale_factor=SCALE, reduced_motion="reduce")
            page = await context.new_page()

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
            await page.locator("[data-test=meeting-add]").first.click()
            faults += await audit(page, "dialog[open] [data-test=meeting-where]", f"390 px, {tone}, lieu du rendez-vous")
            await context.close()
        await browser.close()
    for fault in faults:
        print(fault)
    print(json.dumps({"défauts": len(faults)}, ensure_ascii=False))
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
