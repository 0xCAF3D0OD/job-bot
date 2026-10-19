"""Les icônes de jobA1 (docs/97, docs/100), tirées du logo : l'onglet du navigateur (favicon.svg
et favicon-32.png), l'application (apple-touch-icon, icon-192, icon-512, icon-maskable-512 : la
boucle blanche et le diamant pêche sur un carré bleu, l'« icône d'app » de la planche) et la
version noire (logo-noir.svg, « noir seul »). Les tracés viennent de src/brandPaths.ts ; rien
n'est redessiné.

    cd backend && uv run --with playwright python ../frontend/scripts/icones.py

CHROME=… pour utiliser un navigateur installé plutôt que celui de Playwright.
"""

import asyncio
import os
import re
from pathlib import Path

from playwright.async_api import async_playwright

FRONT = Path(__file__).resolve().parent.parent
PUBLIC = FRONT / "public"
SOURCE = (FRONT / "src" / "brandPaths.ts").read_text("utf-8")

BLUE, STAR, DARK_INK, DARK_STAR = "#2340C8", "#F4A261", "#9DB0FF", "#E8B48A"
VIEWBOX = (4, 6, 92, 92)
LOOP = re.search(r'LOGO_LOOP =\s*"([^"]+)"', SOURCE)
DIAMOND = re.search(r'LOGO_DIAMOND = "([^"]+)"', SOURCE)
DIAMOND_SMALL = re.search(r'LOGO_DIAMOND_SMALL_SIZE = "([^"]+)"', SOURCE)
assert LOOP and DIAMOND and DIAMOND_SMALL, "tracés introuvables dans src/brandPaths.ts"
VB = " ".join(str(v) for v in VIEWBOX)


def line(d: str, color: str, stroke: float) -> str:
    return (
        f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{stroke}" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
    )


def logo(ink: str, star: str, stroke: float, small: bool = False) -> str:
    # La boucle et le diamant au même trait (docs/100) ; petit (32 px et moins) : trait de 8,5
    # pour la boucle, 8 pour le diamant, un peu plus grand, comme sur la planche.
    if small:
        return line(LOOP.group(1), ink, 8.5) + line(DIAMOND_SMALL.group(1), star, 8)
    return line(LOOP.group(1), ink, stroke) + line(DIAMOND.group(1), star, stroke)


def favicon_svg() -> str:
    # L'onglet : la version 32 / 16 px de la planche, qui suit le mode sombre du navigateur.
    common = "fill:none;stroke-linecap:round;stroke-linejoin:round"
    style = (
        f".i{{{common};stroke:{BLUE};stroke-width:8.5}}.s{{{common};stroke:{STAR};stroke-width:8}}"
        f"@media (prefers-color-scheme:dark){{.i{{stroke:{DARK_INK}}}.s{{stroke:{DARK_STAR}}}}}"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VB}">'
        f'<style>{style}</style><path class="i" d="{LOOP.group(1)}"/>'
        f'<path class="s" d="{DIAMOND_SMALL.group(1)}"/></svg>\n'
    )


def black_svg() -> str:
    # « Noir seul » : la boucle et le diamant en noir, pour les documents et l'impression.
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VB}">{logo("#000000", "#000000", 5)}</svg>\n'


def app_icon(size: int, logo_share: float) -> str:
    # La boucle blanche et le diamant pêche sur un carré bleu plein (l'« icône d'app » de la
    # planche), dans un seul dessin : la vue s'élargit autour du logo (92 unités) selon sa part.
    x0, y0, w, _ = VIEWBOX
    total = w / logo_share
    sx, sy = x0 - (total - w) / 2, y0 - (total - w) / 2
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="{sx} {sy} {total} {total}" style="display:block">'
        f'<rect x="{sx}" y="{sy}" width="{total}" height="{total}" fill="{BLUE}"/>'
        f"{logo('#FFFFFF', STAR, 5)}</svg>"
    )


def plain(size: int, stroke: float, small: bool = False) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="{VB}" style="display:block">{logo(BLUE, STAR, stroke, small)}</svg>'
    )


async def render(browser, svg: str, size: int, target: Path) -> None:
    # Une page neuve par icône, à sa taille : changer la taille d'une page déjà rendue
    # laissait parfois l'ancien rendu dans la capture.
    page = await browser.new_page(viewport={"width": size, "height": size})
    body = f'<html><body style="margin:0;background:transparent">{svg}</body></html>'
    await page.set_content(body)
    await page.screenshot(path=str(target), omit_background=True)
    await page.close()
    print("écrit", target.relative_to(FRONT))


async def main() -> None:
    (PUBLIC / "favicon.svg").write_text(favicon_svg(), "utf-8")
    print("écrit public/favicon.svg")
    (PUBLIC / "logo-noir.svg").write_text(black_svg(), "utf-8")
    print("écrit public/logo-noir.svg")
    async with async_playwright() as p:
        chrome = os.environ.get("CHROME")
        launch = {"executable_path": chrome} if chrome else {}
        browser = await p.chromium.launch(**launch)
        await render(browser, plain(32, 8.5, small=True), 32, PUBLIC / "favicon-32.png")
        await render(browser, app_icon(180, 0.69), 180, PUBLIC / "apple-touch-icon.png")
        await render(browser, app_icon(192, 0.69), 192, PUBLIC / "icon-192.png")
        await render(browser, app_icon(512, 0.69), 512, PUBLIC / "icon-512.png")
        # « maskable » : le logo dans la zone sûre (le cercle de 80 %), donc plus petit.
        await render(browser, app_icon(512, 0.5), 512, PUBLIC / "icon-maskable-512.png")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
