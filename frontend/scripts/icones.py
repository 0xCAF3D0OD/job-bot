"""Les icônes de jobA1 (docs/97), tirées du logo : l'onglet du navigateur (favicon.svg et
favicon-32.png) et l'application (apple-touch-icon, icon-192, icon-512, icon-maskable-512 : le
logo blanc sur un carré bleu, la version « app » de la planche). Les tracés viennent de
src/brandPaths.ts ; rien n'est redessiné.

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
LOOPS = re.search(r"LOGO_LOOPS = \[\s*\"([^\"]+)\",\s*\"([^\"]+)\"", SOURCE)
STAR_PATH = re.search(r'LOGO_STAR = "([^"]+)"', SOURCE)
assert LOOPS and STAR_PATH, "tracés introuvables dans src/brandPaths.ts"


def logo(ink: str, star: str, stroke: float) -> str:
    loops = "".join(
        f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="{stroke}" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
        for d in LOOPS.groups()
    )
    return f'{loops}<path d="{STAR_PATH.group(1)}" fill="{star}"/>'


def favicon_svg() -> str:
    # Le favicon SVG suit le mode sombre du navigateur.
    loops = "".join(f'<path class="i" d="{d}"/>' for d in LOOPS.groups())
    style = (
        f".i{{fill:none;stroke:{BLUE};stroke-width:6;stroke-linecap:round;stroke-linejoin:round}}"
        f".s{{fill:{STAR}}}"
        f"@media (prefers-color-scheme:dark){{.i{{stroke:{DARK_INK}}}.s{{fill:{DARK_STAR}}}}}"
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="4 4 92 92">'
        f'<style>{style}</style>{loops}<path class="s" d="{STAR_PATH.group(1)}"/></svg>\n'
    )


def app_icon(size: int, logo_share: float) -> str:
    # Le logo blanc et l'étoile pêche sur un carré bleu plein (l'icône « app » de la planche),
    # dans un seul dessin : la vue s'élargit autour du logo (92 unités) selon sa part.
    total = 92 / logo_share
    start = 4 - (total - 92) / 2
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="{start} {start} {total} {total}" style="display:block">'
        f'<rect x="{start}" y="{start}" width="{total}" height="{total}" fill="{BLUE}"/>'
        f"{logo('#FFFFFF', STAR, 5)}</svg>"
    )


def plain(size: int, stroke: float) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="4 4 92 92" style="display:block">{logo(BLUE, STAR, stroke)}</svg>'
    )


async def render(page, svg: str, size: int, target: Path) -> None:
    await page.set_viewport_size({"width": size, "height": size})
    body = f'<html><body style="margin:0;background:transparent">{svg}</body></html>'
    await page.set_content(body)
    await page.screenshot(path=str(target), omit_background=True)
    print("écrit", target.relative_to(FRONT))


async def main() -> None:
    (PUBLIC / "favicon.svg").write_text(favicon_svg(), "utf-8")
    print("écrit public/favicon.svg")
    async with async_playwright() as p:
        chrome = os.environ.get("CHROME")
        launch = {"executable_path": chrome} if chrome else {}
        browser = await p.chromium.launch(**launch)
        page = await browser.new_page()
        await render(page, plain(32, 6), 32, PUBLIC / "favicon-32.png")
        await render(page, app_icon(180, 0.64), 180, PUBLIC / "apple-touch-icon.png")
        await render(page, app_icon(192, 0.64), 192, PUBLIC / "icon-192.png")
        await render(page, app_icon(512, 0.64), 512, PUBLIC / "icon-512.png")
        # « maskable » : le logo dans la zone sûre (le cercle de 80 %), donc plus petit.
        await render(page, app_icon(512, 0.5), 512, PUBLIC / "icon-maskable-512.png")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
