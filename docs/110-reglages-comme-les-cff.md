# 110 — Les Réglages comme les CFF (version 0.78.0)

> Statut : **à valider** (points en fin de page).
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

## Points à valider

1. **Sur téléphone**, à la place des lignes dépliables :
   - **(a)** une **seule longue page**, toutes les sections l'une sous l'autre, comme la maquette et la page Paramètres des CFF ;
   - **(b)** une **liste des rubriques** qui ouvre **une page par rubrique**, comme le profil CFF (Paramètres, Commandes, Moyens de paiement).
2. **Les descriptions toujours visibles** dans les Réglages, et plus de « i » : d'accord ?
3. **Consulter en gris, modifier en blanc bordé**, avec le crayon rond : d'accord ?
4. **La portée** : les Réglages d'abord (0.78.0), puis le Profil (Critères, Parcours, Coordonnées) avec les mêmes règles (0.78.1) ?
