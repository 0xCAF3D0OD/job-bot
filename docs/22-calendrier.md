# 22 — Suivi et preuves ORP en un seul onglet, en calendrier (version 0.15.0)

> Statut : **à valider**.
> Retours d'usage du 2026-10-07 : « Suivi et Preuves ORP sont quasiment identiques, il faudrait un seul onglet ; voir le suivi sous forme de calendrier, cliquer sur le jour de postulation et voir la carte de la candidature ».

## 1. Un seul onglet

La rubrique Candidatures passe à **trois onglets** : **Offres** · **Suivi** · **Alertes**. L'onglet **Suivi** regroupe l'ancien Suivi et les Preuves ORP ; les anciennes adresses (`/candidatures/preuves`, liens des rappels ORP et de la cloche) y mènent.

## 2. En haut : le mois et les preuves ORP

Une barre, de gauche à droite :

- le **mois** (← →) ;
- le compteur **« 14 / 20 candidatures »** avec sa barre ;
- l'**état des preuves** (« en cours », « à remettre avant le 5 novembre », « remises le 3 novembre ») ;
- **une seule action ORP** selon le moment : « Compléter 2 ligne(s) », puis « Marquer comme remis » ;
- « Ajouter une candidature ».

« Plus d'options » garde le PDF, le CSV, le journal joint et le tableau du formulaire ORP (vue « Formulaire »).

## 3. Le calendrier du mois

Une grille lundi → dimanche, une case par jour :

- **une pastille par candidature envoyée** ce jour-là, à la couleur de son statut (en attente, relancée, entretien, refus, engagement, sans réponse) ; au-delà de trois, « +2 » ;
- un **petit repère « entretien »** le jour d'un entretien prévu ;
- un **repère « à relancer »** le jour où une candidature en attente atteint 10 jours ;
- **aujourd'hui** encadré ; les jours sans candidature restent simples ;
- un **point rouge** sur une candidature à compléter pour l'ORP (adresse manquante).

**Cliquer sur un jour** ouvre, à droite (ou en dessous sur téléphone), **les cartes de ce jour**.

## 4. La carte d'une candidature

- **Entreprise, poste, lieu**, mode (électronique…), « assignée par l'ORP » le cas échéant ;
- **statut** modifiable directement (liste), avec la date d'entretien ;
- **ce qui manque pour l'ORP** (« adresse de l'entreprise ») et un bouton « Compléter » ;
- liens : **lettre** et **CV** (Word), **lien de candidature**, l'**offre** d'origine ;
- **« Copier pour Job-Room »** : les champs dans l'ordre de leur formulaire, comme aujourd'hui, mais pour cette seule candidature ;
- « Modifier » et « Supprimer » dans un menu « ⋯ ».

Sans jour choisi, le panneau montre **les candidatures à relancer** du mois (ou rien à faire).

## 5. Vue liste, en option

Un bouton **Calendrier / Liste** : la liste actuelle (tableau, « Tous les mois ») reste disponible ; le choix est retenu par le navigateur.

## 6. Livraison

Une seule PR (**0.15.0**), sans migration : l'API fournit déjà tout (candidatures du mois, lignes ORP, champs Job-Room).

## Points à valider

1. **Trois onglets** : Offres · Suivi · Alertes ; Preuves ORP fondu dans Suivi (§1).
2. **Barre du mois** avec compteur, état des preuves et une action ORP à la fois (§2).
3. **Calendrier** : pastilles colorées par statut, repères entretien et relance, point rouge si à compléter (§3).
4. **Carte** au clic sur un jour, avec statut modifiable et « Copier pour Job-Room » (§4).
5. **Vue liste** en option (§5).
