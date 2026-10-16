# 60 — Retours d'actions et illustrations en grand sur ordinateur (version 0.47.1)

> Statut : **validé** le 2026-10-15, livré.
> Suite de docs/59. Retour du 2026-10-15 après 0.47.0 : « je ne vois pas où sont les illustrations » (elles n'étaient que sur les pages vides, que les vraies données n'affichent presque jamais). Kevin veut **les réussites et la prise en main illustrées**, et des images **plus grandes**, « quitte à placer l'image d'un côté et le formulaire ou autres de l'autre » ; **sur ordinateur seulement**.

## 1. La règle sur ordinateur (820 px et plus)

- Là où une illustration a sa place, la zone passe en **deux colonnes** : **l'illustration à gauche, 260 px de large**, le contenu (texte, liste, formulaire) à droite. Toujours du même côté.
- L'illustration est **jouée une fois** à l'apparition, puis reste fixe (docs/59) ; teintes douces, encre grise.
- **Une seule** à l'écran à la fois.
- **Téléphone (sous 820 px) : rien ne change par rapport à 0.47.0.** Les nouvelles illustrations (prise en main, formulaires, connexion) ne s'y affichent pas ; les réussites y gardent une petite image (96 px) au-dessus du texte.

## 2. Où

### 2.1 Les réussites (une fois, au moment de l'action)

| Moment | Où | Illustration | Ce qui s'affiche à droite |
|---|---|---|---|
| **Candidature marquée envoyée** (Préparer › ③ Postuler) | à la place des étapes de l'onglet | message-sent | « Candidature envoyée chez Exemple SA. » · « Comptée dans tes preuves ORP d'octobre : 7 sur 10. » · liens **Voir dans le Suivi** et **Retour aux offres** |
| **Preuves ORP marquées remises** (Suivi) | dans la barre du mois, à la place de l'action ORP, le temps de la visite | done | « Preuves de septembre remises. » · « Prochaine remise avant le 5 novembre. » |
| **Candidature passée en Engagement** (panneau d'une candidature, ou proposition de l'assistant confirmée) | en haut du panneau | handshake-deal, avec des **confettis** violets et menthe, une fois | « Félicitations ! » · rappel de signaler l'engagement à ton conseiller ORP |

### 2.2 La prise en main

- **« Pour bien démarrer » et « Comment ça marche »** (ouverts, sur Aujourd'hui) : l'illustration de **l'étape à faire** à gauche, la liste à droite ; elle change quand l'étape change.

| Étape | Illustration |
|---|---|
| Ce que je cherche | settings |
| CV et blocs de profil | my-resume |
| Coordonnées | profile |
| Objectif ORP | stepping-up |
| Notifications | lock-screen-notifications |
| Collecte Gmail | online-connection |
| Créer mes alertes | mailbox |
| Trier les offres | mobile-inbox |
| Préparer et postuler | message-sent |
| Suivre et relancer | date-picker |
| Remettre les preuves ORP | certification |

- **Assistant de création des alertes** (formulaire en trois étapes) : à gauche, mailbox (tes recherches), online-connection (le site), done (c'est prêt) ; le formulaire à droite.

### 2.3 Les formulaires de départ

Remplis une fois, ils gagnent l'illustration à gauche :

- **Connexion** : login.
- **Profil › Coordonnées** : profile.
- **Profil › Ce que je cherche** : settings.

### 2.4 Les pages vides

Celles de 0.47.0 (Offres, Suivi en liste, Bilan, Actualités, page introuvable) passent aussi en deux colonnes, image de 260 px à gauche. L'assistant, plus étroit, garde la sienne au-dessus.

## 3. Les retours d'actions (prévus en docs/59 §3)

| Action | Retour |
|---|---|
| **Trier une offre** (Plus tard, Ignorer) | la carte s'efface vers la droite, les suivantes remontent ; bulle « Passée en Plus tard · Annuler » |
| **Marquer comme envoyée** | le bouton devient « ✓ Envoyée », puis le moment illustré (§2.1) ; le compteur du mois monte de 1 |
| **Première ouverture d'Aujourd'hui et du Bilan** | les chiffres des tuiles comptent jusqu'à leur valeur, les barres montent, la jauge se remplit ; une fois par visite |
| **Nouvelles offres** (après « Collecter ») | elles apparaissent en fondu, en glissant de 8 px |

## 4. Les illustrations

**11 de plus** dans le dépôt (login, profile, my-resume, settings, lock-screen-notifications, online-connection, mailbox, message-sent, certification, done, handshake-deal), en plus des 6 de 0.47.0, réutilisées (mobile-inbox, date-picker, stepping-up…). Les animées le sont déjà dans `animees/` ; **login** est animée selon `CONSIGNES.md`. Toutes passent par `scripts/illustrations.mjs` (jouées une fois, couleurs du thème).

## 5. Livraison

Une PR (**0.47.1**), captures sur ordinateur (clair et sombre) de chaque endroit du §2, et vérification que le téléphone n'a pas changé.

## Points à valider

1. **Deux colonnes, illustration de 260 px à gauche**, sur ordinateur seulement ; téléphone inchangé (§1).
2. **Les trois réussites** illustrées : envoyée, preuves remises, Engagement avec confettis (§2.1).
3. **Prise en main et assistant des alertes** illustrés à gauche (§2.2) ; **connexion, coordonnées, critères** (§2.3) ; pages vides en deux colonnes (§2.4).
4. **Les retours d'actions** (§3).
5. **Une PR** (§5).

## Écarts avec la livraison

- **Composant `IllustratedSide`** : image de 260 px à gauche, contenu à droite, à partir de 821 px. Sous 820 px, l'image disparaît (prise en main, alertes, formulaires, connexion) ou reste petite au-dessus (réussites, pages vides).
- **Candidature envoyée** : le moment apparaît en tête de l'onglet ③ Postuler, à la place de l'ancien message en haut de page : « Candidature envoyée chez Acme SA. » ; « Comptée dans tes preuves ORP d'octobre : 7 sur 10. » (lu depuis le mois ORP de la candidature) ; liens « Voir dans le Suivi » (le bon mois) et « Retour aux offres ». Il reste jusqu'à ce qu'on quitte la page.
- **Preuves remises** : sous la barre du mois, tant qu'on reste sur ce mois ; « Prochaine remise avant le 5 novembre 2026 » vient du mois suivant. Les noms de mois sont élidés (« d'octobre », « d'août »).
- **Engagement** : dans le panneau d'une candidature quand son statut passe en Engagement pendant qu'il est ouvert, et dans la carte de proposition de l'assistant confirmée. 18 confettis (violet, menthe, orange), 1 s, partant de l'image ; rien si « réduire les animations ».
- **Formulaires** : connexion, Coordonnées et Ce que je cherche ; l'image reste en haut à gauche pendant qu'on fait défiler un long formulaire.
- **login** animée pour l'occasion (la porte s'entrouvre, la poignée pulse), « OK » avec `verifier.py`. 17 illustrations en tout (176 Ko).
- **Trier une offre** : « Passée en Plus tard. · Annuler » au-dessus de la liste ; « Annuler » remet le statut d'avant. La carte s'efface vers la droite (250 ms), les suivantes remontent ; la liste est devenue une liste à plat (titres de jour et cartes) pour que chaque carte s'anime seule.
- **Entrée des chiffres** : les comptes des tuiles (« 21 », « 4 / 10 ») et le compte de la jauge montent jusqu'à leur valeur ; une date (« 5 octobre ») ne bouge pas. Les barres de « Ta semaine » et « Par mois » montent l'une après l'autre, celles du parcours s'étirent, les arcs de la jauge apparaissent. Une fois par visite (rechargement de la page).
- **Nouvelles offres** : toute carte qui arrive dans la liste (après « Collecter », « Afficher plus » ou un changement de filtre) apparaît en fondu en glissant de 8 px.
- **Vérifié** sur ordinateur : connexion, Coordonnées, Ce que je cherche, assistant des alertes, page introuvable, Bilan vide, prise en main. La candidature envoyée, les preuves remises et l'Engagement sont couverts par des tests.
