# 88 — Une interface qui s'affiche au lieu de parler (versions 0.70.0 et 0.70.1)

> Statut : **validé** le 2026-10-19 (maquette validée le même jour).
> Origine : ta remarque du 2026-10-19 : « quelque chose que je ne retrouve pas dans des interfaces professionnelles ». Le point retenu : l'interface te parle au lieu de s'afficher.

## Le constat

- **Les titres sont des phrases** : « Les offres pour toi », « Toi et ta recherche », « Tes prérequis », « Ta semaine ».
- **Le titre ne reprend pas le menu** : on clique sur « Candidatures » et on lit « Les offres pour toi ».
- **Chaque page a un sous-titre** qui explique ce qu'elle fait.
- **Il y a 105 petits textes d'aide**, répartis dans 47 fichiers, et des prix dans les boutons (« Rédiger avec l'IA (≈ 0,02 CHF) »).

Les outils professionnels (Linear, Stripe, Notion) font l'inverse :
- **un titre** : un nom, le même que dans le menu ;
- **des étiquettes** : des noms ;
- **des boutons** : un verbe à l'infinitif ;
- **l'aide** : elle se demande, elle ne s'affiche pas en permanence.

## Les règles (ajoutées à `docs/interface.md`)

1. **Titre de page = entrée du menu**, mot pour mot. Pas de sous-titre. La connexion garde sa phrase : c'est une page de présentation.
2. **Titres de cartes, d'onglets et de sections : un nom**, sans « ton », « ta » ni « tes ».
3. **Boutons : un verbe à l'infinitif**. Par exemple « Demander un certificat intermédiaire », et non « Demande un certificat… ».
4. **Le tutoiement reste dans les phrases** : messages, erreurs, états vides. jobA1 reste ton assistant. Il ne reste que là.
5. **Un texte d'aide reste visible dans trois cas seulement** :
   - une erreur, avec quoi faire ;
   - un avertissement avant une action irréversible ;
   - ce qui part à l'IA, au moment où ça part, en une ligne.

   Le reste passe dans un **« ? »** à côté du titre de la partie (un petit volet au clic), ou disparaît.
6. **Les prix sortent des boutons**. Le prix d'une action IA est dans le « ? » de la partie et dans l'info-bulle du bouton. La dépense du mois reste dans Réglages › IA.
7. **Un état vide : une phrase**, plus l'action qui le remplit.

## 0.70.0 : les titres et les étiquettes

| Où | Avant | Après |
|---|---|---|
| Aujourd'hui | « Lundi 19 octobre » + sous-titre | « Aujourd'hui », avec la date en petit au-dessus |
| Candidatures | « Les offres pour toi », « Tes candidatures et tes preuves ORP », « Tes alertes emploi », « Ce qui marche dans ta recherche », « Ton rendez-vous ORP » | « Candidatures » pour tous les onglets : l'onglet dit où l'on est |
| Actualités | « Le marché de l'emploi, et de quoi progresser » + sous-titre | « Actualités » |
| Formations | « Se former dans son domaine » + sous-titre | « Formations » |
| Profil | « Toi et ta recherche » + sous-titre | « Profil » |
| Onglets de Profil | Ce que je cherche · Mon parcours · Mes coordonnées | Critères · Parcours · Coordonnées |
| Réglages | « Tes réglages » | « Réglages » |
| Tes données | « Tes données » + sous-titre | « Données personnelles » |
| Diagnostic | sous-titre | sans sous-titre |
| Cartes d'Aujourd'hui | Tes 7 derniers jours · Ta semaine · La dose du jour | 7 derniers jours · Semaine · Meilleures offres |
| Profil, cartes | Tes prérequis · Ce que donnent tes critères | Critères · Effet des critères |

Le reste du même genre suit la même règle : les titres de cartes en « Ton… » ou « Tes… », et les boutons à l'impératif.

**Un test** vérifie que chaque page affiche comme titre le libellé de son entrée du menu. Un autre vérifie qu'aucun titre (h1, h2, h3, onglet) ne commence par « Ton », « Ta » ou « Tes ».

## 0.70.1 : les textes d'aide

- **Un composant `HelpTip`** : un « ? » de 1,5 rem (2,75 rem au doigt), à côté du titre de la partie. Il ouvre un petit volet de trois lignes au plus. Il se ferme avec Échap ou par un clic ailleurs, et les lecteurs d'écran le lisent sous le nom « Aide : … ».
- **Les 105 textes d'aide sont revus un par un** avec la règle 5. Chacun reste, passe dans le « ? » ou disparaît. Le tableau du tri sera dans les écarts.
- **Les deux prix dans les boutons** (lettre de correction, et la lecture des certificats, dont le prix est dans un texte d'aide) passent dans le « ? » et l'info-bulle.

## Ce qui ne change pas

- Les couleurs, les cartes, les illustrations et les animations : ce sont les points 2 et 3, pour plus tard si tu veux.
- Les messages d'erreur, les confirmations de suppression et la page de connexion.
- L'assistant : son texte de présentation suit les nouveaux noms (assistant-v9) s'il cite un ancien titre.

## Ce qu'on peut prendre à Sphere, et ce qu'on laisse

Sphere est un **site vitrine** de cabinet de recrutement, fait pour séduire en une visite. jobA1 est un **outil** qu'on ouvre tous les jours. On en prend la discipline, pas le spectacle.

- **À prendre** :
  - des titres qui sont des noms (« Featured Jobs », « Insights ») ;
  - la petite étiquette en capitales au-dessus d'un titre, pour situer : la date au-dessus de « Aujourd'hui » ;
  - des cartes d'offre réduites à trois faits (lieu, salaire, contrat) et une seule action ;
  - aucune phrase d'explication.
- **À laisser** :
  - les titres géants, le défilement en parallaxe, les photos et les carrousels : ils ralentissent un écran de travail ;
  - à la rigueur, la page « Découvrir jobA1 » peut s'en inspirer, puisqu'elle est une vitrine.

## Écarts de la 0.70.0

- **Profil › Critères** : la carte s'appelle « Prérequis », pas « Critères », pour ne pas répéter l'onglet ; son bouton devient « Modifier les prérequis ».
- **« Mon domaine » devient « Domaine »** (Actualités, Formations, Réglages, profils d'essai), et le reste du même genre : Alertes, Compte, Profils d'essai, Ressenti, Jours de recherche, Points forts, Entraînements, Enseignements, Prises de contact, Mois en bref, Questions au conseiller, Obligations et échéances, Semaines, Parcours.
- **La page Tes données devient « Données personnelles »**, avec ses liens (connexion, Plateforme, fiche de l'extension) ; son adresse `/tes-donnees` ne change pas.
- **Boutons** : « Demander un certificat intermédiaire », « Indiquer l'objectif mensuel ».
- **L'assistant passe en `assistant-v9`** : les nouveaux noms, rien d'autre.
- **Gardés** : la connexion, la présentation (Découvrir) et l'accueil, qui sont des pages de présentation.
- **Vérifié** : 314 tests de l'interface (2 nouveaux : le titre de chaque page est celui du menu, et aucun titre ne commence par un possessif), 530 tests serveur, lint et typecheck. Captures sur la démo, ordinateur et téléphone : Aujourd'hui, Candidatures, Profil, Actualités, sans débordement.
