# 116 — Des offres dès le départ, et seulement celles du métier (version 0.85.0)

> Statut : **validé** le 2026-10-21 (« oui pour tout, vas-y »). Ordre retenu : §3 et §4 en 0.85.0 ; §1 en 0.86.0 ; §2 b et c ensuite.
> Origine : tes questions du 2026-10-21 : « comment faire pour que l'utilisateur ait déjà des offres en créant son compte ; s'il a déjà un compte, il serait bien de pouvoir le lier à son compte jobA1 », et, plus tôt le même jour : « pourquoi Amy a-t-elle une offre de menuisier ? elle est communicante », « les actualités d'Amy ne sont pas en lien avec son travail ».
> Se construit sur docs/03 (la collecte), docs/104 (les premières offres, coupées en 0.82.4), docs/112 (les codes des sites), docs/113 (la boîte des invités) et docs/15, docs/16 (les actualités).
> Je ne suis pas juriste : les points marqués « à vérifier » touchent aux conditions d'utilisation de sites tiers.

## Le constat

| Problème | Pourquoi |
|---|---|
| **Un nouveau compte est vide** pendant un à trois jours | les offres n'arrivent que par les e-mails d'alerte ; la recherche publique de jobup, qui donnait les premières offres (docs/104), est coupée : ses conditions (§7) interdisent les robots |
| **Une personne qui a déjà des alertes jobup** doit tout recréer | jobA1 ne lit que son adresse `alertes+nom-code@joba1.ch` |
| **Des offres hors métier** (le menuisier d'Amy, communicante) | jobA1 garde toutes les offres d'un e-mail jobup, **« Recommandations jobup » comprises** ; le filtre regarde le lieu, le taux, le contrat, les langues, jamais le métier |
| **Des actualités hors métier** | le catalogue suit l'emploi en général (RTS, Le Temps, SECO) et l'informatique (ton métier) ; rien sur la communication, la boulangerie, la santé… Quand rien ne parle du métier, l'aperçu montre l'économie en général |

## La proposition

### 1. Lier ses alertes existantes : une règle de transfert, jamais un mot de passe

jobup, jobs.ch et Indeed n'offrent aucun moyen de connecter un compte à une autre application. jobA1 **ne demandera jamais le mot de passe d'un site** (c'est interdit par leurs conditions, et c'est l'accès complet au compte).

Le chemin : la personne garde ses alertes là où elles sont, et **sa propre boîte e-mail transfère les e-mails d'alerte** vers son adresse jobA1.

- Dans l'assistant des alertes, une entrée **« J'ai déjà des alertes sur jobup / Indeed »**.
- Un pas-à-pas selon sa messagerie (Gmail, Outlook, Infomaniak, Bluewin, autre), avec le filtre **prêt à copier** : seulement les expéditeurs des alertes (`from:(alertes@jobup.ch OR …)`), **jamais** tout ce que le site envoie (pas les réinitialisations de mot de passe, pas les messages des recruteurs).
- **Gmail demande de confirmer l'adresse de transfert** : il envoie un code à l'adresse jobA1 ; jobA1 l'affiche déjà sur la page Alertes (docs/112). La personne le recopie dans Gmail.
- Les alertes existantes amènent des offres **dès le lendemain**, souvent dès la première heure.
- **À vérifier par un essai** avant d'écrire le code : qu'un e-mail transféré par Gmail garde l'expéditeur d'origine (jobup le reconnaît) et que la boîte Infomaniak le range bien au bon compte (l'en-tête `Delivered-To`, lu par jobA1, doit porter `alertes+nom-code@joba1.ch`).

### 2. Des offres dès la création du compte

Trois voies, de la plus sûre à la plus incertaine :

**a. Le transfert (§1)**, pour qui a déjà des alertes : le plus rapide, aucun risque.

**b. Les offres que jobA1 connaît déjà.** jobA1 reçoit chaque jour des annonces publiques pour tous ses comptes. À la création d'un compte, on lui montre celles **des 14 derniers jours** qui correspondent à son métier et à ses lieux (au plus 20), notées comme les autres.
  - Seule l'annonce passe d'un compte à l'autre : titre, entreprise, lieu, lien vers le site. **Jamais l'e-mail**, jamais qui l'a reçue, jamais une note ni une candidature d'un autre compte.
  - Une table d'annonces commune à la plateforme, à part des tables personnelles (docs/78).
  - Limite : utile seulement s'il y a assez de comptes ; au début, peu d'annonces par métier.
  - **À vérifier** : que les conditions de jobup et d'Indeed permettent de montrer à une personne une annonce reçue par une autre (on ne montre que le titre et le lien vers leur page).

**c. Job-Room (le site de l'ORP).** C'est un service public (SECO) ; il a une interface de données, mais je n'ai trouvé **aucune condition d'accès publiée**. Je propose de **demander un accès officiel** au SECO (travail.swiss), plutôt que de lire le site par robot. Cette démarche sert aussi ta présentation à l'ORP.

### 3. Seulement les offres du métier

- **Les recommandations de jobup** (« Recommandations jobup », « Ces offres pourraient t'intéresser ») ne sont gardées que si **leur titre contient un mot de l'alerte ou du métier** (comme le filtre des mots, sans accents ni casse). Les autres sont comptées dans le journal (« 3 recommandations écartées, hors métier »), pas montrées.
- Même règle pour les sites lus par l'IA, qui signalent déjà les blocs de recommandations.
- **Les offres des alertes elles-mêmes** restent toutes : la personne a choisi ses mots sur le site. Une offre hors sujet aura une note basse.

### 4. Les actualités du métier

- **Le catalogue s'élargit par familles de métiers** : communication et marketing, vente et commerce, restauration et métiers de bouche, bâtiment, santé et social, administration et finance, logistique, informatique (l'actuel). Deux ou trois sources romandes par famille, choisies et vérifiées lors du code (un flux RSS public qui marche).
- **À l'accueil**, le métier choisit la famille ; la personne peut en changer dans Progresser.
- **Si rien ne parle du métier cette semaine**, l'aperçu le dit (« Rien de neuf sur ton métier cette semaine ») et propose « Toutes les actualités » ; il ne remplit plus avec l'économie en général.

## Garde-fous

- **Aucun mot de passe d'un site**, jamais.
- **Un filtre de transfert limité aux expéditeurs d'alertes** ; la page le dit : « Ne transfère pas tout : seulement les alertes. »
- **L'annonce commune ne contient que des données publiques** ; supprimer son compte n'enlève pas une annonce que d'autres ont reçue, mais enlève tout ce qui la lie à soi.
- **Pas dans la démo.**

## Écarts (0.85.0 : §3 et §4)

- **§3, seulement jobup** : seuls les e-mails « Suggestions d'offres » de jobup sont des recommandations reconnues (le libellé « Recommandations jobup » du journal). Les sites lus par l'IA ne signalent pas leurs blocs de recommandations, contrairement à ce que disait le cadrage : leurs offres passent toutes, comme avant.
- **§3, la comparaison** : le début des mots (six lettres), sans accents ni casse, pour que « communicante » trouve « Chargé·e de communication » ; les mots trop généraux (« responsable », « assistante », « poste », les villes) ne comptent pas. Les mots du métier : les alertes actives et « Mon domaine ». Sans aucun mot connu, tout passe.
- **§3, le journal** : la colonne « Offres » dit « (+ 4 hors métier, écartées) ».
- **§4, les sources vérifiées** (le flux répond, articles du jour ou de la semaine) : communication, Cominmag et CB News ; commerce, Le Temps — Entreprises et Ecommerce Mag ; bâtiment, espazium (TRACÉS) ; santé et social, Le Temps — Santé et Infirmiers.com ; finance et administration, Investir.ch et Le Temps — Finance ; logistique, Supply Chain Magazine ; informatique, les sources existantes. **Restauration** : aucun flux romand trouvé (GastroJournal, HGZ, htr refusent ou n'en ont pas) ; à la place, une veille Google Actualités du catalogue (« restaurant OR boulangerie OR pâtisserie OR hôtellerie Suisse romande »).
- **§4, les sources créées une fois** par la migration 0064 : un invité ne peut pas créer de source (table de la plateforme), il s'y abonne.
- **§4, les comptes déjà créés** (Amy, Eliot) reçoivent les sources de leur métier à leur prochaine visite des actualités ; une fois par métier.
- **§4, changer de famille** : dans Progresser › Actualités, suivre ou retirer des sources, comme avant ; changer de métier à l'accueil suit la nouvelle famille.
- **§4, l'aperçu** garde les articles qui contiennent un mot du domaine, ceux des sources de la famille et des veilles, et les articles sur l'emploi des sources « marché du travail » (SECO) ; sinon « Rien de neuf sur ton métier pour l'instant. ».

## Vérifié (0.85.0)

- Tests backend : les titres gardés ou écartés (communication, menuisier) ; un vrai e-mail jobup de recommandations, une offre sur cinq gardée pour une alerte « ingénieur système » ; la famille de dix métiers ; chaque famille a des sources ; un compte « Communicante » suit Cominmag et CB News, et un article de Cominmag sans le mot « communicante » sort dans « Mon domaine » ; « Pâtissier » suit la veille de la restauration. 598 tests, ruff, mypy.
- Tests de l'interface : l'aperçu ne demande que le domaine et dit « Rien de neuf sur ton métier » ; le journal compte les recommandations écartées. 407 tests, lint, vue-tsc.

## Écarts (0.86.0 : §1)

- **Où** : sous les deux colonnes de la page Alertes, une ligne repliée **« J'ai déjà des alertes »** (« les transférer »), au-dessus d'« Alertes reçues ». Seulement pour un compte qui a sa propre adresse jobA1.
- **Le pas-à-pas** selon la messagerie : **Gmail** (ajouter l'adresse de transfert, recopier le code, laisser « Désactiver le transfert » coché, puis un filtre « De » → « Transférer à ») ; **Outlook** (une règle « De » → « Transférer à », sans code) ; **Autre** (chercher « règle » ou « filtre »). L'adresse jobA1 avec « Copier l'adresse ».
- **Les expéditeurs à copier** : `candidat@jobup.ch`, `candidat@my.jobup.ch`, `alert@indeed.com`, `donotreply@jobalert.indeed.com`, en filtre Gmail (`from:(… OR …)`) ou en liste. **jobs.ch n'y est pas** : son expéditeur d'alertes n'est pas connu ; à ajouter après un premier e-mail réel.
- **Le code de Gmail** (9 chiffres) est reconnu comme un code de vérification et s'affiche dans « Les e-mails des sites », sous le nom « Gmail ». jobA1 n'ouvre pas le lien de Google : la personne recopie le code elle-même.
- **Le rangement** : un e-mail transféré garde son destinataire d'origine (`To`) ; Gmail ajoute `X-Forwarded-To`, que jobA1 lit désormais pour trouver le compte.
- **Reste à faire, par toi** : un essai réel avec ta boîte Gmail vers une adresse d'invité, pour confirmer que Gmail garde l'expéditeur (jobup reconnu) et que la boîte Infomaniak range bien l'e-mail.

## Vérifié (0.86.0)

- Tests backend : une alerte jobup transférée (`To` : la boîte Gmail, `X-Forwarded-To` : l'adresse jobA1) rangée au bon compte ; le code de confirmation de Gmail (9 chiffres) montré sous « Gmail », avec la notification. 600 tests, ruff, mypy.
- Tests de l'interface : le pas-à-pas Gmail (adresse, code, filtre), Outlook, la copie des expéditeurs ; aucun mot de passe demandé. 408 tests, lint, vue-tsc.
- Captures Playwright à 1440 et 414 px : la ligne sous les colonnes, le filtre qui passe à la ligne sur téléphone.

## §2 b : pas pour les annonces de jobup (vérifié le 2026-10-21)

Les conditions de JobCloud pour les personnes en recherche d'emploi (décembre 2025) interdisent, au §7, d'« extraire, reproduire, copier, vendre, exploiter ou revendre des données du site », et au §8 toute « transmission ou reproduction » au-delà de l'usage personnel, sans l'accord exprès de JobCloud. Montrer à Amy une annonce jobup reçue par Eliot, c'est transmettre une donnée du site à un tiers : **non, sans accord de JobCloud**. Indeed a des règles du même ordre.

Ce qui reste permis : chaque personne reçoit ses propres alertes, sur son adresse ou par son propre transfert (§1). Les annonces partagées entre comptes ne viendront que d'une source qui l'autorise (Job-Room, si le SECO donne un accès, §2 c ; ou des employeurs qui publient eux-mêmes).

## §2 c : la demande d'accès à Job-Room (à envoyer par toi)

À : l'adresse de contact de travail.swiss / Job-Room (SECO, Arbeitsmarkt/Arbeitslosenversicherung).

> Objet : Accès aux offres de Job-Room pour un outil d'aide aux demandeurs d'emploi
>
> Bonjour,
>
> Je développe jobA1, un outil gratuit qui aide les demandeurs d'emploi inscrits à l'ORP à suivre leurs alertes, préparer leurs candidatures et tenir le formulaire « Preuves des recherches personnelles ». Les données restent en Suisse.
>
> Pour que les personnes trouvent des offres dès leur inscription, j'aimerais afficher les offres publiques de Job-Room qui correspondent à leur métier et à leur région, avec un lien vers l'annonce sur Job-Room. Je ne souhaite pas lire le site par un robot sans votre accord.
>
> Existe-t-il un accès officiel (interface de données ou export) pour ce type d'usage, et à quelles conditions ?
>
> Je vous remercie de votre réponse.
>
> Kevin Di Nocera, jobA1 (joba1.ch)

## Les questions

1. **§1, lier ses alertes par une règle de transfert** (avec le pas-à-pas et le code de Gmail affiché par jobA1) : d'accord ?
2. **§2 b, les annonces que jobA1 connaît déjà**, montrées à un nouveau compte : d'accord, sous réserve de vérifier les conditions de jobup et d'Indeed ? Ou attendre ?
3. **§2 c, Job-Room** : veux-tu que je prépare la demande d'accès au SECO (un e-mail court, à envoyer toi-même) ?
4. **§3, les recommandations hors métier écartées** (comptées dans le journal) : d'accord ? Ou les garder, repliées sous « Recommandations » ?
5. **§4, les actualités par familles de métiers**, et « rien de neuf » plutôt que l'économie : d'accord ? Des sources que tu veux voir ?
6. **L'ordre** : je propose §3 et §4 d'abord (0.85.0, sans dépendance), puis §1 après l'essai de transfert (0.86.0), puis §2 b et c selon tes réponses.

## Complément 0.86.2

- **La démo** : `/api/news` répondait par une erreur 500. À la lecture des actualités, jobA1 abonne le profil aux sources de son métier (§4), une écriture, que la base de la démo refuse (lecture seule, docs/72). La démo n'abonne plus rien ; elle garde les sources de son jeu de données. Trouvé en parcourant toutes les pages de la démo (0.87.0) ; un test de la démo le vérifie désormais.
