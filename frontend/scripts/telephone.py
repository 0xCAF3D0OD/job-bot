"""Audit téléphone de la démo : en 320, 360 et 390 px, sur chaque page, et sur chaque page avec le
panneau de la cloche ouvert, il échoue si

- un élément visible sort de l'écran (bord gauche < 0 ou bord droit > largeur), sauf dans un
  conteneur qui défile horizontalement exprès (overflow-x auto ou scroll), ou si la page défile
  horizontalement ;
- une cible tactile visible (button, a, input, select, textarea, [role=button], label cliquable)
  fait moins de 24 × 24 px (WCAG 2.2, 2.5.8, niveau AA), en comptant la zone étendue par un
  ::before ou ::after positionné. Un lien dans une phrase est exempté (exception « en ligne »).

Une commande isolée (bouton, lien d'action, onglet, radio, ligne cliquable) de moins de 44 × 44 px
est listée en avertissement, sans échec (Apple HIG : 44 points ; Material 3 : 48 dp).

    make demo                      # ou make demo-image (http://localhost:8280)
    cd backend && uv run --with playwright python ../frontend/scripts/telephone.py http://localhost:5200
"""

import asyncio
import json
import os
import sys

from playwright.async_api import Page, async_playwright
from regles import PAGES

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5200"
WIDTHS = [320, 360, 390]
HEIGHT = 640
PUBLIC = ["connexion", "inscription", "la-plateforme", "conditions", "a-propos", "bienvenue", "page-introuvable"]
MIN_TARGET = 24
COMFORT_TARGET = 44

AUDIT = r"""() => {
  const W = document.documentElement.clientWidth;
  const faults = [];
  const warnings = [];
  const label = (e) => {
    const t = (e.innerText || e.value || e.getAttribute('aria-label') || e.getAttribute('title') || '').trim().replace(/\s+/g, ' ');
    const cls = typeof e.className === 'string' && e.className ? '.' + e.className.trim().split(/\s+/)[0] : '';
    return `${e.tagName.toLowerCase()}${cls}${t ? ' « ' + t.slice(0, 40) + ' »' : ''}`;
  };
  const shown = (e) => {
    const s = getComputedStyle(e);
    if (s.visibility === 'hidden' || s.display === 'none' || parseFloat(s.opacity) === 0) return false;
    const r = e.getBoundingClientRect();
    if (r.width <= 1 || r.height <= 1) return false;
    // Masqué pour l'écran seulement (lecteur d'écran) : clip ou taille d'un pixel.
    if (s.clip && s.clip !== 'auto') return false;
    if (s.clipPath && s.clipPath !== 'none' && s.clipPath.includes('inset(50%')) return false;
    return true;
  };
  // Le rectangle réellement visible : coupé par les ancêtres qui cachent leur débordement ; null
  // si un ancêtre défile horizontalement exprès.
  const visibleRect = (e) => {
    const r = e.getBoundingClientRect();
    let left = r.left, right = r.right;
    // html et body coupent tout ce qui dépasse de l'écran (overflow-x: clip) : un contenu coupé au bord
    // reste un défaut, on ne s'arrête donc pas à leur coupure.
    for (let a = e.parentElement; a && a !== document.body && a !== document.documentElement; a = a.parentElement) {
      const s = getComputedStyle(a);
      if (s.overflowX === 'auto' || s.overflowX === 'scroll') return null;
      if (s.overflowX === 'hidden' || s.overflowX === 'clip') {
        const ra = a.getBoundingClientRect();
        left = Math.max(left, ra.left);
        right = Math.min(right, ra.right);
      }
      if (s.position === 'fixed') break;
    }
    return right - left > 1 ? { left, right } : null;
  };

  if (document.documentElement.scrollWidth > W + 1) {
    faults.push(`la page défile horizontalement (${document.documentElement.scrollWidth} px pour ${W})`);
  }
  const out = [];
  for (const e of document.body.querySelectorAll('*')) {
    if (!shown(e)) continue;
    const v = visibleRect(e);
    if (!v) continue;
    if (v.left < -0.5 || v.right > W + 0.5) out.push(e);
  }
  // Seulement l'élément le plus haut qui déborde : ses enfants débordent avec lui.
  for (const e of out) {
    if (out.some((o) => o !== e && o.contains(e))) continue;
    const v = visibleRect(e);
    faults.push(`hors de l'écran (${Math.round(v.left)} → ${Math.round(v.right)} px) : ${label(e)}`);
  }

  // La zone d'un ::before ou ::after positionné en absolu, qui agrandit la cible.
  const px = (v) => (v && v.endsWith('px') ? parseFloat(v) : null);
  // Le bloc qui contient un pseudo-élément positionné : l'élément s'il est positionné, sinon son plus
  // proche ancêtre positionné (une ligne entière cliquable par le ::after de son titre).
  const containing = (e) => {
    for (let a = e; a && a !== document.body; a = a.parentElement) {
      const s = getComputedStyle(a);
      if (s.position !== 'static' || s.transform !== 'none') {
        const r = a.getBoundingClientRect();
        const bl = parseFloat(s.borderLeftWidth), br = parseFloat(s.borderRightWidth);
        const bt = parseFloat(s.borderTopWidth), bb = parseFloat(s.borderBottomWidth);
        return { left: r.left + bl, right: r.right - br, top: r.top + bt, bottom: r.bottom - bb, width: r.width - bl - br, height: r.height - bt - bb };
      }
    }
    return { left: 0, right: innerWidth, top: 0, bottom: innerHeight, width: innerWidth, height: innerHeight };
  };
  const pseudoRect = (e, which) => {
    const s = getComputedStyle(e, which);
    if (!s || s.content === 'none' || s.content === 'normal' || s.display === 'none') return null;
    if (s.position !== 'absolute' && s.position !== 'fixed') return null;
    const r = containing(e);
    const [l, rt, t, b, w, h] = [px(s.left), px(s.right), px(s.top), px(s.bottom), px(s.width), px(s.height)];
    let x0 = null, x1 = null, y0 = null, y1 = null;
    if (l !== null && rt !== null) { x0 = r.left + l; x1 = r.right - rt; }
    else if (l !== null && w !== null) { x0 = r.left + l; x1 = x0 + w; }
    else if (rt !== null && w !== null) { x1 = r.right - rt; x0 = x1 - w; }
    else if (w !== null) { x0 = r.left + (r.width - w) / 2; x1 = x0 + w; }
    if (t !== null && b !== null) { y0 = r.top + t; y1 = r.bottom - b; }
    else if (t !== null && h !== null) { y0 = r.top + t; y1 = y0 + h; }
    else if (b !== null && h !== null) { y1 = r.bottom - b; y0 = y1 - h; }
    else if (h !== null) { y0 = r.top + (r.height - h) / 2; y1 = y0 + h; }
    if (x0 === null || y0 === null) return null;
    return { left: x0, right: x1, top: y0, bottom: y1 };
  };
  // Un lien dans une phrase : exempté (WCAG 2.5.8, « en ligne »).
  const inline = (e) => {
    if (e.tagName !== 'A' || getComputedStyle(e).display !== 'inline') return false;
    const p = e.parentElement;
    return !!p && (p.innerText || '').trim().length > (e.innerText || '').trim().length + 10;
  };
  const targets = document.body.querySelectorAll(
    'button, a[href], input:not([type=hidden]), select, textarea, [role=button], label'
  );
  for (const e of targets) {
    if (!shown(e) || inline(e)) continue;
    if (e.tagName === 'LABEL' && !(e.htmlFor || e.querySelector('input, select, textarea'))) continue;
    // Un champ caché derrière son étiquette (case ou bouton radio dessiné) : c'est l'étiquette qui compte.
    if (e.tagName === 'INPUT' && e.closest('label') && e.getBoundingClientRect().width < MIN) continue;
    const r = e.getBoundingClientRect();
    if (r.bottom < 0 || r.top > innerHeight * 6) continue;
    // Un champ dans une ligne entière cliquable (cursor: pointer) : c'est la ligne qu'on touche.
    let rowBox = null;
    for (let a = e.parentElement, depth = 0; a && a !== document.body && depth < 4; a = a.parentElement, depth++) {
      if (getComputedStyle(a).cursor !== 'pointer') continue;
      // Le curseur s'hérite : on remonte jusqu'à l'élément qui le pose (la ligne entière).
      let top = a;
      while (top.parentElement && top.parentElement !== document.body && getComputedStyle(top.parentElement).cursor === 'pointer') top = top.parentElement;
      rowBox = top.getBoundingClientRect();
      break;
    }
    let box = rowBox && e.tagName === 'INPUT'
      ? { left: rowBox.left, right: rowBox.right, top: rowBox.top, bottom: rowBox.bottom }
      : { left: r.left, right: r.right, top: r.top, bottom: r.bottom };
    for (const which of ['::before', '::after']) {
      const p = pseudoRect(e, which);
      if (p) box = { left: Math.min(box.left, p.left), right: Math.max(box.right, p.right), top: Math.min(box.top, p.top), bottom: Math.max(box.bottom, p.bottom) };
    }
    const w = box.right - box.left, h = box.bottom - box.top;
    const size = `${Math.round(w)} × ${Math.round(h)} px`;
    if (w < MIN - 0.5 || h < MIN - 0.5) faults.push(`cible de ${size} : ${label(e)}`);
    else if (w < COMFORT - 0.5 || h < COMFORT - 0.5) warnings.push(`cible de ${size}, moins de 44 px : ${label(e)}`);
  }
  return { faults, warnings };
}""".replace("MIN", str(MIN_TARGET)).replace("COMFORT", str(COMFORT_TARGET))


async def open_bell(page: Page) -> bool | str:
    """Ouvre le panneau de la cloche ; False s'il n'y a pas de cloche, un défaut si on ne peut pas la toucher."""
    bell = page.locator("[data-test=bell]").first
    if not await bell.count() or not await bell.is_visible():
        return False
    try:
        await bell.click(timeout=3000)
    except Exception:
        return "la cloche ne se touche pas : un autre élément la recouvre"
    await page.wait_for_timeout(500)
    return True


async def main() -> int:
    total = warned = 0
    async with async_playwright() as p:
        chrome = os.environ.get("CHROME")
        browser = await p.chromium.launch(**({"executable_path": chrome} if chrome else {}))
        probe = await browser.new_page()
        found = await (await probe.request.get(f"{BASE}/api/offers?limit=1")).json()
        await probe.close()
        extra = []
        if found.get("items"):
            offer = found["items"][0]["id"]
            extra = [f"candidatures/offres?offre={offer}", f"candidatures/offres/{offer}/preparer"]
        for width in WIDTHS:
            page = await browser.new_page(viewport={"width": width, "height": HEIGHT}, has_touch=True, is_mobile=True)
            for path in PAGES + extra + PUBLIC:
                for bell in (False, True):
                    await page.goto(f"{BASE}/{path}")
                    await page.wait_for_timeout(1500)
                    if path in PUBLIC and f"/{path}" not in page.url:
                        break  # la démo connectée redirige : la page publique n'existe pas ici
                    opened = await open_bell(page) if bell else True
                    if opened is False:
                        continue
                    result = await page.evaluate(AUDIT)
                    faults = [opened] if isinstance(opened, str) else []
                    faults = list(dict.fromkeys(faults + result["faults"]))
                    where = f"/{path}" + (" (cloche ouverte)" if bell else "")
                    for warning in dict.fromkeys(result["warnings"]):
                        print(f"{width} px  {where}  avertissement : {warning}")
                        warned += 1
                    for fault in faults:
                        print(f"{width} px  {where}  {fault}")
                    total += len(faults)
            await page.close()
        await browser.close()
    print(json.dumps({"défauts": total, "avertissements": warned}, ensure_ascii=False))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
