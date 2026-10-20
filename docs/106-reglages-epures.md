# 106 — Des Réglages épurés (version 0.76.0)

> Statut : **validé** le 2026-10-20 : enregistrement au changement pour un seul champ, le seuil en cinq pastilles, les flèches retirées partout, docs/104 décalé en 0.77.0 et 0.78.0.
> Origine : ta remarque du 2026-10-20, en te baladant dans les Réglages (captures Plateforme, Notifications, Outils, Rythme) : « il y a des cartes dans les cartes, une barre grisée verticale dans la carte […] se concentrer sur l'action, j'aime pas le curseur pour monter ou descendre un nombre », avec Sphere comme référence.
> Les versions prévues par docs/104 (l'adresse à jobA1, les premières offres) passent en 0.77.0 et 0.78.0.

## Ce que montrent les captures

| Rubrique | Ce qui ne va pas |
|---|---|
| **Notifications** | Deux cartes pour une rubrique. La seconde s'appelle « Notifications », comme la rubrique, et ne contient qu'un bouton, suivi d'un filet qui ne sépare rien. « Enregistrer » est isolé sous un filet, loin du seul champ. |
| **Outils** | « Comment l'installer » ouvre un texte avec **une barre grise verticale** à gauche (`.disclosure-body`, `border-left`). Un filet vide ferme la carte. |
| **Rythme** | Chaque étiquette est soulignée en pointillés (le « ? » au survol), ce qui la fait lire comme un lien. Trois blocs séparés par des filets, puis « Enregistrer » tout en bas, loin de ce qu'on vient de changer. |
| **Plateforme** | « Plafond IA » : un champ nombre avec ses **flèches haut / bas**. Même chose dans Notifications (« 70 / 100 »), Recherche d'emploi et ailleurs : 12 champs nombre dans l'interface. |
| **Toutes** | Sur téléphone, chaque rubrique est une ligne dépliable dans un cadre, qui contient elle-même des cartes : **des cadres dans des cadres**. |

**Les flèches des champs nombre** : je ne retrouve ni règle ni correctif qui les retire, ni dans les docs ni dans le code. Elles ont toujours été là.

## Ce que fait Sphere (formulaire de contact)

- **Pas de cadre** autour du formulaire : les champs sont posés sur la page.
- **Une étiquette en gras au-dessus** de chaque champ, et un champ pleine largeur.
- **Un seul bouton plein**, à la fin, là où l'œil arrive.
- Rien d'autre : pas de filet entre les champs, pas de texte d'aide visible.

## Les règles (ajoutées à `docs/interface.md`)

1. **Une rubrique, une carte.** Ses parties sont séparées par un **titre** (pas par un filet ni par une autre carte). Une partie qui n'a qu'une action devient une ligne de la carte : son nom à gauche, l'action à droite.
2. **Pas de barre verticale dans une carte.** Un contenu replié s'ouvre **sous son titre, au même retrait**, sans trait ni fond.
3. **Pas de filet orphelin** : un filet sépare deux choses, jamais la dernière du bord de la carte.
4. **Les titres de partie ne sont pas soulignés.** La description au survol (docs/53) reste, lue aussi par les lecteurs d'écran, mais sans pointillés sous le titre.
5. **L'action est près de ce qu'elle touche.** Un réglage d'un seul champ s'enregistre **dès qu'on le change** (« Enregistré » s'affiche une seconde à côté). Un formulaire de plusieurs champs garde **un seul bouton plein « Enregistrer »**, à la fin, sans filet au-dessus.
6. **Les nombres sans flèches.** Un champ nombre est un champ texte au clavier numérique (`inputmode="numeric"`), sans flèches haut / bas, avec son unité à droite (« CHF / mois », « / 100 »). Quand il n'y a que quelques valeurs sensées, des **choix en pastilles** à la place (voir le point 2 à valider).
7. **Sur téléphone**, la ligne dépliable de la rubrique **est** la carte : son contenu ne remet pas de cadre à l'intérieur.

## Ce qui change, rubrique par rubrique

| Rubrique | Après |
|---|---|
| **Recherche d'emploi** | une carte ; les nombres sans flèches |
| **Rythme** | une carte en trois parties titrées (Jours de recherche, Une pause, Les offres bien notées), sans filets ; étiquettes sans pointillés ; « Enregistrer » plein à la fin |
| **Actualités** | une carte ; titres de parties au lieu des filets |
| **Notifications** | **une seule carte** : « M'avertir d'une offre à partir de » (enregistré au changement), puis une ligne « Notification de test » avec le bouton « Envoyer » à droite. Plus de seconde carte « Notifications ». |
| **IA** | une carte ; le plafond sans flèches |
| **Compte** | Connexion et Données personnelles : deux parties titrées d'une même carte, plus deux cartes |
| **Outils** | « Comment l'installer » s'ouvre sans barre grise ; « Navigateurs reliés » en lignes séparées par un filet ; plus de filet en bas |
| **Plateforme** | « Plafond IA » sans flèches, enregistré au changement |

Le changement vaut **sur ordinateur et sur téléphone** : tes captures sont sur ordinateur.

## Écarts

- **« Une rubrique, une carte »** se fait dans `SettingsSection` : la carte entoure la rubrique, et les cartes des panneaux (Sites suivis, Agenda, Extension, Connexion, Données personnelles, la dépense de l'IA) y perdent leur cadre. Les panneaux eux-mêmes ne changent pas : ailleurs, ils gardent leur carte.
- **Les filets entre les parties** disparaissent dans les Réglages seulement. Les autres formulaires (Profil, Critères) gardent les leurs pour cette version.
- **Les flèches** sont retirées partout par une règle CSS : les champs restent des champs nombre (les bornes et la validation ne changent pas), avec le clavier numérique sur téléphone.
- **Notifications** : la seconde partie s'appelle « Téléphone ». « Envoyer une notification de test » devient la ligne « Notification de test », avec « Envoyer » à droite.
- **IA** : le plafond de l'exploitant s'enregistre au changement (ou avec Entrée). Le plafond des comptes, dans Plateforme, le faisait déjà.

## Vérifié

- Tests (350) : une seule carte pour la rubrique ; les cinq pastilles, enregistrées au clic avec « Enregistré » ; un seuil d'avant hors des cinq toujours proposé ; « Envoyer » et le titre « Téléphone » ; le plafond de l'IA enregistré au changement, sans bouton ; « Enregistrer » plein dans Recherche d'emploi. Lint et typecheck.
- Capture des rubriques Notifications, Rythme, Outils, IA et Compte, sur ordinateur, avec des données fictives. Le téléphone n'a pas été capturé.

## Décisions (2026-10-20)

1. **Enregistrement** : un réglage d'un seul champ s'enregistre au changement ; un formulaire de plusieurs champs garde un seul « Enregistrer » plein à la fin.
2. **Le seuil des notifications** : cinq pastilles, 50 · 60 · 70 · 80 · 90.
3. **Les flèches** : retirées des 12 champs nombre de l'interface, pas seulement dans les Réglages.
4. **Les versions** : l'adresse à jobA1 et les premières offres (docs/104) passent en 0.77.0 et 0.78.0.

## Complément 0.76.1 : le téléphone

Ton retour du 2026-10-20, capture des Actualités à 414 px : « il faut adapter pour le téléphone, simplifier pour que ça passe dessus ».

- **Le contenu collait au bord gauche** de la ligne dépliable : la règle « pas de barre verticale » de la 0.76.0 retirait aussi la marge du contenu de la ligne elle-même. Elle ne vise plus que les repliables **dans** une carte ; le contenu de la ligne a 1 rem de chaque côté, sans barre.
- **Plus serré** sous 820 px : les parties à 1 rem au lieu de 1,5 rem, le bouton « Enregistrer » à 0,75 rem.
- **Les cinq pastilles** du seuil et « / 100 » tiennent sur une ligne (2,75 rem par pastille, la taille au doigt).
- **Les exemples des champs de mots-clés** : « Autre mot-clé » dans Réglages › Actualités, « Ton métier, un outil, un diplôme… » dans Actualités et Formations, au lieu de « DevOps, Kubernetes, CKA… » (même règle que docs/104 §5).
- L'ordinateur ne change pas.
- **Vérifié** : capture à 414 px des Actualités et des Notifications ouvertes, avec des données fictives (la liste des sources n'y figure pas), tests, lint et typecheck.

