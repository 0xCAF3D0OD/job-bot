# 58 — Des illustrations animées pour donner vie à la plateforme (version 0.46.0)

> Statut : **validé** le 2026-10-15 ; 0.46.0 livrée (0.46.1 à suivre).
> Demande du 2026-10-15 : « animer un peu la plateforme pour lui donner vie », avec des illustrations unDraw (`illustration1/`, dont 33 déjà animées dans `animees/`) ; idées : les chargements, la génération d'un fichier, les étapes de prise en main d'un nouvel utilisateur.

## 1. Le principe

- Les **pictogrammes au trait restent** dans les tuiles, cartes, boutons et bulles : à 22 px, une illustration devient une tache.
- Les **illustrations vont dans les grands espaces**, quand il n'y a rien d'autre à montrer ou qu'il se passe quelque chose : prise en main, attente, document en cours, page vide, réussite, erreur. Jamais dans le tableau de bord rempli ni dans les listes : le quotidien reste calme.
- **Une seule illustration à la fois** à l'écran, entre 160 et 220 px de large sur ordinateur, 120 à 140 px sur téléphone, centrée au-dessus de son texte.
- **Animation douce** et en boucle (celles de `animees/`), arrêtée si le système demande moins de mouvement (« réduire les animations ») : l'image reste alors fixe.

## 2. Les couleurs, en clair et en sombre

Les originaux ont des contours presque noirs et de grands aplats gris clair : en thème sombre, les contours disparaissent et les aplats éblouissent. Les illustrations sont donc **insérées dans la page** (pas en image) et leurs couleurs passent par celles de la plateforme, **sans toucher aux formes** :

| Couleur unDraw | Devient | En clair | En sombre |
|---|---|---|---|
| violet #6C63FF | `--accent` | #635BFF | #8F89FF |
| encre #090814, #2F2E41, #3F3D56 | `--illu-ink` | inchangée | gris clair |
| plans #E6E6E6, #F2F2F2, #D6D6E3, #CCC | `--illu-plane` | inchangés | gris bleuté sombre |
| blanc #FFF | `--surface` | blanc | fond des cartes |
| peau, cheveux, autres | inchangées | | |

Un script du dépôt fait ce remplacement (et vérifie qu'aucune forme ne change), comme `verifier.py` pour les animations.

## 3. Où, et lesquelles

### 3.1 Prise en main d'un nouvel utilisateur

« Pour bien démarrer » et « Comment ça marche » (en bas d'Aujourd'hui) : quand on les ouvre, **l'étape à faire** s'affiche en grand avec son illustration, son texte et son bouton ; les autres restent en lignes cochées dessous.

| Étape | Illustration |
|---|---|
| Coordonnées | profile |
| CV déposé | my-resume |
| Ce que je cherche (critères) | settings |
| Objectif ORP | stepping-up |
| Notifications | lock-screen-notifications |
| Créer mes alertes | mailbox |
| Trier les offres | mobile-inbox |
| Préparer et postuler | message-sent |
| Suivre et relancer | date-picker |
| Remettre les preuves ORP | certification |

Dans l'**assistant de création d'alertes** (trois étapes) : mailbox, puis online-connection, puis done.

### 3.2 Les attentes

- **Chargement d'une page** : rien ne change sous 0,4 s (les blocs gris actuels). Au-delà, l'illustration « loading-ui » animée prend leur place, et reste au moins 0,6 s pour ne pas clignoter. **Pas d'attente imposée** : une page qui arrive en 0,2 s s'affiche en 0,2 s.
- **Rédaction par l'IA** (lettre, CV, pistes d'entretien : 10 à 30 s) : « ai-generated-document » animé, avec une phrase qui change toutes les 4 s (« Je lis l'offre… », « Je choisis tes expériences… », « Je relis… ») ; à l'arrivée, le document remplace l'illustration.
- **Fichier en préparation** (PDF, Word, export ORP, s'il dépasse 0,4 s) : « processing ».

### 3.3 Les pages vides

| Page | Illustration | Texte (inchangé ou presque) |
|---|---|---|
| Offres, aucune offre | mobile-inbox | les offres arrivent avec tes alertes |
| Suivi, aucune candidature ce mois | date-picker | |
| Bilan, pas encore de candidature | stepping-up | |
| Actualités, rien avec ces filtres | newsfeed | |
| Formations, aucune suivie | certification | |
| Alertes, rien reçu encore | mailbox | |
| Assistant, discussion vide | chat-bot | au-dessus des suggestions |

### 3.4 Les réussites (brèves)

Une illustration dans le message de confirmation, **2 à 3 secondes**, puis le message habituel :

- candidature marquée envoyée : message-sent ;
- preuves ORP marquées remises : done ;
- CV ou document déposé : successful-upload ; en cas d'échec : upload-warning ;
- candidature passée en **Engagement** : handshake-deal (la seule « fête » de la plateforme).

### 3.5 Les erreurs

- plateforme injoignable : connection-lost ;
- page introuvable : page-eaten ;
- Diagnostic, un service en panne : maintenance.

## 4. Ce qu'on n'utilise pas

Les illustrations datées ou saisonnières (2019, 2021, 2022, new-decade, Noël, Halloween, Pâques) et celles hors sujet (add-to-cart, discount, mobile-gift, cookie-consent, qr-code-scan, online-transactions, two-factor-authentication, buggy-code). Elles ne sont pas copiées dans le dépôt.

## 5. Ce qu'il faut faire

- **Retenues : 23 illustrations** (§3). 14 sont déjà animées dans `animees/` ; les **9 autres**, de `undraw/` (my-resume, lock-screen-notifications, mailbox, mobile-inbox, message-sent, processing, newsfeed, chat-bot, page-eaten), sont animées selon `CONSIGNES.md` (rien d'inventé, image au repos identique à l'original, vérifiées par `verifier.py`).
- Copiées dans `frontend/src/assets/illustrations/` (environ 200 Ko en tout, chargées seulement quand elles s'affichent).
- Un composant `Illustration` (nom, taille, texte pour les lecteurs d'écran ou rien si décorative).
- **Licence** : unDraw permet l'usage dans une application, gratuitement et sans mention ; une ligne dans le README indique leur origine.

## 6. Livraison

Deux PR, pour voir le rendu avant de tout poser :

| PR | Contenu |
|---|---|
| **0.46.0** | Couleurs (§2), composant, prise en main (§3.1), attentes (§3.2) |
| **0.46.1** | Pages vides, réussites, erreurs (§3.3 à §3.5) |

Captures en clair et en sombre, ordinateur et téléphone, et une courte vidéo des animations.

## Points à valider

1. **Pictogrammes gardés**, illustrations seulement dans les grands espaces, une à la fois (§1).
2. **Recoloration** aux couleurs de la plateforme pour le thème sombre, sans toucher aux formes (§2).
3. **Prise en main** : l'étape à faire en grand avec son illustration (§3.1).
4. **Chargement sans attente imposée** (0,4 s puis au moins 0,6 s), rédaction IA avec phrases qui changent (§3.2).
5. **Pages vides, réussites, erreurs** (§3.3 à §3.5) et la liste écartée (§4).
6. **Deux PR** (§6).

## Écarts avec la livraison (0.46.0)

- **15 illustrations** dans cette version (celles de la prise en main et des attentes) ; les 8 des pages vides, réussites et erreurs viendront avec 0.46.1. Six ont été animées pour l'occasion selon `CONSIGNES.md` (my-resume, mailbox, mobile-inbox, message-sent, lock-screen-notifications, processing), toutes « OK » avec `verifier.py`.
- **Préparation** : `frontend/scripts/illustrations.mjs <animées> <originaux>` écrit `src/assets/illustrations/` (148 Ko). Il retire la taille fixe, met les couleurs en minuscules, préfixe classes et animations par le nom de l'illustration, limite « réduire les animations » à l'illustration, et s'arrête si une forme diffère de la source.
- **Couleurs** : la feuille de style reprend les couleurs unDraw par attribut (`.illu [fill="#6c63ff"]`) : le violet suit `--accent` ; en sombre seulement, l'encre passe en gris clair (#B4B4CC), les plans en gris bleuté sombre, le blanc au fond des cartes. En clair, l'illustration reste l'originale.
- **Prise en main** : l'étape à faire est une carte entière cliquable (pas de bouton ni de « › », docs/57) : illustration, « Étape N sur M », l'intitulé, où la faire. « Brancher la collecte sur Gmail », sans page dans la plateforme, n'est pas cliquable. Illustrations : critères → settings, CV → my-resume, coordonnées → profile, objectif ORP → stepping-up, notifications → lock-screen-notifications, collecte Gmail → online-connection ; alertes → mailbox, tri → mobile-inbox, postuler → message-sent, suivi → date-picker, ORP → certification. Assistant des alertes : mailbox, online-connection, done.
- **Chargement** : sur les cinq pages qui avaient des blocs gris (Aujourd'hui, Suivi, Bilan, Actualités, Formations). Vérifié avec un serveur ralenti : blocs gris, puis l'illustration et « Chargement… ».
- **Rédaction** : lettre et CV (première version), et pistes d'entretien de l'IA (« Je relis tes retours d'entretien… »). Une nouvelle version d'un document existant garde le document grisé, comme avant. Non essayée en vrai (pas d'IA sur l'instance de test) : couverte par un test.
- **Fichiers** : les liens de téléchargement de la plateforme ne changent pas ; un seul écouteur les télécharge pour savoir quand le fichier est prêt. Au-delà de 0,4 s, une bulle en bas à droite : « processing » et « Je prépare ton fichier… » ; en cas d'échec, « Téléchargement impossible pour l'instant ». Le nom du fichier vient du serveur. Vérifié avec l'export CSV d'un mois ORP sur un serveur ralenti.
