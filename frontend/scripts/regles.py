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
  moins de 6 px sous un champ (docs/132) ;
- un trait sur un, deux ou trois côtés qui remonte au bout parce que la boîte a un coin arrondi
  (un onglet souligné, un séparateur ; décision de Kevin du 2026-11-05 : les traits restent droits).

    make demo                      # la démo locale, données fictives (http://localhost:5200)
    cd backend && uv run --with playwright python ../frontend/scripts/regles.py
"""

import asyncio
import json
import os
import re
import sys
from pathlib import Path

from playwright.async_api import async_playwright

from explore import states

# La police manuscrite (Caveat Brush) est réduite aux seuls caractères des titres qui l'utilisent
# (docs/139 étapes 8c et 11b) : les fins de titre des premiers pas, « C'est fait ! » et « te revoir. »
# de la connexion (2026-11-05). Un titre
# changé sans refaire le sous-ensemble s'afficherait avec une lettre dans une autre police.
FRONTEND = Path(__file__).resolve().parent.parent
HAND_FONT = FRONTEND / "src/assets/fonts/caveat-brush-titres.woff2"


def hand_titles() -> list[str]:
    """Les textes écrits en Caveat Brush, lus dans le code : `hand: "…"` des premiers pas, le
    titre de « C'est fait ! », puis la fin du titre de la connexion."""
    welcome = (FRONTEND / "src/views/WelcomeView.vue").read_text("utf-8")
    goal = (FRONTEND / "src/components/GoalReached.vue").read_text("utf-8")
    login = (FRONTEND / "src/views/LoginView.vue").read_text("utf-8")
    titles = re.findall(r'hand: "([^"]+)"', welcome)
    titles += [t.strip() for t in re.findall(r'class="goal-reached-title">([^<]+)<', goal)]
    titles += [t.strip() for t in re.findall(r'class="login-hand">([^<]+)<', login)]
    return titles


def missing_glyphs(font: Path = HAND_FONT, texts: list[str] | None = None) -> list[str]:
    """Les caractères des titres absents de la table cmap de la police (fonttools)."""
    from fontTools.ttLib import TTFont

    cmap = TTFont(font).getBestCmap()
    wanted = "".join(hand_titles() if texts is None else texts)
    return sorted({c for c in wanted if not c.isspace() and ord(c) not in cmap})


BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5200"
PAGES = [
    "aujourdhui",
    "assistant",
    "candidatures/offres",
    "candidatures/suivi",
    "candidatures/alertes",
    "bilan",
    "candidatures/rendez-vous-orp",
    "bilan/formations",
    "notifications",
    "compte",
    "profil",
    "profil?onglet=parcours",
    "profil?onglet=coordonnees",
    "reglages?rubrique=recherche",
    "reglages?rubrique=rythme",
    "reglages?rubrique=notifications",
    "reglages?rubrique=ia",
    "reglages?rubrique=affichage",
    "reglages?rubrique=formule",
    "reglages?rubrique=donnees",
    "reglages?rubrique=outils",
    "tes-donnees",
    "accessibilite",
    "bienvenue",
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
  // Un trait qui ne fait pas le tour (souligné d'onglet, séparateur) reste droit : aucun coin arrondi
  // au bout d'un côté tracé, sinon le trait remonte sur les côtés (2026-11-05, Kevin).
  {
    const corners = { Top: ['TopLeft', 'TopRight'], Bottom: ['BottomLeft', 'BottomRight'], Left: ['TopLeft', 'BottomLeft'], Right: ['TopRight', 'BottomRight'] };
    for (const e of main.querySelectorAll('*')) {
      if (!vis(e)) continue;
      const s = getComputedStyle(e);
      const drawn = Object.keys(corners).filter((k) => parseFloat(s[`border${k}Width`]) > 0 && s[`border${k}Style`] !== 'none' && s[`border${k}Color`] !== 'rgba(0, 0, 0, 0)');
      if (!drawn.length || drawn.length === 4) continue;
      if (drawn.some((k) => corners[k].some((c) => parseFloat(s[`border${c}Radius`]) > 0))) {
        faults.push(`trait qui remonte au bout : ${e.className || e.tagName} « ${text(e).slice(0, 40)} »`);
      }
    }
  }
  // Le texte à au moins 1,25 rem (20 px) du bord de sa carte ; la carte la plus extérieure.
  const cards = [...main.querySelectorAll('.dash-card, .form-card, .settings-card, .disclosure, .training-tile, .alerts-summary')]
    .filter((c) => vis(c) && !c.parentElement.closest('.dash-card, .form-card, .settings-card, .disclosure, .training-tile'));
  // Réglages sur ordinateur (1.6.35, modèle Polaris) : la grande carte n'a plus de cadre ; chaque réglage a sa
  // carte, dessinée derrière ses contrôles (::before). C'est elle qui compte.
  const boxOf = new Map();
  for (const c of [...cards]) {
    const s = getComputedStyle(c);
    if (!c.matches('.settings-card') || parseFloat(s.borderTopWidth) > 0 || s.backgroundColor !== 'rgba(0, 0, 0, 0)') continue;
    cards.splice(cards.indexOf(c), 1);
    for (const f of c.querySelectorAll('fieldset')) {
      const b = getComputedStyle(f, '::before');
      if (!vis(f) || b.content === 'none') continue;
      const r = f.getBoundingClientRect();
      boxOf.set(f, { left: r.left + parseFloat(b.left), right: r.right - parseFloat(b.right), top: r.top, bottom: r.bottom });
      cards.push(f);
    }
  }
  for (const c of cards) {
    const box = boxOf.get(c) ?? c.getBoundingClientRect();
    const walker = document.createTreeWalker(c, NodeFilter.SHOW_TEXT);
    let worst = Infinity;
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (!node.textContent.trim() || !vis(node.parentElement) || node.parentElement.closest('button.pill, .pill, .chip, .badge, input, select, textarea, .segmented, .icon-button, .logo, .score-ring')) continue;
      const range = document.createRange();
      range.selectNodeContents(node);
      // Un texte coupé par « … » : seule sa partie visible compte (1.6.2).
      const clipper = node.parentElement.closest('*');
      const clip = getComputedStyle(clipper).overflowX !== 'visible' ? clipper.getBoundingClientRect() : null;
      for (const raw of range.getClientRects()) {
        const r = clip
          ? { width: raw.width, top: raw.top, bottom: raw.bottom, left: Math.max(raw.left, clip.left), right: Math.min(raw.right, clip.right) }
          : raw;
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
      // Les conteneurs qui défilent ou rognent (une fiche fixée qui défile en elle-même) : un texte
      // hors de leur partie visible ne se voit pas, il ne compte pas (1.6.19).
      const frames = [];
      for (let p = b.parentElement; p && p !== document.body; p = p.parentElement) {
        const s = getComputedStyle(p);
        if (/(auto|scroll|hidden|clip)/.test(s.overflowY)) frames.push(p.getBoundingClientRect());
      }
      const range = document.createRange();
      range.selectNodeContents(n);
      for (const q of range.getClientRects()) {
        if (q.width < 1 || q.bottom > clip.bottom + 1 || q.top < clip.top - 1) continue;
        if (frames.some((f) => q.bottom <= f.top + 1 || q.top >= f.bottom - 1)) continue;
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
    // Seulement ce qui est au premier plan : une fiche ouverte par-dessus la liste la cache, y
    // compris plus bas que l'écran (un calque fixe qui couvre tout l'écran cache tout le reste).
    const layer = (() => {
      for (let e = document.elementFromPoint(innerWidth / 2, innerHeight / 2); e && e !== document.body; e = e.parentElement) {
        const r = e.getBoundingClientRect();
        if (getComputedStyle(e).position === 'fixed' && r.width >= innerWidth - 1 && r.height >= innerHeight - 1) return e;
      }
      return null;
    })();
    const onTop = (e, r) => {
      if (layer && !layer.contains(e)) return false;
      const x = (Math.max(r.left, 0) + Math.min(r.right, innerWidth)) / 2;
      const y = (r.top + r.bottom) / 2;
      if (y < 0 || y > innerHeight) return true;
      const hit = document.elementFromPoint(x, y);
      return !!hit && (e.contains(hit) || hit.contains(e));
    };
    const list = [...items.entries()].filter(([e, r]) => onTop(e, r));
    // Deux textes de deux zones qui défilent chacune de leur côté (la liste et la fiche ouverte à
    // côté) ne se touchent jamais pour de vrai : on ne les compare pas.
    const scroller = (e) => {
      for (let p = e.parentElement; p && p !== document.body; p = p.parentElement) {
        if (/(auto|scroll)/.test(getComputedStyle(p).overflowY) && p.scrollHeight > p.clientHeight + 1) return p;
      }
      return null;
    };
    const zone = new Map(list.map(([e]) => [e, scroller(e)]));
    for (const [b, rb] of list) {
      if (rb.ctl) continue;
      let best = null;
      for (const [a, ra] of list) {
        if (a === b || a.contains(b) || b.contains(a) || ra.top >= rb.top || zone.get(a) !== zone.get(b)) continue;
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
            # La démo n'a pas d'IA : on simule sa présence pour auditer l'onglet Assistant.
            await page.route("**/api/assistant/status", lambda route: route.fulfill(json={"available": True}))
            for path in PAGES + extra:
                await page.goto(f"{BASE}/{path}")
                await page.wait_for_timeout(1700)
                async for state in states(page):
                    faults = list(dict.fromkeys(await page.evaluate(AUDIT, MAX_WORDS)))
                    for fault in faults:
                        print(f"{size['width']} px  /{path}{state}  {fault}")
                    total += len(faults)
            await page.close()
        await browser.close()
    print(json.dumps({"défauts": total}, ensure_ascii=False))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
