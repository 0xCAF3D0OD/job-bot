# 132 — La lecture : phrases courtes, interrupteurs, de l'air (version 1.4.1)

> Statut : **demandé directement** le 2026-10-22 (« est-ce que tu peux simplifier des phrases longues ? les cases à cocher, je ne suis pas fan, je préfère les interrupteurs ; attention au texte trop proche ; regarde si ça respecte les règles »). Pas de cadrage à part : ce document dit ce qui a été fait.

## Ce qui a été fait

1. **Les phrases longues** : un inventaire des textes de 16 mots ou plus (66). Ceux de l'application sont réécrits en une idée par phrase (« Une annonce vue ailleurs : jobA1 la lit, tu la relis, elle rejoint tes offres. » au lieu de 35 mots ; « 12 caractères au moins. Le mot de passe n'est jamais enregistré en clair. » au lieu de 32). Dans les pages légales, seules les plus longues (28 mots et plus) sont coupées, sans changer ce qu'elles disent. La page de présentation garde ses phrases.
2. **Les interrupteurs** : toutes les cases à cocher prennent la forme glissante des sites suivis, bleue quand elle est activée (critères, questions au conseiller, conditions, formulaires…), par une seule règle de style. Les jours de recherche gardent leurs pastilles.
3. **Le texte collé** : un nouveau contrôle dans l'audit des règles mesure l'écart entre les lettres de deux textes voisins (moins de 3,5 px) ou sous un champ (moins de 6 px), seulement ce qui est visible et au premier plan. Il a trouvé : l'aide sous le champ des questions au conseiller, l'entreprise sous le titre de la fiche d'une offre, « Il te manque : … » sous l'entreprise dans une carte d'offre. Les trois sont écartés.
4. **Les aides à 16 mots au plus** (au lieu de 20) dans l'audit ; le récapitulatif des données du compte devient une liste (Offres, Candidatures…), la ligne de Plus est raccourcie.

## Les règles

`docs/interface.md` : Titres et textes 8 (des phrases courtes), Les contrôles 3 bis (une case à cocher est un interrupteur) et 6 (l'audit : 16 mots, texte collé).

## Vérifié

- Tests de l'interface : 449, lint, vue-tsc.
- Les trois audits à zéro sur la démo et sur un compte neuf, avec le nouveau contrôle.
- Captures : Profil › Critères (les interrupteurs), Réglages › Rythme (les pastilles des jours intactes), la fiche d'une offre, les données du compte.
