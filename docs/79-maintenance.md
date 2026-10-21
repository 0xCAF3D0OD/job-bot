# 79 — La page de maintenance (version 0.65.0)

> Statut : **validé** le 2026-10-18.
> Origine : ta demande du 2026-10-18 : quand tu mets la plateforme à jour (`git pull`, puis redémarrage), les personnes qui l'utilisent à ce moment-là voient des erreurs. Elles devraient voir à la place une page claire qui dit que la plateforme revient tout de suite.

## 1. En clair

Pendant une mise à jour, la plateforme passe par trois moments où elle ne répond pas normalement :

| Moment | Ce qui se passe aujourd'hui | Ce qu'on verra |
|---|---|---|
| **Le serveur redémarre** (quelques secondes) | messages « API injoignable » ici et là, boutons sans effet | la page de maintenance, qui revient toute seule |
| **Le code est nouveau, mais la base pas encore mise à jour** (entre `git pull` et `jobbot migrate`) | erreurs au hasard selon les pages | la page de maintenance |
| **Tu annonces une maintenance** (pour une opération plus longue) | rien de prévu | la page de maintenance, avec ton message si tu en mets un |

La page dit simplement : « jobA1 se met à jour, ça revient dans un instant ». Elle vérifie toute seule toutes les 10 secondes, et **la personne retrouve sa page exactement où elle était** dès que la plateforme répond. Ce qu'elle était en train d'écrire (lettre, réponse d'entraînement…) n'est pas perdu : la page de maintenance se pose par-dessus, sans recharger.

## 2. Comment

**Côté interface** : un seul endroit voit toutes les réponses du serveur (`api/client.ts`). Quand le serveur est injoignable, ou répond « en maintenance » (503), la page de maintenance s'affiche par-dessus tout. Elle sonde le serveur toutes les 10 secondes, puis disparaît.

**Côté serveur** :
- **Base pas à jour** : l'API sait déjà le voir (`/readyz` le dit). Tant que la base n'est pas à la dernière migration, toutes les routes répondent 503 « en maintenance », au lieu de se tromper à moitié.
- **Maintenance annoncée** : deux commandes, `jobbot maintenance on "message facultatif"` et `jobbot maintenance off`. Entre les deux, l'API répond 503 « en maintenance » à tout le monde, sauf à toi, l'exploitant : tu peux vérifier la plateforme avant de la rouvrir. Le réglage est gardé dans la base : il survit à un redémarrage.

**Pour la démo en ligne** : quand l'API ne répond pas du tout (pendant `docker compose up --build`), Caddy sert lui-même une page de maintenance statique, au même style, au lieu d'une page d'erreur 502.

**Une commande pour mettre à jour** : `make update` fait tout dans l'ordre :
1. annonce la maintenance ;
2. `git pull` ;
3. installe les dépendances ;
4. `jobbot migrate` ;
5. lève la maintenance.

Il reste ensuite à redémarrer `make dev`, ce que la commande te rappelle. La page reste affichée pendant tout ce temps.

## 3. Ce qu'on ne fait pas

- **Pas de bandeau d'annonce à l'avance** (« maintenance ce soir à 20 h ») : avec quelques invités, un message direct suffit.
- **Pas de mise à jour sans aucune coupure** (deux serveurs en parallèle) : trop lourd pour une plateforme sur un seul ordinateur.
- **Ta plateforme derrière le tunnel** : si **tout** est arrêté, y compris l'interface, c'est le tunnel qui affiche sa propre erreur ; on ne peut pas la remplacer depuis jobA1. Avec `make dev`, l'interface reste en marche pendant que l'API redémarre : c'est le cas courant, et il est couvert.

## 4. Livraison

Une PR, **0.65.0**, après les PR de sécurité 0.64.1 et 0.64.2. Elle peut aussi passer avant, si tu préfères l'avoir tout de suite. Pas de migration : le réglage va dans `platform_settings`, qui existe déjà.

Ce qui sera vérifié :
- un test pour chaque cas (serveur injoignable, base pas à jour, maintenance annoncée, l'exploitant qui passe quand même) ;
- une saisie en cours qui survit à la maintenance ;
- dans Docker, la page de Caddy pendant un redémarrage de la démo ;
- des captures, sur ordinateur et sur téléphone.

## Points à valider

1. **La page par-dessus tout**, qui revient toute seule et garde la page en cours (§1, §2).
2. **Les trois cas** : serveur qui redémarre, base pas à jour, maintenance annoncée par `jobbot maintenance on/off` (§2).
3. **L'exploitant passe pendant une maintenance annoncée** (§2).
4. **`make update`** pour la mise à jour en une commande (§2).
5. **La page statique de Caddy** pour la démo en ligne (§2).
6. **0.65.0 après la sécurité**, ou avant si tu préfères (§4).

## Écarts avec le cadrage

- **Pour la démo, pas de page statique de Caddy** : une réponse « en maintenance » (503, JSON), que l'interface reconnaît pour montrer sa propre page d'attente. L'interface elle-même est servie par Caddy, qui ne s'arrête pas quand l'API redémarre. Une page à part ne se serait vue que si Caddy redémarrait aussi ; dans ce cas, c'est le navigateur qui affiche son erreur, quelques secondes, et on ne peut pas la remplacer.
- **Le texte de la page** reste vrai dans les deux cas, une mise à jour ou une connexion coupée : « jobA1 revient dans un instant », puis « La plateforme se met à jour, ou la connexion est coupée », ou ton message s'il y en a un. Une coupure de ton propre réseau ressemble en effet, vue du navigateur, à un serveur qui redémarre.
- **Un 503 d'une route** (IA ou registre momentanément indisponibles) reste une erreur de la page : seul un 503 marqué « maintenance », ou un 502 à 504 de l'intermédiaire, montre la page d'attente. Une requête annulée par la page non plus.
- **Le rappel pour l'exploitant** se lit au chargement de la page : après `jobbot maintenance off`, il disparaît au prochain rechargement.
- **`make update`** lève la maintenance avant que tu redémarres `make dev`. Si la base a changé, l'ancienne API voit une base plus récente que son code et répond « en maintenance » d'elle-même jusqu'au redémarrage. Sinon, rien ne change pour les autres comptes. La première fois (depuis une version d'avant 0.65), la commande `jobbot maintenance` n'existe pas encore : l'étape le dit et continue.
- **Une base injoignable n'est pas une maintenance** : l'état de la plateforme l'explique, comme avant.
- **Vérifié** :
  - 497 tests serveur, dont 3 nouveaux (`test_maintenance.py`), et 293 tests de l'interface, dont 3 nouveaux :
    - détection par le client ;
    - page posée par-dessus et rendue avec la saisie intacte ;
    - rappel pour l'exploitant.
  - Dans la démo Docker, l'API arrêtée pendant une visite :
    - la page d'attente s'affiche, sur ordinateur et sur téléphone ;
    - elle disparaît 6 à 7 secondes après le retour de l'API.
  - Sur une instance de brouillon avec `jobbot maintenance on` : l'exploitant passe et voit le rappel.

## 0.82.1 — La page d'attente refaite

Ton retour du 2026-10-21, capture sur téléphone à l'appui : « j'aime pas trop la page de maintenance, il faut la refaire, il n'y a pas de structure, sur téléphone et ordinateur ».

- **Ce qui n'allait pas** : un titre et deux phrases posés au milieu d'une page blanche, sans en-tête ; un grand vide au-dessus, où **le dessin manquait** : il se téléchargeait à la demande, justement quand le serveur ne répondait plus.
- **L'en-tête de jobA1** (le logo et le nom), comme sur les autres pages : on sait où l'on est.
- **Une carte**, au centre sur ordinateur (36 rem), en haut sur téléphone :
  - le dessin de la maintenance, **dans l'application dès le départ** (il ne dépend plus du réseau) ;
  - le titre « jobA1 revient dans un instant » et la raison (annoncée par l'exploitant, ou « la plateforme se met à jour, ou la connexion est coupée ») ;
  - **une bande grise** : un point qui pulse, **« Nouvel essai dans 7 secondes »** (compte à rebours), et **« Réessayer maintenant »**, qui sonde tout de suite ;
  - la note qui rassure, en gris : « Ce que tu écrivais n'est pas perdu : tout reprend là où tu en étais. »
- **Sur téléphone**, le bouton prend toute la largeur (3 rem de haut), sous le compte à rebours.
- **Rien d'autre ne change** : la page se pose par-dessus sans recharger, le reste est inerte, le curseur revient où il était ; avec « réduire les animations », le point ne pulse pas.
- **Vérifié** : tests (le compte à rebours, « Réessayer maintenant » qui sonde aussitôt et ferme la page si l'API répond, le dessin présent sans téléchargement, l'en-tête, la note) ; captures Playwright à 414 et 1280 px, et la bande d'état mesurée dans la carte à 414, 900 et 1280 px.
