"""Audit d'accessibilité (docs/117 §1) : axe-core, la référence des contrôles WCAG, sur chaque
page de la démo, sur ordinateur et sur téléphone, plus un parcours au clavier. Le script
n'écrit rien : il liste les défauts « graves » et « critiques » et le parcours qui bloque ; le
résultat doit être vide avant une PR d'interface.

    make demo                      # la démo locale, données fictives (http://localhost:5200)
    cd backend && uv run --with playwright python ../frontend/scripts/accessibilite.py

Options : l'adresse en premier argument (par défaut http://localhost:5200) ; CHROME=… pour
utiliser un navigateur installé plutôt que celui de Playwright.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from playwright.async_api import Page, async_playwright

from explore import states

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5200"
AXE = (Path(__file__).parent.parent / "node_modules" / "axe-core" / "axe.min.js").read_text()
PAGES = [
    "aujourdhui",
    "candidatures/offres",
    "candidatures/suivi",
    "candidatures/alertes",
    "bilan",
    "candidatures/rendez-vous-orp",
    "bilan/formations",
    "profil",
    "profil?onglet=parcours",
    "profil?onglet=coordonnees",
    "reglages",
    "tes-donnees",
    "accessibilite",
    "la-plateforme",
]
SIZES = [{"width": 1440, "height": 900}, {"width": 390, "height": 844}]
# Les niveaux qui bloquent une PR ; « modéré » et « mineur » sont listés à part, sans bloquer.
BLOCKING = ("critical", "serious")
# SCHEME=dark pour vérifier les contrastes en mode sombre (docs/133).
SCHEME = "dark" if os.environ.get("SCHEME") == "dark" else "light"

RUN = """async () => {
  const result = await axe.run(document, { resultTypes: ['violations'] });
  return result.violations.map((v) => ({
    id: v.id, impact: v.impact, help: v.help,
    nodes: v.nodes.slice(0, 3).map((n) => n.target.join(' ')),
    count: v.nodes.length,
  }));
}"""


async def audit(page: Page, path: str, width: int) -> tuple[int, int]:
    await page.goto(f"{BASE}/{path}")
    await page.wait_for_timeout(1800)
    await page.add_script_tag(content=AXE)
    blocking = minor = 0
    async for state in states(page):
        for v in await page.evaluate(RUN):
            if v["impact"] in BLOCKING:
                blocking += 1
                print(f"{width} px  /{path}{state}  [{v['impact']}] {v['id']} : {v['help']} ({v['count']})")
                for node in v["nodes"]:
                    print(f"    {node}")
            else:
                minor += 1
    return blocking, minor


async def focused(page: Page) -> str:
    return await page.evaluate(
        "(() => { const e = document.activeElement; if (!e) return '';"
        " return (e.getAttribute('aria-label') || e.textContent || '').trim().slice(0, 40); })()"
    )


async def tab_to(page: Page, text: str, limit: int = 80) -> bool:
    """Tab jusqu'à l'élément dont le nom contient `text` ; il doit montrer un contour."""
    for _ in range(limit):
        await page.keyboard.press("Tab")
        if text.lower() in (await focused(page)).lower():
            outline = await page.evaluate(
                "(() => { const s = getComputedStyle(document.activeElement);"
                " return s.outlineStyle !== 'none' || s.boxShadow !== 'none'; })()"
            )
            return bool(outline)
    return False


async def keyboard_journey(page: Page) -> list[str]:
    """Aujourd'hui → Candidatures → une offre → « Cette note ne me correspond pas », au clavier."""
    problems: list[str] = []
    await page.goto(f"{BASE}/aujourdhui")
    await page.wait_for_timeout(1800)
    if not await tab_to(page, "Candidatures"):
        problems.append("« Candidatures » introuvable au clavier, ou sans contour visible")
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(1800)
    if "/candidatures" not in page.url:
        problems.append("Entrée sur « Candidatures » n'ouvre pas la page")
    await page.goto(f"{BASE}/candidatures/offres")
    await page.wait_for_timeout(1800)
    first = await page.evaluate(
        "(() => { const b = document.querySelector('.offer-row');"
        " return b ? (b.getAttribute('aria-label') || b.textContent || '').trim().slice(0, 20) : ''; })()"
    )
    # Un compte sans offre (docs/128) : rien à atteindre, l'écran vide est vérifié plus haut.
    if not first:
        if not await page.query_selector("[data-test=offers-none-yet]"):
            problems.append("aucune offre affichée, et pas d'écran vide qui le dise")
    elif not await tab_to(page, first):
        problems.append("la première offre n'est pas atteignable au clavier")
    else:
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(1500)
        if not await tab_to(page, "Cette note ne me correspond pas", 120):
            problems.append("« Cette note ne me correspond pas » introuvable au clavier")
        else:
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(500)
            if not await tab_to(page, "Trop haute", 10):
                problems.append("après « Cette note… », « Trop haute » n'est pas le suivant au clavier")
    await page.keyboard.press("Escape")
    return problems


async def main() -> int:
    blocking = minor = 0
    async with async_playwright() as p:
        chrome = os.environ.get("CHROME")
        browser = await p.chromium.launch(**({"executable_path": chrome} if chrome else {}))
        for size in SIZES:
            context = await browser.new_context(viewport=size, reduced_motion="reduce", color_scheme=SCHEME)
            page = await context.new_page()
            for path in PAGES:
                b, m = await audit(page, path, size["width"])
                blocking, minor = blocking + b, minor + m
            await context.close()
        context = await browser.new_context(viewport=SIZES[0], reduced_motion="reduce")
        problems = await keyboard_journey(await context.new_page())
        for problem in problems:
            print(f"clavier : {problem}")
        await browser.close()
    print(
        json.dumps(
            {"défauts graves": blocking, "défauts mineurs": minor, "parcours au clavier": problems},
            ensure_ascii=False,
        )
    )
    return 1 if blocking or problems else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
