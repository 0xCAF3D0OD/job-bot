# 24 — Assistant : discuter avec la plateforme (version 0.17.0)

> Statut : **à valider**.
> Retours d'usage du 2026-10-07 : un petit chatbot qui comprend le contexte de la plateforme, pour discuter et obtenir des informations cohérentes avec ses données.

## 1. Ce qu'on voit

- Un bouton rond **« Assistant »** en bas à droite, sur toutes les pages (après connexion).
- Il ouvre un **panneau de discussion** sur le côté (plein écran sur téléphone), qui ne cache pas la page.
- En haut du panneau, **trois suggestions** selon la page, par exemple :
  - Offres : « Lesquelles postuler en priorité ? », « Explique-moi la note de cette offre » ;
  - Suivi : « Où en suis-je ce mois pour l'ORP ? », « Qui relancer cette semaine ? » ;
  - Aujourd'hui : « Que faire aujourd'hui ? ».
- Les réponses contiennent des **liens vers les pages** (« ouvrir l'offre », « voir le Suivi d'octobre »).
- « **Nouvelle discussion** » et « **Effacer** » en haut du panneau.

## 2. Ce qu'il sait

### 2.1 La plateforme

Un **guide** rédigé une fois (dans le dépôt) : à quoi sert chaque page, comment marchent les alertes, la note, la préparation, le suivi, les preuves ORP, la connexion, les profils d'essai. L'assistant répond à « où se trouve… ? » et « comment faire… ? » à partir de ce guide, pas de mémoire.

### 2.2 Tes données, à la demande

L'assistant **ne reçoit pas tout d'avance** : il demande ce dont il a besoin, par des fonctions de lecture que la plateforme exécute, par exemple :

| Fonction | Ce qu'elle rend |
|---|---|
| offres à examiner | titre, entreprise, lieu, note, résumé de l'IA (les 20 meilleures) |
| une offre | le détail, le résumé, les points forts et manques |
| candidatures | par mois : entreprise, poste, date, statut, entretien |
| preuves ORP | le mois : compteur, objectif, lignes à compléter, état de la remise |
| alertes | recherches suivies et leur état |
| retours d'entretien | enseignements (questions difficiles, à préparer) |
| profil | tes blocs de profil (expériences, compétences) |
| actualités, formations | les dernières de ton domaine, tes formations suivies |
| page en cours | la page ouverte et l'élément choisi (offre, jour, mois) |

**Jamais** : tes coordonnées (nom, adresse, téléphone, e-mail), le contenu brut de tes e-mails, tes mots de passe ou clés.

## 3. Ce qu'il fait, et ne fait pas (première version)

- **Répond et explique** : où trouver quoi, ce que veulent dire tes chiffres, quelles offres regarder d'abord, qui relancer.
- **Conseille** : recherche d'emploi, entretiens, à partir de tes données. Pour les règles de l'assurance chômage, il donne l'information générale et renvoie à ton conseiller ORP : ce n'est pas un avis officiel.
- **Rédige du texte** à copier : un e-mail de relance, de remerciement après un entretien, une réponse à une question difficile.
- **Ne modifie rien** : pas de statut changé, pas de candidature créée, pas d'e-mail envoyé. (Des actions avec ta confirmation pourront venir plus tard.)
- **Pas de recherche sur Internet** dans cette version.

## 4. Coût, confidentialité, conservation

- **Modèle** : Claude Sonnet 5, réponses affichées au fil de l'écriture. Environ **0,01 à 0,03 $ par question** selon les données consultées ; dans le plafond mensuel (`llm_calls`, `purpose = chat`). Sans clé API, le bouton n'apparaît pas.
- **Conversations** gardées sur ta plateforme **30 jours** (pour reprendre une discussion), effaçables à tout moment ; seules les 20 dernières répliques d'une discussion sont renvoyées à l'IA.
- **Profils d'essai** : l'assistant suit le profil affiché pour les actualités et les formations, comme le reste.

## 5. Base (migration 0034)

```
chat_conversations  id, title, created_at, updated_at
chat_messages       id, conversation_id, role (user|assistant), content, page?, created_at
```

## 6. Livraison en deux PR

| PR | Contenu |
|---|---|
| **0.17.0-a** | Panneau, discussion au fil de l'eau, guide de la plateforme, fonctions de lecture, conservation |
| **0.17.0-b** | Contexte de la page (élément choisi), suggestions par page, liens dans les réponses, raccourcis (« demander à l'assistant » sur une offre, une carte) |

## Points à valider

1. **Bouton et panneau** sur toutes les pages, suggestions selon la page (§1).
2. **Données lues à la demande** par des fonctions, jamais tes coordonnées ni tes e-mails (§2).
3. **Lecture seule** dans cette version : répond, conseille, rédige, ne modifie rien (§3).
4. **Sonnet 5**, environ 0,01 à 0,03 $ par question, dans le plafond (§4).
5. **Conversations gardées 30 jours**, effaçables (§4).
6. **Deux PR** (§6).
