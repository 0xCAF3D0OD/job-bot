# 130 — Les pages rangées : la même forme partout (versions 1.3.0 et 1.3.1)

> Statut : **validé d'avance** le 2026-10-22 (« écris le cadrage 130 et exécute le cadrage »). Les choix ouverts sont tranchés ici, dans le sens des règles validées ; les écarts sont notés à la fin.
> Origine : le tour de toutes les pages de la démo, à 1440 et 390 px, après la 1.2.0 (« es qu'il y a d'autres composants à simplifier ou à structurer selon les règles d'ergonomie et UI/UX qu'on a définies »).

## Le constat

Déjà propres : Candidatures › Offres et la fiche d'une offre, Préparer, Bilan › Résultats.

À reprendre, par ordre d'importance :

1. **Le Suivi** : cinq contrôles sur la ligne du haut (le mois, le compte et sa barre, Calendrier/Liste, « + », « ⋯ ») ; sur téléphone, « ⋯ » seul sur sa ligne. « À relancer » : une carte encadrée par candidature, avec une pastille de statut et un pied coloré, dans une liste coupée par un fondu ; l'action s'appelle tantôt « Sans réponse », tantôt « Relancer ». « À déclarer dans Job-Room » : une troisième forme de ligne.
2. **Le Rendez-vous** : huit cartes ; plusieurs restent à moitié vides, étirées à la hauteur de leur voisine (« Compétences demandées qui manquent », « Obligations et échéances ») ; « Message au conseiller » seul sur sa rangée ; une phrase sous les onglets (Titres 1) ; un crayon seul en bas du carnet.
3. **Profil › Parcours** : une barre orange verticale sur un certificat (« pas de barre verticale dans une carte ») ; les blocs sur 4 colonnes (Structure 5 : 3 au plus) ; un crayon sur chaque bloc (clic direct : toute la carte s'ouvre).
4. **Réglages** : une seule grande carte mêle un formulaire et son « Enregistrer » avec des interrupteurs qui s'appliquent tout de suite ; des descriptions de trois lignes (Comme les CFF 1 : une ligne) ; un filet en trop en haut, un grand vide en bas.
5. **Formations** : quatre étages de filtres avant le contenu (Catalogue/Suivies, un encadré, Domaine/Tout, trois listes) ; 25 grandes cartes, chacune avec un vide sous le texte.
6. **Partout** : les titres du Profil et des Réglages plus gras que ceux de Candidatures et du Bilan ; « Prérequis » sous l'onglet « Critères » ; des cartes étirées dans le vide (« Code de vérification » dans Alertes).

## La phrase qui guide

**Une liste a la même forme sur toutes les pages ; une carte a un rôle ; rien ne s'étire dans le vide.**

La forme de ligne est celle d'Aujourd'hui (docs/129 §3) : le logo ou l'initiale, le texte (en gras, puis une ou deux lignes grises coupées par « … »), l'action à droite.

## 1.3.0 — Le Suivi et le Rendez-vous

### A. Le Suivi

- **Deux lignes en haut** :
  - ligne 1 : « ‹ Octobre 2026 › » à gauche ; à droite, Calendrier/Liste, « Ajouter » et « ⋯ » (le même endroit sur téléphone, sans ligne seule) ;
  - ligne 2 : « 6 / 10 candidatures » et sa barre ; à droite, l'état ORP et son action quand il y en a une (« Compléter 2 lignes », « Marquer comme remis »).
- **« À relancer »** passe à la forme de ligne d'Aujourd'hui : l'initiale, l'entreprise, le poste et la date, puis ce qui se passe (« relancée, sans réponse », « sans réponse depuis 10 jours ») ; l'action à droite, du même mot pour une même étape. Plus de cadre par candidature, plus de pastille de statut (le statut est dans la phrase), plus de liste défilante estompée : **5 lignes**, puis « Voir les N autres » qui déplie la suite.
- **Un jour choisi dans le calendrier** : ses candidatures, dans la même forme de ligne.
- **« À déclarer dans Job-Room »** : la même forme ; la date en ligne grise ; l'action « Déclarer » ouvre la candidature.
- **Le calendrier ne change pas** (ses marques « entretien », « relancer », « suite attendue » servent à prévoir) ; la légende et les enseignements restent repliés.

### B. Le Rendez-vous

```
┌ Le prochain rendez-vous ───────────────────────── ⋯ ┐
│ mardi 27 octobre à 09:30, ORP de Lausanne            │
└──────────────────────────────────────────────────────┘
Préparer
┌ Questions au conseiller ───┐  ┌ La feuille ─────────────────┐
│ ☐ … ☑ …  [Une autre…] [+]  │  │ Rien n'est envoyé à l'ORP.   │
│                            │  │ Nom [   ]  [Télécharger PDF] │
│                            │  │ En message : [Rédiger (IA)]  │
└────────────────────────────┘  └──────────────────────────────┘
Le mois
┌ Mois en bref · Ce qui bloque · Compétences qui manquent · Obligations ┐
│ (une carte grise, quatre parties sur deux colonnes, des filets)        │
└────────────────────────────────────────────────────────────────────────┘
▸ Le carnet                                         2 rendez-vous
```

- **« Préparer »** : deux cartes côte à côte, ce qu'on modifie (carte blanche) ; « Message au conseiller » rejoint « La feuille » (la feuille en PDF, ou le même contenu en message).
- **« Le mois »** : ce qu'on consulte, **une seule carte** sur fond gris, ses quatre parties en deux colonnes ; plus de cartes étirées.
- **La phrase sous les onglets** devient la description de « La feuille » (« Rien n'est envoyé à l'ORP : tu la télécharges ou l'envoies toi-même. »).
- **Le carnet** : une ligne repliable « Le carnet · 2 rendez-vous » ; dans chaque rendez-vous passé, « Modifier » sur la ligne de son titre (Structure 9), plus de crayon seul en bas.

## 1.3.1 — Profil, Réglages, Formations, les titres

### C. Profil

- **Critères** : le titre de section reprend l'onglet, « Critères » (plus « Prérequis »).
- **Parcours** :
  - les certificats : plus de barre orange ; l'état « à revoir » reste dans son étiquette et sa phrase ;
  - les blocs sur **3 colonnes** au plus ; **toute la carte d'un bloc s'ouvre** au clic, avec survol ; le crayon disparaît.

### D. Réglages

- **Une carte par réglage** dans chaque rubrique, comme les CFF : « Recherche d'emploi » sépare le formulaire (objectif, date de remise, seuil, « Enregistrer ») des **sites suivis** (interrupteurs, appliqués tout de suite), chacun sous son titre de section.
- **Les descriptions en une ligne** ; le pourquoi au survol (`HoverNote`). Exemple : « Objectif mensuel de l'ORP » → « Les candidatures demandées chaque mois. » (au survol : « Le Suivi compte avec toi. »).
- Plus de filet en haut de carte ; une carte s'arrête à son contenu.

### E. Formations

- **Une seule ligne de filtres** : Catalogue/Suivies à gauche, puis Domaine/Tout et les trois listes ; l'encadré « Formation et chômage » devient une ligne repliable sous les filtres.
- **Les cartes** s'arrêtent à leur contenu : le marque-page sur la ligne du titre, plus de vide en bas.

### F. Partout

- **Les titres de page** : la même graisse sur toutes les pages (celle de Candidatures et du Bilan).
- **Les titres de section** : la même taille et la même graisse partout (celle des Alertes).
- **Alertes** : « Les alertes » puis « Les e-mails des sites », l'un sous l'autre, chacun sur toute la largeur (une carte seule prend toute la largeur, Structure 1) : « Code de vérification » ne s'étire plus à la hauteur de la liste des alertes.

## Garde-fous

- Rien ne disparaît : chaque action d'aujourd'hui garde un chemin (le statut d'une candidature est dans son panneau, comme avant).
- Les écrans suivent `docs/interface.md` ; les trois audits à zéro sur la démo et sur un compte neuf ; captures à 1440 et 390 px.

## Livraison

- **1.3.0** : A et B.
- **1.3.1** : C, D, E, F.

## Écarts (1.3.0)

- **Règles relues avant de construire** ; captures à 1440 et 390 px de la démo (Suivi en calendrier, Rendez-vous) ; les trois audits à zéro sur la démo et sur un compte neuf.
- **Le Suivi** : « Ajouter » devient une pilule avec son mot (l'ancien « + » rond) ; sur téléphone, « Ajouter » et « ⋯ » montent sur la ligne du mois, Calendrier/Liste prend toute la largeur dessous (sans quoi « Calendrier » était coupé).
- **L'action « Sans réponse »** devient **« Classer sans réponse »** (un bouton dit ce qu'il fait, à l'infinitif : Titres 3), sa phrase « Relancée, sans réponse ». Le statut de la candidature reste lu par les lecteurs d'écran quand la phrase dit déjà l'étape.
- **Les titres des listes portent le compte** : « À relancer · 6 », « À déclarer dans Job-Room · 4 », comme sur Aujourd'hui.
- **Le Rendez-vous** : la carte du rendez-vous rejoint « Préparer », à côté des questions (deux cartes de hauteur proche) ; « La feuille » prend toute la largeur, le PDF et le message côte à côte. « Le mois » est une carte blanche : une carte grise disparaissait sur le fond gris de la page.
- **Le calendrier** ne change pas.

## Vérifié (1.3.0)

- Tests de l'interface : l'en-tête du Suivi sur deux lignes, les lignes « À relancer » (5 puis « Voir les 2 autres »), « À déclarer » dans la même forme, le Rendez-vous en parties (Préparer, Le mois en une carte, le carnet replié avec « Modifier »). 451 tests, lint, vue-tsc.
- Les trois audits à zéro sur la démo et sur un compte neuf.

## Écarts (1.3.1)

- **Les titres** : le Profil et les Réglages avaient des règles à part (0.78.4, d'après docs/110 : page à 2,4 rem en gras, sections à 1,5 rem en gras). Elles sont retirées : **une seule taille et une seule graisse** partout, celles des autres pages (page 2 rem, section 1,35 rem, graisse 500). C'est le choix du §F, plus récent que docs/110 ; `docs/interface.md` (Structure 8) est mis à jour. Dis-le si tu préfères l'inverse (tout en gras, à 2,4 et 1,5 rem) : c'est une règle à changer, pas du code.
- **Les Réglages gardent une carte par rubrique** (docs/106 §1, « une rubrique, une carte ») au lieu d'une carte par réglage comme le proposait le §D : la règle validée l'emporte. Ce qui gênait est corrigé dans la carte : le filet en haut à droite (une règle de séparation tombait au-dessus du second réglage d'une rangée), les descriptions sur une ligne (« Les candidatures demandées chaque mois. », le reste au survol ; « Le jour où les preuves sont dues. »), et la rangée d'actions vide sous les sites suivis, qui laissait un grand vide en bas quand il n'y avait rien à proposer.
- **Profil** : « Prérequis » devient « Critères » (le titre et le message « Critères enregistrés ») ; un bloc inactif a son titre grisé au lieu d'une carte à 60 % d'opacité.
- **Formations** : l'encadré « Formation et chômage » avait aussi une barre verticale bleue ; il devient une ligne repliable sur ordinateur comme sur téléphone.
- **Alertes** : les deux colonnes de la 0.83.2 passent en une colonne ; « Code de vérification » ne s'étire plus.
- **L'assistant** : consigne `assistant-v18` (le Suivi en lignes et « Classer sans réponse », le Rendez-vous décrit pour la première fois, les Formations sur une ligne). La 1.3.0 avait laissé l'ancienne description du Suivi.

## Vérifié (1.3.1)

- Captures à 1440 et 390 px : Profil (Critères, Parcours), Réglages, Formations, Alertes ; les graisses mesurées sur chaque page (titre de page 500, 32 px ; section 500, 21,6 px).
- Tests : 451 de l'interface, lint, vue-tsc ; 632 backend (dont la consigne de l'assistant), ruff, mypy.
- Les trois audits à zéro sur la démo et sur un compte neuf.
