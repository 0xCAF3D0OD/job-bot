"""L'historique des versions, assemblé (1.6.36), numéroté à la fusion.

Une PR dépose un fragment sans numéro, `changelog.d/<sujet>.md` (minuscules, chiffres et tirets) :
sa première ligne est le contenu de la version, une ligne facultative « État : … » remplace l'état
par défaut (« livrée »). Sur main, après chaque fusion, une action GitHub donne à chaque fragment le
numéro suivant, dans l'ordre de fusion, le renomme en `changelog.d/X.Y.Z.md` et assemble
`CHANGELOG.md` (.github/workflows/changelog.yml). Une PR ne touche donc aucun fichier partagé :
ni `CHANGELOG.md`, ni un numéro qu'une autre PR pourrait prendre aussi.

    python3 scripts/changelog.py            # assemble CHANGELOG.md
    python3 scripts/changelog.py --number   # numérote les fragments, puis assemble (sur main)
    python3 scripts/changelog.py --check    # vérifie les fichiers de changelog.d (CI)
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / "changelog.d"
TARGET = ROOT / "CHANGELOG.md"
NAME = re.compile(r"^(\d+)\.(\d+)\.(\d+)\.md$")
FRAGMENT = re.compile(r"^[a-z0-9][a-z0-9-]*\.md$")
STATE = re.compile(r"^État\s*:\s*(.+)$")

HEADER = """# Historique des versions

Une ligne par version, la plus récente en bas. Le détail de chaque version (ce qui change, ce
qui est vérifié) est dans le document de cadrage qu'elle cite.

**Ce fichier est assemblé : ne le modifie pas.** Une PR dépose `changelog.d/<sujet>.md`, sans
numéro (la première ligne : le contenu ; une ligne « État : … » facultative, sinon « livrée ») ;
sur main, `scripts/changelog.py` lui donne le numéro suivant à la fusion et assemble ce tableau.

| Version | Contenu | État |
|---|---|---|
"""


def version(path: Path) -> tuple[int, int, int]:
    match = NAME.match(path.name)
    if not match:
        raise ValueError(
            f"{path.name} : le nom doit être <sujet>.md (minuscules, chiffres, tirets) ou X.Y.Z.md"
        )
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
    """Les versions numérotées, dans l'ordre des numéros."""
    found = [path for path in folder.iterdir() if NAME.match(path.name)]
    return sorted(found, key=version)


def fragments(folder: Path = FOLDER) -> list[Path]:
    """Les fragments pas encore numérotés, par nom."""
    return sorted(path for path in folder.iterdir() if FRAGMENT.match(path.name))


def merged_at(path: Path) -> tuple[int, str]:
    """L'ordre de fusion d'un fragment : la date du commit qui l'a ajouté, puis son nom."""
    result = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%ct", "-1", "--", path.name],
        cwd=path.parent, capture_output=True, text=True, check=False,
    )
    stamp = result.stdout.strip()
    return (int(stamp) if stamp.isdigit() else 0, path.name)


def number(
    folder: Path = FOLDER, order: Callable[[Path], tuple[int, str]] = merged_at
) -> list[tuple[str, str]]:
    """Donne à chaque fragment le numéro suivant, dans l'ordre de fusion, et le renomme."""
    numbered = files(folder)
    major, minor, patch = version(numbered[-1]) if numbered else (0, 0, 0)
    renamed = []
    for path in sorted(fragments(folder), key=order):
        patch += 1
        target = folder / f"{major}.{minor}.{patch}.md"
        if target.exists():
            raise ValueError(f"{target.name} existe déjà : numérotation impossible")
        path.rename(target)
        renamed.append((path.name, target.name))
    return renamed


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
            if not FRAGMENT.match(path.name):
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
        waiting = len(fragments()) if not errors else "?"
        print(f"changelog.d : {count} versions, {waiting} à numéroter, {len(errors)} erreur(s)")
        return 1 if errors else 0
    if "--number" in argv:
        for before, after in number():
            print(f"{before} → {after}")
    TARGET.write_text(assemble(), encoding="utf-8")
    print(f"{TARGET.name} assemblé : {len(files())} versions")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
