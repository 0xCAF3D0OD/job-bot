# 128 — Les premiers pas : une seule prochaine action (version 1.1.0)

> Statut : **à valider**.
> Origine : un retour remonté le 22 octobre 2026, « quelqu'un qui arrive sur la plateforme est un peu perdu, il y a beaucoup d'information », et ta demande « écris le cadrage 128 ».

## Le constat

L'accueil en questions (`/bienvenue`, docs/66 et docs/121) marche : métier, lieux, taux, ORP, CV. Il se termine sur « Créer mes alertes ». C'est après que ça se gâte :

- **Aujourd'hui montre tout d'un coup** : la phrase du jour, les bandeaux, « À faire » (offres du jour, à préparer, relances), le mois ORP, le rythme, puis les guides.
- **Les deux guides sont tout en bas et repliés** : « Comment ça marche » (5 étapes) et « Pour bien démarrer » (6 étapes). Ils se recoupent : 11 lignes à lire, dont deux « pas encore disponible sur cette plateforme ».
- **Aucun ne dit quoi faire maintenant.** Ce sont des listes de rubriques, pas une action.
- **Un nouveau compte n'a pas d'offre** : elles arrivent par les alertes, un ou deux jours après leur création. D'ici là, Aujourd'hui est vide, sans expliquer pourquoi.
- **Les écrans vides** des pages (Offres, Suivi, Bilan, Rendez-vous) devaient être revus un par un (docs/126 §5) ; ce n'est pas encore fait.

## La phrase qui guide

**La première semaine, Aujourd'hui dit une seule chose à faire, et pourquoi.** Le reste attend d'avoir quelque chose à montrer.

## 1. La carte « Premiers pas »

Elle remplace, en haut d'Aujourd'hui, l'action sous la phrase du jour (docs/interface.md, Structure 17 : une seule action). Elle disparaît d'elle-même à la fin.

**Sa forme** : une carte de toute la largeur. À gauche, le visage du 1 en 56 px. Au milieu, le titre de l'étape (une action), une ligne qui dit pourquoi, le bouton. À droite, en gris, « 2 sur 5 ». Sous la carte, cinq points (pleins pour les étapes faites), comme ceux de l'accueil.

**Les cinq étapes**, dans l'ordre, chacune cochée par le serveur à partir de ce qui existe déjà :

| # | Le titre | La ligne | Le bouton | Faite quand |
|---|---|---|---|---|
| 1 | Dis ce que tu cherches | jobA1 trie les offres avec tes critères. | Compléter mon profil | des critères et un CV (l'accueil le fait ; déjà cochée pour presque tous) |
| 2 | Crée tes alertes | Les offres arrivent ici, notées pour toi. | Créer mes alertes | une alerte reconnue, **ou** une offre ajoutée à la main |
| 3 | Garde ta première offre | Celles qui te vont passent en « À préparer ». | Voir les offres du jour | une offre « À préparer » ou envoyée |
| 4 | Prépare ta candidature | Lettre et CV adaptés à l'offre, en quelques minutes. | Préparer | une lettre ou un CV rédigé pour une offre |
| 5 | Marque-la comme envoyée | Elle compte pour ton mois ORP. | Ouvrir la préparation | une candidature au Suivi |

- **L'étape 1 déjà cochée** montre qu'on a avancé : « 1 sur 5 » dès l'arrivée.
- **Une étape ne revient jamais en arrière** : une offre gardée puis écartée laisse l'étape 3 faite.
- **Le bouton va droit au bon endroit** : l'étape 3 descend sur l'offre du jour ; les étapes 4 et 5 ouvrent la préparation de l'offre gardée la plus récente (onglet ① puis ④).
- **La dernière étape faite** : le visage fait le clin d'œil, « Première candidature notée. Elle compte pour ton mois ORP. » (la carte de réussite de la 0.95.0), puis la carte disparaît pour de bon.
- **« Masquer »** sur la ligne du titre (Structure 9), pour qui connaît déjà : la carte ne revient plus. Pas de visite guidée en bulles par-dessus l'écran : on la passe sans lire, et elle cache ce qu'elle explique.

**L'attente des offres** (étape 2 faite, aucune offre encore) : la carte dit « Tes alertes sont prêtes. Les premières offres arrivent d'ici un ou deux jours. », le visage en attente (le geste « waiting » de la 0.94.0), et le bouton « Ajouter une offre que j'ai vue » (`/candidatures/offres?ajouter=1`).

## 2. Un Aujourd'hui allégé pendant les premiers pas

Tant que la carte est là :

- **Disparaissent** : « Comment ça marche » et « Pour bien démarrer » (pour tout le monde, définitivement : la carte les remplace) ; le rythme de la semaine (rien à mesurer encore) ; les onglets vides de « À faire ».
- **Restent** : la phrase du jour, les bandeaux (un entretien, une relance restent prioritaires), les offres du jour dès qu'il y en a, et **le mois ORP**, compact, comme le demande le garde-fou de docs/126 (le cycle ORP visible en 5 secondes).
- Les réglages encore utiles de l'ancienne liste (l'objectif ORP, les coordonnées, les notifications) ne sont pas perdus : l'accueil les demande, le Profil et les Réglages les montrent ; un bandeau les rappelle quand ils manquent au moment où ils servent (les coordonnées avant le premier PDF, l'objectif avant la fin du mois). Les étapes « pas encore disponible » disparaissent.

## 3. Des écrans vides qui disent quoi faire

Pas de ligne d'explication sous les titres (la règle Titres 1 reste). À la place, la première fois, une page vide l'est pour une raison : elle le dit, avec l'action qui la remplit (Structure 13, le visage en 120 px).

| Page | La phrase | L'action |
|---|---|---|
| Candidatures › Offres | Pas encore d'offre. Elles arrivent par tes alertes. | Créer mes alertes · Ajouter une offre |
| Candidatures › Suivi | Pas encore de candidature. Une candidature envoyée s'ajoute ici. | Voir les offres |
| Candidatures › Rendez-vous | Ta feuille ORP se remplit avec tes candidatures. | Voir les offres |
| Bilan › Résultats | Le bilan commence après tes premières candidatures. | Voir les offres |

Je les vérifie aussi sur la démo (docs/126 §5) et sur un compte neuf.

## 4. Savoir si ça marche

- **Le chiffre** : la part des comptes créés depuis 30 jours qui ont marqué **une première candidature dans les 7 jours**, et combien se sont arrêtés à chaque étape (« 3 à l'étape 2 »).
- **Où** : dans Réglages › Plateforme, pour l'équipe jobA1 seulement. **Des nombres, rien d'autre** : ni nom, ni offre, ni contenu ; le calcul passe par le rôle du serveur, pas par les données d'une personne.
- **Le test avec 5 personnes** (docs/127) ajoute une tâche de départ : « Tu viens de créer ton compte : que fais-tu en premier ? », sur un compte neuf.

## Garde-fous

- **Les comptes existants** : ceux qui ont déjà une candidature ne voient jamais la carte ; les anciens guides disparaissent pour eux aussi.
- **Le cycle ORP reste visible en 5 secondes** sur Aujourd'hui.
- **Rien n'est nouveau dans la base** sauf « premiers pas masqués » (un réglage, comme les guides d'aujourd'hui) ; les étapes se lisent dans ce qui existe.
- Les écrans suivent `docs/interface.md` ; les trois audits à zéro ; captures à 1440 et 390 px d'un compte neuf à chaque étape.

## Livraison proposée

- **1.1.0** : la carte et ses cinq étapes, l'attente des offres, Aujourd'hui allégé, les anciens guides retirés (§1, §2), les écrans vides (§3), le chiffre (§4). Avec, en passant, l'espace avant le point après un lien (vue en 1.0.1).

## Les questions

1. **Les cinq étapes** et leurs mots (§1) : d'accord, ou une étape en plus ou en moins (l'objectif ORP, par exemple) ?
2. **Les anciens guides** : les retirer pour tout le monde, d'accord ?
3. **La démo** : son compte a déjà tout fait, la carte n'y apparaît donc pas. La laisser ainsi (une démo « en cours de route ») et tester les premiers pas sur un compte neuf, ou montrer la démo à l'étape 3 ?
4. **Le chiffre** (§4) dans Réglages › Plateforme : d'accord ?
