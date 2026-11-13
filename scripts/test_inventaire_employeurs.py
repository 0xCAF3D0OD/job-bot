"""Tests de l'inventaire des pages carrières, sans réseau : `python3 -m unittest discover -s scripts`."""

import json
import unittest

import inventaire_employeurs as inv
from inventaire_employeurs import Employer, Page, Polite


def jobposting(title="Infirmier", town="Lausanne", date="2026-11-01"):
    item = {"@type": "JobPosting", "title": title, "datePosted": date}
    if town:
        item["jobLocation"] = {"@type": "Place", "address": {"addressLocality": town, "addressCountry": "CH"}}
    return f'<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@graph": [item]})}</script>'


def site(pages):
    """Un faux web : les adresses absentes répondent 404 ; garde la liste des lectures."""
    seen = []

    def fetch(url):
        seen.append(url)
        page = pages.get(url)
        if page is None:
            return Page(404, url, "")
        return page if isinstance(page, Page) else Page(200, url, page)

    return Polite(fetch, sleep=lambda _s: None), seen


TERMS_OK = "<p>Le contenu est protégé par le droit d'auteur.</p>"


class Detection(unittest.TestCase):
    def test_jobposting_dans_un_graph(self):
        found = inv.postings(jobposting())
        self.assertEqual(len(found), 1)
        self.assertTrue(inv.complete(found[0]))
        self.assertFalse(inv.complete(inv.postings(jobposting(town=""))[0]))
        self.assertEqual(inv.postings("<script type='application/ld+json'>{pas du json</script>"), [])

    def test_logiciels(self):
        self.assertEqual(inv.platform("https://acme.jobs.personio.de/job/1"), ("Personio", "1"))
        self.assertEqual(inv.platform("https://career5.successfactors.eu/career?company=x"), ("SuccessFactors", "3"))
        self.assertEqual(inv.platform("https://careers.bouygues-construction.com/go/Losinger-Marazzi-FR/9592101/"), ("SuccessFactors", "3"))
        self.assertEqual(inv.platform("https://swisscom.wd103.myworkdayjobs.com/en-US/X"), ("Workday", "autre"))
        self.assertEqual(inv.platform("https://www.example.ch"), ("", ""))

    def test_pages_d_offres(self):
        self.assertTrue(inv.is_offer("https://jobs.sicpa.com/job/Prilly-Chemist/1390396033/"))
        self.assertTrue(inv.is_offer("https://emploi.unisante.ch/offres/infirmier-12345"))
        self.assertFalse(inv.is_offer("https://www.vaudoise.ch/fr/carrieres/pourquoi-nous-rejoindre"))
        self.assertFalse(inv.is_offer("https://www.marti.ch/kataloge/2024"))

    def test_conditions(self):
        self.assertEqual(
            inv.terms_verdict("<p>L'extraction automatique du contenu par des robots est interdite.</p>")[0], "interdite"
        )
        self.assertEqual(inv.terms_verdict(TERMS_OK), ("rien", ""))
        self.assertEqual(inv.terms_verdict("Les robots des moteurs de recherche sont autorisés.")[0], "permise")

    def test_lieux_vaudois(self):
        self.assertTrue(inv.in_vaud("Lausanne, Switzerland"))
        self.assertTrue(inv.in_vaud("Écublens VD"))
        self.assertTrue(inv.in_vaud("Yverdon-les-Bains", "CH"))
        self.assertFalse(inv.in_vaud("Genève"))
        self.assertFalse(inv.in_vaud("Crans-Montana"))
        self.assertFalse(inv.in_vaud("Lausanne", "US"))


class Robots(unittest.TestCase):
    def test_une_page_interdite_n_est_jamais_lue(self):
        web, seen = site({"https://a.ch/robots.txt": "User-agent: *\nDisallow: /\n", "https://a.ch/": "x"})
        result = inv.inspect(Employer("A", "sante", "https://a.ch/"), web)
        self.assertEqual((result.robots, result.verdict), ("interdit", "non lisible"))
        self.assertEqual(seen, ["https://a.ch/robots.txt"])

    def test_robots_403_vaut_tout_interdit_et_404_absent(self):
        web, _ = site({"https://b.ch/robots.txt": Page(403, "https://b.ch/robots.txt", "")})
        self.assertFalse(web.allowed("https://b.ch/emplois"))
        web, _ = site({})
        self.assertTrue(web.allowed("https://c.ch/emplois"))
        self.assertEqual(web.robots_state["https://c.ch"], "absent")

    def test_crawl_delay_respecte(self):
        waits = []
        pages = {"https://d.ch/robots.txt": "User-agent: *\nCrawl-delay: 5\n", "https://d.ch/": "x", "https://d.ch/b": "y"}
        web = Polite(lambda url: Page(200, url, pages.get(url, "")), sleep=waits.append)
        web.get("https://d.ch/")
        web.get("https://d.ch/b")
        self.assertTrue(waits and max(waits) > 4)


class Inventaire(unittest.TestCase):
    def test_lisible_en_suivant_les_liens_jusqu_aux_offres(self):
        web, _ = site({
            "https://e.ch/robots.txt": "User-agent: *\nAllow: /\n",
            "https://e.ch/": "<a href='/fr/carrieres/'>Carrières</a><a href='/fr/conditions-generales'>Conditions générales</a>",
            "https://e.ch/fr/carrieres/": "<a href='/fr/carrieres/pourquoi-nous'>Pourquoi nous</a><a href='/fr/offres-d-emploi'>Nos offres d'emploi</a>",
            "https://e.ch/fr/offres-d-emploi": "<a href='/fr/emploi/infirmier-12345'>Infirmier</a><a href='/fr/emploi/assc-12346'>ASSC</a>",
            "https://e.ch/fr/emploi/infirmier-12345": jobposting("Infirmier", "Lausanne"),
            "https://e.ch/fr/emploi/assc-12346": jobposting("ASSC", "Genève"),
            "https://e.ch/fr/conditions-generales": TERMS_OK,
        })
        result = inv.inspect(Employer("E", "sante", "https://e.ch/"), web)
        self.assertEqual(result.page_carrieres, "https://e.ch/fr/offres-d-emploi")
        self.assertEqual((result.balisage, result.offres_vaud, result.conditions), ("oui", "1", "rien"))
        self.assertEqual(result.verdict, "lisible")

    def test_flux_public_du_cas_1(self):
        feed = json.dumps({"jobs": [{"title": "Dev", "location": {"name": "Lausanne, Switzerland"}},
                                    {"title": "PM", "location": {"name": "Zurich"}}]})
        web, _ = site({
            "https://f.ch/": "<a href='/legal'>Legal</a><a href='/careers'>Careers</a>",
            "https://f.ch/careers": "<iframe src='https://boards.greenhouse.io/embed/job_board?for=fco'></iframe>",
            "https://boards-api.greenhouse.io/v1/boards/fco/jobs": feed,
            "https://f.ch/legal": TERMS_OK,
        })
        result = inv.inspect(Employer("F", "informatique", "https://f.ch/"), web)
        self.assertEqual((result.logiciel, result.balisage, result.offres_vaud), ("Greenhouse", "flux Greenhouse", "1"))
        self.assertEqual(result.verdict, "lisible")

    def test_cas_3_et_conditions_introuvables(self):
        web, _ = site({
            "https://g.ch/emplois": "<iframe src='https://www.refline.ch/012345/search.html'></iframe>",
        })
        result = inv.inspect(Employer("G", "batiment", "https://g.ch/emplois"), web)
        self.assertEqual((result.logiciel, result.cas, result.verdict), ("Refline", "3", "non lisible"))
        self.assertIn("conditions à vérifier (pas de page trouvée)", result.raison)

    def test_balisage_partiel(self):
        web, _ = site({
            "https://h.ch/jobs/": "<a href='/jobs/123-dev'>Dev</a><a href='/cgu'>CGU</a>",
            "https://h.ch/jobs/123-dev": jobposting(town=""),
            "https://h.ch/cgu": TERMS_OK,
        })
        result = inv.inspect(Employer("H", "bureau", "https://h.ch/jobs/"), web)
        self.assertEqual((result.balisage, result.verdict), ("partiel", "non lisible"))

    def test_seuil(self):
        employers = [Employer("A", "sante;informatique", "", verdict="lisible"), Employer("B", "sante", "", verdict="non lisible"),
                     Employer("C", "bureau", "", verdict="non lisible", cas="3")]
        text = "\n".join(inv.summary(employers))
        self.assertIn("1 employeurs lisibles sur 3 (33%)", text)
        self.assertIn("pas atteint", text)
        self.assertIn("informatique : 1 lisibles sur 1", text)
        self.assertIn("(C)", text)


if __name__ == "__main__":
    unittest.main()
