"""Quels audits d'écran une PR doit passer : téléphone, ordinateur, les deux ou aucun (décision de Kevin du 14.11.2026).

Le téléphone (jusqu'à 820 px, la limite de usePhone.ts et des styles) et l'ordinateur (dès 821 px) placent les
éléments très différemment : une PR qui ne touche que l'un ne doit pas attendre l'audit de l'autre, et une PR de
documentation n'attend aucun des deux. Chaque fichier changé reçoit un ou deux formats :

- aucun : la documentation (docs/, *.md, changelog.d/), l'extension, les tests, les autres workflows ;
- téléphone ou ordinateur seul : un composant qui ne s'affiche que dans ce format (liste ci-dessous, à tenir à jour),
  ou, dans un .css ou le <style> d'un .vue, une ligne placée dans un @media qui ne vise que ce format
  (par exemple « @media (max-width: 820px) » pour le téléphone, « @media (min-width: 821px) » pour l'ordinateur) ;
- les deux : tout le reste, dont ce qui est partagé (stores, services, API, serveur, routes, gabarits des .vue,
  styles hors @media et variables de :root). Un fichier inconnu compte pour les deux : dans le doute, on vérifie.

Une ligne retirée est lue dans l'ancienne version du fichier, une ligne ajoutée dans la nouvelle.

    python3 scripts/ci_formats.py BASE [HEAD]

écrit « telephone=true|false » et « ordinateur=true|false » dans $GITHUB_OUTPUT (ou à l'écran), et la raison de
chaque fichier dans $GITHUB_STEP_SUMMARY (ou à l'écran).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from fnmatch import fnmatch

PHONE = "telephone"
DESK = "ordinateur"
BOTH = frozenset({PHONE, DESK})
NONE: frozenset[str] = frozenset()
PHONE_MAX = 820  # usePhone.ts : PHONE_QUERY = "(max-width: 820px)"

# Aucun audit d'écran : rien de ce qui suit n'arrive dans la démo.
NO_SCREEN = [
    "docs/*",
    "*.md",
    "changelog.d/*",
    "LICENSE",
    "scripts/*",  # historique, numéros de docs/ (ce fichier compris : il a ses propres tests)
    "extension/*",
    "backend/tests/*",
    "frontend/src/*.test.ts",
    "frontend/vitest.total.ts",
    "frontend/scripts/test_*.py",  # testés par audit-regles.yml
    ".github/*",
]
# Exceptions à la liste précédente : elles changent ce que l'audit vérifie.
SCREEN_ANYWAY = [
    "docs/mobile/outils/*",  # audit-grille.js, lancé par frontend/scripts/grille.py
    ".github/workflows/audit-telephone.yml",
]
# Un seul format. Vérifié dans le code le 14.11.2026 ; un composant affiché dans les deux formats n'a rien à faire
# ici, même si son nom dit le contraire (ProfileDesktop et AlertsPhoneList servent aussi au téléphone).
ONLY = {
    "frontend/src/components/HomePhone.vue": PHONE,  # TodayView : v-if="phone"
    "frontend/src/components/BottomNav.vue": PHONE,  # .tab-bar en display: none au-delà de 820 px
    "frontend/src/components/RendezVousPhone.vue": PHONE,  # OrpMeetingView : v-if="compact" (téléphone)
    "frontend/src/components/RendezVousDesktop.vue": DESK,  # OrpMeetingView : wideView, dès 1024 px
    "frontend/src/components/OfferFilterSheet.vue": PHONE,  # OffersView : v-if="phone"
    "frontend/src/components/LayoutSheetLink.vue": PHONE,  # PreparationView et CvPanel : v-if="phone"
    "frontend/src/components/TriageMini.vue": DESK,  # TodayView, dans le bloc v-if="!phone && today"
    "frontend/src/components/TriageNone.vue": DESK,  # TodayView (même bloc) et TriageMini
    "frontend/src/components/bilan/BilanResultsWide.vue": DESK,  # InsightsView : v-if="!phone"
    "frontend/scripts/telephone.py": PHONE,  # 320, 360 et 390 px seulement
    "frontend/scripts/panneaux.py": DESK,  # 1440 px seulement
}

WIDTH = re.compile(r"\(\s*(min|max)-width\s*:\s*(\d+(?:\.\d+)?)px\s*\)")


def media_formats(prelude: str) -> frozenset[str]:
    """Les formats que vise un @media, d'après ses largeurs ; sans largeur (couleurs, mouvements), les deux."""
    query = prelude.strip()[len("@media") :].strip().lower()
    if re.fullmatch(r"(only\s+)?print", query):
        return NONE
    found: set[str] = set()
    for part in query.split(","):
        if re.search(r"\bnot\b", part):
            return BOTH  # une négation : on ne cherche pas à la résoudre
        low, high = 0.0, float("inf")
        for kind, value in WIDTH.findall(part):
            if kind == "min":
                low = max(low, float(value))
            else:
                high = min(high, float(value))
        if low <= PHONE_MAX and low <= high:
            found.add(PHONE)
        if high > PHONE_MAX and low <= high:
            found.add(DESK)
    return frozenset(found)


def line_formats(css: str, first_line: int = 1) -> dict[int, frozenset[str]]:
    """Pour chaque ligne du CSS, les formats où elle s'applique : ceux de ses @media, imbriqués compris.

    Le texte d'un sélecteur ou d'une déclaration prend les formats du bloc où il s'applique : la ligne
    « @media (max-width: 820px) { » et l'accolade qui ferme ce bloc comptent pour le téléphone seul. Une ligne vide
    ou de commentaire ne change rien à l'écran : aucun format.
    """
    marks: dict[int, set[str]] = {}
    lines = {first_line}
    stack: list[frozenset[str]] = []  # par accolade ouverte : les formats qu'elle laisse passer
    current = BOTH
    prelude = ""
    pending: set[int] = set()  # les lignes du sélecteur ou de la déclaration en cours
    line = first_line

    def mark(rows: set[int], formats: frozenset[str]) -> None:
        for k in rows:
            marks.setdefault(k, set()).update(formats)

    i, n = 0, len(css)
    while i < n:
        char = css[i]
        if css.startswith("/*", i):
            end = css.find("*/", i + 2)
            end = n if end < 0 else end + 2
            for _ in range(css.count("\n", i, end)):
                line += 1
                lines.add(line)
            i = end
            continue
        if char in "\"'":
            end = i + 1
            while end < n and css[end] != char and css[end] != "\n":
                end += 2 if css[end] == "\\" else 1
            prelude += css[i : end + 1]
            pending.add(line)
            i = end + 1
            continue
        if char == "\n":
            line += 1
            lines.add(line)
            prelude += " "
        elif char == "{":
            text = prelude.strip()
            current = current & (media_formats(text) if text.startswith("@media") else BOTH)
            stack.append(current)
            mark(pending | {line}, current)
            prelude, pending = "", set()
        elif char == "}":
            mark(pending | {line}, current)
            if stack:
                stack.pop()
            current = stack[-1] if stack else BOTH
            prelude, pending = "", set()
        elif char == ";":
            mark(pending | {line}, current)
            prelude, pending = "", set()
        elif not char.isspace():
            prelude += char
            pending.add(line)
        else:
            prelude += char
        i += 1
    mark(pending, current)
    return {k: frozenset(marks[k]) if k in marks else NONE for k in lines}


def vue_formats(source: str) -> dict[int, frozenset[str]]:
    """Dans un .vue : les lignes du <style> selon leurs @media, tout le reste (gabarit, script) pour les deux."""
    lines = source.split("\n")
    result = {k: BOTH for k in range(1, len(lines) + 1)}
    start = None
    for number, text in enumerate(lines, 1):
        if start is None and re.match(r"\s*<style\b", text):
            start = number
        elif start is not None and re.match(r"\s*</style>", text):
            css = "\n".join(lines[start : number - 1])
            for k, formats in line_formats(css, start + 1).items():
                if start < k < number:
                    result[k] = formats
            start = None
    return result


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def show(rev: str, path: str) -> str:
    try:
        return git("show", f"{rev}:{path}")
    except subprocess.CalledProcessError:
        return ""


HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def changed_lines(base: str, head: str, old: str, new: str) -> tuple[list[int], list[int]]:
    """Les lignes retirées (numéros de l'ancienne version) et ajoutées (numéros de la nouvelle)."""
    removed: list[int] = []
    added: list[int] = []
    diff = git("diff", "-U0", "--no-color", "-M", base, head, "--", *{old, new})
    for row in diff.splitlines():
        match = HUNK.match(row)
        if match:
            o, oc, a, ac = match.groups()
            removed += range(int(o), int(o) + int(1 if oc is None else oc))
            added += range(int(a), int(a) + int(1 if ac is None else ac))
    return removed, added


def matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch(path, pattern) for pattern in patterns)


def off_screen(path: str) -> bool:
    return matches(path, NO_SCREEN) and not matches(path, SCREEN_ANYWAY)


def file_formats(path: str, old_path: str, base: str, head: str) -> tuple[frozenset[str], str]:
    """Les formats d'un fichier changé, et pourquoi."""
    if all(off_screen(p) for p in (path, old_path)):
        return NONE, "n'arrive pas à l'écran"
    if path in ONLY and old_path in (path, *ONLY):
        return frozenset({ONLY[path]}), "ne s'affiche que dans ce format"
    if path.startswith("frontend/src/") and path.endswith((".css", ".vue")) and old_path == path:
        reader = line_formats if path.endswith(".css") else vue_formats
        before, after = reader(show(base, path)), reader(show(head, path))
        removed, added = changed_lines(base, head, old_path, path)
        found: set[str] = set()
        for k in removed:
            found |= before.get(k, BOTH)
        for k in added:
            found |= after.get(k, BOTH)
        if not removed and not added:
            return NONE, "aucune ligne changée"
        return frozenset(found), "d'après les @media des lignes changées"
    return BOTH, "partagé"


def label(formats: frozenset[str]) -> str:
    return {NONE: "aucun", BOTH: "les deux"}.get(formats) or ("téléphone" if PHONE in formats else "ordinateur")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    base, head = argv[1], argv[2] if len(argv) > 2 else "HEAD"
    total: set[str] = set()
    rows = []
    for row in git("diff", "--name-status", "-M", base, head).splitlines():
        status, *paths = row.split("\t")
        old_path, path = paths[0], paths[-1]
        if status.startswith("D"):
            # Un fichier effacé : ce qu'il faisait à l'écran disparaît dans son format.
            formats = NONE if off_screen(path) else frozenset({ONLY[path]}) if path in ONLY else BOTH
            why = "effacé"
        else:
            formats, why = file_formats(path, old_path, base, head)
        total |= formats
        rows.append(f"| `{path}` | {label(formats)} | {why} |")
    outputs = f"{PHONE}={'true' if PHONE in total else 'false'}\n{DESK}={'true' if DESK in total else 'false'}\n"
    summary = (
        "## Audits d'écran ciblés\n\n"
        f"Téléphone : **{'oui' if PHONE in total else 'non'}** · Ordinateur : **{'oui' if DESK in total else 'non'}**\n\n"
        "| Fichier | Format | Raison |\n|---|---|---|\n" + "\n".join(rows) + "\n"
    )
    for name, text in (("GITHUB_OUTPUT", outputs), ("GITHUB_STEP_SUMMARY", summary)):
        target = os.environ.get(name)
        if target:
            with open(target, "a", encoding="utf-8") as handle:
                handle.write(text)
    print(summary)
    print(outputs, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
