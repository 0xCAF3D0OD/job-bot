# 120 — Le code hors de la notification, les copies d'alertes limitées (version 0.90.0)

> Statut : **à valider**.
> Origine : les deux points restés ouverts du cadrage 113 (§3 et §4, « Écarts ») : ta réponse portait sur ta boîte e-mail, ces deux points n'y touchaient pas. Ta demande du 2026-10-21 : « fais le cadrage pour le point 2 ».

## Le constat

### 1. Le code part dans la notification du téléphone

Quand un site envoie un code de vérification à un invité, jobA1 le montre dans la page Alertes, dans la cloche, **et l'envoie sur son téléphone** : « jobup : 482 913 » (docs/112).

| Où passe le code | Qui peut le lire | Combien de temps |
|---|---|---|
| La page Alertes, la cloche | l'invité, dans son compte | 30 minutes, puis « Code expiré » |
| **La notification du téléphone** | **ntfy.sh**, un service tiers gratuit qui relaie le message, et quiconque connaît le sujet ntfy de l'invité (une suite de 24 caractères tirée au hasard, `jobbot-…`) | ntfy.sh garde les messages quelques heures (12 h par défaut) |

Avec ce code, on entre dans le compte jobup de l'invité. C'est le seul endroit où le code sort de la Suisse et de jobA1.

### 2. Les copies des e-mails d'alerte sont gardées sans limite

jobA1 garde une copie de chaque e-mail d'alerte d'un invité, telle quelle. Les codes et les messages des sites ont déjà une limite (30 minutes, 30 jours) ; **les alertes, aucune**.

- **À quoi elles servent** : relire une alerte quand un analyseur est corrigé ou ajouté (`jobbot reparse`), et les remettre à l'invité dans l'export de ses données (Réglages › Compte).
- **Ce qu'elles contiennent en plus des offres** : le nom et l'adresse de l'invité, ses mots de recherche, parfois des « suggestions basées sur les offres consultées » (ce qu'il a regardé sur jobup), et les **liens de désinscription** des sites, qui permettent de gérer ses alertes sans mot de passe.
- **Ce qui ne dépend pas d'elles** : les offres, leur note, le journal (« Alertes reçues »), les candidatures et les preuves ORP sont gardés à part.

## La proposition

### 1. La notification sans le code

- La notification dit **« Code jobup reçu »** ; la toucher ouvre la page Alertes, où le code s'affiche en tête (docs/112, 0.84.2).
- La cloche et la page Alertes gardent le code, 30 minutes, comme aujourd'hui.
- Une étape de plus pour l'invité (ouvrir jobA1) ; en échange, le code ne passe plus par un service tiers.
- **Ton compte** : pareil, par cohérence (tes codes ne passent plus non plus par ntfy.sh).

### 2. Les copies d'alertes des invités gardées 90 jours

- **Au bout de 90 jours**, la copie brute de l'e-mail est effacée par la tâche qui efface déjà les codes et les messages des sites (toutes les 15 minutes). Les offres, le journal, les candidatures et les preuves ORP restent.
- **Ce qu'on perd** : une alerte de plus de 90 jours ne peut plus être relue par un nouvel analyseur (un analyseur se corrige en général dans les jours qui suivent un changement de format), et l'export ne contient plus les e-mails de plus de 90 jours.
- **Tes alertes à toi** : rien ne change (ta boîte, tes données), sauf si tu préfères la même règle pour tous (question 3).
- **Le dire** : « Données personnelles » passe de « les e-mails d'alerte reçus pour toi, tels quels » à « … gardés 90 jours ».

## Garde-fous

- L'effacement ne touche que la copie brute d'une alerte **déjà analysée** : une alerte en attente de l'IA (plafond, clé absente) est gardée jusqu'à sa lecture.
- La relecture (`jobbot reparse`) compte déjà les copies manquantes sans s'arrêter : rien à changer de son côté.
- Pas dans la démo (rien n'y est effacé).

## Les questions

1. **La notification sans le code** (« Code jobup reçu », un toucher ouvre la page Alertes) : d'accord ?
2. **90 jours** pour les copies d'alertes des invités : d'accord, ou une autre durée (30 jours suffiraient pour relire après un changement de format) ?
3. **Tes alertes à toi** : sans limite comme aujourd'hui, ou la même règle que les invités ?
4. **Une version** : les deux points ensemble en 0.90.0 ?
