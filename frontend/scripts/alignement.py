"""Audit des rangées de contrôles (docs/94) : sur chaque page, les contrôles (boutons, listes de
choix, champs, sélecteurs, ⋯) qui sont sur une même rangée doivent avoir la même hauteur et le
même centre, à 2 px près. Le script n'écrit rien : il liste les rangées en défaut, et le
résultat doit être vide avant une PR d'interface.

    make demo                      # la démo locale, données fictives (http://localhost:5200)
    cd backend && uv run --with playwright python ../frontend/scripts/alignement.py

Options : l'adresse en premier argument (par défaut http://localhost:5200) ; CHROME=… pour
utiliser un navigateur installé plutôt que celui de Playwright. « Chercher d'autres
formations » n'apparaît qu'avec l'IA : le script la simule sur la page Formations.
"""

import asyncio
import json
import os
import sys

from playwright.async_api import Route, async_playwright

from explore import states

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5200"
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
    "reglages?rubrique=rythme",
    "reglages?rubrique=notifications",
    "reglages?rubrique=ia",
    "reglages?rubrique=compte",
    "reglages?rubrique=outils",
    "tes-donnees",
    "reglages/diagnostic",
]
SIZES = [{"width": 1440, "height": 900}, {"width": 390, "height": 844}]
TOLERANCE = 2

# Les contrôles visibles hors de la barre du haut, des panneaux et des menus ; regroupés quand
# ils se chevauchent verticalement dans un même bloc.
AUDIT = """(tolerance) => {
  const sel = 'button:not(.capsule-zone):not(.link):not([role=menuitem]):not(.tile-open), '
    + 'select, .segmented, a.button-link, input:not([type=checkbox]):not([type=radio])'
    + ':not([type=range]):not([type=hidden]):not([type=file])';
  const skip = '.topbar, .tab-bar, .side-panel, .bell-panel, .account-panel, '
    + '.more-menu .menu, [role=dialog]';
  const box = (e) => e.getBoundingClientRect();
  const els = [...document.querySelectorAll(sel)].filter((e) => {
    const r = box(e);
    return r.width > 0 && r.height > 0 && r.height < 70
      && getComputedStyle(e).visibility !== 'hidden' && !e.closest(skip)
      && !(e.tagName === 'BUTTON' && e.parentElement.closest('.segmented'));
  });
  const scope = (e) => e.closest('section, form, .container, .dash-card, header') || document.body;
  const parent = els.map((_, i) => i);
  const find = (i) => (parent[i] === i ? i : (parent[i] = find(parent[i])));
  for (let i = 0; i < els.length; i++) {
    for (let j = i + 1; j < els.length; j++) {
      const a = box(els[i]), b = box(els[j]);
      const overlap = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      const sameRow = overlap > 0.4 * Math.min(a.height, b.height);
      if (sameRow && scope(els[i]) === scope(els[j])) parent[find(i)] = find(j);
    }
  }
  const groups = {};
  els.forEach((e, i) => (groups[find(i)] = groups[find(i)] || []).push(e));
  const describe = (e) => {
    const r = box(e);
    const text = e.textContent || e.value || e.placeholder || e.getAttribute('aria-label') || '';
    const centre = Math.round((r.top + r.bottom) / 2);
    const name = `${e.tagName.toLowerCase()} « ${text.trim().slice(0, 24)} »`;
    return `${name} ${Math.round(r.height)} px, centre ${centre}`;
  };
  return Object.values(groups).filter((g) => {
    if (g.length < 2) return false;
    const heights = g.map((e) => box(e).height);
    const centres = g.map((e) => (box(e).top + box(e).bottom) / 2);
    const spread = (values) => Math.max(...values) - Math.min(...values);
    return spread(heights) > tolerance || spread(centres) > tolerance;
  }).map((g) => g.map(describe));
}"""


async def can_suggest(route: Route) -> None:
    response = await route.fetch()
    data = await response.json()
    data["can_suggest"] = True
    await route.fulfill(response=response, json=data)


async def main() -> int:
    faults = 0
    async with async_playwright() as p:
        chrome = os.environ.get("CHROME")
        launch = {"executable_path": chrome} if chrome else {}
        browser = await p.chromium.launch(**launch)
        for size in SIZES:
            context = await browser.new_context(viewport=size, reduced_motion="reduce")
            page = await context.new_page()
            await page.route("**/api/trainings?*", can_suggest)
            for path in PAGES:
                await page.goto(f"{BASE}/{path}")
                await page.wait_for_timeout(1800)
                async for state in states(page):
                    for row in await page.evaluate(AUDIT, TOLERANCE):
                        faults += 1
                        print(f"{size['width']} px  /{path}{state}\n  " + "\n  ".join(row))
            await context.close()
        await browser.close()
    print(json.dumps({"rangées en défaut": faults}, ensure_ascii=False))
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
