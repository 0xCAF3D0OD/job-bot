# 76 — Revue après 0.57 à 0.62 (versions 0.62.1 et 0.62.2)

> Statut : **validé** le 2026-10-18.
> Six versions depuis la dernière revue (docs/69) : le remplissage de Job-Room par l'extension, l'installation en un clic, la démo publique et `make demo`, les offres allégées, les actions rangées dans « ⋯ », l'entraînement à l'entretien. Relecture du serveur (sécurité, ménage), de l'interface (restes, cohérence, documentation), de l'extension et de l'accessibilité, en lisant le code. Chaque constat ci-dessous a un fichier et une ligne ; les plus graves ont été vérifiés une seconde fois.

## 1. À corriger d'abord (0.62.1)

| Gravité | Constat | Correction |
|---|---|---|
| **Haute** | **`jobbot demo-seed` peut effacer une vraie base.** Le garde-fou (`demo/__init__.py:22-36`) ne regarde que les comptes : il laisse passer une base dont le seul compte est l'exploitant **sans mot de passe**, ce qui arrive sur une installation neuve ou sans connexion (`JOBBOT_AUTH_ENABLED=false`). Le remplissage supprime alors tous les comptes, donc toutes les données (`demo/seed.py:84-89`). La commande ne vérifie même pas que le mode démo est allumé (`__main__.py:66-86`). | La commande refuse sans `JOBBOT_DEMO=true`. Le garde-fou refuse aussi dès qu'il trouve une offre, une candidature ou un document hors du compte fictif, et une base de démo porte un marqueur posé au premier remplissage. Tests : base d'exploitant sans mot de passe avec une candidature → refus, rien d'effacé. |
| **Moyenne** | **« Un seul cadre par bloc » n'est jamais arrivé dans main.** Le dernier ajout de la 0.61.0 a été poussé après ta fusion de la PR #179 : le tableau des preuves, le journal des alertes, Sites suivis, Sources et « Comment l'ajouter » ont toujours leur double cadre. | Le reprendre tel quel (règles CSS et complément du doc 74). |
| Moyenne | **Le jeton de liaison de l'extension n'expire pas vraiment.** La révocation « s'il n'est pas lu dans les 2 minutes » n'existe que dans la page (`ExtensionLinkView.vue:47`) : si l'onglet est fermé avant, le jeton reste valide sans limite. Le README l'annonce pourtant (`extension/README.md:32-33`). | Le serveur refuse et supprime un jeton jamais utilisé, créé il y a plus de 2 minutes. Test. |
| Basse | **En démo, un téléchargement écrit en base** : le CSV des preuves enregistre le mois comme « exporté » (`api/routes/orp.py:244-247`), même pour un visiteur. | En démo, toutes les requêtes passent en lecture seule dans la base (`SET TRANSACTION READ ONLY`), ce qui couvre aussi les lectures qui écrivent. |
| Basse | **L'entraînement accepte deux réponses en même temps** : deux envois simultanés peuvent ajouter deux questions et payer deux appels (`interviews/practice.py:329-351`). L'interface bloque le double clic, donc c'est peu probable. | Verrou sur l'entraînement pendant un échange, et statut revérifié avant d'ajouter un tour. |
| Basse | **Le plafond de l'entraînement est estimé un peu court** : la dernière réponse déclenche le retour (environ 0,06 $) mais n'est estimée qu'à 0,02 $ (`practice.py:339`). | Estimation du retour quand c'est la dernière question ; constantes nommées. |

**Vérifié sans problème** : la séparation des comptes pour la nouvelle table des entraînements (une candidature d'un autre compte → 404), la portée du jeton de l'extension (seulement `/api/extension/…`), l'origine vérifiée exactement lors de la liaison en un clic, le jeton jamais transmis au script de la page Job-Room, l'extension qui ne soumet jamais le formulaire, les permissions minimales, le mode démo qui refuse toute écriture (connexion comprise), l'IA de l'entraînement sans outil et ses réponses affichées comme du texte (pas de HTML), rien de personnel envoyé à l'IA.

## 2. L'assistant, encore à l'heure de 0.57 (0.62.2)

Sa consigne (`assistant-v7.md`) ne connaît rien depuis 0.57 :
- les offres groupées par jour, la note en cercle, « Plus de filtres » (l. 77) ;
- les « ⋯ » : celui d'Entreprise et d'Annonce dans une offre, celui des lignes du Suivi, de la barre des Preuves ORP, des Entretiens (l. 78-91). Il parle encore de « Voir chez l'employeur » et de liens visibles qui ont bougé ;
- l'entraînement à l'entretien (ses trois entrées, le coût, jamais compté comme un vrai entretien) ;
- l'extension depuis la boutique et la liaison en un clic (l. 108, 126), la page `/extension/relier` dans ses liens ;
- la démo publique.

La consigne passe en **`assistant-v8`** ; un test vérifie qu'elle cite l'entraînement et les « ⋯ ».

## 3. La cohérence de l'interface (0.62.2)

| Constat | Correction |
|---|---|
| Une offre **pas encore notée** garde une pastille « à noter » à côté des cercles (`OfferCard.vue:69-72`). | Un cercle vide en pointillés, avec « – » ou « à noter » au survol. |
| Des **« ⋯ » à une seule action ordinaire**, contre la règle du doc 74 : Annonce (souvent un seul site), Entreprise (parfois « Contacts » seul), Entretiens (parfois « M'entraîner » seul). | Le menu commun affiche directement l'action quand il n'en a qu'une, sans suppression. |
| Le panneau d'une candidature garde **trois liens côte à côte** dans Documents (Lettre, CV, Lien de candidature), avec d'autres libellés que le « ⋯ » du tableau (`ApplicationPanel.vue:325-356`). | Les mêmes libellés partout (« Lettre (Word) », « CV (Word) », « Ouvrir l'annonce ») ; la lettre reste visible, le reste dans le « ⋯ » de la partie. |
| Les **noms des « ⋯ »** varient : « Plus d'actions sur ce mois », « Voir l'annonce sur les sites », « Plus d'actions »… | Partout « Actions sur … », comme le dit le doc 74. |
| **« M'entraîner »** : trois conditions différentes pour l'afficher, et un bouton plein dans la préparation contre un lien dans Mes enseignements. Ouvert depuis le panneau d'une candidature, l'entraînement ne met pas à jour la liste « Mes entraînements ». | Une seule condition (l'IA configurée) ; le même style ; la liste suit. |
| Un entraînement terminé **sans retour lisible** laisse une fenêtre vide (`InterviewPractice.vue:426`) ; un échec au premier échange ne rend pas l'entraînement créé. | Un message et « Réessayer le retour » ; le premier échec rend l'entraînement en attente, avec « Réessayer ». |

## 4. L'accessibilité (0.62.2)

- **L'entraînement** : le focus n'est pas gardé dans la fenêtre, il ne va nulle part à l'ouverture, Échap ne ferme que si le focus est dedans, et il ne revient pas au bouton d'ouverture. La zone annoncée relit aussi ta propre réponse. Le défilement doux ignore « réduire les animations ».
- **Le repère « À retravailler »** : rouge sur fond rose, contraste 4,4:1, un peu sous le minimum (4,5:1) pour un petit texte. Texte un peu plus foncé.
- **Le menu « ⋯ »** : la liste n'a pas de nom pour les lecteurs d'écran ; Tab ne le ferme pas ; les flèches peuvent buter sur une action indisponible ; Début et Fin ne sont pas gérés.

## 5. Le ménage (0.62.2, rien ne change à l'écran)

| Reste | Correction |
|---|---|
| **CSS mort** : `.row-actions`, `.small-link`, `.kw-missing`, `.stat…` (l'ancien Aujourd'hui), `.score.high/.mid/.low/.stale` et leur version sombre. Doublons : `.filter-customize`, `.more-menu`, `.offers-grid`, `.practice-head h3`. | Retirés ou fusionnés. |
| **Code en double** entre les pistes de l'IA et l'entraînement : nettoyage du texte, lecture de la réponse `<reponse>`, contexte de l'offre, contrôle du plafond et appel à l'IA. Le modèle est écrit en dur trois fois. | Un petit module commun. Au passage, les pistes de l'IA enregistrent le coût d'une réponse illisible (aujourd'hui annulé avec l'erreur). |
| Petits doublons : `Day` (deux fois), `_today` / `local_today`, les valeurs permises de l'entraînement (module et routes), `JobRoomFillOut` qui recopie `JobRoomFill`. | Une seule source chacun. |
| **« Ajouter à À préparer »** réutilise un modèle qui exige `done` et limite à 200 caractères ; un point plus long que l'IA renverrait donne une erreur. Une réponse faite d'espaces donne 409, une vide 422. | Un modèle à part ; points tronqués à 200 ; réponse nettoyée à la validation. |
| **L'extension** : le script Job-Room se reconnaît par une variable globale de la page (une page pourrait la fournir) ; un champ devenu `textarea` arrêterait tout le remplissage ; la question « assignée par l'ORP » est trouvée par le premier « oui/non » de la page. | Le script passé directement, sans variable globale ; le bon setter selon le type de champ ; le groupe ciblé par son intitulé. Nouvelle version de l'extension, 0.58.2, à renvoyer à Mozilla. |
| **Docs** : `exploitation.md` dit encore « hors Actualités » pour `JOBBOT_AUTH_ENABLED` ; le doc 75 dit « en flux » au §10 ; le README de l'extension dit « ne coche aucune case » ; `docs/interface.md` n'a aucune des règles récentes. | À jour. `interface.md` gagne : la note en cercle, la règle des « ⋯ », une ligne par élément et par jour, un seul cadre par bloc, plein écran sur téléphone pour l'entraînement. |
| **`make demo`** ouvre le navigateur après 5 secondes fixes. | Il attend que l'interface réponde. |

## 6. Les tests qui manquent

- Le garde-fou de la démo sur une base d'exploitant sans mot de passe ; `demo-seed` sans le mode démo ; le CSV en démo qui n'écrit rien.
- Le jeton de liaison expiré au bout de 2 minutes.
- L'entraînement : « Réessayer » quand le recruteur a déjà répondu, « Terminer » sur un entraînement terminé, réponses de l'IA illisibles (pas de balise, JSON faux, liste au lieu d'objet), départ sur une candidature inconnue (404).
- Le test du garde-fou de la démo vérifie d'abord que sa base de test est propre (sinon il passerait pour une autre raison).

## 7. Livraison

| Version | Contenu |
|---|---|
| **0.62.1** | §1 : le garde-fou de la démo, « un seul cadre par bloc », le jeton de liaison, la lecture seule de la démo, l'entraînement verrouillé et mieux estimé. Sans migration (le marqueur de démo est un réglage). |
| **0.62.2** | §2 à §6 : `assistant-v8`, cohérence, accessibilité, ménage, docs, tests ; l'extension 0.58.2. Sans migration. |

Vérification : tous les tests sans en retirer, plus ceux du §6 ; captures avant / après des pages touchées par §1 (cadres) et §3, ordinateur et téléphone ; captures identiques pour le ménage du §5.

## Points à valider

1. **0.62.1 d'abord**, avec en priorité le garde-fou de la démo (§1).
2. **« Un seul cadre par bloc »** repris dans 0.62.1, tel que tu l'avais validé (§1).
3. **`assistant-v8`** (§2).
4. **Les corrections de cohérence** du §3, notamment : afficher directement l'action d'un « ⋯ » qui n'en a qu'une, et le cercle en pointillés pour une offre pas encore notée.
5. **Une nouvelle version de l'extension (0.58.2)** à envoyer à Mozilla après la tienne en revue (§5).
6. **Deux PR, 0.62.1 puis 0.62.2**, sans migration (§7).

## Écarts avec le cadrage (0.62.1)

- **Une migration (0053)**, contrairement au « sans migration » prévu : le jeton de liaison a une date d'expiration (`expires_at`), posée à la création par « Relier ce navigateur » et effacée à sa première utilisation. La fonction qui retrouve le compte d'un jeton refuse un jeton expiré. Les jetons créés à la main n'en ont pas. Passer par la date de révocation aurait évité la migration, mais un jeton pas encore lu serait déjà considéré comme révoqué.
- **Pas de marqueur de démo** : le garde-fou regarde directement les données. Il refuse dès qu'un compte autre que le compte fictif a une offre, une candidature, un document ou un bloc de profil, et la commande refuse sans `JOBBOT_DEMO=true`. Un marqueur n'apportait rien de plus.
- **La lecture seule de la démo a trouvé deux autres lectures qui écrivaient** : la liste des formations (mise à jour du catalogue) et la page des alertes (propositions de recherches). Avec la base en lecture seule, elles cassaient la démo ; en démo, elles n'écrivent plus. Vérifié en parcourant toutes les pages de la démo, volets ouverts : 197 appels, aucune erreur. Un test garde ces deux pages.
- **Le verrou de l'entraînement** : le test des deux envois simultanés vérifie le résultat (un seul passe, une seule question suit). Mais avec le client de test, les deux requêtes ne se chevauchent pas vraiment : il passe aussi sans le verrou. Le verrou reste justifié par la lecture du code.
- **« Un seul cadre par bloc »** repris tel qu'il avait été validé ; le même parcours de toutes les pages ne trouve plus aucun cadre dans un cadre.
