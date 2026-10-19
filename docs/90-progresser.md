# 90 — Trois entrées : Aujourd'hui, Candidatures, Progresser (version 0.70.3)

> Statut : **validé** le 2026-10-19.
> Origine : ta remarque du 2026-10-19 : « Profil, Actualités et Formations ne sont-ils pas secondaires par rapport aux deux autres ? », puis la maquette du même jour, et ta remarque sur la pastille « 6 ».
> Se construit sur la 0.70.2 (la capsule, docs/89) : à faire après sa fusion.

## Le principe

- **Deux pages de travail, une page pour avancer** :
  - **Aujourd'hui** ;
  - **Candidatures** ;
  - **Progresser**, qui réunit Actualités et Formations.
- **Profil passe dans le menu du compte**, en tête, au-dessus de Réglages. Comme Réglages, on le remplit au début, puis on y revient rarement.

## Le menu

| | Avant (0.70.2) | Après |
|---|---|---|
| Menu principal | Aujourd'hui, Candidatures, Actualités (6), Formations, Profil | Aujourd'hui, Candidatures, Progresser • |
| Menu du compte | Réglages, Données personnelles, Diagnostic, Collecter maintenant, Se déconnecter | **Profil**, Réglages, Données personnelles, Diagnostic, Collecter maintenant, Se déconnecter |
| ☰ (téléphone) | 5 pages | 3 pages |

**Un point, pas un chiffre.** Un chiffre veut dire « des choses à traiter » (offres à examiner, relances). Des articles à lire n'en sont pas. Progresser porte donc un **petit point** quand il y a des articles nouveaux ; le chiffre reste sur l'onglet Actualités, dans la page.

## La page Progresser (`/progresser`)

- **Le titre** est « Progresser ».
- **Deux onglets** : **Actualités** (avec le nombre de nouveaux articles) et **Formations**. La page est construite comme Candidatures : une page parente, un onglet par adresse.
  - `/progresser/actualites`
  - `/progresser/formations`
- **Pas d'onglets dans des onglets.** Les découpages qui existent déjà deviennent un **sélecteur** en haut du contenu, comme Calendrier / Liste dans le Suivi :
  - Actualités : **Emploi · Économie · Vidéos**, avec leurs compteurs ;
  - Formations : **Catalogue · Suivies** (« Mes formations » devient « Suivies », règle de docs/88).
- **Un même filtre partout** : le bouton « Domaine », les filtres et les sources ne changent pas. Ils restent dans chaque onglet.
- **Se souvenir de l'onglet** : Progresser rouvre le dernier onglet choisi, comme Candidatures.

## Les anciennes adresses

Elles continuent de marcher et mènent au bon endroit, avec leurs paramètres :
- **`/actualites`** (y compris `?rubrique=…`) → `/progresser/actualites` ;
- **`/formations`** (y compris `?onglet=miennes`) → `/progresser/formations`, sélecteur sur « Suivies ». Les notifications de financement ORP utilisent ce lien.
- **`/profil`** ne change pas : la page reste, seule son entrée change de place.

Côté serveur, les liens écrits dans les notifications passent aux nouvelles adresses. Les anciens restent valables.

## Aujourd'hui

- **La carte « Progresser »** mène à l'onglet Formations.
- **La carte « Comprendre le marché »** mène à l'onglet Actualités.
- Rien d'autre ne change.

## L'assistant

**`assistant-v11`** connaît :
- les trois entrées ;
- la page Progresser, ses deux onglets et leurs sélecteurs ;
- Profil dans le menu du compte ;
- les nouvelles adresses.

## Vérifié avant la PR

- **Tests** :
  - le menu a trois entrées et le point s'affiche sur Progresser ;
  - le menu du compte commence par Profil ;
  - les anciennes adresses mènent au bon onglet, avec leurs paramètres ;
  - les sélecteurs fonctionnent ;
  - le titre de chaque page reprend son entrée (docs/88).
- **Captures sur la démo**, sur ordinateur et téléphone, en clair et en sombre :
  - le menu ;
  - Progresser, sur ses deux onglets ;
  - le menu du compte.

## À trancher en essayant

- **Si Profil te manque dans le menu**, il revient en une ligne, en quatrième entrée.

## Écarts

- **Les rubriques sont des pastilles**, pas un sélecteur comme Calendrier / Liste : Emploi · Économie · Vidéos et Catalogue · Suivies sont des liens (l'adresse change, le retour du navigateur marche), et les Actualités ont déjà un sélecteur Domaine / Tout juste dessous. Deux sélecteurs identiques l'un sur l'autre se confondaient.
- **« Marché de l'emploi » devient « Emploi »** partout (c'était déjà son nom court sur téléphone).
- **Le chiffre de l'onglet Actualités** suit la règle d'avant : il compte les nouveautés depuis la dernière visite, il disparaît donc une fois les Actualités ouvertes, et le point du menu avec lui.
- **Vérifié** :
  - 319 tests de l'interface (mis à jour : les trois entrées, Profil en tête du menu du compte, le point, les anciennes adresses avec leurs paramètres, `/progresser` qui rouvre le dernier onglet) et 530 tests serveur, lint et typecheck ;
  - captures sur la démo, sur ordinateur en clair et en sombre et sur téléphone : le menu et son point, Progresser sur ses deux onglets, le menu du compte ; sans débordement.
