# 129 — « À faire » rangé : une carte, un rôle (version 1.2.0)

> Statut : **validé** le 2026-10-22 (« oui pour tout »). Lu ainsi : les deux rangées (1), 3 lignes au plus (2), **la note** dans la ligne d'une offre à préparer (3 : la date à laquelle elle a été gardée n'est pas enregistrée, il faudrait une migration). Dis-le si une de ces lectures est fausse.
> Origine : ta remarque du 22 octobre 2026 sur Aujourd'hui, « ce n'est pas très structuré, surtout la partie à faire, c'est pas bien rangé », avec une capture à 1440 px.

## Le constat

Sur ta capture, la carte « À faire » mêle trois choses, chacune avec sa propre forme :

1. **L'offre du jour** : une grande fiche avec « Écarter » et « Garder », et « 1 sur 5 » qui flotte en haut à droite, sans titre auquel se rattacher.
2. **Les offres à préparer**, cachées derrière un sélecteur « Du jour / À préparer », juste à côté du libellé « Offres du jour » : le même mot deux fois.
3. **Les relances**, une liste en dessous, sous un petit libellé en capitales.

Et :

- **Les écarts sont irréguliers** : environ 70 px entre « À faire » et « Offres du jour », 60 px avant l'offre, un grand vide avant « Toutes les relances (12) ». La règle demande 0,75 rem entre un titre et son contenu (docs/interface.md, Structure 2).
- **Les lignes de relance n'ont pas de colonnes** : un long intitulé (« Internship – Software Engineer – Application Monitoring & Observability ») repousse la date, et « Relancer » ne tombe pas au même endroit d'une ligne à l'autre (docs/43 : colonnes d'action de largeur fixe).
- **« Mois ORP » est étiré** à la hauteur de « À faire » et garde un grand vide en bas, sans rien d'utile dedans (Structure 4).

## La phrase qui guide

**Sur Aujourd'hui, chaque carte répond à une seule question, et toutes ont la même forme.**

## 1. Deux rangées de deux cartes

```
┌ Offres du jour ───── 1 sur 5 ┐  ┌ Mois ORP ─────────── 🙂 ┐
│ [logo] DevOps & Reliability… │  │ 7 / 13 · On rattrape     │
│ Rocken® · Zurich · À creuser │  │ ▬▬▬▬▬▬▬▭▭▭▭▭▭            │
│ [ Écarter ]     [ Garder ]   │  │ Cette semaine    5 / 6   │
└──────────────────────────────┘  └──────────────────────────┘
┌ À préparer · 5 ─── Tout voir ┐  ┌ À relancer · 12 ─ Tout voir ┐
│ [R] DevOps & Reliab… Préparer│  │ [L] Lombard Odier… Relancer │
│ [A] Ingénieur systè… Préparer│  │ [S] Swisscom AG    Relancer │
│ [V] Gestionnaire d…  Préparer│  │ [U] UBS            Relancer │
└──────────────────────────────┘  └─────────────────────────────┘
```

- **Rangée 1** : « Offres du jour » (3/5) et « Mois ORP » (2/5), comme aujourd'hui. Les deux ont un contenu de hauteur proche : la carte du mois ne s'étire plus dans le vide.
- **Rangée 2** : « À préparer » et « À relancer », moitié-moitié, la même forme.
- **La carte « À faire » disparaît**, et avec elle son sélecteur « Du jour / À préparer » et ses deux libellés en capitales.
- **Une carte sans rien dedans ne s'affiche pas** ; sa voisine prend toute la largeur (Structure 1 : une carte seule prend toute la largeur). Exemple : aucune relance, « À préparer » occupe la rangée.
- **Sur téléphone**, les cartes s'empilent dans cet ordre : Offres du jour, Mois ORP, À préparer, À relancer.

## 2. Le titre porte le compte et le lien

- **« Offres du jour »**, et « 1 sur 5 » en gris à droite, sur la ligne du titre (il quitte le haut de la fiche).
- **« À préparer · 5 »** et **« À relancer · 12 »** : le nombre dans le titre ; « Tout voir » à droite sur la même ligne (Structure 9 et 10), vers les Offres au statut « En cours » et vers le Suivi. « Toutes les relances (12) » en bas de carte disparaît.
- **Les jours sans recherche et en pause** : la carte des offres s'appelle toujours « Offres du jour » ; sa phrase dit « Jour sans recherche… » ou « En pause jusqu'au… » à la place de l'offre (aujourd'hui, c'est le libellé qui changeait).

## 3. Une seule forme de ligne pour les deux listes

| Colonne | Contenu |
|---|---|
| Logo | le logo de l'entreprise ou son initiale, 40 px, le même arrondi pour les deux |
| Texte | **l'entreprise** en gras, dessous le poste puis la date (« envoyée le 12 septembre » pour une relance, « gardée le … » pour une offre à préparer), **une ligne chacun, coupée par « … »** si elle est trop longue ; le titre complet au survol |
| Action | « Préparer » ou « Relancer », dans une colonne de largeur fixe, alignée à droite, à la même place sur chaque ligne |

- **Au plus 3 lignes par carte** (2 relances aujourd'hui) ; « Tout voir » pour le reste.
- **Toute la ligne est cliquable**, avec survol (docs/interface.md, clic direct) ; l'action à droite dit ce qui se passe.
- Des filets entre les lignes, pas de cadre par ligne (un seul cadre par bloc).

## 4. Les écarts des règles, partout

- 0,75 rem entre le titre d'une carte et son contenu ; 1,25 rem entre deux cartes ; 1,5 rem de marge intérieure (Structure 2 et 3).
- Les deux cartes d'une rangée ont la même hauteur, le contenu reste en haut (Structure 4) : l'audit des règles le vérifie déjà.

## Ce qui ne change pas

- Les premiers pas (docs/128) restent en haut ; pendant ce temps, seules les cartes qui ont un contenu s'affichent, comme aujourd'hui.
- La phrase du jour, son action et les bandeaux datés, au-dessus des cartes.
- Le jour calme (« Rien d'urgent aujourd'hui »).
- L'offre du jour elle-même : la note, « pourquoi », « Écarter » et « Garder », « Annuler » pendant 6 secondes, le balayage au doigt.

## Garde-fous

- Le cycle ORP reste visible en 5 secondes (docs/126) : le mois ORP reste en haut à droite.
- Les écrans suivent `docs/interface.md` ; les trois audits à zéro, sur la démo et sur un compte neuf ; captures à 1440 et 390 px (avec et sans relances, avec et sans offres à préparer, jour sans recherche).

## Livraison proposée

- **1.2.0** : les deux rangées (§1), les titres avec compte et lien (§2), la forme de ligne commune (§3), les écarts (§4). Le serveur envoie 3 relances au lieu de 2.

## Les questions

1. **Les deux rangées** (§1) : d'accord, ou « À préparer » ailleurs (par exemple seulement dans Candidatures › Offres) ?
2. **3 lignes au plus** par carte (§3) : d'accord ?
3. **Dans la ligne d'une offre à préparer** : la date à laquelle elle a été gardée, ou la note (« Proche », « À creuser ») ?

## Écarts (1.2.0)

- **Règles relues avant de construire** ; captures à 1440 et 390 px de la démo (offres du jour, 2 à préparer, 6 relances).
- **La ligne d'une offre à préparer** : l'entreprise, le poste, la note en mot (« Proche », « Très proche »). La date à laquelle l'offre a été gardée n'existe pas dans la base.
- **« Ensuite »** : sous l'offre du jour, la suivante de la file (une ligne, sur ordinateur). Sans elle, la carte des offres gardait un vide sous les boutons, à côté du mois ORP plus haut ; la règle demande de le remplir d'une information utile (Structure 4).
- **Le mois ORP** ne répète plus « Encore N cette semaine » sous les points de la semaine : le compte au-dessus (« 1 / 3 candidatures ») le dit déjà. Les phrases de pause, de semaine faite et de jour sans recherche restent.
- **Une relance relancée sans réponse** s'écrit « relancée, sans réponse » : « sans réponse depuis la relance » était coupé sur téléphone.
- **La colonne de l'action** prend la largeur du mot : chaque carte n'a qu'une action, elle reste alignée d'une ligne à l'autre, et le texte garde la place.
- **« Voir les offres à préparer »**, à la fin du tri, amène sur la carte « À préparer » au lieu de changer d'onglet.
- **Jour en pause** : « En pause : pas d'offre du jour. » dans la carte, qui garde son titre.
- **Le style ancien de « À faire »** (le sélecteur, les libellés en capitales, une classe `.today-list` restée d'une version passée qui écrasait les nouvelles lignes) est retiré.

## Vérifié (1.2.0)

- Tests de l'interface : les quatre cartes, leurs titres avec le compte et « Tout voir », la forme de ligne, 3 lignes au plus, une carte vide absente et sa voisine sur toute la largeur, la pause ; « 1 sur N » exposé à la carte. 450 tests, lint, vue-tsc.
- Backend : 3 relances envoyées. 632 tests, ruff, mypy.
- Les trois audits à zéro, sur la démo et sur un compte neuf.
