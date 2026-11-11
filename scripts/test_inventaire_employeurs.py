"""Tests de l'inventaire des pages carrières, sans réseau : `python3 -m unittest discover -s scripts`."""

import json
import unittest

import inventaire_employeurs as inv
from inventaire_employeurs import Employer, Page, Polite

JOBPOSTING = """<script type="application/ld+json">{"@context":"https://schema.org","@graph":[
{"@type":"Organization","name":"X"},{"@type":"JobPosting","title":"Infirmier"}]}</script>"""


def site(pages: dict[str, Page | str]):
    """Un faux web : les adresses absentes répondent 404 ; garde la liste des lectures."""
    seen: list[str] = []

    def fetch(url: str) -> Page:
        seen.append(url)
        page = pages.get(url)
        if page is None:
            return Page(404, url, "")
        return page if isinstance(page, Page) else Page(200, url, page)

    return Polite(fetch, sleep=lambda _s: None), seen


class Detection(unittest.TestCase):
    def test_compte_les_jobposting_meme_dans_un_graph(self):
        self.assertEqual(inv.postings(JOBPOSTING), 1)
        self.assertEqual(inv.postings("<script type='application/ld+json'>{pas du json</script>"), 0)

    def test_reconnait_les_logiciels(self):
        self.assertEqual(inv.platform("https://acme.jobs.personio.de/job/1"), ("Personio", "1"))
        self.assertEqual(inv.platform('<iframe src="https://career5.successfactors.eu/career?company=x">'), ("SuccessFactors", "3"))
        self.assertEqual(inv.platform("https://www.refline.ch/123/index.html"), ("Refline", "3"))
        self.assertEqual(inv.platform("https://recruitingapp-1.umantis.com/Jobs/All"), ("Abacus / umantis", "3"))
        self.assertEqual(inv.platform("https://www.example.ch"), ("", ""))

    def test_conditions(self):
        self.assertEqual(
            inv.terms_verdict("<p>Bienvenue.</p><p>L'extraction automatique du contenu par des robots est interdite.</p>")[0],
            "interdite",
        )
        self.assertEqual(inv.terms_verdict("<p>Le contenu est protégé par le droit d'auteur.</p>"), ("rien", ""))
        self.assertEqual(inv.terms_verdict("Les robots des moteurs de recherche sont autorisés.")[0], "permise")


class Robots(unittest.TestCase):
    def test_une_page_interdite_n_est_jamais_lue(self):
        web, seen = site({
            "https://a.ch/robots.txt": "User-agent: *\nDisallow: /\n",
            "https://a.ch/": "<a href='/carriere'>Carrière</a>",
        })
        result = inv.inspect(Employer("A", "sante", "https://a.ch/"), web)
        self.assertEqual(result.cas, "robots.txt interdit")
        self.assertEqual(seen, ["https://a.ch/robots.txt"])

    def test_robots_403_vaut_tout_interdit(self):
        web, seen = site({"https://b.ch/robots.txt": Page(403, "https://b.ch/robots.txt", "")})
        self.assertFalse(web.allowed("https://b.ch/emplois"))

    def test_site_injoignable(self):
        web, _ = site({"https://c.ch/robots.txt": Page(0, "https://c.ch/robots.txt", "")})
        self.assertEqual(inv.inspect(Employer("C", "bureau", "https://c.ch/"), web).cas, "erreur")

    def test_crawl_delay_respecte(self):
        waits: list[float] = []
        pages = {"https://d.ch/robots.txt": "User-agent: *\nCrawl-delay: 5\n", "https://d.ch/": "x", "https://d.ch/b": "y"}
        web = Polite(lambda url: Page(200, url, pages.get(url, "")), sleep=waits.append)
        web.get("https://d.ch/")
        web.get("https://d.ch/b")
        self.assertTrue(waits and max(waits) > 4)


class Liste1(unittest.TestCase):
    def test_cas_2_jobposting_sur_une_page_d_offre(self):
        web, _ = site({
            "https://e.ch/robots.txt": "User-agent: *\nAllow: /\nSitemap: https://e.ch/sitemap.xml\n",
            "https://e.ch/": "<a href='/fr/carriere/'>Carrière</a><a href='/fr/conditions-generales'>Conditions générales</a>",
            "https://e.ch/fr/carriere/": "<a href='/fr/emploi/infirmier-12345'>Infirmier</a>",
            "https://e.ch/fr/emploi/infirmier-12345": JOBPOSTING,
            "https://e.ch/fr/conditions-generales": "<p>Toute extraction automatisée par robot est interdite sans accord écrit.</p>",
        })
        result = inv.inspect(Employer("E", "sante", "https://e.ch/"), web)
        self.assertEqual((result.cas, result.jobposting, result.sitemap), ("2", 1, "oui"))
        self.assertEqual(result.page_carrieres, "https://e.ch/fr/carriere/")
        self.assertEqual(result.conditions, "interdite")

    def test_cas_3_logiciel_sans_jobposting(self):
        web, _ = site({
            "https://f.ch/robots.txt": "",
            "https://f.ch/": "<a href='/emplois'>Offres d'emploi</a>",
            "https://f.ch/emplois": "<iframe src='https://www.refline.ch/012345/search.html'></iframe>",
        })
        result = inv.inspect(Employer("F", "batiment", "https://f.ch/"), web)
        self.assertEqual((result.cas, result.logiciel, result.conditions), ("3", "Refline", "pas de page trouvée"))

    def test_resume_compte_la_part_du_cas_3(self):
        employers = [Employer("A", "sante", "", logiciel="SuccessFactors", cas="2"), Employer("B", "sante", "", cas="inconnu")]
        text = "\n".join(inv.summary(employers))
        self.assertIn("même avec JobPosting : 1 (50 %)", text)


class Liste2(unittest.TestCase):
    def test_lieux_vaudois(self):
        self.assertTrue(inv.in_vaud("Lausanne, Switzerland"))
        self.assertTrue(inv.in_vaud("Écublens VD"))
        self.assertTrue(inv.in_vaud("Yverdon-les-Bains", "CH"))
        self.assertTrue(inv.in_vaud("Remote / Nyon"))
        self.assertFalse(inv.in_vaud("Genève"))
        self.assertFalse(inv.in_vaud("Crans-Montana"))
        self.assertFalse(inv.in_vaud("Lausanne", "US"))

    def test_comptes_tires_des_adresses(self):
        personio, greenhouse, recruitee = inv.FEEDS[0], inv.FEEDS[1], inv.FEEDS[3]
        self.assertEqual(personio.slug("https://acme-sa.jobs.personio.com/job/123"), "acme-sa")
        self.assertEqual(greenhouse.slug("https://boards.greenhouse.io/spotme/jobs/42"), "spotme")
        self.assertIsNone(greenhouse.slug("https://boards.greenhouse.io/embed/job_board?for=x"))
        self.assertIsNone(recruitee.slug("https://www.recruitee.com/"))

    def test_flux(self):
        xml = "<workzag-jobs><position><name>Comptable</name><office>Lausanne</office></position></workzag-jobs>"
        self.assertEqual(inv.parse_personio(xml), [("Comptable", "Lausanne", "")])
        lever = json.dumps([{"text": "Dev", "categories": {"location": "Lausanne", "allLocations": ["Lausanne", "Zurich"]}, "country": "CH"}])
        self.assertEqual(inv.parse_lever(lever)[0][0], "Dev")
        self.assertTrue(inv.in_vaud(*inv.parse_lever(lever)[0][1:]))
        self.assertEqual(inv.parse_greenhouse("pas du json"), [])


if __name__ == "__main__":
    unittest.main()
