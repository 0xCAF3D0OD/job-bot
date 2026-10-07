# 19 — Navigation par grandes catégories (version 0.12.0)

> Statut : **validé** le 2026-10-07 (rubrique « Candidatures »). livré : PR a (menu, rubrique Candidatures).
> Retours d'usage du 2026-10-07 : réunir Offres et Candidatures ; ranger la plateforme par catégories claires.

## 1. Six entrées, une par question

| Menu | La question | Contenu |
|---|---|---|
| **Aujourd'hui** | Où j'en suis ? | page d'accueil après connexion (§3) |
| **Candidatures** | Que faire pour trouver un emploi ? | Offres, Suivi, Preuves ORP, Journal des recherches (§2) |
| **Actualités** | Comment évolue le marché ? | inchangé |
| **Formations** | Que puis-je améliorer ? | inchangé |
| **Profil** | Qui suis-je ? | Ce que je cherche, Mon parcours, Mes coordonnées (inchangé) |
| **Réglages** | Comment la plateforme fonctionne ? | regroupés par thème (§4) |

- Les six entrées tiennent sur une ligne (la barre élargie de la PR #65 est gardée).
- **Profil** et **Réglages** reviennent dans la barre. Le menu du compte (icône) ne garde que le **profil affiché** (profils d'essai) et **Se déconnecter**.
- Sans connexion : toujours seulement les Actualités.

## 2. « Candidatures » : une rubrique, quatre onglets

Nom retenu par Kevin (plutôt que « Trouver du travail ») ; « Jobs » reste possible si tu le préfères. L'onglet de suivi s'appelle donc **Suivi**, pour ne pas répéter « Candidatures ».

Sous le titre de la rubrique, quatre onglets toujours visibles :

| Onglet | Aujourd'hui dans | Pastille |
|---|---|---|
| **Offres** | page Offres | nombre d'offres à examiner |
| **Suivi** | Candidatures › Suivi | nombre à relancer |
| **Preuves ORP** | Candidatures › Preuves ORP | lignes à compléter |
| **Journal des recherches** | Candidatures › Journal | — |

- **Offres** garde sa mise en page (filtres à gauche, détail qui entre par la droite).
- **Suivi** et **Preuves ORP** partagent l'en-tête du mois (mois, « 14 / 20 », état des preuves, « Ajouter une candidature »), comme aujourd'hui.
- « Marquer comme envoyée » depuis une offre et « Préparer ma candidature » ne changent pas ; après l'envoi, un lien « Voir le suivi » ouvre l'onglet.
- **Adresses** : `/candidatures/offres`, `/candidatures/suivi`, `/candidatures/preuves`, `/candidatures/journal` ; `/candidatures` seul ouvre les Offres. Les anciennes (`/offres`, `/orp`, `/journal`, `/candidatures?vue=…`, liens des alertes et rappels) redirigent vers le bon onglet, avec le mois.

## 3. Aujourd'hui, la page d'accueil

Un bloc par catégorie, chacun avec un lien vers sa rubrique :

| Bloc | Contenu |
|---|---|
| **Candidatures** | offres à examiner (les 3 mieux notées), candidatures à relancer, preuves du mois (« 14 / 20, à remettre avant le 5 ») |
| **Comprendre le marché** | les 3 dernières actualités de ton domaine |
| **Progresser** | formations en cours, et une formation de ton domaine pas encore suivie |
| **Pour bien démarrer** | la liste actuelle, tant qu'elle n'est pas terminée |

C'est la page ouverte après la connexion.

## 4. Réglages regroupés

Une colonne de sommaire à gauche (ancres), puis les sections dans cet ordre :

1. **Recherche d'emploi** : objectif mensuel ORP, date limite des preuves, sites suivis, seuil de notification des offres.
2. **Actualités** : « Mon domaine », sources, veilles.
3. **Notifications** : ntfy et test.
4. **IA** : plafond mensuel et dépense du mois.
5. **Profils d'essai**.
6. **Connexion** : compte, « Se déconnecter partout ».
7. **État technique**.

Rien n'est supprimé : seuls l'ordre et les titres changent.

## 5. Livraison en deux PR

| PR | Contenu |
|---|---|
| **0.12.0-a** | Menu à six entrées, rubrique « Candidatures » à quatre onglets, redirections |
| **0.12.0-b** | Page Aujourd'hui par catégories, Réglages regroupés |

Aucune migration : seule l'interface change.

## Points à valider

1. **Six entrées** : Aujourd'hui, Candidatures, Actualités, Formations, Profil, Réglages ; menu du compte réduit au profil affiché et à la déconnexion (§1).
2. **« Candidatures »** (ou « Jobs ») avec quatre onglets : Offres, Suivi, Preuves ORP, Journal des recherches (§2).
3. **Aujourd'hui** en blocs par catégorie (§3).
4. **Réglages** regroupés par thème, avec sommaire (§4).
5. **Deux PR** ; la PR #65 (barre sur une ligne) peut être fusionnée avant, la PR a ajuste le menu du compte (§5).

## Écarts avec la PR a

- **Titre de la rubrique** : il change avec l'onglet (« Les offres pour toi », « Tes candidatures », « Preuves de recherches d'emploi », « Journal des recherches »), sous la mention « Candidatures ».
- **Pastilles** : offres à examiner et candidatures à relancer (comme la page Aujourd'hui), lignes à compléter du mois ORP par défaut ; relues à chaque changement d'onglet.
- **Mois** : il suit d'un onglet à l'autre (`?mois=`).
- **Préparer ma candidature** : `/candidatures/offres/<id>/preparer`, sans les onglets (page à part, comme avant).
- **Anciennes adresses** : `/offres`, `/offres/<id>/preparer`, `/orp`, `/journal`, `/candidatures?vue=…` et `/candidatures?mois=…` redirigent ; les alertes de la cloche et les rappels ntfy pointent sur les nouvelles adresses.
- **Menu du compte** : seulement le profil affiché et la déconnexion ; l'icône n'apparaît pas s'il n'y a rien à proposer (un seul profil, connexion désactivée).
- **Contient la PR #65** (barre sur une ligne) : la fusionner avant, ou la fermer après celle-ci.
