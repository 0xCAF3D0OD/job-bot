"""Audit des contrôles de la démo, en 1440, 320, 360 et 390 px, sur chaque page et chaque état ouvert
(onglets, rubriques) ; il échoue si

- dans une même rangée de contrôles (boutons, listes de choix, champs, contrôles segmentés, ⋯ : mêmes
  bloc et ligne visuelle), les hauteurs diffèrent de plus de 1 px (docs/94, la règle de
  alignement.py) ;
- le texte d'une liste de choix passe sous son chevron : le chevron fait 1,1 rem et se trouve à
  --space-3 (0,75 rem) du bord droit, donc padding-left + le plus long choix (mesuré avec la police
  calculée) ≤ clientWidth − 0,75 rem − 1,1 rem. Le message nomme la liste et son padding-right.

    make demo                      # ou make demo-image (http://localhost:8280)
    make audit-controles DEMO_URL=http://localhost:5200
"""

import asyncio
import json
import os
import sys

from playwright.async_api import Route, async_playwright

from explore import states
from regles import PAGES

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5200"
SIZES = [
    {"width": 1440, "height": 900},
    {"width": 320, "height": 640},
    {"width": 360, "height": 640},
    {"width": 390, "height": 640},
]
TOLERANCE = 1

AUDIT = r"""(tolerance) => {
  const faults = [];
  const box = (e) => e.getBoundingClientRect();
  const rem = parseFloat(getComputedStyle(document.documentElement).fontSize);
  const visible = (e) => {
    const r = box(e), s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
  };

  // 1. Les rangées de contrôles : regroupés quand ils se chevauchent en hauteur dans un même bloc.
  const sel = 'button:not(.capsule-zone):not(.link):not([role=menuitem]):not(.tile-open), '
    + 'select, .segmented, a.button-link, input:not([type=checkbox]):not([type=radio])'
    + ':not([type=range]):not([type=hidden]):not([type=file])';
  const skip = '.topbar, .tab-bar, .side-panel, .bell-panel, .account-panel, '
    + '.more-menu .menu, [role=dialog]';
  const els = [...document.querySelectorAll(sel)].filter((e) => visible(e) && box(e).height < 70
    && !e.closest(skip) && !(e.tagName === 'BUTTON' && e.parentElement.closest('.segmented')));
  const scope = (e) => e.closest('section, form, .container, .dash-card, header') || document.body;
  const parent = els.map((_, i) => i);
  const find = (i) => (parent[i] === i ? i : (parent[i] = find(parent[i])));
  for (let i = 0; i < els.length; i++) {
    for (let j = i + 1; j < els.length; j++) {
      const a = box(els[i]), b = box(els[j]);
      const overlap = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (overlap > 0.4 * Math.min(a.height, b.height) && scope(els[i]) === scope(els[j])) parent[find(i)] = find(j);
    }
  }
  const groups = {};
  els.forEach((e, i) => (groups[find(i)] = groups[find(i)] || []).push(e));
  const name = (e) => {
    const text = e.tagName === 'SELECT'
      ? (e.getAttribute('aria-label') || (e.labels && e.labels[0] && e.labels[0].innerText) || e.name || '')
      : (e.innerText || e.value || e.placeholder || e.getAttribute('aria-label') || '');
    return `${e.tagName.toLowerCase()} « ${text.trim().replace(/\s+/g, ' ').slice(0, 30)} »`;
  };
  for (const g of Object.values(groups)) {
    if (g.length < 2) continue;
    const heights = g.map((e) => box(e).height);
    if (Math.max(...heights) - Math.min(...heights) <= tolerance + 0.01) continue;
    faults.push('rangée de hauteurs inégales : ' + g.map((e) => `${name(e)} ${Math.round(box(e).height * 10) / 10} px`).join(', '));
  }

  // 2. Le texte d'une liste de choix ne passe jamais sous son chevron.
  const ctx = document.createElement('canvas').getContext('2d');
  for (const s of document.querySelectorAll('select')) {
    if (!visible(s) || s.multiple || s.size > 1 || s.closest('[hidden]')) continue;
    const cs = getComputedStyle(s);
    ctx.font = `${cs.fontStyle} ${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
    let longest = '', width = 0;
    for (const o of s.options) {
      const w = ctx.measureText(o.text).width;
      if (w > width) { width = w; longest = o.text; }
    }
    const room = s.clientWidth - 0.75 * rem - 1.1 * rem;
    const needed = parseFloat(cs.paddingLeft) + width;
    if (needed > room + 0.5) {
      faults.push(`liste ${name(s)} : « ${longest.slice(0, 30)} » passe sous le chevron `
        + `(${Math.round(needed)} px pour ${Math.round(room)} px ; padding-right ${cs.paddingRight})`);
    }
  }
  return faults;
}"""


async def can_suggest(route: Route) -> None:
    """« Chercher d'autres formations » n'apparaît qu'avec l'IA : on la simule."""
    response = await route.fetch()
    data = await response.json()
    data["can_suggest"] = True
    await route.fulfill(response=response, json=data)


async def main() -> int:
    total = 0
    async with async_playwright() as p:
        chrome = os.environ.get("CHROME")
        browser = await p.chromium.launch(**({"executable_path": chrome} if chrome else {}))
        for size in SIZES:
            phone = size["width"] < 820
            context = await browser.new_context(viewport=size, reduced_motion="reduce", has_touch=phone, is_mobile=phone)
            page = await context.new_page()
            await page.route("**/api/trainings?*", can_suggest)
            for path in PAGES:
                await page.goto(f"{BASE}/{path}")
                await page.wait_for_timeout(1500)
                seen: set[str] = set()  # un défaut déjà vu dans un autre état de la page ne compte qu'une fois
                async for state in states(page):
                    for fault in await page.evaluate(AUDIT, TOLERANCE):
                        if fault in seen:
                            continue
                        seen.add(fault)
                        print(f"{size['width']} px  /{path}{state}  {fault}")
                        total += 1
            await context.close()
        await browser.close()
    print(json.dumps({"défauts": total}, ensure_ascii=False))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
