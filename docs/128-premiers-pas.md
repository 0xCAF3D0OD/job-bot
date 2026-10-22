# 128 — Les premiers pas : une seule prochaine action (version 1.1.0)

> Statut : **validé** le 2026-10-22 (« oui pour tout »). Lu ainsi : les cinq étapes et leurs mots (1), les anciens guides retirés pour tout le monde (2), **la démo laissée « en cours de route »**, les premiers pas se testent sur un compte neuf (3, le premier choix), le chiffre dans Réglages › Plateforme (4). Dis-le si une de ces lectures est fausse.
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

## Écarts (1.1.0)

- **Règles relues avant de construire** ; vérifiées sur captures à 1440 et 390 px d'un compte neuf (une base jetable, `jobbot_premiers`), à chaque étape : rien de fait, alertes créées sans offre, offres du jour, préparer, marquer envoyée, la réussite ; puis Offres, Suivi, Rendez-vous et Bilan vides, et la carte de Réglages › Plateforme.
- **« Tes alertes sont prêtes »** devient **« Alertes prêtes »** : un titre ne commence pas par un possessif (docs/interface.md, Titres). La ligne dessous reste « Les premières offres arrivent d'ici un ou deux jours. ».
- **L'étape 5** ouvre la préparation sur ③ Postuler, où se trouve « Marquer comme envoyée » (le cadrage disait ④).
- **La carte de réussite** : le serveur ne peut pas l'annoncer « une seule fois » à la lecture, car d'autres parties de la page lisent aussi Aujourd'hui (la pastille de la barre d'onglets) et la consommaient. L'interface dit au serveur qu'elle l'a montrée (`PUT /api/first-steps`, `celebrated`) ; un compte qui avait déjà tout fait avant la 1.1.0 ne la voit jamais.
- **La démo est en lecture seule** : elle lit les étapes sans rien garder ; son compte a tout fait, la carte n'y apparaît pas (vérifié : sans cela, Aujourd'hui de la démo tombait en erreur).
- **Le menu du compte** perd « Comment ça marche » (il réaffichait les anciens guides). « Masquer » sur la carte est définitif, avec « Annuler » pendant 6 secondes.
- **Le Bilan vide** ne montre plus les tuiles à zéro ni la jauge ORP vide (quand rien n'a jamais été envoyé) ; **le Suivi vide** montre son message en vue calendrier comme en liste.
- **Les réglages de l'ancienne liste** (coordonnées, objectif ORP) étaient déjà rappelés au moment où ils servent : « En-tête incomplet » dans le CV et la lettre, « Objectif ORP à saisir » dans le Suivi. Le lien « complète tes coordonnées » menait aux Réglages ; il mène maintenant au Profil › Coordonnées, où elles sont.
- **L'espace avant le point** après un lien : le lint laisse maintenant `<RouterLink>` sur une ligne, comme `<a>` ; les six liens concernés sont corrigés.
- **L'assistant** : consigne `assistant-v16` (la carte « Premiers pas », plus les anciens guides ; le menu principal à jour).
- **Le chiffre** : une fonction de la base (`first_steps_progress`, migration 0070) qui ne répond qu'à l'exploitant, des nombres et des dates seulement.
- **Vu en passant, non corrigé** (hors des pages touchées, visible seulement hors démo) : dans les Réglages de l'exploitant, une aide de plus de 20 mots (sauvegardes non réglées), des « cadres dans un cadre », un contraste et un lien sans soulignement ; dans Formations et Actualités, un attribut ARIA refusé sur le filtre « domaine ». Les audits ne les voient pas sur la démo.

## Vérifié (1.1.0)

- Tests backend : les cinq étapes cochées d'après les données, jamais en arrière, l'offre à préparer, la réussite jusqu'à ce que l'interface la confirme, un compte d'avant la 1.1.0 sans carte ni réussite, la démo en lecture seule, le chiffre de l'équipe (et rien pour un compte invité, même en appelant la fonction). 632 tests, ruff, mypy.
- Tests de l'interface : la carte à chaque étape (titre, bouton, adresse), l'attente des offres, Aujourd'hui allégé, « Masquer » et « Annuler », la réussite confirmée ; les écrans vides des Offres, du Suivi, du Rendez-vous et du Bilan ; la carte de la Plateforme. 449 tests, lint, vue-tsc.
- Les trois audits sur la démo à zéro.

## Écarts (1.1.1)

Les audits passés sur un vrai compte (l'exploitant, sans connexion, une base jetable), et plus seulement sur la démo : ils voient les Réglages de l'exploitant et les écrans d'un compte neuf.

- **Les titres de la carte « Premiers pas » deviennent des noms** (docs/interface.md, Titres 2), le verbe reste sur le bouton : « Critères et CV », « Alertes sur les sites d'emploi », « Première offre gardée », « Lettre et CV pour l'offre », « Candidature envoyée » (sa ligne : « Marque-la comme envoyée : elle compte pour ton mois ORP. »). Les mots validés au §1 étaient des verbes ; la règle des titres l'emporte, comme en docs/126. L'assistant passe à `assistant-v17`.
- **Les cinq points** se lisent en une phrase (« 2 étapes faites sur 5 ») au lieu d'un libellé caché par point, que l'audit voyait déborder.
- **Autres titres** : « Que veux-tu recevoir ? » (l'assistant des alertes) devient « Offres à recevoir » ; « Langues que tu ne parles pas » (Profil) devient « Langues non parlées ».
- **Les aides du Profil** (types d'offres exclus, langues) : une ligne visible, les mots-clés au survol (docs/118 §1).
- **Réglages de l'exploitant** : la liste des profils d'essai a des filets entre les lignes au lieu d'un cadre par ligne (un seul cadre par bloc) ; un site ou un profil en pause a son nom grisé au lieu d'une ligne à 60 % d'opacité, qui rendait l'indication illisible ; les liens des sites suggérés sont soulignés ; « Sauvegardes non réglées » tient en une ligne.
- **Formations et Actualités** : le bouton « Domaine » (un choix radio) perd `aria-expanded`, refusé sur ce rôle ; il désigne le champ qu'il ouvre par `aria-controls`.
- **L'audit au clavier** ne demande plus d'atteindre la première offre quand il n'y en a pas : il vérifie alors que l'écran vide le dit.

## Vérifié (1.1.1)

- Les trois audits à zéro sur la démo **et** sur un compte neuf de l'exploitant.
- Captures à 1440 et 390 px : la carte « Premiers pas », les profils d'essai, les sites suivis, les langues du Profil.
- Tests : 449 de l'interface, lint, vue-tsc ; 632 backend (dont la consigne de l'assistant), ruff, mypy.
