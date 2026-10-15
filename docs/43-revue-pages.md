# 43 — Revue page par page (version 0.35.0)

> Statut : **validé** le 2026-10-15. Livré : PR a, PR b.
> Revue de chaque page sur ordinateur (1280 px) et téléphone (375 px), le 2026-10-15, avec des données fictives (30 offres, 12 candidatures, 89 actualités, le catalogue de formations). Jugée selon tes règles : compact, symétrique, linéaire, rien de trop long par rapport au reste, aucun libellé coupé, ouvertures fluides, barres d'accent droites.

**En bref** : aucun débordement horizontal sur téléphone, les dépliages tiennent. Les défauts sont surtout de **cohérence entre pages** (en-têtes, largeurs, pluriels « (s) ») et de **longueur** (Actualités : 11 écrans sur téléphone ; Formations ; les guides de démarrage sur Aujourd'hui).

## 1. Partout

| # | Constat | Correction proposée |
|---|---|---|
| 1 | **Deux styles d'en-tête et trois largeurs.** Candidatures : titre à gauche, sans bandeau, contenu sur toute la largeur. Aujourd'hui, Actualités, Formations, Profil : grand titre centré sur un bandeau blanc (~190 px avant le contenu), contenu plus étroit. Réglages : encore une autre largeur. Passer d'une page à l'autre fait « sauter » la mise en page. | **Un seul en-tête et une seule largeur** pour toutes les pages : le style de Candidatures (petite étiquette, titre à gauche, onglets dessous), contenu aligné sur la même colonne. Le bandeau centré disparaît. *(Point à valider : c'est le plus visible.)* |
| 2 | **Pluriels « (s) »** : « 21 offre(s) à examiner », « Compléter 3 ligne(s) », « 0 alerte(s) », « 1 prise(s) de contact »… une quarantaine dans l'interface. | Vrais accords : « 21 offres », « 3 lignes », « 1 prise de contact » ; « aucune alerte » pour zéro. |
| 3 | **Page vide pendant le chargement** : sur téléphone, Suivi, Actualités, Aujourd'hui restent blancs une à deux secondes, puis tout apparaît d'un coup et pousse la page. | Des **blocs gris à la forme du contenu** (cartes, lignes) le temps du chargement, remplacés sans saut. |
| 4 | **« Pour filtrer selon ton domaine, indique tes mots-clés dans Réglages → Actualités »** répété sur Actualités et Formations ; il faut quitter la page. | Tant que le domaine est vide, **« Mon domaine » ouvre un petit champ sur place** (« DevOps, Kubernetes… », Ajouter). La phrase disparaît. |
| 5 | **Chevron « › » sur des boutons qui n'emmènent nulle part** (« Enregistrer › »). | Chevron réservé à ce qui ouvre une autre page ou l'étape suivante. |

## 2. Aujourd'hui

| # | Constat | Correction proposée |
|---|---|---|
| 6 | **Ordinateur** : « Comment ça marche » et « Pour bien démarrer » occupent ~650 px **avant** les chiffres du jour. Sur téléphone, ils sont déjà repliés en bas. | Même ordre que le téléphone : **le point du jour d'abord**, les deux guides repliés en bas (une ligne chacun avec « 3 / 5 »). |
| 7 | « Candidatures commencées » (1 ligne) à côté de « Les mieux notées » (3 lignes) : la carte de gauche est **vide aux deux tiers**, son lien collé en bas. | Les deux cartes prennent la hauteur de leur contenu, **lien juste sous la dernière ligne** ; s'il y a moins de lignes, une ligne discrète « rien d'autre en cours ». |
| 8 | La relance d'un **contact** est un bandeau isolé entre le titre et les chiffres. | Intégrée à la case « à relancer » : « 5 à relancer · 1 contact ». |
| 9 | « Comprendre le marché » montre des titres **sans rapport** (« Le journaliste qui a révélé l'affaire Pierin Vincenz… », une vidéo en anglais). | Seulement des articles de **ton domaine** ou marqués « marché de l'emploi » ; section masquée s'il n'y en a pas (voir §4). |

## 3. Candidatures

| # | Constat | Correction proposée |
|---|---|---|
| 10 | **Téléphone : l'onglet « Bilan » est coupé** (4 onglets + pastilles = 371 px pour 343). Défaut introduit par la 0.34.0. | Onglets et pastilles resserrés sur téléphone : les quatre tiennent sans défilement. |
| 11 | **Offres, ordinateur** : « Candidature spontanée » seul sur sa ligne au-dessus de la liste (une bande vide) ; la liste s'arrête 60 px avant le bord des onglets. | Bouton sur la ligne « 21 offres », à droite ; liste alignée sur les onglets. |
| 12 | **Offres** : un titre de jour **au-dessus de chaque carte** quand les offres sont espacées (« Samedi 10 octobre · 1 offre », « Mercredi 7 octobre · 1 offre »…). | Mêmes groupes que les Actualités : **Aujourd'hui · Cette semaine · Plus ancien**, la date reste sur la carte. |
| 13 | **Offres, filtres** : « Effacer tout (0) » ressemble à un champ désactivé. | Masqué tant qu'aucun filtre n'est actif. |
| 14 | **Suivi, ordinateur** : cinq éléments sur la ligne du mois (mois, compteur, pastille ORP en tout petit, « Compléter 3 lignes », « Ajouter »), et « Calendrier / Liste » seul sur la ligne suivante. | Ligne 1 : mois, compteur, Calendrier / Liste, « ＋ ». Ligne 2, seulement s'il y a à faire : « Preuves de septembre à remettre avant le 5 octobre · Compléter 3 lignes ». |
| 15 | **Alertes, ordinateur** : l'assistant occupe 60 % de la largeur, la moitié droite est vide, « Alertes reçues » dessous fait toute la largeur. | Assistant sur toute la largeur, aligné avec « Alertes reçues ». |

## 4. Actualités

| # | Constat | Correction proposée |
|---|---|---|
| 16 | **« Marché de l'emploi » parle d'autre chose** : Credit Suisse, Lindt, Porsche, Nestlé, TSMC. Les sources d'économie générale passent toutes. | L'onglet ne garde que les **sources marquées « marché de l'emploi »** (SECO…) et les articles qui parlent d'emploi (emploi, chômage, recrutement, salaires, licenciements, postes). Le reste de l'économie passe dans un onglet **« Économie »**, ou disparaît si tu préfères. *(Point à valider.)* |
| 17 | **Téléphone : 60 articles d'un coup, 11 écrans.** | **12 au plus** (la une, Aujourd'hui, le début de Cette semaine), puis « Voir plus » ; « Plus ancien » replié. |
| 18 | **Téléphone** : le premier article commence à ~580 px (titre sur deux lignes, onglets, bascule, phrase d'aide). | Titre court sur téléphone (« Actualités »), phrase d'aide supprimée (§1 n° 4) : l'article de tête dès le premier écran. |
| 19 | **Ordinateur** : la phrase d'aide est collée à l'image de tête. | Disparaît avec le n° 4. |

## 5. Formations

| # | Constat | Correction proposée |
|---|---|---|
| 20 | « Financement possible seulement avec l'accord préalable de ton conseiller ORP » **répété sur chaque carte payante** (déjà dit dans l'encadré du haut). | Retiré des cartes ; la mention « payant » suffit. |
| 21 | **Catalogue long** : 24 cartes à la suite (~3 écrans sur ordinateur, 3 sur téléphone), certifications et cours mêlés. | Deux groupes titrés, **Certifications** puis **Cours**, comme les sections des Actualités ; « Mon domaine » par défaut dès qu'il a des mots-clés. |
| 22 | La ligne « examen en centre ou en ligne · anglais · payant · avancé » passe souvent sur **deux lignes**, d'une carte à l'autre les blocs ne s'alignent plus. | Ligne raccourcie (« examen · anglais · payant · avancé ») ; le détail du format reste dans la carte ouverte. |

## 6. Profil

| # | Constat | Correction proposée |
|---|---|---|
| 23 | « Ce que je cherche » : une carte à **60 % de la largeur**, le reste de la page vide. | Carte pleine largeur, résumé **en lignes alignées** (Lieux · Télétravail · Taux · Types exclus), comme les cartes du Bilan. |
| 24 | « Lieux : VD » : un code. | « Lieux : Vaud ». |
| 25 | Le sous-titre de la page ne parle que des prérequis (« une offre qui ne les respecte pas passe dans Écartées »). | Sous-titre commun aux trois onglets ; l'explication des prérequis va dans le « ? » de la carte. |

## 7. Réglages

| # | Constat | Correction proposée |
|---|---|---|
| 26 | **Sites suivis : colonnes décalées.** jobup et Indeed n'ont pas « Retirer », leur case « suivi » est donc plus à droite que celle des autres sites. | Colonne d'action de largeur fixe (vide pour les sites intégrés) : cases et compteurs alignés. |
| 27 | **Recherche d'emploi** : quatre champs d'un nombre, chacun dans son bloc (~450 px). | Sur ordinateur, **grille 2 × 2** ; un seul « Enregistrer ». |
| 28 | **Sources des Actualités** : chaque ligne mêle deux listes, une case et deux actions, sur deux lignes qui ne s'alignent pas d'une source à l'autre. | Mêmes colonnes pour toutes les sources (nom · pays · langue · marché de l'emploi · suivie · retirer). |

## 8. Ce que changent les lectures du 2026-10-15

Lus : NN/g, *State of UX 2026* ; UX Collective, *The most popular experience design trends of 2026* ; Awwwards, recherche « job board ».

**Ce qui confirme le plan**

- NN/g : l'interface n'est plus ce qui distingue un produit ; ce qui compte, c'est **résoudre le vrai problème** et mesurer le résultat, pas le « design de façade ». → Les corrections qui changent ce que tu fais (Aujourd'hui, Actualités pertinentes) passent **avant** l'harmonisation visuelle (voir §10, ordre revu).
- NN/g : lassitude envers l'IA ; elle doit **rester en arrière-plan**, avec transparence, contrôle, constance et une solution quand elle échoue. → C'est déjà la règle de la plateforme (coût affiché, modèle gratuit si l'IA manque, rien envoyé sans toi). Pour le tri des Actualités (n° 16), **des règles simples, pas d'IA** : gratuit, prévisible, explicable.
- UX Collective, « concevoir pour l'intention » : montrer d'abord ce que la personne vient faire. → Va dans le sens du n° 6, et ajoute le n° 30.
- Awwwards : grilles de cartes, palette neutre, une couleur d'accent pour l'action, filtres, transitions discrètes. → Déjà notre ligne. Ces sites sont des vitrines (une visite, effet « waouh ») ; jobA1 est un outil de tous les jours : rien à en copier de plus.

**Trois ajouts**

| # | Constat | Correction proposée |
|---|---|---|
| 29 | **Titres mal hiérarchisés** (UX Collective, « Machine Experience » : les lecteurs d'écran et les assistants s'appuient sur les titres). Les cartes d'offres n'ont pas de titre (un simple texte) ; le Suivi saute du titre de page à un sous-sous-titre ; la feuille ORP ajoute un second titre de page. | Un titre de page, un titre par section, un titre par carte : on navigue d'offre en offre au clavier et au lecteur d'écran. Rien ne change à l'écran. |
| 30 | **Aujourd'hui dans le même ordre tous les jours**, qu'un entretien ait lieu demain ou non. | Le plus urgent en premier : entretien demain, remise ORP dans moins de 5 jours, puis le reste dans l'ordre habituel. |
| 31 | **Plusieurs alertes orange en même temps** (« 5 à relancer », « 5 octobre », le bandeau contact) : la recherche d'emploi est déjà stressante (UX Collective, design émotionnel). | **Une seule chose en orange** : la plus urgente ; les autres en couleur normale. Ton calme dans les textes. |

**Écarté** : le verre dépoli (« glassmorphism » : nuit au contraste, docs/28), la nostalgie, la voix et les gestes, les systèmes de design générés par l'IA, les modes « selon l'humeur » (le thème sombre suit déjà celui du système).

## 9. Ce que je n'ai pas retenu de la revue

- Les rapports PDF « Design Critique » (notes de logo génériques).
- Les couleurs et la typographie : cohérentes d'une page à l'autre.
- Le téléphone en général : aucun débordement, menu, cartes des alertes et des filtres corrects.

## 10. Livraison en trois PR (ordre revu)

D'abord ce qui change ce que tu fais, puis la cohérence, puis les détails. Chaque PR a un **critère vérifiable** :

| PR | Contenu | Vérifié quand |
|---|---|---|
| **0.35.0-a** | Ce qui sert la tâche : Aujourd'hui (n° 6 à 9, 30, 31), pertinence et longueur des Actualités (n° 16 à 19), onglet Bilan sur téléphone (n° 10), chargement (n° 3), « Mon domaine » sur place (n° 4) | les chiffres du jour visibles au premier écran (ordinateur 900 px) ; aucun article hors emploi dans « Marché de l'emploi » sur l'échantillon ; Actualités en 3 écrans au plus sur téléphone ; les 4 onglets visibles sur téléphone |
| **0.35.0-b** | Cohérence : un en-tête et une largeur (n° 1), vrais pluriels (n° 2), chevrons (n° 5), titres hiérarchisés (n° 29) | même position du titre et des bords sur toutes les pages ; aucun « (s) » dans l'interface ; un seul titre de page partout |
| **0.35.0-c** | Détails par page : Candidatures (n° 11 à 15), Formations (n° 20 à 22), Profil (n° 23 à 25), Réglages (n° 26 à 28) | captures avant / après, ordinateur et téléphone |

## Points à valider

1. **Un seul en-tête** (style de Candidatures) et une seule largeur pour toutes les pages (n° 1).
2. **Actualités** : « Marché de l'emploi » limité à l'emploi par des règles simples, le reste dans un onglet « Économie » — ou supprimé (n° 16).
3. **Offres groupées** Aujourd'hui · Cette semaine · Plus ancien au lieu d'un titre par jour (n° 12).
4. **Les trois ajouts** (n° 29 à 31) et l'**ordre revu** des PR (§10).
5. Le reste des corrections (§1 à §7).

## Écarts avec la PR a

- **Actualités** : trois onglets, **Marché de l'emploi · Économie · Vidéos** (l'option « onglet Économie » plutôt que la suppression). « Marché de l'emploi » garde un article s'il parle d'emploi (chômage, salaires, embauches, licenciements, conjoncture…, en français, allemand et anglais) ou contient un mot de ton domaine ; le reste va dans « Économie ». Sur l'échantillon : 10 articles d'emploi sur 65, dont un discutable (la Fed, qui parle d'emploi dans son résumé). Sur téléphone, l'onglet s'appelle « Emploi ».
- **Téléphone** : **10** contenus puis « Voir plus » (12 donnaient 3,1 écrans) ; « Plus ancien » n'est pas replié, la limite suffit (2,7 écrans au plus).
- **Aujourd'hui** :
  - en tête, un entretien d'aujourd'hui ou de demain, et la remise ORP à 5 jours ou moins — ou passée (« échéance passée le 5 octobre ») ;
  - **une seule case en orange** : la remise ORP si elle est urgente, sinon les relances, sinon la remise ;
  - « 5 à relancer · 1 contact » remplace le bandeau des contacts ;
  - les deux guides, repliés en une ligne chacun, passent en bas sur ordinateur comme sur téléphone ;
  - les deux cartes côte à côte gardent la même hauteur (ton retour du 2026-10-14), 3 lignes au plus chacune, le lien juste sous la liste, et « Rien d'autre en cours » quand l'une en a moins ;
  - « Comprendre le marché » : ton domaine, sinon l'emploi ; la section disparaît s'il n'y a rien.
- **« Mon domaine » sur place** : Actualités et Formations ; les mots saisis activent aussitôt le filtre.
- **Chargement** : blocs gris sur Aujourd'hui, Actualités, Formations, Suivi et Bilan.
- **Onglets sur téléphone** : marges resserrées pour tous les onglets ; Offres 21 · Suivi 8 · Alertes · Bilan tiennent sur 343 px.
- **Vérifié** dans le navigateur avec les données fictives : chiffres du jour au premier écran (ordinateur 900 px), Actualités 2,5 à 2,7 écrans sur téléphone, onglets entiers, champ « Mon domaine ».

## Écarts avec la PR b

- **Un en-tête, une largeur** : toutes les pages prennent l'en-tête de Candidatures (étiquette, titre à gauche, onglets dessous) et la même largeur de contenu (80 rem, 1280 px). Les onglets d'Actualités, Formations et Profil montent dans l'en-tête ; Candidatures passe dans la même bande grise que les autres pages. Le sous-titre reste, en petit sous le titre, masqué sur téléphone. Mesuré sur les 9 pages : titre et bords au même pixel (ordinateur 1600 px et téléphone 375 px).
- **Pluriels** : plus aucun « (s) » dans l'interface, ni dans les notifications (cloche, ntfy) ni dans les messages des commandes.
- **Chevrons** : retirés des boutons d'action (Enregistrer, Ajouter, Créer, Renoter, Collecter maintenant, Afficher plus, Marquer comme remis, Rédiger la lettre, Préparer le CV, Se connecter) ; gardés pour ce qui ouvre une autre page ou l'étape suivante (Continuer, Compléter, Ouvrir, liens vers les sites).
- **Titres** : un seul titre de page partout (la feuille ORP n'en ajoute plus) ; le panneau du Suivi et les jours de la liste des offres ont un vrai titre de section. **Les cartes d'offres restent des boutons** : un titre ne peut pas se trouver dans un bouton ; on passe d'une offre à l'autre avec Tab, chaque carte annonçant son poste.
