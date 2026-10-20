# 110 — Les Réglages comme les CFF (version 0.78.0)

> Statut : **validé** le 2026-10-20 : (a) une longue page sur téléphone, avec des marqueurs pour la parcourir ; les descriptions visibles ; consulter en gris, modifier en blanc bordé ; les Réglages d'abord, le Profil ensuite.
> Origine : ta demande du 2026-10-20, six captures du profil CFF à l'appui (Paramètres, Commandes, Moyens de paiement) : « regarde bien comment ils font : la relation entre les titres et les informations, le décalage des informations, l'encadrement des informations, la rigueur des informations proposées et de celles qui sont modifiables ».
> Les versions prévues par docs/104 (l'adresse à jobA1, les premières offres) passent en 0.79.0 et 0.80.0.

## Ce que font les CFF

### 1. Les titres et les informations

| Niveau | Aspect | Exemple |
|---|---|---|
| **Chemin** | petit, gris, au-dessus du titre | ⌂ › Profil › Paramètres |
| **Titre de page** | très grand (environ 2,4 rem), gras | Paramètres |
| **Titre de section** | grand (environ 1,5 rem), gras, **hors de la carte**, au-dessus d'elle | Communication, Centres d'intérêt |
| **Titre d'un réglage** | gras, taille du texte, **dans la carte** | Informations et offres |
| **Description** | normale, grise, juste sous le titre, interligne large | « Vous recevez des informations… » |

Chaque niveau a une seule taille et une seule graisse. Rien d'autre ne sert de titre.

### 2. Le décalage des informations

- **Interrupteur** : le titre et sa description forment un bloc à gauche ; l'interrupteur est à droite, **centré sur le bloc**.
- **Case à cocher ou bouton radio** : la case à gauche, le libellé à côté ; la description passe **sous le libellé, alignée sur lui**, pas sous la case.
- **Champ** (dates) : l'étiquette **petite et grise dans le champ**, au-dessus de la valeur ; l'icône à droite.
- **Billet** (un objet) : le nom en gras à gauche, le prix en gras à droite, sur la même ligne ; le détail gris dessous.

### 3. L'encadrement

- **Ce qu'on modifie** est dans **une carte blanche bordée**, coins de 12 px, 1,5 rem de marge ; ses réglages sont séparés par des filets.
- **Ce qu'on consulte** (billets, moyens de paiement) est sur **un fond gris, sans bordure**, une carte par objet.
- **Un objet qu'on peut modifier** porte **un bouton crayon rond, blanc**, à droite (Twint ✎).
- **Une action** (« Enregistrer le moyen de paiement ») est **un bouton pleine largeur, en pilule bordée**, sous ce qu'elle complète.
- **Rien à montrer** : **un cadre pointillé** avec une phrase (« Pas de bons d'achat disponibles »), puis l'action qui le remplit.

### 4. La rigueur

- **Chaque réglage dit ce qu'il change**, en une phrase, sous son titre. Aucun réglage sans description.
- **Chaque chose modifiable a un contrôle visible** : un interrupteur, une case, un bouton radio, un champ ou un crayon. Ce qui n'en a pas ne se modifie pas.
- **Une section, une carte**. Une carte ne mélange pas ce qu'on consulte et ce qu'on modifie.
- **Les mêmes contrôles partout** : un interrupteur pour oui ou non, des boutons radio pour un choix unique, des cases pour plusieurs choix.

## Ce que fait jobA1 aujourd'hui

- **Sur téléphone**, les rubriques sont des lignes dépliables : le titre de la rubrique est dans la ligne, et le contenu se déplie dedans. Il n'y a pas de titre de section au-dessus d'une carte.
- **Les titres de partie** (« Jours de recherche ») ont la même graisse que le texte (500), et les descriptions sont souvent cachées dans le « i ».
- **Les cases des jours** et les boutons radio ont leur libellé à côté, sans description dessous.
- **Ce qu'on consulte et ce qu'on modifie** sont dans la même carte : par exemple « Connecté en tant que eliot » à côté de « Se déconnecter partout » et des données personnelles.
- **Les actions** sont de petits boutons ou des liens, de tailles différentes selon la rubrique.

## La proposition (maquette jointe)

1. **Les titres** :
   - un **titre de page** de 2,4 rem en gras, avec le chemin au-dessus sur téléphone ;
   - un **titre de section** de 1,5 rem en gras, **au-dessus de la carte** ;
   - un **titre de réglage** en gras (600) dans la carte, et sa **description grise toujours visible** dessous. Le « i » disparaît des Réglages : la description est là.
2. **Le décalage** :
   - l'interrupteur à droite, centré sur le titre et la description ;
   - les boutons radio et les cases avec leur description sous le libellé, alignée sur lui ;
   - les dates avec leur étiquette dans le champ.
3. **L'encadrement** :
   - les réglages dans une carte blanche bordée ;
   - les informations (le compte, les données personnelles, les navigateurs reliés) sur un fond gris, sans bordure ;
   - un crayon rond pour ce qu'on modifie dans un objet ;
   - les actions en pilules pleine largeur, sur téléphone ;
   - les états vides en cadre pointillé.
4. **Les contrôles** :
   - « Recevoir sur mon téléphone » devient un interrupteur ;
   - les jours de recherche deviennent des pastilles Lu à Di, à la place des cases ;
   - le seuil garde ses cinq pastilles ;
   - « Les offres bien notées » garde ses boutons radio, avec une description sous chacun.
5. **Ce qui ne change pas** : les rubriques, l'enregistrement (au changement pour un seul champ, un « Enregistrer » plein pour un formulaire), la largeur de la page sur ordinateur.

**Pas de point final** dans les titres : c'est la marque des CFF, pas une règle de lisibilité.

## Décisions (2026-10-20)

1. **Téléphone** : une seule longue page, « avec des marqueurs pour vite parcourir les éléments ».
2. **Les descriptions** toujours visibles, plus de « i » dans les Réglages.
3. **Consulter en gris, modifier en blanc bordé**, avec le crayon rond.
4. **La portée** : les Réglages en 0.78.0, le Profil avec les mêmes règles en 0.78.2 (0.78.1 corrige les marqueurs).

## Écarts

- **Les marqueurs** : une rangée de pastilles (Recherche d'emploi, Rythme, Actualités…) collée sous la barre du haut. Un appui mène à la section ; la pastille de la section en cours se colore pendant la lecture et reste visible dans la rangée. Un lien `?rubrique=…` mène directement à sa section.
- **Sur ordinateur**, le sommaire de gauche et une rubrique à la fois restent (docs/48 §2) ; les titres, les descriptions, les contrôles et l'encadrement changent comme sur téléphone.
- **Les lignes dépliables** des Réglages disparaissent (`SettingsSection` n'utilise plus `DisclosureRow`).
- **Les jours de recherche** restent de vraies cases à cocher (clavier, lecteurs d'écran), présentées en pastilles Lu à Di, toutes sur une ligne sur téléphone.
- **« Recevoir sur mon téléphone »** devient un interrupteur ; « Arrêter » disparaît (l'interrupteur l'éteint). Le compte de l'exploitant n'a que la ligne « Notification de test ».
- **Les informations en gris** : « Connecté en tant que … », le résumé des données personnelles, le sujet ntfy, le plafond fixé par l'exploitant, la dépense de l'IA du mois.
- **Les pilules** : Refaire l'accueil, Se déconnecter partout, Exporter mes données, Créer une adresse d'abonnement, Parcourir les suggestions ; pleine largeur sur téléphone.
- **Les « i » qui restent** sont ceux des formulaires d'ajout d'une source d'actualités (dans le panneau latéral) : ils seront repris avec le Profil (0.78.2).
- **Le crayon rond** n'a pas encore d'usage dans les Réglages (aucun objet n'y est modifiable autrement que par un interrupteur) : il servira dans le Profil.

## Vérifié

- Tests : la longue page et ses marqueurs (toutes les rubriques, un marqueur qui mène à sa section) ; la section sous son titre, sans ligne dépliable sur téléphone ; l'interrupteur du téléphone ; « Se déconnecter partout » en pilule ; tests complets, lint, typecheck.
- Capture Playwright de la page entière à 414 px, avec tous les panneaux et des données fictives (5 900 px de haut) : marqueurs, titres, descriptions, pastilles, choix, dates, informations en gris, pilules ; largeur de la page mesurée à 414 px.

### Les questions posées

1. **Sur téléphone**, à la place des lignes dépliables :
   - **(a)** une **seule longue page**, toutes les sections l'une sous l'autre, comme la maquette et la page Paramètres des CFF ;
   - **(b)** une **liste des rubriques** qui ouvre **une page par rubrique**, comme le profil CFF (Paramètres, Commandes, Moyens de paiement).
2. **Les descriptions toujours visibles** dans les Réglages, et plus de « i » : d'accord ?
3. **Consulter en gris, modifier en blanc bordé**, avec le crayon rond : d'accord ?
4. **La portée** : les Réglages d'abord (0.78.0), puis le Profil (Critères, Parcours, Coordonnées) avec les mêmes règles (0.78.1) ?

## Complément 0.78.1 : les marqueurs

Ta capture du 2026-10-20 : en lisant Actualités, le marqueur « Actualités » collait au bord gauche de l'écran, coupé.

- **La cause** : pour garder le marqueur en cours visible, la rangée défile jusqu'à lui, sans tenir compte de sa propre marge.
- **Après** :
  - la rangée garde 1 rem à gauche et 1,75 rem à droite quand elle défile (`scroll-padding-inline`) ;
  - un espace termine la rangée ;
  - **un fondu discret** sur les bords montre qu'elle continue.
- **Vérifié** : capture Playwright de la rangée à 414 px, avec le premier, un marqueur du milieu et le dernier en cours : aucun ne touche un bord, et le dernier n'est pas sous le fondu.

## Complément 0.78.2 : le Profil

Ta demande du 2026-10-20 : « fais le profil avec les règles des CFF » (décision 4).

- **La page** : fond blanc, comme les CFF, pour que ce qu'on consulte (en gris) s'en détache ; le titre « Profil » en grand et en gras sur téléphone, les titres de section à 1,5 rem.
- **Critères** :
  - « Prérequis » est un titre de section au-dessus du résumé ;
  - le résumé (lieux, taux, types exclus, mots interdits) est **une carte grise, sans bordure**, avec **un crayon rond** en haut à droite pour le modifier (il remplace le bouton « Modifier les prérequis ») ;
  - dans le formulaire, chaque prérequis a **sa description visible** sous son titre (lieux, télétravail, taux, types exclus, mots interdits, langues). Les « i » disparaissent.
- **Parcours** :
  - les documents et les blocs de profil sont **des objets gris** ;
  - chaque bloc porte **un crayon rond** (toute la carte l'ouvre toujours, comme avant) ;
  - « Nouveau bloc » est une pilule ;
  - le type d'un bloc a sa description visible dans le formulaire.
- **Coordonnées** :
  - « Coordonnées » est un titre de section au-dessus de la carte ;
  - une phrase dit à quoi elles servent : « pour tes lettres, ton CV et les formulaires ; elles ne partent jamais à l'IA » (docs/65 §6) ;
  - « Enregistrer mes coordonnées » prend toute la largeur sur téléphone.
- **Vérifié** : tests (les descriptions visibles et l'absence de « i » dans les Critères), tests complets, lint, typecheck ; capture Playwright des trois onglets à 414 px, avec des données fictives.

## Complément 0.78.3 : retours d'affichage

Tes captures du 2026-10-20 (téléphone, ton compte et la démo).

- **« Enregistrer » collé au bord** : en fin de Recherche d'emploi (contre le filet de Sites suivis) et en fin de Rythme (contre le bord de la carte). Un « Enregistrer » en fin de formulaire garde maintenant 1,5 rem dessous.
- **Le seuil des notifications** : « Enregistré » (ou l'erreur) se mettait à côté des pastilles et coupait « / 100 » sur deux lignes. Il passe **sous** les pastilles, et « / 100 » ne se coupe plus.
- **Dans la démo**, l'erreur « L'enregistrement a échoué » s'ajoutait sous le seuil alors que la bulle « Dans la démo, rien n'est enregistré » le disait déjà : elle ne s'affiche plus en démo.
- **La bulle** : son texte et sa croix sont centrés en hauteur.
- **« Exporter mes données (ZIP) »** passait sur deux lignes avec son état (✓ · 24 Ko) : une pilule reste sur une ligne.
- **« Comment l'installer »** (l'extension) était un bloc de texte illisible : il devient des **étapes numérotées par navigateur** (Firefox ; Chrome, Edge ou Brave), les adresses en petites étiquettes qui passent à la ligne.
- **Les dates « Du » et « Jusqu'au »** : l'étiquette reste dans le champ quand on le touche, comme chez les CFF. Le champ ne montre que « jj.mm.aaaa » : sans l'étiquette, on ne saurait plus si l'on saisit le début ou la fin de la pause.
- **Vérifié** : tests, lint, typecheck ; captures Playwright à 414 px des fins de Recherche et de Rythme, du seuil avec « Enregistré », de l'export terminé et des étapes d'installation.

