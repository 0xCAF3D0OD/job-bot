# 69 — Revue après 0.49 à 0.56 : les comptes, puis le ménage (versions 0.56.1 et 0.56.2)

> Statut : **validé** le 2026-10-18 ; 0.56.1 (§1) et 0.56.2 (§2 à §5) livrées.
> Huit versions de suite (docs/65 à 68) : les vrais comptes (chacun ne voit que ses données), les invitations, l'export et la suppression du compte, l'accueil, la page « La plateforme », les nouvelles illustrations, la connexion jour et soir, le titre animé. La partie illustrations a été refaite plusieurs fois en un jour ; il en reste des traces. Relecture du serveur (sécurité des comptes) et de l'interface (restes, documentation, accessibilité), en lisant le code ; chaque constat ci-dessous a un fichier et une ligne.

## 1. La sécurité des comptes (0.56.1, à livrer d'abord)

| Gravité | Constat | Correction |
|---|---|---|
| **Haute** | **Les Actualités répondent sans connexion, au nom de ton compte.** Le serveur les laisse publiques (`auth/middleware.py:25-28`) et, sans connexion, fait tourner la requête comme l'exploitant (l. 163). N'importe qui peut lire tes sources suivies, tes pays et langues, et **« Mon domaine »** (`/api/news/preferences`), tiré de tes offres postulées ou bien notées : on en déduit ta recherche d'emploi. Une lecture anonyme peut même écrire dans ton profil (première lecture, `news.py:182-188`) et lancer un relevé (l. 280). Depuis 0.55.0, l'interface ne montre plus les Actualités sans connexion, mais le serveur n'a pas suivi. | Les trois adresses `/api/news…` quittent la liste publique ; sans connexion, plus aucun compte par défaut (les pages restées publiques, connexion et « Tes données », n'en ont pas besoin). Un test : sans connexion, `/api/news` et `/api/news/preferences` répondent 401. |
| Moyenne | **Un lien d'invitation peut servir deux fois** s'il est envoyé deux fois en même temps : il est lu sans verrou et marqué « utilisé » à la fin (`auth/links.py:64-103`). Deux comptes peuvent naître du même lien ; « Bob » et « bob » peuvent aussi passer ensemble (la vérification ignore la casse, la base non). | Le lien est verrouillé à la lecture ; l'identifiant devient unique sans tenir compte de la casse (index sur `lower(username)`, migration). |
| Moyenne | **Le journal des tâches est commun** : tout compte connecté voit toutes les exécutions et leurs messages d'erreur (`api/routes/status.py:97-103, 128-140`), qui peuvent citer la boîte mail de l'exploitant ou des données d'un autre compte. | Le détail (avec les erreurs) réservé à l'exploitant ; les autres comptes ne voient que l'état de leur collecte. |
| Basse | **Le choix d'adresse d'une entreprise s'impose à tous** : il modifie le cache commun des entreprises (`api/routes/registry.py:126-147`). | Le choix manuel reste dans l'offre du compte ; seul l'exploitant écrit dans le cache commun. |
| Basse | **L'export n'est pas complet**, alors que son LISEZ-MOI dit « rien d'autre n'est gardé sur toi » (`api/routes/account.py:96-105`) : il manque les formations suggérées pour tes profils, ta ligne de compte (identifiant, adresse de réception, dernière connexion) et tes sessions (navigateurs). | Ajoutés à l'export (`account.json`, sans le mot de passe haché). |
| Basse | **Si le rôle de base de données manque**, la séparation des comptes est contournée sans bruit (`db/base.py:32-34`). | Erreur au démarrage, hors tests. |
| Basse | **Supprimer son compte** demande le mot de passe, mais sans limite d'essais (`account.py:174-192`). | La même limite d'essais que la connexion. |
| Basse | **L'accueil** : changer de métier à l'écran 2 laisse l'ancien dans « Mon domaine » (`welcome.py:45-54`, il ajoute sans jamais retirer). | Le métier choisi remplace celui que l'accueil avait mis, sans toucher aux mots ajoutés ailleurs. |

**Le test des deux comptes** appelle bien toutes les routes, y compris l'accueil, l'export et « Tes données », mais jamais **sans connexion** : c'est pourquoi il n'a pas vu la fuite des Actualités. Il gagne un passage anonyme sur toutes les routes (seules la connexion, les liens d'accès et « Tes données » doivent répondre), et son contrôle de fuite sur l'export ouvre le ZIP au lieu de chercher dans les octets compressés (`tests/test_accounts.py:376`).

**Vérifié sans problème** : les 27 tables par compte (séparation par la base, valeur par défaut, suppression en cascade) ; les sept fonctions spéciales (chemin fixé, droits retirés, elles ne renvoient qu'un identifiant ou un total) ; l'accueil (un compte ne lit ni n'écrit celui d'un autre) ; l'export (ni mot de passe, ni jeton, rien d'un autre compte) ; la suppression (l'exploitant protégé, sessions, liens et fichiers supprimés) ; les liens (256 bits, seule l'empreinte gardée, expiration contrôlée) ; la documentation de l'API fermée en production.

## 2. L'assistant, encore à l'heure de 0.54 (0.56.2)

| Constat | Correction |
|---|---|
| Son guide dit des Actualités « accessible sans connexion » et « seules les Actualités sont publiques » (`assistant-v5.md:111, 129`). | Pages publiques : connexion, « La plateforme », « Tes données », liens d'accès. |
| Il ne connaît pas **« La plateforme »** ; il ne peut pas proposer `/tes-donnees` ni `/bienvenue` (chemins autorisés, l. 20-26). | Ajoutés. |
| « Sept questions » : l'accueil en a huit depuis l'écran de la date de remise ORP ; le libellé « Refaire l'accueil » n'est pas repris ; la rubrique Compte ne cite ni l'export ni la suppression. | Corrigé. |

La consigne passe en **`assistant-v6`** ; un test vérifie qu'elle cite « La plateforme » et ne dit plus que les Actualités sont publiques.

## 3. Le ménage (0.56.2, rien ne change à l'écran)

| Reste | Correction |
|---|---|
| `Illustration.vue:17` cherche une version de 1200 px qui n'existe plus ; la prop `size` n'est jamais passée et n'a aucun style. | Retirées. |
| `scripts/illustrations.mjs` : l'option `ovale` et sa fonction ne servent plus. L'en-tête de `scripts/illustrations-undraw.mjs` décrit encore l'ancien emplacement et les anciennes règles de couleur. | Retirée ; en-tête à jour. |
| `.illu` : largeur de base de 120 px, jamais utilisée telle quelle, et 200 px sur téléphone (plus grand que sur ordinateur) (`style.css:2100, 2135`). | Une seule base cohérente, sans rien changer aux tailles affichées. |
| Commentaires périmés : `IllustratedSide.vue:4` (« 220 px au plus », c'est 300), la connexion (« une illustration à gauche », c'est une scène). | À jour. |
| `docs/interface.md` : « 320 par étape » pour La plateforme (c'est 250, 190 sur téléphone) ; le personnage du titre absent de la famille d'illustrations ; « 480 et 800 px » sans la connexion (1264) ; trois durées non listées (le chemin de La plateforme, la phrase de la connexion, son ciel). | Règles à jour, exceptions écrites. |
| docs/67 : « les 14 dessins » en réserve (il en reste 7) ; les tables du §2 ne signalent pas ce que les compléments 0.55.1 et 0.55.2 ont remplacé. | Renvois ajoutés. |
| `DiscoverView.vue:203` : `data-index="6"` écrit en dur. | Calculé. |

## 4. L'accessibilité (0.56.2)

- **L'accueil** : en changeant d'écran, le bouton qui avait le focus disparaît et le focus tombe en haut de la page ; le clavier et les lecteurs d'écran perdent leur place. Le focus va au titre du nouvel écran. L'écran « La suite » (le personnage qui parle) n'a pas de titre : sa bulle en devient un.
- **La plateforme** : les pastilles 1 à 6 et l'étoile sont lues en plus de la liste numérotée ; elles deviennent décoratives. Avec « réduire les animations », le chemin suit encore le défilement : il s'affiche entier, comme le doc 67 le dit.
- **Le voile des pages qui chargent** : sa petite montée d'entrée n'est pas coupée par « réduire les animations ».
- **La connexion** : la phrase « Less searching. More living. » est cachée aux lecteurs d'écran (deux `aria-hidden` imbriqués). Elle reste décorative : le titre « Se connecter » et le texte du formulaire disent l'essentiel.

## 5. Le test instable

Un test a échoué une fois sous charge (0.55.2). Le plus probable : `BrandFigure.test.ts` (horloge simulée et chargement d'un dessin à la demande, avec une attente d'une seconde) ; `LoadingDrawing.test.ts` a le même mécanisme sans horloge simulée. Les deux chargent leur dessin avant de démarrer l'horloge simulée, avec une attente plus longue. Vérification : toute la suite lancée 20 fois de suite pendant que la construction tourne, sans échec.

## 6. Vérifications

- Tous les tests passent, sans en retirer ; nouveaux tests : Actualités et toutes les routes privées refusées sans connexion, lien d'invitation utilisé deux fois en même temps (un seul compte), identifiant unique sans la casse, journal des tâches réservé, export complet, limite d'essais à la suppression, métier remplacé à l'accueil, consigne `assistant-v6`, focus de l'accueil.
- Une migration (identifiant unique sans la casse), vérifiée sur une copie de ta base, effacée ensuite.
- Captures avant / après d'Aujourd'hui, de la connexion, de La plateforme et de l'accueil : **identiques** (le ménage ne change rien à l'écran).

## 7. Livraison

Deux PR : **0.56.1** (§1, la sécurité, à fusionner vite) puis **0.56.2** (§2 à §5).

## Points à valider

1. **Fermer les Actualités sans connexion côté serveur**, et plus aucun compte par défaut sans connexion (§1, haute).
2. **Les autres corrections de sécurité** : lien verrouillé et identifiant unique sans la casse, journal des tâches réservé, cache des entreprises, export complet, rôle de base vérifié, limite d'essais, métier de l'accueil (§1).
3. **Le test des deux comptes** étendu aux appels sans connexion (§1).
4. **L'assistant** à jour, consigne `assistant-v6` (§2).
5. **Le ménage** et **l'accessibilité** (§3, §4), sans rien changer à l'écran sauf le focus de l'accueil.
6. **Le test instable** stabilisé (§5).
7. **Deux PR**, la sécurité d'abord (§7).

## Écarts avec la livraison (0.56.1)

- **Les Actualités** : les trois adresses quittent la liste publique ; sans connexion, plus aucun compte n'est rattaché à la requête. Côté interface, le compteur des Actualités du menu ne s'interroge plus qu'une fois connecté (il recevait maintenant un refus toutes les 5 minutes). Vérifié : sans connexion, `/api/news` et `/api/news/preferences` répondent 401, « Tes données » et la connexion répondent ; la page de connexion et « La plateforme » ne font plus d'appel aux Actualités.
- **Le test sans connexion** appelle toutes les routes du schéma (plus de 140) sans cookie : toutes répondent 401 sauf la connexion, les liens d'accès, « Tes données », l'agenda et l'extension (qui vérifient leur propre jeton) ; aucune ne montre une donnée de A ni ne modifie quoi que ce soit. En remettant les Actualités publiques, il échoue : il aurait vu la fuite.
- **Le lien d'invitation** est verrouillé dès sa lecture. Le test est déterministe : pendant qu'une transaction tient le lien, une seconde attend (délai de verrou dépassé), puis le trouve utilisé ; sans le verrou, il échoue. Un premier test qui lançait les deux demandes « en même temps » passait aussi sans le verrou : remplacé.
- **L'identifiant unique** sans tenir compte des majuscules : migration **0050** (index sur `lower(username)`). Vérifiée sur une copie de ta base (aucun doublon, la connexion prend bien le rôle de l'application), effacée ensuite.
- **Le journal des tâches** (`/api/job-runs`) : réservé à l'exploitant (403 pour les autres). Dans l'état de la collecte, les autres comptes voient l'échec avec « voir avec l'exploitant » au lieu du message.
- **Le choix d'adresse** d'une entreprise : celui d'un autre compte que l'exploitant ne s'écrit plus dans le cache commun ; il vaut pour ses propres offres.
- **L'export** ajoute `compte.json` (identifiant, dates, plafond de l'IA, code de l'adresse de réception, sans l'empreinte du mot de passe), `sessions.json` (dates et navigateur, sans jeton) et `data/trainings.json` (formations suggérées pour tes profils) ; son LISEZ-MOI le dit.
- **Le rôle de base** : si la base a les règles de séparation mais pas le rôle de l'application, la connexion est refusée ; une base pas encore migrée reste joignable (l'état dit qu'elle est à mettre à jour).
- **La suppression du compte** : après cinq mots de passe faux, il faut attendre (429), comme à la connexion.
- **L'accueil** : changer de métier retire l'ancien de « Mon domaine », sans toucher aux mots ajoutés ailleurs ; le profil est verrouillé pendant la modification.
- **Tests** : 440 côté serveur (9 nouveaux), 253 côté interface.

## Écarts avec la livraison (0.56.2)

- **L'assistant** : consigne `assistant-v6` (pages publiques, « La plateforme », accueil avec la date de remise, « Refaire l'accueil », tes données dans Réglages › Compte, liens `/tes-donnees`, `/bienvenue`, `/la-plateforme`). En plus du cadrage : l'interface n'acceptait pas les liens vers le **Bilan** (`/candidatures/bilan`), pourtant cités dans le guide depuis 0.48 ; ils passent, avec les trois nouveaux.
- **Le ménage** : `Illustration` sans la version de 1200 px ni la prop `size` ; le script des images sans l'option `ovale` (régénérées : identiques) ; l'en-tête du script unDraw à jour ; `.illu` a une base de 300 px et plus de règle téléphone (chaque usage fixe sa largeur : rien ne change à l'écran, mesuré dans l'accueil et La plateforme) ; commentaires à jour ; `docs/interface.md` (tailles de La plateforme, personnage du titre hors famille, 1264 px de la connexion, durées de la connexion et du chemin) et docs/67 (réserve, renvois dans les tables) corrigés.
- **L'accessibilité** : dans l'accueil, le focus va au titre de chaque nouvel écran (test qui échoue sans) ; la bulle de « La suite » est le titre de son écran, à l'identique à l'écran ; les pastilles de La plateforme sont décoratives, son chemin est entier d'emblée avec « réduire les animations » ; la montée du voile des pages qui chargent est coupée aussi. La phrase de la connexion reste décorative.
- **Le test instable** : `BrandFigure` et `LoadingDrawing` chargent leur dessin avant de démarrer, avec une attente de 5 s ; l'horloge simulée ne touche plus que les minuteries et la date. Toute la suite lancée **20 fois** pendant que la construction tournait en boucle : **aucun échec**.
- **Tests** : 254 côté interface, 440 côté serveur.
