"""Les icônes de jobA1 (docs/103), tirées du logo « le visage du 1 », réglage S5 (droit) :
- « badge » : le visage blanc et la bille pêche dans un carré bleu aux coins arrondis, fond
  transparent autour — l'onglet du navigateur (favicon.svg, favicon-32.png) et l'extension
  (extension/icons/16, 32, 48, 128) ;
- « plein » : le carré bleu plein, le visage à 70 % — l'application (apple-touch-icon, icon-192,
  icon-512) ;
- « maskable » : le même, le visage à 52 %, dans la zone sûre (icon-maskable-512) ;
- la version noire (logo-noir.svg), sans carré, pour les documents.
Les tracés viennent de src/brandPaths.ts ; rien n'est redessiné.

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
EXTENSION = FRONT.parent / "extension" / "icons"
SOURCE = (FRONT / "src" / "brandPaths.ts").read_text("utf-8")

BLUE, SPARK, WHITE = "#2340C8", "#F4A261", "#FFFFFF"
# Le visage à 70 % du carré plein ; à 52 % pour la version « maskable ».
FULL, MASKABLE = "translate(15 15) scale(0.7)", "translate(24 24) scale(0.52)"


def text(name: str) -> str:
    found = re.search(rf'export const {name} = "([^"]+)"', SOURCE)
    assert found, f"{name} introuvable dans src/brandPaths.ts"
    return found.group(1)


def point(name: str) -> tuple[str, str]:
    found = re.search(rf"export const {name} = \{{ x: ([\d.]+), y: ([\d.]+)", SOURCE)
    assert found, f"{name} introuvable dans src/brandPaths.ts"
    return found.group(1), found.group(2)


ONE, SMILE = text("ICON_ONE"), text("ICON_SMILE")
EYE, BALL = point("ICON_EYE"), point("ICON_SPARK")


def face(ink: str, ball: str, stroke: float, radius: float) -> str:
    # Le visage S5 : le 1 (sourcil et nez), l'œil, la bille, le sourire.
    line = (
        f'stroke="{ink}" stroke-width="{stroke}" '
        'stroke-linecap="round" stroke-linejoin="round" fill="none"'
    )
    return (
        f'<path d="{ONE}" {line}/>'
        f'<circle cx="{EYE[0]}" cy="{EYE[1]}" r="{radius}" fill="{ink}"/>'
        f'<circle cx="{BALL[0]}" cy="{BALL[1]}" r="{radius}" fill="{ball}"/>'
        f'<path d="{SMILE}" {line}/>'
    )


def badge(size: int | None = None) -> str:
    # Le carré arrondi : le visage à 72 %, au trait un peu épaissi pour les petites tailles.
    dims = f' width="{size}" height="{size}" style="display:block"' if size else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"{dims}>'
        f'<rect x="4" y="4" width="92" height="92" rx="26" fill="{BLUE}"/>'
        f'<g transform="translate(14 14) scale(.72)">{face(WHITE, SPARK, 15.4, 10.1)}</g></svg>'
    )


def full(size: int, transform: str) -> str:
    # Le carré bleu plein, sans coins : la plateforme les arrondit elle-même.
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" '
        f'width="{size}" height="{size}" style="display:block">'
        f'<rect width="100" height="100" fill="{BLUE}"/>'
        f'<g transform="{transform}">{face(WHITE, SPARK, 14, 10)}</g></svg>'
    )


def black_svg() -> str:
    # « Noir seul » : le visage en noir, sans carré, pour les documents et l'impression.
    black = face("#000000", "#000000", 14, 10)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="8 8 86 86">{black}</svg>\n'


async def render(browser, svg: str, size: int, target: Path) -> None:
    # Une page neuve par icône, à sa taille : changer la taille d'une page déjà rendue
    # laissait parfois l'ancien rendu dans la capture.
    page = await browser.new_page(viewport={"width": size, "height": size})
    body = f'<html><body style="margin:0;background:transparent">{svg}</body></html>'
    await page.set_content(body)
    await page.screenshot(path=str(target), omit_background=True)
    await page.close()
    print("écrit", target.relative_to(FRONT.parent))


async def main() -> None:
    (PUBLIC / "favicon.svg").write_text(badge() + "\n", "utf-8")
    print("écrit frontend/public/favicon.svg")
    (PUBLIC / "logo-noir.svg").write_text(black_svg(), "utf-8")
    print("écrit frontend/public/logo-noir.svg")
    async with async_playwright() as p:
        chrome = os.environ.get("CHROME")
        launch = {"executable_path": chrome} if chrome else {}
        browser = await p.chromium.launch(**launch)
        await render(browser, badge(32), 32, PUBLIC / "favicon-32.png")
        for size in (16, 32, 48, 128):
            await render(browser, badge(size), size, EXTENSION / f"{size}.png")
        for size, name in ((180, "apple-touch-icon"), (192, "icon-192"), (512, "icon-512")):
            await render(browser, full(size, FULL), size, PUBLIC / f"{name}.png")
        # « maskable » : le visage dans la zone sûre (le cercle de 80 %), donc plus petit.
        await render(browser, full(512, MASKABLE), 512, PUBLIC / "icon-maskable-512.png")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
