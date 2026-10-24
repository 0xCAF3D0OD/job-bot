"""Test de l'audit des règles (1.6.3) : la mesure « texte à moins de 1,25 rem du bord » ignore la
partie cachée d'un texte coupé par « … » (1.6.2), mais trouve toujours un vrai texte collé au bord.

    make test-audit
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
        # CHROME si donné ; sinon le Chrome installé ; sinon le Chromium de Playwright (la CI).
        chrome = os.environ.get("CHROME")
        if chrome:
            browser = p.chromium.launch(executable_path=chrome)
        else:
            try:
                browser = p.chromium.launch(channel="chrome")
            except Exception:
                browser = p.chromium.launch()
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


def stuck(page: Page, body: str) -> list[str]:
    page.set_content(BASE % body)
    return [f for f in page.evaluate(AUDIT, MAX_WORDS) if "texte collé" in f]


def test_un_vrai_texte_colle_a_celui_du_dessus_est_trouve(page: Page) -> None:
    line = '<p style="margin: 0; line-height: 1.2">%s</p>'
    body = line % "Premier texte" + line % "Second texte"
    assert stuck(page, body)


def test_un_texte_rogne_par_une_fiche_qui_defile_ne_compte_pas(page: Page) -> None:
    # 1.6.19 : sur téléphone, le détail d'une offre est une fiche fixée qui défile en elle-même ;
    # sa suite, rognée sous l'écran, n'est pas visible et ne colle à rien.
    body = (
        '<div style="position: fixed; inset: 0; overflow: auto; background: #fff">'
        '<div style="height: 430px"></div>'
        '<p style="margin: 0; line-height: 1">Suite rognée de la fiche</p></div>'
        '<div style="height: 448px"></div>'
        '<p style="margin: 0; line-height: 1">Il te manque : Spark, SQL</p>'
    )
    assert stuck(page, body) == []
