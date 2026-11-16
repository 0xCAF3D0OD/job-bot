"""La ligne « Pourquoi » de chaque changement du CV adapté (§32 et §37 du 16.11.2026).

L'IA (prompt cv-v2) donne une raison par changement : profil réécrit, bloc déplacé, bloc retiré.
Une raison ne cite QUE des mots de l'annonce, entre guillemets, dans la langue de l'annonce ; pour
un retrait, elle peut aussi donner la contrainte de place « pour tenir sur une page ». Ici, le
serveur vérifie chaque citation dans le texte de l'offre, sans accents ni majuscules, par mots ou
expressions entiers (« Go » ne valide pas « Google »). Une raison qui cite un mot absent, qui ne
cite rien, ou qui est vide est écartée : l'interface n'affiche alors pas de ligne « Pourquoi ».

Un changement demandé par l'utilisateur (« Demander une modification du CV », ou ses retouches)
n'a pas de raison de l'IA : il est marqué `user_targets` et l'API le renvoie avec `origin: "user"`.
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Literal

SUMMARY: Literal["summary"] = "summary"
Target = int | Literal["summary"]
PLACE = "pour tenir sur une page"
REASON_MAX = 220
QUOTE_MAX = 80
# Les citations : « … », “ … ”, " … ".
QUOTED = re.compile(r"«\s*([^«»]+?)\s*»|“\s*([^“”]+?)\s*”|\"\s*([^\"]+?)\s*\"")


def fold(text: str) -> str:
    """Sans accents ni majuscules, apostrophes et espaces unifiées : pour comparer seulement."""
    decomposed = unicodedata.normalize("NFKD", text.replace("\u2019", "'"))
    plain = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(plain.casefold().split())


def cites(offer: str, quote: str) -> bool:
    """`quote` figure dans `offer` (déjà passé par `fold`) comme mot ou expression entière."""
    needle = fold(quote)
    if not needle:
        return False
    pattern = r"(?<!\w)" + r"\s+".join(re.escape(w) for w in needle.split()) + r"(?!\w)"
    return re.search(pattern, offer) is not None


@dataclass(frozen=True)
class Reason:
    target: Target
    text: str
    quotes: tuple[str, ...]

    def as_json(self) -> dict[str, Any]:
        return {"target": self.target, "text": self.text, "quotes": list(self.quotes)}


def check(text: str, offer: str, *, removed: bool) -> Reason | None:
    """La raison si elle est valable, sinon None. `offer` est le texte de l'offre passé par `fold`.
    Le champ `target` est rempli par l'appelant."""
    text = " ".join(text.split())
    if not text or len(text) > REASON_MAX:
        return None
    quotes = tuple(next(g for g in m.groups() if g) for m in QUOTED.finditer(text))
    if any(len(q) > QUOTE_MAX or not cites(offer, q) for q in quotes):
        return None
    if not quotes and not (removed and PLACE in fold(text)):
        return None
    return Reason(target=SUMMARY, text=text, quotes=tuple(dict.fromkeys(quotes)))


def target_of(value: str) -> Target | None:
    value = value.strip().lower()
    if value in ("profil", "profile", SUMMARY):
        return SUMMARY
    return int(value) if value.isdigit() else None


def validate(
    raw: list[tuple[str, str]],
    offer_text: str,
    *,
    summary: str,
    kept: list[int],
    eligible: set[int],
) -> list[Reason]:
    """Les raisons valables, une par cible au plus : le profil s'il est écrit, un bloc gardé ou
    retiré parmi les blocs de CV. `raw` : les paires (cible, raison) rendues par l'IA."""
    offer = fold(offer_text)
    seen: set[Target] = set()
    reasons = []
    for value, text in raw:
        target = target_of(value)
        if target is None or target in seen:
            continue
        if target == SUMMARY and not summary.strip():
            continue
        if target != SUMMARY and target not in eligible:
            continue
        reason = check(text, offer, removed=target != SUMMARY and target not in kept)
        if reason is None:
            continue
        seen.add(target)
        reasons.append(Reason(target=target, text=reason.text, quotes=reason.quotes))
    return reasons


def changed_targets(before: dict[str, Any], after: dict[str, Any]) -> list[Target]:
    """Ce qui diffère entre deux versions : le profil, les blocs retirés, ajoutés ou déplacés."""
    changed: list[Target] = []
    if (before.get("summary") or "").strip() != (after.get("summary") or "").strip():
        changed.append(SUMMARY)
    old = [int(i) for i in before.get("chunk_ids", [])]
    new = [int(i) for i in after.get("chunk_ids", [])]
    changed += [i for i in old if i not in new]
    changed += [i for i in new if i not in old]
    common_new = [i for i in new if i in old]
    common_old = [i for i in old if i in new]
    changed += [i for n, i in enumerate(common_new) if common_old[n] != i]
    return list(dict.fromkeys(changed))


def carry_over(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Une version changée par l'utilisateur garde les raisons de l'IA des parties qu'il n'a pas
    touchées ; ce qu'il a changé passe dans `user_targets`, sans raison."""
    changed = changed_targets(before, after)
    user = list(dict.fromkeys([*before.get("user_targets", []), *changed]))
    reasons = [r for r in before.get("reasons", []) if r.get("target") not in changed]
    return {
        **({"reasons": reasons} if reasons else {}),
        **({"user_targets": user} if user else {}),
    }
