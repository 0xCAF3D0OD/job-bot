"""Audit des règles de l'interface (docs/118 §4, docs/interface.md) : sur chaque page de la
démo, sur ordinateur et sur téléphone, ce que les règles interdisent et qu'un script peut voir.
Il n'écrit rien : il liste les défauts, et le résultat doit être vide avant une PR d'interface.

- un texte d'aide de plus de 16 mots (description, indication, encadré ; docs/132) ;
- un titre (de page, de carte, de section, de repliable, légende) avec « je, tu, ton, ta,
  tes, mon, ma, mes » ou qui finit par « ? » ;
- une barre verticale dans une carte ;
- deux cadres l'un dans l'autre ;
- un texte à moins de 1,25 rem du bord de sa carte (docs/93) ;
- deux cartes d'une même rangée de hauteurs différentes (docs/93) ;
- un texte collé à ce qui est au-dessus : moins de 3,5 px entre les lettres de deux textes, ou
  moins de 6 px sous un champ (docs/132).

    make demo                      # la démo locale, données fictives (http://localhost:5200)
    cd backend && uv run --with playwright python ../frontend/scripts/regles.py
"""

import asyncio
import json
import os
import sys

from playwright.async_api import async_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5200"
PAGES = [
    "aujourdhui",
    "candidatures/offres",
    "candidatures/suivi",
    "candidatures/alertes",
    "bilan",
    "candidatures/rendez-vous-orp",
    "bilan/actualites",
    "bilan/formations",
    "profil",
    "profil?onglet=parcours",
    "profil?onglet=coordonnees",
    "reglages",
    "reglages?rubrique=rythme",
    "reglages?rubrique=actualites",
    "reglages?rubrique=notifications",
    "reglages?rubrique=ia",
    "reglages?rubrique=compte",
    "reglages?rubrique=outils",
    "tes-donnees",
    "accessibilite",
]
SIZES = [{"width": 1440, "height": 900}, {"width": 390, "height": 844}]
MAX_WORDS = 16

AUDIT = r"""(maxWords) => {
  const main = document.querySelector('main') || document.body;
  const skip = '.topbar, .tab-bar, .demo-banner, [role=dialog], .capsule';
  const vis = (e) => {
    const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden' && !e.closest(skip);
  };
  const words = (t) => (t || '').trim().split(/\s+/).filter(Boolean).length;
  const text = (e) => e.innerText.trim().replace(/\s+/g, ' ');
  const faults = [];
  const help = '.setting-desc, .hint, .notice, .page-head-sub, p.muted, .setting-info';
  for (const e of main.querySelectorAll(help)) {
    if (!vis(e) || e.parentElement.closest(help)) continue;
    if (words(e.innerText) > maxWords) faults.push(`aide de ${words(e.innerText)} mots : « ${text(e).slice(0, 70)}… »`);
  }
  const pronoun = /(^|[\s'’])(je|j'|j’|tu|te|t'|t’|ton|ta|tes|me|m'|m’|mon|ma|mes)(?=[\s,.:;!?]|$)/i;
  const titles = 'h1, h2, h3, legend, .disclosure-title, .section-title, .summary-title strong';
  for (const e of main.querySelectorAll(titles)) {
    if (!vis(e)) continue;
    const t = text(e);
    if (pronoun.test(t) || /\?$/.test(t)) faults.push(`titre : « ${t.slice(0, 60)} »`);
  }
  const card = '.form-card, .settings-card, .disclosure, .dash-card, .journal-toggle';
  for (const e of main.querySelectorAll('*')) {
    if (!vis(e) || !e.closest(card)) continue;
    const s = getComputedStyle(e);
    if (parseFloat(s.borderLeftWidth) >= 2 && parseFloat(s.borderRightWidth) === 0 && s.borderLeftStyle !== 'none') {
      faults.push(`barre verticale : ${e.className || e.tagName} « ${text(e).slice(0, 40)} »`);
    }
  }
  const framed = (e) => {
    const s = getComputedStyle(e);
    return ['Top', 'Right', 'Bottom', 'Left'].every((side) => parseFloat(s[`border${side}Width`]) > 0 && s[`border${side}Style`] !== 'none')
      && e.getBoundingClientRect().height > 60
      && !e.matches('input, textarea, select, button, a, .pill, .chip, .badge, img, video, svg, .illu');
  };
  const boxes = [...main.querySelectorAll('div, section, form, article, li, fieldset, details, ul, ol')].filter((e) => vis(e) && framed(e));
  for (const e of boxes) {
    const outer = boxes.find((o) => o !== e && o.contains(e));
    if (outer) faults.push(`cadre dans un cadre : ${e.className || e.tagName} dans ${outer.className || outer.tagName}`);
  }
  // Le texte à au moins 1,25 rem (20 px) du bord de sa carte ; la carte la plus extérieure.
  const cards = [...main.querySelectorAll('.dash-card, .form-card, .settings-card, .disclosure, .training-tile, .alerts-summary')]
    .filter((c) => vis(c) && !c.parentElement.closest('.dash-card, .form-card, .settings-card, .disclosure, .training-tile'));
  for (const c of cards) {
    const box = c.getBoundingClientRect();
    const walker = document.createTreeWalker(c, NodeFilter.SHOW_TEXT);
    let worst = Infinity;
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (!node.textContent.trim() || !vis(node.parentElement) || node.parentElement.closest('button.pill, .pill, .chip, .badge, input, select, textarea, .segmented, .icon-button, .logo, .score-ring')) continue;
      const range = document.createRange();
      range.selectNodeContents(node);
      for (const r of range.getClientRects()) {
        // Ce qui n'est pas dans la carte (caché, replié, défilé) ne compte pas.
        if (r.width === 0 || r.left < box.left || r.right > box.right || r.top < box.top || r.bottom > box.bottom) continue;
        worst = Math.min(worst, r.left - box.left, box.right - r.right);
      }
    }
    if (worst < 19) faults.push(`texte à ${Math.round(worst)} px du bord : ${c.className.split(' ')[0]} « ${text(c).slice(0, 40)} »`);
  }
  // Les cartes côte à côte (même parent, même haut) ont la même hauteur.
  for (const c of cards) {
    const a = c.getBoundingClientRect();
    for (const d of cards) {
      if (d === c || d.parentElement !== c.parentElement) continue;
      const b = d.getBoundingClientRect();
      if (Math.abs(a.top - b.top) < 2 && a.left < b.left && Math.abs(a.height - b.height) > 2) {
        faults.push(`rangée de hauteurs différentes : ${c.className.split(' ')[0]} (${Math.round(a.height)} px) et ${d.className.split(' ')[0]} (${Math.round(b.height)} px)`);
      }
    }
  }
  // Un texte collé à ce qui est au-dessus (docs/132) : on mesure les lettres (pas les boîtes,
  // qui comptent l'interligne), seulement leur partie visible, contre un autre texte ou un champ.
  {
    const hidden = '.visually-hidden, .suivi-calendar, svg, [inert]';
    const blockOf = (e) => { let b = e; while (b && b !== main && getComputedStyle(b).display.startsWith('inline')) b = b.parentElement; return b; };
    const items = new Map();
    const walker = document.createTreeWalker(main, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const n = walker.currentNode;
      if (!n.textContent.trim()) continue;
      const el = n.parentElement;
      if (!el || !vis(el) || el.closest(hidden) || getComputedStyle(el).opacity === '0') continue;
      const b = blockOf(el);
      if (!b) continue;
      const clip = b.getBoundingClientRect();
      const range = document.createRange();
      range.selectNodeContents(n);
      for (const q of range.getClientRects()) {
        if (q.width < 1 || q.bottom > clip.bottom + 1 || q.top < clip.top - 1) continue;
        const it = items.get(b) || { top: 1e9, bottom: -1e9, left: 1e9, right: -1e9, ctl: false };
        it.top = Math.min(it.top, q.top); it.bottom = Math.max(it.bottom, q.bottom);
        it.left = Math.min(it.left, q.left); it.right = Math.max(it.right, q.right);
        items.set(b, it);
      }
    }
    for (const e of main.querySelectorAll('input:not([type=checkbox]):not([type=radio]):not([type=hidden]), textarea, select')) {
      if (!vis(e) || e.closest(hidden)) continue;
      const r = e.getBoundingClientRect();
      items.set(e, { top: r.top, bottom: r.bottom, left: r.left, right: r.right, ctl: true });
    }
    // Seulement ce qui est au premier plan : une fiche ouverte par-dessus la liste la cache.
    const onTop = (e, r) => {
      const x = (Math.max(r.left, 0) + Math.min(r.right, innerWidth)) / 2;
      const y = (r.top + r.bottom) / 2;
      if (y < 0 || y > innerHeight) return true;
      const hit = document.elementFromPoint(x, y);
      return !!hit && (e.contains(hit) || hit.contains(e));
    };
    const list = [...items.entries()].filter(([e, r]) => onTop(e, r));
    for (const [b, rb] of list) {
      if (rb.ctl) continue;
      let best = null;
      for (const [a, ra] of list) {
        if (a === b || a.contains(b) || b.contains(a) || ra.top >= rb.top) continue;
        if (Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left) < 24) continue;
        const gap = rb.top - ra.bottom;
        if (best === null || gap < best[1]) best = [a, gap, ra.ctl];
      }
      if (best && best[1] > -2 && best[1] < (best[2] ? 6 : 3.5)) {
        faults.push(`texte collé (${Math.round(best[1])} px) : « ${text(b).slice(0, 40)} »`);
      }
    }
  }
  return faults;
}"""


async def main() -> int:
    total = 0
    async with async_playwright() as p:
        chrome = os.environ.get("CHROME")
        browser = await p.chromium.launch(**({"executable_path": chrome} if chrome else {}))
        # La fiche d'une offre et Préparer, sur la première offre de la démo.
        probe = await browser.new_page()
        found = await (await probe.request.get(f"{BASE}/api/offers?limit=1")).json()
        await probe.close()
        extra = []
        if found.get("items"):
            offer = found["items"][0]["id"]
            extra = [f"candidatures/offres?offre={offer}", f"candidatures/offres/{offer}/preparer"]
        for size in SIZES:
            page = await browser.new_page(viewport=size)
            for path in PAGES + extra:
                await page.goto(f"{BASE}/{path}")
                await page.wait_for_timeout(1700)
                faults = list(dict.fromkeys(await page.evaluate(AUDIT, MAX_WORDS)))
                for fault in faults:
                    print(f"{size['width']} px  /{path}  {fault}")
                total += len(faults)
            await page.close()
        await browser.close()
    print(json.dumps({"défauts": total}, ensure_ascii=False))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
