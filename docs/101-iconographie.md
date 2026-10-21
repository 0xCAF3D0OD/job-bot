# 101 — L'iconographie (version 0.72.0)

> Statut : **validé** le 2026-10-19.
> Origine : ta planche « Iconographie » du 2026-10-19 : « remplace le plus possible du texte par une iconographie cohérente, voici le style que j'attends, sauf bien sûr ce qui a déjà été défini comme icône, comme l'assistant ».
> Se construit sur la 0.71.6 (PR #219, fusionnée).

## Le style (la planche)

- **Grille de 24 px, trait de 1,8 px arrondi, coins doux.** C'est déjà le style de `AppIcon` (25 icônes aujourd'hui) : on l'étend, on ne repart pas de zéro.
- **La couleur suit le texte** (`currentColor`) : violette dans le menu choisi, grise dans les métadonnées, blanche sur un bouton plein.
- **Trois tailles** : 16 px dans le texte et les pastilles, 20 px dans les menus et les boutons, 24 px seules.
- **Le point orange marque uniquement les actions IA** : l'icône « Action IA » de la planche, un carré arrondi avec un point pêche `#F4A261` dans le coin.

## Ce qui ne change pas

- **Le logo**, **la mascotte** et le bouton « Assistant » : ils ont déjà leur dessin.
- **Les logos des entreprises**, des connexions (Google…) et les graphiques.
- **L'étincelle à 4 branches** reste réservée à l'IA.

## Les trois façons de remplacer le texte

### 1. Icône et texte : là où on se repère

L'icône s'ajoute devant le mot, qui reste. C'est le cas de la barre latérale de la planche.

- **Le menu principal** :
  - Aujourd'hui (calendrier) ;
  - Candidatures (cercle coché).
- **Le menu du compte** :
  - Profil (personne) ;
  - Réglages (curseurs) ;
  - Données personnelles (bouclier) ;
  - Diagnostic (activité) ;
  - Collecter maintenant (actualiser) ;
  - Se déconnecter (sortie).
- **Les onglets des pages** :
  - **Candidatures** : Offres (mallette), Suivi (liste cochée), Alertes (cloche), Bilan (statistiques), Rendez-vous (calendrier) ;
  - **Progresser** : Actualités (journal), Formations (livre) ;
  - **Profil** : Critères (filtre), Parcours (dossier), Coordonnées (lettre) ;
  - **Réglages** : la liste de gauche reprend les icônes de ses rubriques, plus une pour Rythme (horloge).
- **Les boutons principaux** :
  - « Envoyer la candidature » (avion en papier) ;
  - « Joindre le CV » (document) ;
  - « Déposer un document » (importer).
- **Les éléments des menus ⋯** : chaque ligne prend son icône (modifier, télécharger, ouvrir, supprimer…), comme un menu d'application.

### 2. L'icône remplace l'étiquette : les métadonnées

Le mot qui annonce la valeur disparaît ; l'icône le dit à sa place, comme les pastilles de la planche (`[Lieu]`, `[Salaire]`, `[Délai]`).

| Aujourd'hui | Après |
|---|---|
| « Entreprise · Lieu · date » sur une ligne | entreprise (immeuble), lieu (repère), date (horloge) |
| Taux, télétravail, type de contrat (« À savoir ») | pastilles : taux, télétravail (maison), contrat (mallette) |
| « Vue 3 fois, depuis le… » | œil, puis le nombre et la date |
| « Adresse : … » | repère, puis l'adresse |
| La source d'une offre ou d'une actualité | globe, puis le nom |
| Format, langue, prix, durée d'une formation (dans le détail) | les mêmes icônes que sur la carte (0.70.6) |
| Les marques ✓ / ! / ✗ de « À savoir » | cercle coché, triangle d'alerte, croix |

Chaque pastille garde son sens pour un lecteur d'écran : le mot retiré reste lisible par lui (« Lieu : Lausanne »), pas à l'écran.

### 3. Icône seule : les actions secondaires

Le bouton n'a plus de texte, seulement l'icône, dans un bouton rond de la hauteur commune (`--control-h`, docs/94). **Au survol et au focus, une infobulle donne son nom**, et un lecteur d'écran l'annonce (`aria-label`).

- **Copier** (« Copier » → deux feuilles ; « Copié » devient une coche pendant 2 s).
- **Supprimer**, **Écarter**, **Révoquer** hors des menus (corbeille).
- **Modifier** (crayon).
- **Garder / favori** (signet), à la place du cœur et de « Garder ».
- **Fermer** (croix), à la place des « × » et des « Fermer » de panneau.
- **Mois précédent / suivant** (flèches), à la place de ← →.
- **Ajouter** à côté d'un champ (plus), à la place de « Ajouter » et du « ＋ ».
- **Monter / descendre** (flèches), à la place de ↑ ↓.
- **Ouvrir ailleurs** (flèche qui sort), à la place de « ↗ ».
- **Filtrer** (entonnoir) avec le nombre de filtres actifs en pastille, à la place de « Filtrer · 2 ».
- **Actualiser / relever** (actualiser).

**Restent en texte**, parce qu'une icône seule serait ambiguë :
- les choix qui engagent (« Marquer comme remis », « J'ai postulé », « Relancer ») ;
- les formats de fichier, qui gardent leur nom à côté de l'icône de téléchargement (« PDF », « Word ») ;
- « Annuler » et les confirmations.

### Les actions IA

Chaque bouton qui lance l'IA prend **l'icône « Action IA » avec le point orange**, devant son texte :
- rédiger : la lettre, la relance, un message, avec l'IA ;
- préparer le CV, la demande à l'ORP ;
- les pistes de l'IA, m'entraîner ;
- proposer des blocs, des mots-clés ;
- chercher d'autres formations, l'adresse au registre, l'offre chez l'employeur ;
- renoter, relire ;
- « Demander à l'assistant » dans les menus.

Le point orange n'apparaît **nulle part ailleurs**.

### Les signes qui deviennent des icônes

Tous les caractères utilisés comme icônes sont remplacés : × ← → ↗ ＋ ↑ ↓ ⌄ › ▶ ★, les ✓ décoratifs, et les émojis 👤 / 🧪 du choix du profil. Les ✓ qui disent « fait » (étapes de préparation, « Copié », « suivie ») deviennent la coche de l'iconographie.

## Comment

- **`AppIcon`** passe de 25 à environ 45 icônes. Une seule forme pour les flèches, tournée. Les tracés sont dessinés pour jobA1, dans le style de la planche.
- **Un composant `IconButton`** : l'icône seule, le nom en `aria-label`, l'infobulle au survol et au focus, la hauteur commune.
- **L'icône « Action IA »** est une icône à part (`ai`), avec son point pêche ; aucune autre n'a de point.
- **Un test** vérifie que tout bouton sans texte a un `aria-label`, et qu'aucun des caractères listés ne reste dans les gabarits.
- **`docs/interface.md`** gagne une règle « Iconographie » : le style, les trois façons, le point orange réservé à l'IA.

## Progresser prend le livre

**Progresser** était l'étincelle dans la capsule (docs/92). La planche de la mascotte réserve l'étincelle à 4 branches à l'IA : Progresser prend **le livre** (ta réponse du 2026-10-19). L'étincelle reste sur la rubrique IA des Réglages.

## Vérifié avant la PR

- **Tests** :
  - les icônes et leurs noms ;
  - `IconButton` (nom annoncé, infobulle au focus) ;
  - plus aucun caractère-icône dans les gabarits ;
  - tout bouton sans texte a un nom ;
  - le point orange seulement sur les actions IA.
- **L'audit des rangées** (docs/94) est vide : les boutons ronds gardent la hauteur commune.
- **Captures**, en clair et en sombre, sur ordinateur et sur téléphone :
  - le menu et le menu du compte ;
  - une offre (pastilles, actions) ;
  - le Suivi ;
  - la préparation (actions IA) ;
  - une formation ;
  - les Réglages.

## Écarts

- **Les icônes** sont dans `frontend/src/icons.ts` (58 au lieu de 25), affichées par `AppIcon`. Les chevrons et coches posés en CSS (filtres, téléchargement terminé, proposition faite) utilisent les mêmes tracés en masque.
- **Le menu ⋯** donne une icône à chaque action. Sans icône précisée : un lien externe prend « ouvrir ailleurs », un fichier « télécharger », une suppression la corbeille.
- **Candidatures prend le cercle coché** dans le menu et dans la barre d'onglets du téléphone (avant : la boîte de réception), comme sur la planche.
- **Sur téléphone, les cinq onglets de Candidatures** placent l'icône au-dessus du mot, pour tenir sur une ligne.
- **Le point orange a été retiré de trois boutons** qui ne lancent pas l'IA :
  - « Préparer la demande à l'ORP » (un texte sans IA) prend le document ;
  - « Demander une correction » (un modèle de lettre) prend l'enveloppe ;
  - « Ajouter des alertes avec l'assistant » (l'assistant de création, sans IA) prend le plus.
- **« Copier »** devient une icône seule, avec son nom en infobulle ; « Copié » devient la coche pendant 2 s.
- **Restent en texte** :
  - la feuille ORP imprimée, qui reproduit le formulaire officiel (« Adresse : ») ;
  - le sélecteur « Domaine / Tout » ;
  - les choix qui engagent (« Marquer comme remis », « J'ai postulé », « Relancer »…) ;
  - les envois de formulaire.
- **Le choix du profil** (menu du compte) : « Nom (principal) » et « Nom (essai) » remplacent les émojis 👤 / 🧪, qu'une liste de choix ne peut pas remplacer par une icône.
- **Retiré** : les anciennes règles CSS du bouton « × / ← Offres » du détail d'une offre. Ce sont maintenant deux contrôles, la croix (jusqu'à 1 200 px) et « ← Offres » (sur téléphone).
- **Vérifié** :
  - 329 tests de l'interface (nouveaux : aucun caractère-icône dans les gabarits, le point pêche sur la seule icône IA ; tests mis à jour pour les noms des boutons à icône), lint et typecheck ;
  - audit des rangées vide ;
  - captures sur la démo, en clair, en sombre et sur téléphone : Aujourd'hui, Offres et une offre ouverte, le Suivi, Formations, Réglages, Profil, le menu du compte.

## 0.82.2 — L'assistant hors du cadre sur téléphone

Ton retour du 2026-10-21, capture du Suivi à 414 px : « pourquoi l'assistant sort du cadre ? ».

- **La cause** : le bouton « + » (ajouter une candidature), tout à droite de l'en-tête du Suivi, porte son nom en infobulle (§ icônes seules). Même invisible, l'infobulle occupe sa place : centrée sous le bouton, elle dépassait le bord droit d'environ 45 px. Sur téléphone, le navigateur élargit alors tout l'écran à 457 px, et ce qui est fixé à droite, le bouton de l'assistant, part au-delà du bord.
- **La correction**, à deux niveaux :
  - sur écran tactile, l'infobulle d'un bouton icône, qui ne s'affiche jamais au toucher, **ne prend plus de place** (sauf au focus clavier) ;
  - partout, **`html, body { overflow-x: clip; }`** : un débordement sur le côté, quel qu'il soit, est rogné au lieu d'élargir l'écran. « clip » ne crée pas de zone de défilement : les en-têtes collants restent collants (vérifié après défilement).
- **Vérifié** : la vraie page Suivi (calendrier, téléphone) mesurée avec Playwright en mode mobile : 457 px avant, 414 px après ; le bouton de l'assistant à 14 px du bord ; l'en-tête toujours collé en haut après défilement. Un test garde les deux règles.
