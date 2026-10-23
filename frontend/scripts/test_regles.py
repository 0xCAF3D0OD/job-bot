"""Test de l'audit des règles (1.6.3) : la mesure « texte à moins de 1,25 rem du bord » ignore la
partie cachée d'un texte coupé par « … » (1.6.2), mais trouve toujours un vrai texte collé au bord.

    cd backend
    uv run --with playwright --with pytest pytest ../frontend/scripts/test_regles.py
"""

import os
import sys
from pathlib import Path

import pytest
from playwright.sync_api import Page, sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from regles import AUDIT, MAX_WORDS

LONG = "Pour les formulaires de candidature, facultatif, quatre sur cinq"
BASE = """
<style>
  body { margin: 0; font: 16px/1.5 sans-serif; }
  .form-card { width: 320px; border: 1px solid #ccc; box-sizing: border-box; }
  .cut { display: block; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
</style>
<main>%s</main>
"""


@pytest.fixture(scope="module")
def page():
    with sync_playwright() as p:
        chrome = os.environ.get("CHROME")
        browser = p.chromium.launch(**({"executable_path": chrome} if chrome else {}))
        yield browser.new_page(viewport={"width": 400, "height": 400})
        browser.close()


def faults(page: Page, body: str, setup: str = "") -> list[str]:
    page.set_content(BASE % body)
    if setup:
        page.evaluate(setup)
    return [f for f in page.evaluate(AUDIT, MAX_WORDS) if "du bord" in f]


# Le bord se mesure depuis l'extérieur de la carte : 4 px de marge et 1 px de bordure font 5 px.


def test_un_vrai_texte_colle_au_bord_est_trouve(page: Page) -> None:
    found = faults(
        page, '<div class="form-card" style="padding: 24px 4px"><p>Texte collé</p></div>'
    )
    assert found and "texte à 5 px du bord" in found[0]


def test_la_partie_cachee_d_un_texte_coupe_ne_compte_pas(page: Page) -> None:
    # La carte est taillée pour que le texte entier finisse à 4 px de son bord droit : avant la
    # 1.6.2, l'audit le comptait. Coupé à 200 px, sa partie visible en est loin.
    body = (
        '<div class="form-card" style="padding: 24px 0 24px 24px">'
        f'<span class="cut" style="width: 200px">{LONG}</span></div>'
    )
    setup = """() => {
      const span = document.querySelector('.cut');
      const range = document.createRange();
      range.selectNodeContents(span.firstChild);
      const full = range.getBoundingClientRect().width;
      document.querySelector('.form-card').style.width = `${1 + 24 + full + 4 + 1}px`;
    }"""
    assert faults(page, body, setup) == []


def test_un_texte_coupe_mais_visible_pres_du_bord_est_trouve(page: Page) -> None:
    # Coupé par « … », mais sa partie visible touche le bord : c'est un vrai défaut.
    body = f'<div class="form-card" style="padding: 24px 4px"><span class="cut">{LONG}</span></div>'
    found = faults(page, body)
    assert found and "texte à 5 px du bord" in found[0]
