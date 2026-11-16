"""Les tests de l'assemblage des décisions : python3 -m unittest discover -s scripts."""

import tempfile
import unittest
from pathlib import Path

import decisions


class Decisions(unittest.TestCase):
    def folder(self, files: dict[str, str]) -> Path:
        directory = Path(tempfile.mkdtemp())
        for name, text in files.items():
            (directory / name).write_text(text, encoding="utf-8")
        return directory

    def test_triees_par_date_puis_par_heure(self) -> None:
        folder = self.folder(
            {
                "2026-11-15-1709-soir.md": "## Soir\n\n- c\n",
                "2026-11-15-0905-matin.md": "## Matin\n\n- b\n",
                "2026-11-15-sans-heure.md": "## Sans heure\n\n- a\n",
                "2026-11-14-veille.md": "## Veille\n\n- z\n",
                "README.md": "x",
            }
        )
        titles = [line for line in decisions.assemble(folder).splitlines() if line.startswith("## ")]
        self.assertEqual(titles, ["## Veille", "## Sans heure", "## Matin", "## Soir"])

    def test_le_texte_est_repris_tel_quel(self) -> None:
        folder = self.folder({"2026-11-15-un.md": "## Un\n\n| Date | Décision |\n|---|---|\n| 2026-11-15 | x |\n"})
        self.assertIn("\n## Un\n\n| Date | Décision |\n|---|---|\n| 2026-11-15 | x |\n", decisions.assemble(folder))

    def test_les_fichiers_mal_formes_sont_signales(self) -> None:
        folder = self.folder(
            {
                "bandeau-peche.md": "## Sans date\n\n- x\n",
                "2026-02-30-date.md": "## Date impossible\n\n- x\n",
                "2026-11-15-2575-heure.md": "## Heure impossible\n\n- x\n",
                "2026-11-15-Majuscules.md": "## Nom\n\n- x\n",
                "2026-11-15-sans-titre.md": "- x\n",
                "2026-11-15-titre-seul.md": "## Titre seul\n",
                "2026-11-15-bon.md": "## Bon\n\n- x\n",
                "README.md": "x",
            }
        )
        errors = decisions.check(folder)
        self.assertEqual(len(errors), 6, errors)
        self.assertFalse(any("2026-11-15-bon.md" in error for error in errors))

    def test_les_fichiers_du_depot_sont_valides(self) -> None:
        # DECISIONS.md n'est pas comparé : sur une PR, il est assemblé seulement après la fusion.
        self.assertEqual(decisions.check(), [])


if __name__ == "__main__":
    unittest.main()
