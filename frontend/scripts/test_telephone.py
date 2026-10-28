"""Test de l'audit téléphone : il trouve un élément hors de l'écran et une cible trop petite, mais
laisse passer un conteneur qui défile exprès, un lien dans une phrase et une cible agrandie par un
::before positionné.

    make test-audit
"""

import os
import sys
from pathlib import Path

import pytest
from playwright.sync_api import Page, sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from telephone import AUDIT

BASE = """
<style>
  body { margin: 0; font: 16px/1.5 sans-serif; }
  button { margin: 0; padding: 0; border: 0; }
</style>
<main>%s</main>
"""


@pytest.fixture(scope="module")
def page():
    with sync_playwright() as p:
        chrome = os.environ.get("CHROME")
        if chrome:
            browser = p.chromium.launch(executable_path=chrome)
        else:
            try:
                browser = p.chromium.launch(channel="chrome")
            except Exception:
                browser = p.chromium.launch()
        yield browser.new_page(viewport={"width": 320, "height": 640})
        browser.close()


def audit(page: Page, html: str) -> list[str]:
    page.set_content(BASE % html)
    return page.evaluate(AUDIT)


def test_un_bloc_trop_large_sort_de_l_ecran(page: Page) -> None:
    faults = audit(page, '<div class="large" style="width: 400px; height: 20px"></div>')
    assert any("hors de l'écran" in f and "div.large" in f for f in faults)
    assert any("défile horizontalement" in f for f in faults)


def test_un_conteneur_qui_defile_expres_est_exclu(page: Page) -> None:
    html = '<div style="overflow-x: auto; width: 300px"><div style="width: 600px; height: 20px"></div></div>'
    assert audit(page, html) == []


def test_un_debordement_cache_par_son_parent_est_exclu(page: Page) -> None:
    html = '<div style="overflow: hidden; width: 300px"><div style="width: 600px; height: 20px"></div></div>'
    assert audit(page, html) == []


def test_une_cible_trop_petite(page: Page) -> None:
    faults = audit(page, '<button class="petit" style="width: 20px; height: 20px">x</button>')
    assert any("cible de 20 × 20 px" in f and "button.petit" in f for f in faults)


def test_une_cible_agrandie_par_un_before_positionne(page: Page) -> None:
    html = """
    <style>
      .zone { position: relative; width: 20px; height: 20px; }
      .zone::before { content: ""; position: absolute; inset: -12px; }
    </style>
    <button class="zone">x</button>
    """
    assert audit(page, html) == []


def test_une_ligne_entiere_cliquable_par_le_after_de_son_titre(page: Page) -> None:
    html = """
    <style>
      .ligne { position: relative; padding: 12px; }
      .titre { font-size: 14px; line-height: 1; }
      .titre::after { content: ""; position: absolute; inset: 0; }
    </style>
    <div class="ligne"><button class="titre">Poste</button><p>Entreprise</p></div>
    """
    assert audit(page, html) == []


def test_un_contenu_coupe_par_html_et_body_reste_un_defaut(page: Page) -> None:
    html = '<style>html, body { overflow-x: clip; }</style><div class="large" style="width: 400px; height: 20px"></div>'
    assert any("hors de l'écran" in f and "div.large" in f for f in audit(page, html))


def test_un_lien_dans_une_phrase_est_exempte(page: Page) -> None:
    html = '<p style="font-size: 12px">Lis les <a href="#">conditions</a> avant de continuer, merci.</p>'
    assert audit(page, html) == []


def test_un_texte_masque_pour_l_ecran_est_ignore(page: Page) -> None:
    html = (
        '<span style="position: absolute; width: 1px; height: 1px; overflow: hidden; '
        'clip: rect(0 0 0 0); left: -9999px">Lien caché</span>'
    )
    assert audit(page, html) == []
