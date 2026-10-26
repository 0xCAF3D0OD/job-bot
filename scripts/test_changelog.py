"""Les tests de l'assemblage de l'historique (1.6.36) : python3 -m unittest discover -s scripts."""

import tempfile
import unittest
from pathlib import Path

import changelog


class Changelog(unittest.TestCase):
    def folder(self, files: dict[str, str]) -> Path:
        directory = Path(tempfile.mkdtemp())
        for name, text in files.items():
            (directory / name).write_text(text, encoding="utf-8")
        return directory

    def test_les_versions_dans_l_ordre_des_numeros(self) -> None:
        folder = self.folder(
            {
                "1.10.0.md": "Dix\n",
                "1.2.0.md": "Deux\n",
                "1.2.10.md": "Deux, dix\n",
                "README.md": "x",
            }
        )
        rows = [line for line in changelog.assemble(folder).splitlines() if line.startswith("| 1")]
        self.assertEqual([row.split(" | ")[0] for row in rows], ["| 1.2.0", "| 1.2.10", "| 1.10.0"])

    def test_l_etat_par_defaut_et_l_etat_ecrit(self) -> None:
        folder = self.folder(
            {"0.1.0.md": "Squelette\n", "0.2.0.md": "Collecte\nÉtat : livrée (en partie)\n"}
        )
        text = changelog.assemble(folder)
        self.assertIn("| 0.1.0 | Squelette | livrée |", text)
        self.assertIn("| 0.2.0 | Collecte | livrée (en partie) |", text)

    def test_les_fichiers_mal_formes_sont_signales(self) -> None:
        folder = self.folder(
            {
                "1.6.x.md": "Mauvais nom\n",
                "1.6.1.md": "Deux\nlignes\n",
                "1.6.2.md": "Avec | barre\n",
            }
        )
        errors = changelog.check(folder)
        self.assertEqual(len(errors), 3)

    def test_le_depot_est_bien_forme(self) -> None:
        self.assertEqual(changelog.check(), [])


if __name__ == "__main__":
    unittest.main()
