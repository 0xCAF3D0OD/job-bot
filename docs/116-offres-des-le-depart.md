# 116 — Des offres dès le départ, et seulement celles du métier (version 0.85.0)

> Statut : **à valider**.
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

## Les questions

1. **§1, lier ses alertes par une règle de transfert** (avec le pas-à-pas et le code de Gmail affiché par jobA1) : d'accord ?
2. **§2 b, les annonces que jobA1 connaît déjà**, montrées à un nouveau compte : d'accord, sous réserve de vérifier les conditions de jobup et d'Indeed ? Ou attendre ?
3. **§2 c, Job-Room** : veux-tu que je prépare la demande d'accès au SECO (un e-mail court, à envoyer toi-même) ?
4. **§3, les recommandations hors métier écartées** (comptées dans le journal) : d'accord ? Ou les garder, repliées sous « Recommandations » ?
5. **§4, les actualités par familles de métiers**, et « rien de neuf » plutôt que l'économie : d'accord ? Des sources que tu veux voir ?
6. **L'ordre** : je propose §3 et §4 d'abord (0.85.0, sans dépendance), puis §1 après l'essai de transfert (0.86.0), puis §2 b et c selon tes réponses.
