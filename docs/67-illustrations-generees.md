# 67 — Les illustrations de jobA1 : une famille à nous, générée (version 0.55.0)

> Statut : **validé** le 2026-10-16 (option 3 pour le sombre, les dessins unDraw gardés en réserve), livré.
> Demande du 2026-10-16 : « est-ce que ces images seraient plus adéquates ? » (17 images générées, `illustrations_webp 2`), puis « ce sont des images générées, écris le cadrage ». Kevin les a fait générer pour jobA1 ; il en a les droits d'usage, elles peuvent aller dans le dépôt public.

## 1. Pourquoi changer

- **Plus humaines** : de vraies personnes, variées (âges, fauteuil roulant, voile, prothèse), dans des scènes calmes. Ça dit « Less searching. More living. » mieux que les personnages unDraw, plus froids et plus « modèle ».
- **Faites pour nos pages** : Aujourd'hui, Alertes, Offres, Suivi, Bilan, Formations, Actualités, Preuves ORP… Il y a enfin une carte avec des repères pour « Où veux-tu travailler ? ».
- **Un seul style partout** : on remplace **toutes** les illustrations unDraw, pas seulement celles de l'accueil, pour ne jamais avoir deux familles côte à côte.

## 2. Où va chaque image

Les endroits restent ceux de `docs/62` et de l'accueil (`docs/66`) : on ne remet pas d'image dans les Réglages, le Profil ou les formulaires.

**Pages qui chargent (le voile de transition)**

| Page | Avant (unDraw) | Après |
|---|---|---|
| Aujourd'hui | morning-plans | **01 Dashboard** (le calendrier, la jauge) |
| Offres | mailbox | **02 Candidatures Offres** (les profils qui défilent) |
| Suivi | done | **03 Candidatures Suivi** (l'avion en papier, les jours cochés) |
| Bilan | stepping-up | **06 Bilan** (l'entonnoir) |
| Alertes | message-sent | **02 Alertes** (la carte et le tri des e-mails) |
| Actualités | absorbed | **Actualités A** (le cortège vers la porte ouverte) |
| Formations | certification | **06 Formations** (les livres, le parcours et la médaille) |

**États vides**

| Endroit | Avant | Après |
|---|---|---|
| Offres sans résultat | mailbox | **03 Offres Aucune Offre** (le bac vide, la loupe) |
| Suivi d'un mois vide | done | **03 Candidatures Suivi** |
| Bilan sans candidature | stepping-up | **06 Bilan** |
| Actualités vides | absorbed | **Actualités C** (la vidéo, le chat) |
| Page introuvable | page-eaten | **13 Paramètres** (la lecture tranquille : « rien à voir ici ») |

**Connexion, alertes, moments**

| Endroit | Avant | Après |
|---|---|---|
| Connexion et liens d'accès (moitié gauche) | login | **00 Accueil Bannière** (les e-mails triés, la porte qui s'ouvre) |
| Assistant des alertes, étapes 1 · 2 · 3 | mailbox · message-sent · done | **02 Alertes** · **00 Accueil Bannière** · **03 Candidatures Suivi** |
| Carte « candidature envoyée » | message-sent | **03 Candidatures Suivi** |
| Carte « preuves remises » | done | **04 Preuves ORP** (le classeur, la coche) |
| L'Engagement | handshake-deal | **Actualités A** (on passe la porte) |

**L'accueil (docs/66)**

| Écran | Avant | Après |
|---|---|---|
| Ce qui t'amène | morning-plans | **15 Réseau** (celui qui accueille) |
| Ton métier | stepping-up | **06 Formations** |
| Où travailler | mailbox | **07 Profil** (la carte, la maison, les curseurs) |
| Taux d'activité | tight-deadline | **01 Dashboard** |
| Objectif ORP | certification | **04 Preuves ORP** |
| Date de remise | — | toujours rien : le calendrier occupe l'écran |
| Ton CV | my-resume | **02 Candidatures Offres** |
| Notifications | lock-screen-notifications | **13 Paramètres** (l'interrupteur) |
| C'est prêt | handshake-deal | **03 Candidatures Suivi** |
| La suite (le personnage) | detailed-answer | **12 Messagerie** : sa bulle vide est remplacée par la nôtre, posée au même endroit |

**En réserve** : 14 Agenda (pour les entretiens, plus tard) et Actualités B (économie).

## 3. Le style et ses règles

- **Taille** : celles d'aujourd'hui (220 px au plus, 140 sur téléphone ; carte des moments 170 ; Engagement 380 ; connexion 340). Les images portraits ou carrées gardent une hauteur maximale de 180 px, pour que toutes paraissent de la même taille.
- **Sans cadre ni fond** : la version transparente, posée sur la page.
- **Mode sombre** : ce sont des images, leurs couleurs ne suivent pas le thème. Pour que les blancs (sols, calendriers, cadres) ne fassent pas des taches claires, elles sont légèrement assombries en sombre (luminosité à 85 %). Je te montre les captures avant de choisir le réglage.
- **Une entrée, pas d'animation dessinée** : l'unDraw animait ses formes ; ici l'image apparaît en glissant un peu vers le haut et en fondu (500 ms, une seule fois), comme les autres entrées (`docs/59`). Rien si « réduire les animations ».
- **Décoratives** pour les lecteurs d'écran, comme aujourd'hui.

## 4. Le poids

- Les originaux font 1000 px de large (25 à 65 Ko). On les affiche à 220 px : le dépôt garde une version de **480 px** (deux fois la taille affichée, pour les écrans nets), **20 à 30 Ko** chacune. Connexion et Engagement, affichées en grand : une version de **800 px** en plus (environ 40 Ko).
- Chaque image n'est chargée que quand elle s'affiche, comme aujourd'hui. En tout, le dépôt passe d'environ 120 Ko de dessins unDraw à environ 500 Ko d'images ; une page en charge une ou deux.

## 5. Côté technique

- `frontend/scripts/illustrations.mjs` est réécrit : il prend les originaux de ton dossier, les réduit à 480 et 800 px en WebP et les range dans `src/assets/illustrations/` sous un nom qui dit ce qu'elles montrent (`tableau-de-bord.webp`, `alertes-carte.webp`…). Il a besoin de `sharp`, ajouté pour le développement seulement.
- Le composant `Illustration` garde son nom et ses usages ; il pose une `<img>` (`srcset` 480/800, `loading="lazy"`, `alt=""`) au lieu d'insérer le dessin. Les règles de couleur `.illu [fill=…]` sont retirées ; les dessins unDraw passent en réserve (voir les écarts).
- `docs/interface.md` § Illustrations est mis à jour : la famille (images générées pour jobA1), le mode sombre, l'entrée.

## 6. Livraison

Une PR (**0.55.0**), après la fusion de la 0.54.0. Captures avant/après de chaque endroit, sur ordinateur et téléphone, en clair et en sombre.

## Points à valider

1. **Tout remplacer**, pas seulement l'accueil, pour un seul style (§1).
2. **La table des emplacements** (§2), en particulier : la page introuvable (13 Paramètres), l'Engagement (Actualités A), et 12 Messagerie pour le personnage qui parle.
3. **Le mode sombre** : légèrement assombries, réglage choisi sur captures (§3).
4. **L'entrée en fondu** à la place des animations unDraw (§3).
5. **Le poids** : 480 px (800 px pour les grandes), ~500 Ko au total dans le dépôt (§4).
6. **Une PR**, après la 0.54.0 (§6).

## Écarts avec la livraison

- **Le sombre** : Kevin fera générer une série sombre des mêmes images. `scripts/illustrations.mjs` la prend en second dossier (mêmes noms de fichiers) et l'écrit à côté (`<nom>-sombre-480.webp`) ; la plateforme la choisit d'elle-même en sombre (`<picture>`). En attendant, ou si elle ne convient pas, l'image claire est assombrie à 85 %.
- **La réserve** : les 14 dessins unDraw et leur script sont gardés dans `frontend/reserve/illustrations-undraw/` et `scripts/illustrations-undraw.mjs`, hors de l'application (rien ne les charge), pour revenir en arrière si besoin.
- **Le poids** : 17 fichiers, environ 510 Ko au total (15 à 40 Ko en 480 px, 45 et 50 Ko pour les deux en 800 px). Les marges transparentes des originaux sont rognées, pour que chaque image remplisse sa place ; l'accueil les montre un peu plus grandes (220 px, 170 sur téléphone ; le personnage 280 px), et la bannière de connexion fait 280 px sur téléphone.
- **Le personnage qui parle** : le script efface la bulle vide de *12 Messagerie* (le haut devenu vide part avec les marges) ; la pointe de notre bulle vise sa tête.
- **Les noms** disent ce que montre l'image : tableau-de-bord, offres-profils, suivi-envoi, bilan, alertes-carte, porte-ouverte, formations, aucune-offre, actualites-video, lecture-calme, emails-tries, preuves-orp, accueil-reseau, lieux-carte, messager. `sharp` est ajouté pour le développement seulement.
- **Complément (même jour, « les images plus grandes ; sans connexion, pas les Actualités mais les informations sur la plateforme »)** :
  - **Plus grandes partout** : pages vides et transitions 300 px (200 sur téléphone), carte des moments 220 (170), Engagement 440 (260), connexion 440 (320), accueil 260 (200), le personnage qui parle 320 (240). Chaque image a donc aussi une version de 800 px (le navigateur prend la plus petite qui reste nette) : 1,2 Mo dans le dépôt, une ou deux images de 30 à 60 Ko par page.
  - **Sans connexion**, le menu propose **« La plateforme »** (`/la-plateforme`) au lieu des Actualités : la phrase de jobA1, à quoi il sert, les six étapes illustrées (alertes, offres triées, candidature préparée, suivi, preuves ORP, actualités et formations), ce qu'il advient des données (lien vers `/tes-donnees`), et « Se connecter » (l'accès se fait sur invitation).
  - **Les Actualités demandent maintenant la connexion** (elles étaient ouvertes à tous depuis `docs/18`). La page de connexion ne le mentionne plus : « Tes offres, tes candidatures et tes preuves ORP, au même endroit. »
- **Complément (même jour, « trop simple : comme Duolingo, un tracé sur plusieurs scènes, une partie de la plateforme derrière, une bulle explicative »)** : « La plateforme » devient un parcours.
  - **Un chemin** pointillé relie six pastilles numérotées puis une étoile ; il se colore en violet à mesure qu'on descend, et les pastilles dépassées se remplissent. Sur ordinateur il serpente d'un côté à l'autre ; sur téléphone il descend dans une colonne à gauche, comme une frise.
  - **Chaque scène** : un bout de la plateforme en arrière-plan, légèrement incliné (alertes, offres notées, lettre préparée, calendrier du suivi, preuves ORP, actualités), dessiné en HTML aux couleurs du thème avec des exemples inventés, jamais une capture ; le personnage devant ; à côté, sa **bulle** avec le titre et l'explication. Les scènes alternent de côté et entrent une fois, en fondu, quand elles arrivent à l'écran.
  - **L'arrivée** (l'étoile) : « Tes données restent à toi » et « Se connecter ».
  - « Réduire les animations » : tout est affiché d'emblée, le chemin ne s'anime pas.
- **Complément 0.55.1 (après la fusion, « garder les animations précédentes pour le chargement juste avant d'accéder à Aujourd'hui, Formations… »)** : la transition des pages qui chargent reprend les dessins unDraw animés d'avant, aux couleurs du thème : Aujourd'hui (morning-plans), Offres (mailbox), Suivi (done), Bilan (stepping-up), Alertes (message-sent), Actualités (absorbed), Formations (certification). Leur animation fait patienter, ce que les images fixes ne font pas. Ces sept dessins reviennent dans l'application (`src/assets/dessins/`, composant `LoadingDrawing`) ; les autres restent en réserve. Partout ailleurs, les images générées.
- **Complément 0.55.2 (« utiliser cette image pour la page de connexion, rognée en rond de manière souple ; qu'on voie bien le garçon et la fille, assez grand pour comprendre l'image »)** : une nouvelle image générée, la ville et le bureau reliés par les e-mails triés (`Connexion_Ville.webp`, dans le dossier des images transparentes). Le script en garde le cadre autour du garçon sur son banc et de la fille qui arrive au bureau, en rectangle aux coins très arrondis dont les bords s'estompent dans le fond (le milieu reste net), en 480, 800 et 1200 px (21, 44 et 83 Ko). La moitié gauche de la connexion s'élargit (environ 57 %) et l'image en prend toute la largeur ; sur téléphone, toute la largeur de l'écran. Les liens d'accès (invitation, réinitialisation) ont la même. *00 Accueil Bannière* reste à l'étape 2 de l'assistant des alertes.
