"""Contrôle de la grille et des alignements (MODIFICATIONS du 8 novembre au soir, §2.9 et §2.10) : chaque écran
téléphone du lot 18 est chargé à 390 px, en clair et en sombre, puis `docs/mobile/outils/audit-grille.js` (le script
du paquet du 9 novembre, inchangé) est exécuté dans la page avec `page.evaluate`. Il échoue au premier écart :
une PR n'est verte qu'avec 0 écart.

Le script a été écrit pour les maquettes : il cherche leurs classes (`.row` pour une carte cliquable, `.s.info` pour
une carte d'information, `.go` pour le cercle à flèche, `.scroll` pour la zone qui défile, `.top` et `.bar` pour
l'en-tête et la barre du bas, `.fam`, `.fh`, `.kd` pour la cascade). Avant de le lancer, PRELUDE pose ces classes sur
les éléments de l'application qui jouent le même rôle (table MAPPING, à tenir à jour avec les écrans). Le bandeau
« Démo » (démo seulement) et ce qui n'est pas affiché (display: none) sont retirés : le script ne regarde pas la
visibilité.

    make demo                      # ou make demo-image (http://localhost:8280)
    cd backend && uv run --with playwright python ../frontend/scripts/grille.py http://localhost:5200
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from playwright.async_api import async_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5200"
AUDIT = (Path(__file__).resolve().parents[2] / "docs/mobile/outils/audit-grille.js").read_text(encoding="utf-8")

# Ordinateur (MODIFICATIONS du 9 novembre, §1 et §11) : les mêmes règles à 1440 px, sauf les cibles, de 24 px au moins
# (WCAG 2.5.8) au lieu de 44. Le script du paquet n'a pas ce mode : seule sa règle 6 est adaptée ici.
# La page A4 (lettre, CV) suit sa propre typographie d'imprimé, comme la `.page` des maquettes : hors de la grille de 4.
AUDIT_DESK = (
    AUDIT.replace("r.height<44||r.width<44", "r.height<24||r.width<24")
    .replace("cible tactile >= 44 px", "cible >= 24 px (ordinateur)")
    .replace("document.querySelectorAll('.scroll *, .top, .bar')", "document.querySelectorAll('.scroll *:not(.print-sheet, .print-sheet *), .top, .bar')")
)
assert AUDIT_DESK.count(":not(.print-sheet") == 1 and "<24" in AUDIT_DESK, "le script du paquet a changé : adapter AUDIT_DESK"

# Classe de la maquette ← éléments de l'application qui jouent le même rôle.
MAPPING = {
    "scroll": "main",
    "top": ".topbar, .grille-top",
    "bar": ".grille-bar",
    "row": ".block-row, .grille-row",
    "s info": ".block.info, .grille-info",
    "go": ".arrow-circle",
    "fam": ".grille-fam",
    "fh": ".grille-fh",
    "kd": ".grille-kd",
}
PRELUDE = r"""(mapping) => {
  document.querySelectorAll('.demo-banner').forEach((e) => { e.style.display = 'none'; });
  // Ce qui n'est pas affiché (display: none, par exemple la feuille ORP réservée à l'impression) n'est pas à l'écran :
  // retiré avant l'audit, qui ne regarde pas la visibilité.
  [...document.body.querySelectorAll('*')].filter((e) => e.isConnected && getComputedStyle(e).display === 'none').forEach((e) => e.remove());
  // Les <option> d'une liste fermée non plus (leurs marges sont celles du navigateur, pas les nôtres).
  document.querySelectorAll('select option, select optgroup').forEach((o) => o.remove());
  // Le contenu d'un <details> fermé n'est pas à l'écran non plus.
  document.querySelectorAll('details:not([open])').forEach((d) => [...d.children].filter((c) => c.tagName !== 'SUMMARY').forEach((c) => c.remove()));
  // Une sous-page du téléphone (détail d'une offre) couvre la liste : c'est elle, l'écran.
  const sub = document.querySelector('.detail-panel.offer-blocks');
  if (sub) mapping = { ...mapping, scroll: '.detail-panel.offer-blocks' };
  for (const [classes, selector] of Object.entries(mapping)) {
    document.querySelectorAll(selector).forEach((e) => e.classList.add(...classes.split(' ')));
  }
}"""

# Les écrans téléphone du lot 18 (§10). `{offer}` et `{application}` : une offre à traiter et une candidature
# envoyée de la démo. Un état (« ouvrir ») est un sélecteur sur lequel cliquer avant l'audit.
SCREENS: list[tuple[str, str | None]] = [
    ("compte", None),
    ("bilan/orp", None),
    ("bilan", None),
    ("bilan/orp/candidature/{application}", None),
    ("candidatures/offres/{offer}", None),
    ("candidatures/offres/{offer}", "[data-test=compat-open]"),
    ("candidatures/rendez-vous-orp", None),
    ("candidatures/rendez-vous-orp", "[data-test=rdv-prep-open]"),
    ("candidatures/offres/{offer}/preparer", "[data-test=layout-change]"),
    ("candidatures/alertes", None),
    ("candidatures/alertes", "[data-test^=alert-card-]"),
    ("notifications", None),
    # « Tout est lu » : tout lire, puis l'onglet « Non lues ».
    ("notifications", "[data-test=read-all] && [data-test=filter-unread]"),
]
# Écrans d'ordinateur déjà passés à la maquette du 9 novembre (une ligne par PR de la série).
DESK_SCREENS: list[tuple[str, str | None]] = [
    ("candidatures/offres/{offer}/preparer", None),
    ("candidatures/offres/{offer}/preparer", "[data-test=prep-file] [data-test=versions-open]"),
    ("candidatures/offres/{offer}/preparer?doc=postuler", None),
    ("candidatures/offres/{offer}/preparer?doc=postuler", "[data-test=contacts-open]"),
]


async def main() -> int:
    total = 0
    async with async_playwright() as p:
        chrome = os.environ.get("CHROME")
        browser = await p.chromium.launch(**({"executable_path": chrome} if chrome else {}))
        probe = await browser.new_page()
        offers = await (await probe.request.get(f"{BASE}/api/offers?limit=1&status=to_review")).json()
        applications = await (await probe.request.get(f"{BASE}/api/applications?limit=1")).json()
        await probe.close()
        ids = {
            "offer": offers["items"][0]["id"] if offers.get("items") else 0,
            "application": applications[0]["id"] if applications else 0,
        }
        runs = [(390, 844, SCREENS, AUDIT), (1440, 900, DESK_SCREENS, AUDIT_DESK)]
        for scheme, (width, height, screens, audit) in ((s, r) for s in ("light", "dark") for r in runs):
            phone = width < 821
            page = await browser.new_page(viewport={"width": width, "height": height}, color_scheme=scheme, has_touch=phone, is_mobile=phone)
            for path, opener in screens:
                url = path.format(**ids)
                await page.goto(f"{BASE}/{url}")
                await page.wait_for_timeout(1500)
                for step in opener.split(" && ") if opener else []:
                    await page.click(step)
                    await page.wait_for_timeout(600)
                await page.evaluate(PRELUDE, MAPPING)
                faults = await page.evaluate(audit)
                where = f"/{url}" + (f" ({opener})" if opener else "")
                for fault in faults:
                    print(f"{width} px {scheme}  {where}  {json.dumps(fault, ensure_ascii=False)}")
                total += len(faults)
            await page.close()
        await browser.close()
    print(json.dumps({"écarts": total}, ensure_ascii=False))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
