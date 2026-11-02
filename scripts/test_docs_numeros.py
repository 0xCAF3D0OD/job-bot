"""Les tests de la vérification des numéros de docs/ : python3 -m unittest discover -s scripts."""

import tempfile
import unittest
from pathlib import Path

import docs_numeros


class DocsNumeros(unittest.TestCase):
    def folder(self, names: list[str]) -> Path:
        directory = Path(tempfile.mkdtemp())
        for name in names:
            (directory / name).write_text("x", encoding="utf-8")
        return directory

    def test_des_numeros_distincts_passent(self) -> None:
        folder = self.folder(["1-a.md", "14-b.md", "138-c.md", "regles.md", "README.md"])
        self.assertEqual(docs_numeros.duplicates(folder), {})

    def test_un_numero_pris_deux_fois_est_signale(self) -> None:
        folder = self.folder(["138-c.md", "139-billet.md", "139-classiques.md"])
        self.assertEqual(
            docs_numeros.duplicates(folder), {139: ["139-billet.md", "139-classiques.md"]}
        )

    def test_le_zero_de_tete_compte_comme_le_meme_numero(self) -> None:
        folder = self.folder(["7-a.md", "07-b.md"])
        self.assertEqual(list(docs_numeros.duplicates(folder)), [7])

    def test_le_prochain_numero_suit_le_plus_grand(self) -> None:
        folder = self.folder(["9-a.md", "138-b.md", "apres-le-test.md"])
        self.assertEqual(docs_numeros.next_number(folder), 139)

    def test_un_dossier_n_est_pas_un_document(self) -> None:
        folder = self.folder(["5-a.md"])
        (folder / "5-captures.md").mkdir()
        self.assertEqual(docs_numeros.duplicates(folder), {})


if __name__ == "__main__":
    unittest.main()
