# 42 — Ce qui marche dans ta recherche (version 0.34.0)

> Statut : **validé** le 2026-10-15. livré.
> La plateforme garde tout : d'où vient chaque offre, sa note, la lettre et le CV, les relances, les contacts, les réponses. Elle ne dit jamais **ce qui donne des réponses**. Et au rendez-vous ORP, tu résumes ton mois de tête.

## 1. Un onglet « Bilan » dans Candidatures

À côté de **Offres · Suivi · Alertes**. Une seule page, compacte, de la même largeur que les autres ; sur téléphone, une colonne.

**En haut, le parcours** de la période choisie (**3 derniers mois** par défaut ; ou le mois, ou tout) :

```
Offres reçues 412  →  retenues 96  →  candidatures 31  →  réponses 11  →  entretiens 4  →  engagement 0
```

- Une ligne de chiffres reliés, pas un graphique. Chaque chiffre mène à la liste correspondante (Offres filtrées, Suivi).
- **Réponse** = tout sauf « En attente », « Relancée » et « Sans réponse » : un refus est une réponse.
- **Délai de réponse** habituel, sous la ligne : « réponse en 9 jours d'habitude (de 2 à 21) ».

## 2. Ce qui donne des réponses

Quatre comparaisons, une ligne chacune, avec le **nombre** plutôt qu'un pourcentage :

| Comparaison | Exemple |
|---|---|
| **D'où vient l'offre** (jobup, Indeed, jobs.ch, LinkedIn…, spontanée) | jobup 5 réponses sur 12 · Indeed 1 sur 9 · spontanée 2 sur 3 |
| **Note de l'IA** (80 et plus, 60 à 79, moins de 60) | 80+ : 6 sur 11 · 60–79 : 3 sur 14 |
| **Avec un contact dans l'entreprise** ou sans (docs/31) | avec : 3 sur 4 · sans : 8 sur 27 |
| **Relancée** ou non (docs/38) | relancées : 2 réponses sur 7 après la relance |

- **Peu de données, pas de conclusion** : sous **5 candidatures** dans un groupe, le chiffre est grisé avec « trop peu pour conclure ». Aucune phrase du type « postule sur jobup » tant que les nombres ne le permettent pas.
- Au-dessus du seuil, **une seule phrase** en tête, si un écart est net (au moins le double) : « Tes candidatures avec un contact obtiennent plus souvent une réponse. » Sinon, rien.
- Pas d'IA, aucun coût : de simples comptes sur tes données.

## 3. Pour ton rendez-vous ORP

Un bouton **« Résumé pour l'ORP »** sous le bilan d'un mois : quelques lignes prêtes à copier ou à lire au conseiller.

> Octobre 2026 : 14 candidatures (objectif 12), dont 2 spontanées. 5 réponses, 2 entretiens (Exemple SA, Autre SA), pas encore d'engagement. Sources : jobup 8, LinkedIn 4, spontanées 2. Formation suivie : AWS Solutions Architect (terminée).

- Faits seulement, tirés de tes données : nombre (et objectif), réponses, entretiens nommés, sources, formations du mois (docs/37).
- **Rien n'est envoyé** : un bouton « Copier ».

## 4. Ce que ça ne fait pas

- Pas de prédiction ni de « chance d'être pris ».
- Pas de comparaison avec d'autres personnes : seulement tes données, sur ta plateforme.
- Les offres écartées par tes prérequis ne sont pas jugées : elles comptent seulement dans « reçues ».

## 5. Sans changement de base

Tout se calcule à partir de ce qui existe (offres et leurs sites, notes, candidatures, relances, contacts, formations). Une route `GET /api/insights?from=…&to=…` ; aucune migration.

## 6. Livraison

Une PR (**0.34.0**) : onglet Bilan (§1, §2) et résumé ORP (§3). Ordinateur et téléphone.

## Points à valider

1. **Onglet « Bilan »** dans Candidatures, parcours de la période en une ligne de chiffres (§1).
2. **Quatre comparaisons** (source, note, contact, relance), en nombres, avec le seuil de 5 et une phrase seulement si l'écart est net (§2).
3. **Résumé pour l'ORP** à copier, sans IA (§3).
4. **Une PR** (§6).

## Écarts avec la livraison

- **Période** : « 3 derniers mois » = le mois en cours et les deux précédents ; « Un mois » se choisit avec ← →, comme dans le Suivi, et le mois suit d'un onglet à l'autre. Les offres « reçues » sont comptées par date d'arrivée, les candidatures par date d'envoi ; les spontanées ne sont pas des offres reçues mais comptent comme candidatures.
- **Retenues** : offres qui passent tes prérequis.
- **Entretiens** : candidatures avec une date d'entretien, ou au statut « Entretien » ou « Engagement ».
- **Source** : le premier site où l'offre a été vue ; « spontanée » et « ajoutée à la main » à part. Les spontanées et celles ajoutées à la main n'entrent pas dans « Note de l'IA ».
- **Relance** : « jamais relancées » ne compte que les candidatures envoyées depuis au moins 10 jours (avant, la relance n'est pas encore proposée).
- **Phrase de tête** : au moins le double de réponses en proportion, 5 candidatures de chaque côté et au moins 2 réponses du meilleur côté ; si plusieurs comparaisons s'y prêtent, la plus nette.
- **Date de relance gardée** : une candidature relancée qui reçoit une réponse (refus, entretien) garde sa date de relance ; elle n'est plus effacée qu'au retour en « En attente » (la PR 0.33.1-a l'effaçait dès qu'on quittait « Relancée », le bilan l'aurait perdue).
- **Résumé ORP** : « aucun entretien » ou « aucune réponse pour l'instant » quand c'est zéro ; les formations en cours sont citées avec celles terminées dans le mois.
- **Vérifié** dans le navigateur, ordinateur et téléphone (parcours en 3 × 2 sur téléphone, sans débordement), avec des données de démonstration supprimées ensuite.
