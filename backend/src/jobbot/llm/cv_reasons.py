"""La ligne « Pourquoi » de chaque changement du CV adapté (§32 et §37 du 16.11.2026).

L'IA (prompt cv-v2) donne une raison par changement : profil réécrit, bloc déplacé, bloc retiré.
Une raison ne cite QUE des mots de l'annonce, dans la langue de l'annonce, et l'IA les donne à part
dans `words` (Kevin, 16.11 : le surlignage ne dépend pas des guillemets ; une citation entre
guillemets compte aussi) ; pour un retrait, elle peut aussi donner la contrainte de place « pour
tenir sur une page ». Ici, le serveur vérifie chaque mot ou citation dans le texte de l'offre, sans
accents ni majuscules, par mots ou expressions entiers (« Go » ne valide pas « Google »). Une
raison qui cite un mot absent, qui ne cite rien, ou qui est vide est écartée : l'interface
n'affiche alors pas de ligne « Pourquoi ».

Un changement demandé par l'utilisateur (« Demander une modification du CV », ou ses retouches)
n'a pas de raison de l'IA : il est gardé dans `user_requests` (de quoi le réappliquer) et l'API le
renvoie avec `origin: "user"` tant que la version le contient encore.
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


def check(text: str, offer: str, *, removed: bool, words: tuple[str, ...] = ()) -> Reason | None:
    """La raison si elle est valable, sinon None. `offer` est le texte de l'offre passé par `fold`.
    `words` : les mots de l'annonce que l'IA donne à part (Kevin, 16.11 : le surlignage ne dépend
    pas des guillemets) ; les citations entre guillemets du texte s'y ajoutent. Le champ `target`
    est rempli par l'appelant."""
    text = " ".join(text.split())
    if not text or len(text) > REASON_MAX:
        return None
    quoted = (next(g for g in m.groups() if g) for m in QUOTED.finditer(text))
    quotes = tuple(" ".join(q.split()) for q in (*words, *quoted) if q.strip())
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
    raw: list[tuple[str, str, tuple[str, ...]]],
    offer_text: str,
    *,
    summary: str,
    kept: list[int],
    eligible: set[int],
) -> list[Reason]:
    """Les raisons valables, une par cible au plus : le profil s'il est écrit, un bloc gardé ou
    retiré parmi les blocs de CV. `raw` : les triplets (cible, raison, mots de l'annonce) rendus
    par l'IA."""
    offer = fold(offer_text)
    seen: set[Target] = set()
    reasons = []
    for value, text, words in raw:
        target = target_of(value)
        if target is None or target in seen:
            continue
        if target == SUMMARY and not summary.strip():
            continue
        if target != SUMMARY and target not in eligible:
            continue
        reason = check(text, offer, removed=target != SUMMARY and target not in kept, words=words)
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


def _after(ids: list[int], target: int) -> int | None:
    """Le bloc qui précède `target` dans la liste (None s'il est en tête)."""
    at = ids.index(target)
    return ids[at - 1] if at else None


def requests_from(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    """Les demandes de l'utilisateur qui font passer de `before` à `after`, une par cible :
    profil réécrit (avec son texte), bloc retiré, ajouté ou déplacé (avec le bloc qui le précède),
    de quoi savoir si une version les contient encore, et les réappliquer."""
    new = [int(i) for i in after.get("chunk_ids", [])]
    old = [int(i) for i in before.get("chunk_ids", [])]
    requests: list[dict[str, Any]] = []
    for target in changed_targets(before, after):
        if target == SUMMARY:
            requests.append(
                {"target": SUMMARY, "kind": "summary", "text": after["summary"].strip()}
            )
        elif target not in new:
            requests.append({"target": target, "kind": "removed"})
        else:
            kind = "moved" if target in old else "added"
            requests.append({"target": target, "kind": kind, "after": _after(new, target)})
    return requests


def applied(request: dict[str, Any], content: dict[str, Any]) -> bool:
    """La version `content` contient-elle encore cette demande ?"""
    ids = [int(i) for i in content.get("chunk_ids", [])]
    target = request["target"]
    match request["kind"]:
        case "summary":
            return bool((content.get("summary") or "").strip() == request.get("text"))
        case "removed":
            return target not in ids
        case "added":
            return target in ids
        case _:
            return target in ids and _after(ids, target) == request.get("after")


def merge_requests(
    previous: list[dict[str, Any]], new: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """La liste des demandes, la plus récente par cible."""
    targets = {r["target"] for r in new}
    return [r for r in previous if r["target"] not in targets] + new


def carry_over(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Une version changée par l'utilisateur (retouche ou « Demander une modification du CV »)
    ajoute ce qu'il a changé à ses demandes (`user_requests`) et garde les raisons de l'IA des
    parties qu'il n'a pas touchées."""
    changed = changed_targets(before, after)
    requests = merge_requests(before.get("user_requests", []), requests_from(before, after))
    reasons = [r for r in before.get("reasons", []) if r.get("target") not in changed]
    return {
        **({"reasons": reasons} if reasons else {}),
        **({"user_requests": requests} if requests else {}),
    }


def keep_requests(previous: dict[str, Any] | None) -> dict[str, Any]:
    """Une nouvelle version sans consigne garde la liste des demandes de la version précédente,
    même celles qu'elle ne reprend pas : l'interface propose de les réappliquer."""
    requests = (previous or {}).get("user_requests", [])
    return {"user_requests": requests} if requests else {}
