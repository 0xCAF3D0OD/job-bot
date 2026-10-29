"""Test de l'audit des contrôles : il trouve une rangée de hauteurs inégales et une liste dont le texte
passe sous le chevron, et laisse passer une rangée égale à 1 px près et une liste assez large.

    make test-audit
"""

import os
import sys
from pathlib import Path

import pytest
from playwright.sync_api import Page, sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from controles import AUDIT, TOLERANCE

BASE = """
<style>
  body { margin: 0; font: 16px/1.5 sans-serif; }
  button, select { margin: 0; border: 0; box-sizing: border-box; font: inherit; }
  .row { display: flex; gap: 8px; }
  select { appearance: none; padding: 0 2rem 0 0.75rem; }
</style>
<main><section>%s</section></main>
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
        yield browser.new_page(viewport={"width": 1440, "height": 900})
        browser.close()


def audit(page: Page, html: str) -> list[str]:
    page.set_content(BASE % html)
    return page.evaluate(AUDIT, TOLERANCE)


def test_une_rangee_de_hauteurs_inegales_echoue(page: Page) -> None:
    faults = audit(page, '<div class="row"><button style="height: 44px">Préparer</button><button style="height: 40px">Modifier</button></div>')
    assert len(faults) == 1
    assert "hauteurs inégales" in faults[0] and "Préparer » 44 px" in faults[0] and "Modifier » 40 px" in faults[0]


def test_un_pixel_d_ecart_passe(page: Page) -> None:
    html = '<div class="row"><button style="height: 44px">Préparer</button><select style="height: 43px; width: 200px"><option>Tous</option></select></div>'
    assert audit(page, html) == []


def test_deux_rangees_distinctes_ne_se_comparent_pas(page: Page) -> None:
    html = '<button style="height: 44px; display: block">Un</button><button style="height: 32px; display: block">Deux</button>'
    assert audit(page, html) == []


def test_le_texte_d_une_liste_sous_le_chevron_echoue(page: Page) -> None:
    html = '<select aria-label="Statut" style="width: 140px; height: 44px"><option>Tous</option><option>Entretien obtenu ce mois</option></select>'
    faults = audit(page, html)
    assert len(faults) == 1
    assert "liste select « Statut »" in faults[0] and "Entretien obtenu" in faults[0] and "padding-right 32px" in faults[0]


def test_une_liste_assez_large_passe(page: Page) -> None:
    html = '<select aria-label="Statut" style="width: 320px; height: 44px"><option>Tous</option><option>Entretien obtenu ce mois</option></select>'
    assert audit(page, html) == []


def test_la_liste_se_nomme_par_son_etiquette(page: Page) -> None:
    html = '<label for="tri">Trier par</label><select id="tri" style="width: 90px; height: 44px"><option>Date de publication</option></select>'
    faults = audit(page, html)
    assert any("« Trier par »" in f for f in faults)
