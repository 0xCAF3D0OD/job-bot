# 33 — La plateforme sur téléphone (version 0.26.0)

> Statut : **validé** le 2026-10-15. livré : PR a (menu burger, rien ne déborde, en-tête compact).
> Retour d'usage du 2026-10-15 : adapter l'interface au téléphone, avec un menu « burger » pour gagner de la place, et les indispensables du mobile.

## 1. Le constat (iPhone, 375 px de large)

| Où | Ce qui coince |
|---|---|
| **Barre du haut** | 6 onglets sur une ligne : « Profil » et « Réglages » sont coupés, il faut deviner qu'on peut faire défiler ; logo, cloche, « Collecter » et compte se serrent. |
| **Offres, Alertes, Suivi** | la page **déborde en largeur** (jusqu'à 817 px pour 375) : cartes d'offres, assistant des alertes, bloc ORP du mois ; le navigateur dézoome toute la page. |
| **Aujourd'hui** | « Comment ça marche » : la pastille, le texte et « · où » se retrouvent chacun sur leur ligne. |
| **En-têtes de page** | le grand titre et sa pastille prennent un tiers du premier écran. |
| **Champs** | taille de texte sous 16 px : iPhone **zoome** sur le champ à chaque saisie. |
| **Actions principales** | en haut de page (« Préparer ma candidature », « Postuler ») : loin du pouce une fois la page défilée. |
| **Assistant** | le bouton flottant cache le bas des listes. |

## 2. Le menu « burger »

Sur un écran de moins de **820 px** de large (téléphone, tablette en hauteur) :

- **Barre du haut** sur une ligne : le logo à gauche ; à droite la **cloche** et le bouton **☰** (trois traits). Rien d'autre.
- **☰** ouvre un **panneau qui glisse depuis la droite** (le même que Contacts, docs/32 §2.2), sur toute la hauteur :
  - les **six pages**, une par ligne, grandes (48 px), la page en cours en **gras violet** avec le trait vertical à gauche ; le nombre de nouvelles actualités en pastille ;
  - un trait, puis **« Collecter maintenant »** ;
  - un trait, puis le **compte** : profil d'essai choisi, « Se déconnecter » (ce que contient le menu du compte aujourd'hui).
- Fermeture : ×, Échap, clic à côté, ou dès qu'on choisit une page. Le **☰** devient **×** quand le menu est ouvert.
- Au-delà de 820 px, rien ne change.

## 3. Les indispensables du mobile

### 3.1 Jamais de défilement en largeur

- **Règle** : aucune page ne dépasse la largeur de l'écran. Les rangées de boutons **passent à la ligne par bouton entier** (jamais un libellé coupé en deux, docs/32) ; un bouton trop long pour la rangée prend **toute la largeur**.
- Corrigés : cartes d'offres, assistant des alertes, bloc ORP du mois (« Compléter », « Marquer comme remis »).
- Les **tableaux** (formulaire ORP du mois) deviennent une **liste de fiches** : une candidature par fiche, les colonnes en lignes « libellé : valeur ».

### 3.2 L'action principale sous le pouce

- Sur les pages qui ont **une action principale** (docs/29), elle est dans une **barre fixée en bas de l'écran**, toujours visible :
  - détail d'une offre : « Préparer ma candidature » ;
  - préparation : l'étape suivante (« Rédiger la lettre », « Postuler »…) et « Marquer comme envoyée » ;
  - Suivi : « Compléter N ligne(s) » ou « Marquer comme remis ».
- La barre respecte la **zone du geste d'accueil** de l'iPhone (bas d'écran) ; la bulle d'information et l'Assistant s'affichent **au-dessus** d'elle.

### 3.3 Les pages en plein écran

- **Détail d'une offre** : s'ouvre en **plein écran** avec « ← Offres » en haut (aujourd'hui sous la liste).
- **Filtres des offres** : en plein écran, avec en bas **« Voir les N offres »**.
- Les panneaux latéraux (Contacts, Entreprise, Fiche) sont déjà en plein écran.

### 3.4 Lisible et touchable

- **Champs** en 16 px au moins : plus de zoom automatique.
- **Zones de toucher** de 44 px (déjà en place, docs/28 §4), vérifiées sur les nouveaux éléments (☰, barre du bas, lignes dépliables).
- **En-tête de page compact** : titre plus petit, sans la pastille (« CANDIDATURES »), sous-titre retiré ; l'onglet en cours suffit à se repérer.
- **Assistant** : sur téléphone, un **rond** avec seulement la pastille menthe (sans le mot « Assistant »), au-dessus de la barre du bas.
- **Aujourd'hui** : « Comment ça marche » remis d'aplomb (pastille et texte sur une ligne, « où » juste dessous, en petit).

### 3.5 Sur l'écran d'accueil

- La plateforme peut être **ajoutée à l'écran d'accueil** (« Sur l'écran d'accueil » dans Safari, « Installer » dans Chrome) : icône job-bot, nom court, s'ouvre sans la barre du navigateur, couleur de la barre d'état assortie.
- Pas de mode hors ligne : la plateforme reste en ligne (les données sont sur ton serveur).

## 4. Livraison en deux PR

| PR | Contenu |
|---|---|
| **0.26.0-a** | Menu burger (§2), jamais de défilement en largeur (§3.1, sauf les fiches du formulaire ORP), champs 16 px, en-tête compact, « Comment ça marche » (§3.4) |
| **0.26.0-b** | Barre d'action en bas (§3.2), détail et filtres en plein écran (§3.3), formulaire ORP en fiches (§3.1), Assistant en rond (§3.4), écran d'accueil (§3.5) |

Sans migration ni changement d'API. Chaque PR est vérifiée à 375 px (iPhone), 390 px et 768 px (tablette).

## Points à valider

1. **Burger sous 820 px** : logo, cloche et ☰ ; dans le menu, les pages, « Collecter maintenant » et le compte (§2).
2. **Jamais de défilement en largeur**, boutons qui passent à la ligne entiers, tableaux en fiches (§3.1).
3. **Action principale dans une barre en bas** (§3.2).
4. **Détail d'une offre et filtres en plein écran** (§3.3).
5. **En-tête compact, Assistant en rond, champs 16 px** (§3.4).
6. **Ajout à l'écran d'accueil**, sans mode hors ligne (§3.5).
7. **Deux PR** (§4).

## Écarts avec la PR a

- **Menu burger** : sous 820 px et seulement une fois connecté (sans connexion, la barre ne montre que les Actualités et « Se connecter », qui tiennent sur la ligne). Le menu reprend le panneau latéral ; « Candidatures » mène à la dernière page ouverte de la rubrique, comme sur ordinateur. Le compte n'apparaît que s'il y a quelque chose à y faire (connexion activée ou plusieurs profils).
- **Rien ne déborde** à 375, 390 et 768 px sur les dix pages. Causes trouvées : la règle « jamais de libellé sur deux lignes » (docs/32) s'appliquait aussi aux cartes d'offres, qui sont des boutons (elle ne vise plus que les boutons et liens) ; l'assistant des alertes et les lignes dépliables s'élargissaient sur leur contenu ; un libellé masqué du tableau ORP sortait de son cadre. Le tableau ORP défile dans son propre cadre en attendant les fiches (PR b).
- **En-tête compact** sous 820 px : titre plus petit, sans pastille ni sous-titre.
- **Champs à 16 px** sous 820 px.
- **Aujourd'hui** : « Comment ça marche » et « Pour bien démarrer » remis d'aplomb (pastille et texte sur une ligne, « où » ou l'indication juste dessous, en petit), sur toutes les largeurs.

## Complément du 2026-10-15 : trait droit et page figée sous le menu

- Retour d'usage : le trait violet de la page en cours se courbait en haut et en bas (les liens ont des coins arrondis, qui courbaient sa bordure). C'est désormais un **trait droit** posé à côté du lien. Même correction pour la bulle d'information et la note du formulaire ORP (côté gauche droit, coins arrondis à droite seulement).
- La **barre de défilement** de la page restait visible à côté du menu : tant qu'un panneau latéral est ouvert (menu, Contacts, Entreprise, Fiche), la page derrière **ne défile plus**.
- Le compte, dans le menu, n'a plus les traits du petit menu d'ordinateur.
