# 21 — Simplifier : moins de texte, un chemin clair (version 0.14.0)

> Statut : **validé** le 2026-10-07. livré : PR a (textes, « Comment ça marche »).
> Retours d'usage du 2026-10-07 : « trop d'informations, l'utilisateur peut être perdu ; moi-même je le suis quand je parcours la plateforme ».

## 1. Le constat

- Les pages ont été construites fonction par fonction : chaque fonction a ajouté son paragraphe d'explication, ses réglages et ses cas particuliers, au même niveau que l'essentiel.
- Il manque une vue d'ensemble : **dans quel ordre** faire les choses, et **où** se trouve chaque étape.
- Les pages les plus chargées : **Alertes**, **détail d'une offre**, **Preuves ORP**, **Réglages**, **Profil**.

## 2. Trois règles pour toute la plateforme

1. **Une phrase d'aide au plus** sous un titre. Le reste passe derrière un lien « En savoir plus » (qui se déplie) ou une petite icône « ? ».
2. **L'action principale d'abord**, en un bouton bien visible ; les actions rares dans un menu « ⋯ » ou une section repliée.
3. **Pas de jargon technique** à l'écran (`JOBBOT_…`, `.env`, `make dev`, « worker ») : ces consignes vont dans la documentation, l'écran dit seulement « non configuré, voir l'aide d'installation ».

## 3. Le chemin, affiché une fois

Sur **Aujourd'hui**, un encart **« Comment ça marche »** (masquable), en cinq étapes avec un lien chacune :

1. **Créer mes alertes** sur les sites d'emploi → Candidatures › Alertes
2. **Trier les offres** reçues → Candidatures › Offres
3. **Préparer** lettre et CV, puis **postuler** → bouton « Préparer ma candidature »
4. **Suivre** les réponses et relancer → Candidatures › Suivi
5. **Remettre les preuves** à l'ORP chaque mois → Candidatures › Preuves ORP

Chaque étape est cochée quand elle est faite (au moins une alerte reçue, une offre triée, une candidature envoyée…). Il remplace « Pour bien démarrer » pour ce qui concerne la recherche ; la configuration (CV, coordonnées) reste dans Profil.

## 4. Alertes : un assistant au lieu d'un tableau

**Aujourd'hui** : un long texte, un tableau recherches × sites avec trois états et des cases dans chaque cellule, un pas-à-pas de transfert, puis le journal.

**Proposition** :

- **Tant qu'aucune alerte n'est reçue**, un **assistant en trois étapes**, un écran à la fois :
  1. **Tes recherches** : les mots et lieux proposés, en pastilles à garder ou retirer, et « Ajouter ».
  2. **Crée tes alertes, un site à la fois** : un grand bouton « Ouvrir jobup avec ma recherche », une phrase (« clique sur *Créer une alerte* et donne ton adresse »), puis « C'est fait, site suivant ».
  3. **C'est prêt** : « Tes alertes arrivent dans ta boîte ; elles apparaîtront ici dès le premier envoi. »
- **Ensuite**, un résumé compact : « 4 alertes actives · dernière reçue hier », une ligne par recherche avec un point vert (reçue) ou orange (rien reçu depuis 3 jours), et un bouton **« Gérer mes alertes »** qui ouvre le tableau actuel pour les cas avancés.
- **Le pas-à-pas de transfert** n'apparaît que si une alerte créée n'arrive pas (point orange) : « Rien reçu de LinkedIn ? Vérifie… ».
- **Alertes reçues** (le journal) : repliées par défaut, « Voir les alertes reçues (12 ce mois) ».

## 5. Détail d'une offre : l'essentiel en haut

De haut en bas :

1. Titre, entreprise, lieu, note.
2. **Deux boutons** : « Préparer ma candidature » et « Postuler » (chez l'employeur si trouvée, sinon sur le site).
3. Le **résumé de l'IA** (poste, demande, offre, points forts, manques).
4. Une section repliée **« Entreprise »** : adresse, recherche dans le registre, annonce chez l'employeur, logo.
5. Le menu « ⋯ » : plus tard, ignorer, expirée, chercher chez l'employeur.

## 6. Preuves ORP, Réglages, Profil

- **Preuves ORP** : en haut, l'état et **une seule action** selon le moment (« Compléter 2 lignes », puis « Télécharger le PDF », puis « Marquer comme remis ») ; CSV, colonnes, Job-Room et journal joint dans « Plus d'options ».
- **Réglages** : seulement ce que l'on règle vraiment (objectif ORP, date limite, seuils, plafond IA, sources, profils, connexion) ; l'**État technique** passe dans une page à part (« Diagnostic »), accessible depuis le bas des Réglages.
- **Profil** : chaque onglet commence par ce qui manque (« Il manque ton adresse »), les explications longues repliées.

## 7. Livraison en trois PR

| PR | Contenu |
|---|---|
| **0.14.0-a** | Règles §2 appliquées partout (textes raccourcis, jargon retiré), « Comment ça marche » sur Aujourd'hui |
| **0.14.0-b** | Alertes : assistant, résumé, journal replié |
| **0.14.0-c** | Détail d'une offre, Preuves ORP, Réglages (Diagnostic à part), Profil |

Aucune fonction n'est supprimée : seuls l'ordre, les textes et ce qui est visible d'emblée changent.

## Points à valider

1. **Trois règles** : une phrase d'aide, l'action principale d'abord, pas de jargon technique à l'écran (§2).
2. **« Comment ça marche »** en cinq étapes sur Aujourd'hui (§3).
3. **Alertes en assistant**, puis résumé compact et « Gérer mes alertes » pour le tableau (§4).
4. **Détail d'une offre** réordonné, « Entreprise » repliée (§5).
5. **Preuves ORP** avec une action à la fois ; **Diagnostic** sorti des Réglages (§6).
6. **Trois PR** (§7).

## Écarts avec la PR a

- **Textes** : une phrase d'aide sous chaque titre (Alertes, Sites suivis, Sources et « Mon domaine », Profils d'essai, Compte, Réglages, lettre, CV) ; le détail utile passe dans un « En savoir plus » repliable. Sous-titres des pages raccourcis (Actualités, Formations, Réglages, Connexion, Profil).
- **Jargon technique** retiré de l'écran (`JOBBOT_…`, `.env`, `make dev`) : l'écran dit « réglage d'installation, voir le README », et le README a une nouvelle section **« Réglages d'installation »**. Seule exception : la page de connexion, quand aucun compte n'existe, garde la commande `jobbot set-password` (sans elle, impossible de se connecter).
- **« Comment ça marche »** : cinq étapes cochées automatiquement (au moins une alerte lue, une offre triée, une candidature envoyée, une réponse suivie, un mois de preuves remis), chacune avec son lien et l'endroit où la faire ; masquable. « Pour bien démarrer » reste en dessous pour la configuration.
- Les pages Alertes, détail d'une offre, Preuves ORP, Réglages et Profil seront réorganisées dans les PR b et c.
