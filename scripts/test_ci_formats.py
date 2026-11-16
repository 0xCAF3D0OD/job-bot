"""Les tests du choix des audits d'écran (ci_formats.py) : python3 -m unittest discover -s scripts."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import ci_formats
from ci_formats import BOTH, DESK, NONE, PHONE

CSS = """\
:root { --space-2: 8px; }
.card {
  padding: 16px;
}

@media (max-width: 820px) {
  .card {
    padding: 12px;
  }
  /* commentaire */

  @media (prefers-color-scheme: dark) {
    .card { color: white; }
  }
}
@media (min-width: 821px) {
  .card { padding: 24px; }
}
@media (prefers-reduced-motion: reduce) {
  .card { transition: none; }
}
@media (max-width: 1200px) {
  .card { gap: 8px; }
}
@media print {
  .card { display: none; }
}
"""


class Media(unittest.TestCase):
    def test_largeurs(self) -> None:
        self.assertEqual(ci_formats.media_formats("@media (max-width: 820px)"), {PHONE})
        self.assertEqual(ci_formats.media_formats("@media (max-width: 599px)"), {PHONE})
        self.assertEqual(ci_formats.media_formats("@media (min-width: 821px)"), {DESK})
        self.assertEqual(ci_formats.media_formats("@media (min-width: 1024px)"), {DESK})
        self.assertEqual(ci_formats.media_formats("@media (min-width: 600px) and (max-width: 820px)"), {PHONE})
        self.assertEqual(ci_formats.media_formats("@media (min-width: 821px) and (max-width: 1200px)"), {DESK})

    def test_largeur_a_cheval_ou_sans_largeur(self) -> None:
        self.assertEqual(ci_formats.media_formats("@media (max-width: 1200px)"), BOTH)
        self.assertEqual(ci_formats.media_formats("@media (min-width: 600px)"), BOTH)
        self.assertEqual(ci_formats.media_formats("@media (prefers-color-scheme: dark)"), BOTH)
        self.assertEqual(ci_formats.media_formats("@media (pointer: coarse), (max-width: 820px)"), BOTH)
        self.assertEqual(ci_formats.media_formats("@media not ((hover: hover) and (pointer: fine))"), BOTH)
        self.assertEqual(ci_formats.media_formats("@media print"), NONE)


class Lignes(unittest.TestCase):
    def test_chaque_ligne_suit_son_bloc(self) -> None:
        lines = ci_formats.line_formats(CSS)
        self.assertEqual(lines[1], BOTH)  # :root
        self.assertEqual(lines[3], BOTH)  # hors @media
        self.assertEqual(lines[6], {PHONE})  # la ligne « @media (max-width: 820px) { »
        self.assertEqual(lines[8], {PHONE})
        self.assertEqual(lines[10], NONE)  # un commentaire ne change rien
        self.assertEqual(lines[11], NONE)  # une ligne vide non plus
        self.assertEqual(lines[13], {PHONE})  # imbriqué : téléphone et sombre
        self.assertEqual(lines[15], {PHONE})  # l'accolade qui ferme le bloc
        self.assertEqual(lines[17], {DESK})
        self.assertEqual(lines[20], BOTH)  # mouvements réduits
        self.assertEqual(lines[23], BOTH)  # 1200 px : aussi le téléphone
        self.assertEqual(lines[26], NONE)  # impression

    def test_le_style_d_un_vue(self) -> None:
        source = "<template>\n  <div />\n</template>\n<style scoped>\n@media (min-width: 821px) {\n  .a { gap: 4px; }\n}\n</style>\n"
        lines = ci_formats.vue_formats(source)
        self.assertEqual(lines[2], BOTH)
        self.assertEqual(lines[6], {DESK})


class Depot(unittest.TestCase):
    """Un vrai dépôt git : une PR de chaque sorte."""

    def setUp(self) -> None:
        self.folder = Path(tempfile.mkdtemp())
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "test")
        self.write("frontend/src/style.css", CSS)
        self.write("frontend/src/stores.ts", "export const a = 1;\n")
        self.write("frontend/src/components/HomePhone.vue", "<template><div /></template>\n")
        self.write("docs/mobile/DECISIONS.md", "# Décisions\n")
        self.write("CLAUDE.md", "# Consignes\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "base")
        self.base = self.git("rev-parse", "HEAD").strip()
        self.cwd = os.getcwd()
        os.chdir(self.folder)

    def tearDown(self) -> None:
        os.chdir(self.cwd)

    def git(self, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=self.folder, check=True, capture_output=True, text=True).stdout

    def write(self, path: str, text: str) -> None:
        target = self.folder / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def formats(self) -> set[str]:
        self.git("add", "-A")
        self.git("commit", "-qm", "pr")
        found: set[str] = set()
        for row in subprocess.run(["git", "diff", "--name-status", "-M", self.base, "HEAD"], check=True, capture_output=True, text=True).stdout.splitlines():
            _status, *paths = row.split("\t")
            formats, _ = ci_formats.file_formats(paths[-1], paths[0], self.base, "HEAD")
            found |= formats
        return found

    def test_documentation_seule_aucun_audit(self) -> None:
        self.write("CLAUDE.md", "# Consignes\n- une règle\n")
        self.write("docs/mobile/DECISIONS.md", "# Décisions\n- une décision\n")
        self.assertEqual(self.formats(), set())

    def test_style_du_telephone_seul(self) -> None:
        self.write("frontend/src/style.css", CSS.replace("padding: 12px;", "padding: 8px;"))
        self.assertEqual(self.formats(), {PHONE})

    def test_style_de_l_ordinateur_seul(self) -> None:
        self.write("frontend/src/style.css", CSS.replace("padding: 24px;", "padding: 32px;"))
        self.assertEqual(self.formats(), {DESK})

    def test_commentaire_seul(self) -> None:
        self.write("frontend/src/style.css", CSS.replace("/* commentaire */", "/* un autre commentaire */"))
        self.assertEqual(self.formats(), set())

    def test_style_partage(self) -> None:
        self.write("frontend/src/style.css", CSS.replace("--space-2: 8px", "--space-2: 10px"))
        self.assertEqual(self.formats(), BOTH)

    def test_composant_du_telephone(self) -> None:
        self.write("frontend/src/components/HomePhone.vue", "<template><p /></template>\n")
        self.assertEqual(self.formats(), {PHONE})

    def test_logique_partagee(self) -> None:
        self.write("frontend/src/stores.ts", "export const a = 2;\n")
        self.assertEqual(self.formats(), BOTH)


if __name__ == "__main__":
    unittest.main()
