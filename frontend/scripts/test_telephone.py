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


def run(page: Page, html: str) -> dict[str, list[str]]:
    page.set_content(BASE % html)
    return page.evaluate(AUDIT)


def audit(page: Page, html: str) -> list[str]:
    return run(page, html)["faults"]


def warnings(page: Page, html: str) -> list[str]:
    return run(page, html)["warnings"]


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


def test_l_etiquette_d_un_champ_de_saisie_n_est_pas_mesuree(page: Page) -> None:
    html = """
    <label for="nom" style="display: block; font-size: 14px; line-height: 21px">Nom</label>
    <input id="nom" style="display: block; width: 200px; height: 44px; box-sizing: border-box">
    """
    assert run(page, html) == {"faults": [], "warnings": []}


def test_l_etiquette_d_une_case_assez_grande_n_est_pas_mesuree(page: Page) -> None:
    html = """
    <label style="display: inline-flex; align-items: center; gap: 4px; font-size: 14px; line-height: 18px">
      <input type="checkbox" style="width: 24px; height: 24px; margin: 0">Oui
    </label>
    """
    assert audit(page, html) == []


def test_l_etiquette_d_une_case_a_cocher_cachee_reste_mesuree(page: Page) -> None:
    html = """
    <input id="ok" type="checkbox" style="position: absolute; opacity: 0">
    <label for="ok" style="display: inline-block; font-size: 14px; line-height: 18px">Oui</label>
    """
    assert any("label" in f and "Oui" in f for f in audit(page, html))


def test_un_lien_dans_une_phrase_est_exempte(page: Page) -> None:
    html = '<p style="font-size: 12px">Lis les <a href="#">conditions</a> avant de continuer, merci.</p>'
    assert audit(page, html) == []


def test_un_texte_masque_pour_l_ecran_est_ignore(page: Page) -> None:
    html = (
        '<span style="position: absolute; width: 1px; height: 1px; overflow: hidden; '
        'clip: rect(0 0 0 0); left: -9999px">Lien caché</span>'
    )
    assert audit(page, html) == []


def test_une_cible_entre_24_et_44_px_est_un_avertissement_sans_echec(page: Page) -> None:
    html = '<button class="moyen" style="width: 30px; height: 30px">x</button>'
    assert audit(page, html) == []
    assert any("30 × 30 px, moins de 44 px" in w and "button.moyen" in w for w in warnings(page, html))


def test_une_cible_de_44_px_ne_donne_rien(page: Page) -> None:
    html = '<button style="width: 44px; height: 44px">x</button>'
    assert run(page, html) == {"faults": [], "warnings": []}


def test_un_lien_dans_une_phrase_n_a_pas_d_avertissement(page: Page) -> None:
    html = '<p style="font-size: 12px">Lis les <a href="#">conditions</a> avant de continuer, merci.</p>'
    assert warnings(page, html) == []


def test_un_radio_dans_une_ligne_cliquable_compte_la_ligne(page: Page) -> None:
    html = """
    <div class="ligne" style="cursor: pointer; display: flex; height: 48px; align-items: center">
      <span>Un message par jour</span><div><input type="radio" style="width: 20px; height: 20px; margin: 0"></div>
    </div>
    """
    assert run(page, html) == {"faults": [], "warnings": []}


def test_un_radio_seul_de_20_px_reste_un_defaut(page: Page) -> None:
    faults = audit(page, '<input type="radio" style="width: 20px; height: 20px; margin: 0">')
    assert any("cible de 20 × 20 px" in f for f in faults)

