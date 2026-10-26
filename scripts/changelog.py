"""L'historique des versions, assemblé (1.6.36).

Chaque version a son fichier, `changelog.d/X.Y.Z.md` : sa première ligne est le contenu de la
version, une ligne facultative « État : … » remplace l'état par défaut (« livrée »). Une PR ajoute
son fichier et ne touche plus à `CHANGELOG.md` : deux PR n'éditent jamais le même fichier, donc
plus de conflit. Sur main, une action GitHub assemble `CHANGELOG.md` après chaque fusion
(.github/workflows/changelog.yml).

    python3 scripts/changelog.py           # assemble CHANGELOG.md
    python3 scripts/changelog.py --check   # vérifie les fichiers de changelog.d (CI)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / "changelog.d"
TARGET = ROOT / "CHANGELOG.md"
NAME = re.compile(r"^(\d+)\.(\d+)\.(\d+)\.md$")
STATE = re.compile(r"^État\s*:\s*(.+)$")

HEADER = """# Historique des versions

Une ligne par version, la plus récente en bas. Le détail de chaque version (ce qui change, ce
qui est vérifié) est dans le document de cadrage qu'elle cite.

**Ce fichier est assemblé : ne le modifie pas.** Une version ajoute son fichier
`changelog.d/X.Y.Z.md` (la première ligne : le contenu ; une ligne « État : … » facultative,
sinon « livrée ») ; sur main, `scripts/changelog.py` assemble ce tableau après chaque fusion.

| Version | Contenu | État |
|---|---|---|
"""


def version(path: Path) -> tuple[int, int, int]:
    match = NAME.match(path.name)
    if not match:
        raise ValueError(f"{path.name} : le nom doit être X.Y.Z.md (par exemple 1.6.36.md)")
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch)


def entry(path: Path) -> tuple[str, str]:
    """Le contenu et l'état d'une version, depuis son fichier."""
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    state = "livrée"
    content: list[str] = []
    for line in lines:
        found = STATE.match(line)
        if found:
            state = found.group(1).strip()
        else:
            content.append(line)
    if len(content) != 1:
        lines_found = len(content)
        raise ValueError(
            f"{path.name} : une seule ligne de contenu attendue, {lines_found} trouvée(s)"
        )
    if "|" in content[0] or "|" in state:
        raise ValueError(f"{path.name} : pas de « | », il couperait la ligne du tableau")
    return content[0], state


def files(folder: Path = FOLDER) -> list[Path]:
    found = [path for path in folder.iterdir() if path.suffix == ".md" and path.name != "README.md"]
    return sorted(found, key=version)


def assemble(folder: Path = FOLDER) -> str:
    rows = []
    for path in files(folder):
        content, state = entry(path)
        rows.append(f"| {path.stem} | {content} | {state} |")
    return HEADER + "\n".join(rows) + "\n"


def check(folder: Path = FOLDER) -> list[str]:
    errors = []
    for path in folder.iterdir():
        if path.name == "README.md":
            continue
        try:
            version(path)
            entry(path)
        except ValueError as error:
            errors.append(str(error))
    return errors


def main(argv: list[str]) -> int:
    if "--check" in argv:
        errors = check()
        for error in errors:
            print(error, file=sys.stderr)
        count = len(files()) if not errors else "?"
        print(f"changelog.d : {count} versions, {len(errors)} erreur(s)")
        return 1 if errors else 0
    TARGET.write_text(assemble(), encoding="utf-8")
    print(f"{TARGET.name} assemblé : {len(files())} versions")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
