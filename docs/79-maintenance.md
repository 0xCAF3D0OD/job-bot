# 79 — La page de maintenance (version 0.65.0)

> Statut : **à valider**.
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
