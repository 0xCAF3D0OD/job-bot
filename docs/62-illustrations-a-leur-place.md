# 62 — Les illustrations à leur place : une seule famille, seulement là où elles servent (version 0.48.1)

> Statut : **validé** le 2026-10-16 (Profil retiré aussi), livré.
> Constat du 2026-10-16 sur 0.48.0 (relu par Kevin) : « chaque illustration prise seule est correcte, mais ensemble elles forment un patchwork qui concurrence l'interface au lieu de la servir ». En résumé :
> - **incohérence** : personnages, maquettes d'écran, tête grise, écusson encadré ; certaines dans un cadre avec ombre, d'autres non ; des tailles sans rapport (le téléphone des Notifications coupé, sous le bouton Assistant) ;
> - **désaccord avec l'interface** : traits épais et aplats lourds face à une interface fine ; un gris-violet au lieu des gris neutres ; un air d'unDraw « template » ;
> - **mauvais placement** : dans les Réglages, on vient remplir des champs, l'image est du bruit et serre le contenu ; sur Aujourd'hui, le dessin du calendrier isolé à gauche déséquilibre la page ; aucune information apportée.

## 1. Ce qu'on retire

| Endroit | Aujourd'hui | Après |
|---|---|---|
| **Réglages** (six rubriques) | une image à droite du formulaire | retirée ; une **petite icône au trait** (même famille que la navigation) devant le titre de la rubrique |
| **Préparer › À recopier** | une image à droite du tableau | retirée ; le tableau garde sa largeur de lecture |
| **Aujourd'hui › guides** | le dessin de l'étape à faire à gauche des deux lignes | retiré ; « Comment ça marche » et « Pour bien démarrer » reprennent toute la largeur |
| **Profil › Coordonnées, Ce que je cherche** | une image à gauche du formulaire | retirée (même raison que les Réglages : on y remplit des champs) ; le formulaire reste à sa largeur actuelle |

Icônes des Réglages : Recherche d'emploi (loupe), Actualités (journal), Notifications (cloche), IA (étincelle), Compte (bouclier), Outils (prise). Trois sont nouvelles (étincelle, bouclier, prise), dessinées comme les autres pictogrammes.

## 2. Ce qu'on garde, là où elles ont un rôle

- **Les états vides** : Offres sans résultat, Suivi d'un mois vide, Bilan sans candidature, Actualités vides, page introuvable.
- **La première connexion et la prise en main** : la page de connexion, l'assistant de création des alertes.
- **Les moments** : la carte « candidature envoyée » / « preuves remises », l'Engagement.
- **La transition des pages qui chargent.**

## 3. Une seule famille

- **Seulement des objets et des personnages, sans maquette d'écran ni cadre** : plus de téléphone, de fenêtre ou de calendrier dessinés en interface, plus d'image encadrée avec une ombre décalée.

| Usage | Avant | Après |
|---|---|---|
| Offres sans résultat ; transition Offres | mobile-inbox (téléphone) | **mailbox** (la boîte aux lettres) |
| Suivi vide ; transition Suivi | date-picker (calendrier encadré) | **done** (la personne qui coche) |
| Actualités vides ; transition Actualités | newsfeed (téléphone) | **absorbed** (la personne qui lit en marchant) |
| Alertes, étape 2 (le site) | online-connection (écrans reliés) | **message-sent** (l'avion en papier) |
| Transition Alertes | mailbox | **message-sent** |
| Le reste | stepping-up, morning-plans, certification, login, page-eaten, done, handshake-deal, message-sent | inchangé |

- **Même taille maximale** : 220 px partout (états vides, connexion, alertes, transition), 170 px sur la carte des moments, 380 px pour l'Engagement (le seul moment en grand). Téléphone : 140 px.
- **Couleurs tirées des tokens** : le violet suit `--accent` ; l'encre gris-violet devient le gris neutre `--faint` ; les plans gris clair deviennent `--border` (et leurs équivalents en sombre). Seules les peaux et les cheveux gardent leurs couleurs.
- Les fichiers qui ne servent plus quittent le dépôt (mobile-inbox, date-picker, newsfeed, online-connection, settings, profile, my-resume, lock-screen-notifications, guidelines, artificial-intelligence, security-on). **absorbed** est animée selon `CONSIGNES.md`.

## 4. La règle, écrite une fois

Les lectures du 2026-10-16 (Pixeltrue, Elementor, Clio, Fireart) disent toutes la même chose : un **but** avant chaque image, une **dose** faible, un **seul style** aligné sur la marque, les **couleurs de l'interface**, et jamais une information portée par l'image seule. La règle de la plateforme, ajoutée à `docs/exploitation.md` (partie interface) :

1. Une illustration seulement si l'écran n'a rien d'autre à montrer (vide, erreur, première fois) ou pour marquer un moment (réussite, transition).
2. Jamais dans un formulaire, une liste ou un tableau ; jamais dans une carte.
3. Une seule famille, 220 px au plus, couleurs des tokens, décorative pour les lecteurs d'écran (le texte à côté dit tout).
4. Animée une fois à l'apparition, coupée par « réduire les animations ».

**Plus tard, en option** : les articles conseillent des illustrations propres à la marque plutôt que des images de banque (unDraw se reconnaît). Une suite possible serait de dessiner nos propres illustrations **au trait**, dans le style des pictogrammes (traits fins, accent violet) ; ce n'est pas dans cette version.

## 5. Livraison

Une PR (**0.48.1**), captures avant / après des Réglages, de Préparer, d'Aujourd'hui, de Profil et de chaque état vide, clair et sombre.

## Points à valider

1. **Retirer** les images des Réglages (icône devant le titre à la place), de « À recopier », des guides d'Aujourd'hui, et de Profil (§1).
2. **Garder** les états vides, la connexion, l'assistant des alertes, les moments et la transition (§2).
3. **Une seule famille** : objets et personnages sans maquette d'écran ni cadre, les remplacements du tableau, 220 px au plus, couleurs des tokens (§3).
4. **La règle** écrite dans `docs/exploitation.md` (§4).
5. **Une PR** (§5).

## Écarts avec la livraison

- **La règle** est dans un nouveau `docs/interface.md` (illustrations, mouvement, clic direct), lié depuis le README, plutôt que dans `docs/exploitation.md`, qui est le contrat d'infrastructure.
- **Réglages** : l'icône (20 px, gris) devant le titre de la rubrique ; le formulaire reprend sa largeur d'avant 0.48.0.
- **Préparer › À recopier** : le tableau limité à 40 rem.
- **Aujourd'hui** : les deux guides reprennent toute la largeur ; plus rien ne dépend du guide ouvert.
- **Illustrations** : 10 restent (absorbed, certification, done, handshake-deal, login, mailbox, message-sent, morning-plans, page-eaten, stepping-up), 108 Ko ; 11 fichiers retirés. absorbed animée pour l'occasion (trois papiers qui flottent), « OK » avec `verifier.py`.
- **Couleurs** : encre `--faint`, plans `--border`, papier `--surface`, dans les deux thèmes ; seules les peaux, cheveux et le violet (`--accent`) gardent une couleur propre.
- **Vérifié** sur ordinateur : Réglages › Notifications, Profil › Coordonnées, Préparer › Postuler, Bilan vide, assistant des alertes, page introuvable.
