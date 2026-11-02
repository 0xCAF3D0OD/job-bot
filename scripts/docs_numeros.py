"""Un numéro de cadrage par document : docs/NNN-<sujet>.md n'est pris qu'une fois.

Le numéro d'un document de cadrage se choisit à la main, en prenant le suivant sur main. Deux PR
ouvertes en même temps peuvent donc prendre le même. La CI passe sur le commit de fusion de test
(main + la PR) : si main a déjà ce numéro, la vérification échoue et la PR doit prendre le suivant.

    python3 scripts/docs_numeros.py   # échoue si deux documents de docs/ portent le même numéro
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
NUMBERED = re.compile(r"^(\d+)-.+\.md$")


def duplicates(folder: Path) -> dict[int, list[str]]:
    """Les numéros portés par plus d'un document, avec leurs fichiers."""
    found: dict[int, list[str]] = defaultdict(list)
    for path in folder.iterdir():
        match = NUMBERED.match(path.name)
        if path.is_file() and match:
            found[int(match.group(1))].append(path.name)
    return {number: sorted(names) for number, names in sorted(found.items()) if len(names) > 1}


def next_number(folder: Path) -> int:
    """Le prochain numéro libre : le plus grand, plus un."""
    numbers = [int(m.group(1)) for p in folder.iterdir() if (m := NUMBERED.match(p.name))]
    return max(numbers, default=0) + 1


def main() -> int:
    taken = duplicates(DOCS)
    for number, names in taken.items():
        print(
            f"::error::docs/{number} est pris par plusieurs documents ({', '.join(names)}). "
            f"Le dernier arrivé prend le prochain numéro libre : docs/{next_number(DOCS)}-<sujet>.md."
        )
    return 1 if taken else 0


if __name__ == "__main__":
    sys.exit(main())
