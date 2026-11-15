"""Les décisions de Kevin, un fichier par décision, assemblées dans docs/mobile/DECISIONS.md.

Chaque PR qui note une décision dépose un fichier `docs/decisions/AAAA-MM-JJ-sujet.md`, ou
`docs/decisions/AAAA-MM-JJ-HHMM-sujet.md` quand l'heure est connue (sujet en minuscules, chiffres et
tirets). Sa première ligne est un titre `## …`, la suite est le texte de la décision. Sur main, après
chaque fusion, une action GitHub assemble `docs/mobile/DECISIONS.md`, trié par date puis par heure
(.github/workflows/decisions.yml). Deux PR ne touchent donc jamais le même fichier : plus de conflit
sur la fin de DECISIONS.md.

    python3 scripts/decisions.py            # assemble docs/mobile/DECISIONS.md
    python3 scripts/decisions.py --check    # vérifie les fichiers de docs/decisions (CI)
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / "docs" / "decisions"
TARGET = ROOT / "docs" / "mobile" / "DECISIONS.md"
NAME = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:-(\d{2})(\d{2}))?-([a-z0-9][a-z0-9-]*)\.md$")

HEADER = """# Décisions données après la maquette du 13 novembre

Une décision de Kevin donnée dans la conversation après le 13 novembre passe avant le paquet (LISEZMOI §2, CLAUDE.md).

**Ce fichier est assemblé : ne le modifie pas.** Une décision se note dans son propre fichier,
`docs/decisions/AAAA-MM-JJ-HHMM-sujet.md` (l'heure est facultative), qui commence par un titre `## …`
(docs/decisions/README.md). Sur main, `scripts/decisions.py` assemble ce fichier après chaque fusion,
trié par date puis par heure, la plus récente en bas.
"""


def key(path: Path) -> tuple[str, str, str]:
    """Trie par date, puis par heure (une décision sans heure passe en tête de sa journée), puis par sujet."""
    match = NAME.match(path.name)
    if not match:
        raise ValueError(f"{path.name} : nom attendu AAAA-MM-JJ-sujet.md ou AAAA-MM-JJ-HHMM-sujet.md")
    year, month, day, hour, minute, subject = match.groups()
    try:
        date(int(year), int(month), int(day))
    except ValueError:
        raise ValueError(f"{path.name} : la date {year}-{month}-{day} n'existe pas") from None
    if hour is not None and not (int(hour) < 24 and int(minute) < 60):
        raise ValueError(f"{path.name} : l'heure {hour}{minute} n'existe pas")
    return (f"{year}-{month}-{day}", f"{hour}{minute}" if hour else "", subject)


def entry(path: Path) -> str:
    text = path.read_text(encoding="utf-8").strip("\n")
    if not text.startswith("## "):
        raise ValueError(f"{path.name} : la première ligne doit être un titre « ## … »")
    if len(text.splitlines()) < 2 or not "".join(text.splitlines()[1:]).strip():
        raise ValueError(f"{path.name} : le titre est seul, il manque le texte de la décision")
    return text


def files(folder: Path = FOLDER) -> list[Path]:
    return sorted((p for p in folder.iterdir() if p.suffix == ".md" and p.name != "README.md"), key=key)


def assemble(folder: Path = FOLDER) -> str:
    return HEADER + "".join(f"\n{entry(path)}\n" for path in files(folder))


def check(folder: Path = FOLDER) -> list[str]:
    errors = []
    for path in folder.iterdir():
        if path.name == "README.md":
            continue
        try:
            key(path)
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
        print(f"docs/decisions : {count} décisions, {len(errors)} erreur(s)")
        return 1 if errors else 0
    TARGET.write_text(assemble(), encoding="utf-8")
    print(f"{TARGET.relative_to(ROOT)} assemblé : {len(files())} décisions")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
