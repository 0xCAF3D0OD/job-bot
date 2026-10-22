# 121 — Démarrer en quelques minutes : le profil depuis le CV, les alertes préparées, la note expliquée (version 0.91.0)

> Statut : **validé** le 2026-10-22 (« oui pour tout, vas-y », avec la consigne : vérifier les règles de l'interface avant de construire). Ordre : A.3 seul (0.90.1), puis A (0.91.0), B (0.92.0), C (0.93.0).
> Origine : ta demande du 2026-10-21, après la comparaison avec ApplyNow, SwissJobs.app, ApplyCH, Karivo et Bewerbino : reprendre leurs bonnes idées sans perdre ce qui distingue jobA1. Le plan retenu commence par A (le profil depuis le CV), B (les alertes presque automatiques) et C (la note expliquée).
> Ce qui ne change pas : la collecte par les alertes e-mail de la personne, avec son accord ; jamais de robot sur un site ni de connexion à ses comptes ; les coordonnées jamais envoyées à l'IA ; le cycle ORP visible d'un coup d'œil ; les règles de `docs/interface.md`.

## Le constat

| | Aujourd'hui | Ce qui freine |
|---|---|---|
| **Le profil** | l'accueil (7 à 9 écrans) enregistre le CV sans le lire ; les blocs se proposent plus tard, dans Profil, sur un clic (« Proposer des blocs ») | la première note est fausse ou absente tant que la personne n'a pas trouvé ce bouton ; le télétravail et les langues ne se demandent pas à l'accueil |
| **Les coordonnées et l'IA** | avant l'envoi d'un CV à l'IA, jobA1 retire l'e-mail, le téléphone et les liens (`llm/proposals.py`, `scrub`) | **le nom et l'adresse postale partent encore** : contraire à la règle « coordonnées jamais envoyées à l'IA » |
| **Les alertes** | l'assistant des alertes ouvre la recherche déjà remplie sur chaque site (`alerts/service.py`), affiche l'adresse jobA1, le code de vérification, ouvre les liens « Confirmez votre alerte » | la personne invente ses mots de recherche ; le premier retour arrive au plus tôt quand un e-mail tombe ; l'aide « rien reçu » attend 3 jours |
| **La note** | points forts, manques, compétences demandées, « Cette note ne me correspond pas » | pas de phrase « pourquoi cette note », pas de signal quand le poste demande un niveau au-dessus (ou en dessous), pas de rappel « ajoute ceci à ton profil » là où le manque pèse |

## A. Le profil depuis le CV, pendant l'accueil

1. **Juste après le dépôt du CV**, jobA1 le lit (la proposition de blocs existe déjà) et montre **un seul écran : « Voici ce que j'ai compris »**.
   - Les blocs proposés (expériences, compétences, formations), cochés, à décocher ou corriger.
   - Les critères lus dans le CV, préremplis : postes visés (à côté du métier déjà choisi), taux, langues parlées, télétravail souhaité si le CV le dit, lieux. Chaque valeur modifiable sur place.
   - Un seul bouton plein : « C'est bon ».
2. **Deux nouvelles questions à l'accueil**, en pilules (un clic) : les langues (français, allemand, italien, anglais, autre) et le télétravail (sur place, hybride, à distance, peu importe). Elles se préremplissent depuis le CV quand il les dit.
3. **Les coordonnées ne partent jamais à l'IA** : avant tout envoi d'un document (CV, certificat), jobA1 retire en plus le nom et le prénom de la personne, son adresse postale (rue, NPA, localité) et sa date de naissance, tels qu'ils sont dans ses coordonnées et tels qu'il les repère en tête du CV. Un test le vérifie sur un vrai CV anonymisé.
4. **Sans IA** (pas de clé, plafond atteint, refus) : l'accueil continue comme aujourd'hui, le CV est gardé, Profil proposera les blocs plus tard. Rien ne bloque.
5. **Le coût** : environ 0,05 à 0,10 $ par CV, compté dans le plafond du compte (5 CHF par mois pour un invité).

## B. Les alertes presque automatiques

Ce qu'on ne fera pas : créer l'alerte à la place de la personne, se connecter à ses comptes, lire les sites par robot. La personne crée l'alerte ; jobA1 lui enlève tout le reste.

1. **Des recherches préparées par métier**.
   - Une table de métiers relue par nous (une soixantaine au départ, les plus fréquents à l'ORP) : pour chacun, 2 ou 3 recherches (« communicante » : « chargée de communication », « communication », « relations publiques »), et les sites qui ont du sens (jobup, Indeed, jobs.ch partout ; Job-Room si ses alertes existent, voir 4).
   - Un métier absent de la table : l'IA propose 2 ou 3 recherches à partir du seul nom du métier (rien de personnel, environ 0,001 $) ; la personne les voit avant de les garder.
   - À l'accueil, l'écran « métier » propose ces recherches cochées ; l'assistant des alertes démarre avec elles.
2. **Un site, un écran, un geste**.
   - Le lien qui ouvre la recherche déjà remplie (existe), l'adresse jobA1 **copiée d'avance** au clic, une image du bouton « Créer une alerte » du site (une capture que tu valides), « J'ai créé l'alerte ».
   - Pas de texte à lire au-delà d'une ligne.
3. **La vérification, sans attendre la personne**.
   - Le code de vérification et les liens de confirmation : comme aujourd'hui.
   - **La première alerte reçue d'un site** : une notification (« jobup t'a envoyé ses premières offres : 12 ») et la ligne du site passe à « Reçue ».
   - **Rien reçu après 24 heures** (au lieu de 3 jours) : un message précis par site, avec quoi faire (« Vérifie que l'alerte jobup est active et envoie à alertes+… »), dans la page Alertes et la cloche.
4. **Job-Room**, le site de l'ORP : il est dans la liste, en pause. Je vérifie s'il envoie des alertes par e-mail ; si oui, il rejoint l'assistant (des offres publiques, légitimes, que l'ORP connaît). Sinon, il attend la réponse du SECO (docs/116 §2 c).
5. **Les alertes déjà créées** : le transfert depuis Gmail ou Outlook (docs/116 §1, 0.86.0), proposé dans le même écran.

## C. La note expliquée

1. **Une phrase « pourquoi cette note »**, sous le cercle de la note : ce qui pèse le plus, en une ligne (« Ton expérience Kubernetes colle ; il manque l'allemand demandé. »). Écrite par l'IA avec la note, dans une nouvelle version du prompt (`score-v5`). Les offres déjà notées gardent l'ancienne explication (renoter coûte) ; « Renoter » la donne.
2. **Le niveau** : l'IA dit si le poste vise un niveau **au-dessus** ou **en dessous** du profil (années demandées, responsabilités), et seulement quand c'est net. Affiché comme une étiquette neutre (« Niveau au-dessus »), avec le détail au survol ; jamais une baisse de note cachée.
3. **Le manque qui se corrige en un clic** : quand un manque est une compétence que la personne a peut-être sans l'avoir écrite, un lien « Je l'ai : l'ajouter au profil » ouvre un bloc prérempli (comme « Cette note ne me correspond pas », docs/114), puis l'offre est renotée.
4. **La jauge du profil**, dans Profil seulement : par section (expériences, compétences, langues, critères), « 3 sur 4 », et ce qui manque. Pas de jauge ailleurs.
5. **La note dans les listes, en mots** (ajouté le 2026-10-22 : tu as choisi la maquette O, « en gardant tous les visages ») :
   - **Quatre mots** à la place du chiffre, d'après les seuils de couleur actuels : **Très proche** (85 et plus), **Proche** (70 à 84), **À creuser** (50 à 69), **Loin** (moins de 50).
   - **Le visage du 1**, petit, devant le mot, avec **une expression par mot** : grand sourire, sourire, bouche droite, bouche droite plus courte (jamais déçu : docs/123 §1). Ce sont des dessins de l'iconographie (24 px, trait de 1,8 px), pas le logo agrandi. *(Validé le 2026-10-22 : les seuils 85 / 70 / 50 et le gris chaud pour « À creuser ».)*
   - **Un filet en bas de la carte**, à la longueur de la note (plein à 100), à la couleur du mot ; la part manquante en gris clair. C'est le cercle de la règle actuelle, déplié.
   - **La carte garde** le logo de l'entreprise à gauche, le titre, l'entreprise et le lieu ; le mot et son visage à droite ; « Il te manque : … » sous le titre quand un manque compte (repris de la maquette L).
   - **Les couleurs** : Très proche en vert menthe, Proche dans le bleu lavande de l'accent, À creuser en gris chaud, Loin en gris. **Pas d'orange** : il reste à ce qui demande d'agir (relancer, à compléter).
   - **Pas encore notée** : « Pas encore notée » en gris, sans visage, le filet en pointillés ; le pourquoi au survol (comme le cercle en pointillés aujourd'hui).
   - **Le chiffre reste** dans la fiche de l'offre : le cercle, avec la phrase « pourquoi cette note » (1), là où la précision sert ; et au survol du mot dans la liste (« 76 sur 100 »).
   - **Où** : la liste des Offres, les meilleures offres d'Aujourd'hui, et partout où une offre s'affiche en ligne (Suivi, recherche de l'assistant).
   - **La règle « La note »** de `docs/interface.md` est réécrite : le cercle dans la fiche, le mot, le visage et le filet dans les listes ; jamais une pilule (une pilule pleine est une action).

## Garde-fous

- Les écrans suivent `docs/interface.md` : une ligne de texte, le reste au survol ; les trois audits à zéro avant la PR.
- Rien dans la démo n'appelle l'IA.
- Chaque appel à l'IA est compté dans le plafond du compte ; au plafond, tout continue sans lui.

## Livraison proposée

- **0.91.0** : A (avec la correction des coordonnées, à faire en premier).
- **0.92.0** : B (la table des métiers, les écrans par site, la vérification à 24 heures ; Job-Room selon ce que je trouve).
- **0.93.0** : C (le prompt `score-v5`, l'étiquette de niveau, le manque en un clic, la jauge de Profil).

## Écarts (0.90.1 : A.3, les coordonnées)

- **Un seul endroit** retire les coordonnées avant l'IA : `llm/redact.py`, utilisé par la proposition de blocs (CV) et par les deux lectures de certificats.
- **Retiré** : e-mail, téléphone, liens ; le nom (complet et chaque partie) et l'adresse saisis dans les coordonnées, partout dans le texte ; dans les huit premières lignes, une ligne qui ressemble à un nom seul, à une rue (« Rue… », « …strasse 12 ») ou à « NPA Localité », même sans coordonnées saisies ; la date de naissance avec ce qui l'annonce (« née le 12.03.1990 »), **sans effacer le reste de la phrase** (sur un certificat, « né le 3 mai 1990, a travaillé chez Acme SA » garde l'employeur).
- **Gardé** : les dates d'une expérience, une adresse citée plus bas dans le texte (celle d'un client, d'un employeur).
- **Un effet voulu** : une entreprise qui porte le nom de famille de la personne est aussi masquée ; la prudence l'emporte.
- **Données personnelles** : « Le texte de ton CV, sans tes coordonnées ni ta date de naissance ». La promesse « jamais tes coordonnées » de la même page devient vraie pour le CV.

## Vérifié (0.90.1)

- Tests : un CV d'exemple sans coordonnées saisies (nom, rue, « CH-1020 Renens », téléphone, e-mail, site, date de naissance retirés ; le parcours gardé) ; les coordonnées connues retirées partout ; la requête de proposition sans nom, localité ni année de naissance ; les certificats sans les noms, employeur gardé. 603 tests backend, ruff, mypy.

## Écarts (0.91.0 : A)

- **Règles relues avant de construire** (`docs/interface.md`), et vérifiées sur captures : l'accueil est une page de présentation, ses titres restent des phrases (titres 1) ; une seule ligne d'aide par écran, celle qui dit ce qui part à l'IA (titres 5) ; les blocs en liste, une ligne par bloc séparée par un filet, dans une seule carte à 1,5 rem de marge (listes, aéré, structure 3) ; les postes et les langues en pastilles, comme les autres choix de l'accueil ; un seul bouton plein ; la carte des blocs à la largeur des boutons (cohérence).
- **L'ordre des écrans** : objectif, métier, lieux, taux, (ORP), CV, **« Voici ce que j'ai compris »**, **langues**, **télétravail**, notifications, récapitulatif, la suite. L'écran du CV lu n'apparaît que si l'IA a répondu ; « Continuer » attend la fin de la lecture (« Lecture de ton CV… » dans la carte du CV).
- **Les blocs** : cochés, sauf ceux qui existent déjà (« déjà dans le profil »), décochés. « C'est bon » les ajoute au profil, rattachés au CV. Pas de modification dans l'accueil : elle se fait dans Profil (une liste à cocher reste lisible sur téléphone).
- **Les postes visés** : en pastilles, le métier de l'accueil n'y est pas répété ; gardés dans l'accueil (`roles`, 3 au plus) pour préparer les alertes (B).
- **Les langues** : « En plus du français, quelles langues parles-tu au travail ? » (allemand, italien, anglais, aucune), préremplies par le CV ; elles remplissent le critère des langues non parlées. **Le télétravail** : « Sur place ou hybride » ou « Aussi à distance » (depuis la Suisse), prérempli si le CV le dit.
- **Le taux** lu dans le CV ne remplace pas la réponse déjà donnée à l'accueil.
- **Une seule lecture** : la route `POST /api/documents/{id}/understand` (consignes `propose-chunks-v1` + `cv-understand-v1`), comptée comme une proposition de blocs.
- **Correction de la 0.90.1** : le repérage d'un nom en tête de document ne regarde plus que la **première ligne** (le poste écrit sous le nom, « Ingénieure DevOps », restait masqué) ; les réponses de l'IA (titres de blocs, postes) ne passent plus que par le retrait des contacts.

## Vérifié (0.91.0)

- Tests backend : la lecture du CV à l'accueil (postes dédoublonnés et limités à 3, taux insensé ignoré, langue inconnue écartée, rien d'enregistré, sans coordonnées) ; une réponse sans la partie « understood » ; le poste sous le nom gardé. 606 tests, ruff, mypy.
- Tests de l'interface : le CV déposé est lu, l'écran propose les blocs et les postes, un doublon décoché, « C'est bon » crée les blocs gardés et note les postes, les langues préremplies ; sans IA, l'écran est sauté ; les langues et le télétravail remplissent les critères. 411 tests, lint, vue-tsc.
- Captures à 1440 et 390 px des trois nouveaux écrans ; axe-core sur ces écrans : aucun défaut de l'interface.

## Écarts (0.92.0 : B)

- **Règles relues avant de construire** ; l'écran d'un site vérifié sur capture : une ligne d'aide, le détail au survol (titres 5).
- **La liste** : les 63 métiers du docs/122 (validé), dans `alerts/trades.py`. Ce que la personne tape mène au métier par le début de chaque mot, sans accents ni majuscules (« Employée de commerce » mène à « Employé·e de commerce », « communicante » à « Chargé·e de communication »), le plus précis l'emportant.
- **Un métier hors liste** : l'IA (consigne `trade-searches-v1`, modèle léger, environ 0,001 $) reçoit **seulement le nom du métier** et propose 2 ou 3 recherches, une fois par métier ; sans IA ou au plafond, le métier lui-même sert de recherche. Compté sous « alerts ».
- **Les recherches proposées** (une fois, comme avant) : celles du métier, puis les postes gardés depuis le CV (docs/121 §A), 4 au plus, chacune avec chaque lieu (8 alertes au plus). Sans métier d'accueil (l'exploitant, un compte d'avant l'accueil), « Mon domaine » comme avant.
- **Pas d'écran de métier en plus à l'accueil** : les recherches arrivent toutes prêtes dans l'assistant des alertes, que l'accueil ouvre déjà (« Créer mes alertes »).
- **Un site, un geste** : ouvrir le site copie l'adresse jobA1 (« Adresse copiée : … ») ; il reste à la coller dans « Créer une alerte » (au survol). **Pas de capture du bouton des sites** : une image de l'interface de jobup ou d'Indeed dans jobA1 poserait une question de droits ; à reprendre si tu fournis des captures que tu as le droit d'utiliser.
- **La première alerte d'un site** avec des offres : une notification « jobup t'a envoyé ses premières offres : 12. », une seule fois par site ; comme les offres, elle attend un jour de pause pour le téléphone (la cloche la montre tout de suite).
- **Rien reçu après 24 heures** au lieu de 3 jours : le rappel d'Aujourd'hui (« 1 alerte créée hier n'a encore rien envoyé. »), l'aide de la page Alertes et l'assistant (consigne `assistant-v14`).
- **Job-Room** : rien de public ne dit s'il envoie des alertes par e-mail ; il reste en pause. À vérifier dans ton compte Job-Room.

## Vérifié (0.92.0)

- Tests backend : les métiers reconnus (sept cas), la liste validée (63 métiers, 1 à 3 recherches) ; un compte « Communicante » avec un poste du CV reçoit les recherches du métier puis le poste ; un métier inconnu demande à l'IA une fois, avec seulement son nom ; la première alerte de jobup annoncée une fois. 618 tests, ruff, mypy.
- Tests de l'interface : ouvrir un site copie l'adresse ; « Rien reçu depuis 24 heures ». 412 tests, lint, vue-tsc.
- Les trois audits sur la démo à zéro ; capture de l'écran d'un site à 1440 et 390 px.

## Écarts (0.93.0 : C)

- **Règles relues avant de construire** (`docs/interface.md`), vérifiées sur captures à 1440 et 390 px : la liste des Offres, la fiche (pourquoi, niveau, « Je l'ai » ouvert), la jauge du Profil.
- **Le prompt `score-v5`** ajoute `why` (une phrase, 140 caractères au plus), `level` (« above », « below » ou rien, seulement si c'est net) et `level_detail` (le détail au survol). Migration 0066 (trois colonnes de `evaluations`). Les offres déjà notées n'ont ni phrase ni niveau : rien ne s'affiche, « Renoter » les donne.
- **Le niveau** : une ligne grise sous la phrase, « Niveau au-dessus » ou « Niveau en dessous », le détail au survol ; pas une pastille (une première version en étiquette était trop petite et coupait la phrase).
- **« Je l'ai »** : seulement sous un manque qui nomme une compétence (« Spark : pas d'expérience… », « Pas d'Ansible ») et qu'aucun bloc ne cite ; pas sous une phrase (« Le poste demande plus de développement… »). Le formulaire est prérempli avec la compétence seule (« Spark ») et demande où et comment, en une phrase. « Ajouter au profil » crée un bloc de compétence (`POST /api/offers/{id}/gap-block`, origine « gap ») et renote l'offre (environ 0,003 $, au survol). Le formulaire s'ouvre sous le manque, sans cadre (pas de cadre dans la fiche).
- **La jauge** : cinq parties au lieu des quatre du cadrage, « Profil · 4 sur 5 » : une expérience, deux compétences, une formation, les critères enregistrés, les coordonnées (nom et localité). **Les langues** n'ont pas de partie à elles : elles sont dans les critères (langues non parlées, docs/121 §A.2). La formation et les coordonnées sont ajoutées parce que la note et les lettres s'en servent. Un lien mène à ce qui manque en premier ; la jauge part quand tout est là. Même carte grise que les autres cartes du Profil.
- **La note en mots** (§C.5) : le mot et le visage à droite de la ligne, le chiffre au survol (« Proche : 82 sur 100 ») ; le filet en bas de la ligne, la part manquante en gris clair ; « Il te manque » en gris (plus en orange). Dans la liste des Offres et les meilleures offres d'Aujourd'hui.
- **Le cercle de la fiche** prend les couleurs des mots : vert menthe à 85 et plus, bleu lavande à 70, gris chaud à 50 (**plus d'orange**), gris en dessous. Le même gris clair pour la part manquante du cercle, du filet et de la jauge.
- **Le visage** : un SVG (`FaceMark`), quatre bouches (grand sourire, sourire, bouche droite, bouche droite plus courte), les traits à la couleur du mot, la bille pêche du logo ; décoratif pour les lecteurs d'écran.
- **Pas encore fait** : le Suivi et la recherche de l'assistant gardent leur affichage (ils ne montrent pas la note en ligne aujourd'hui) ; les humeurs dessinées en grand viennent avec docs/123 (0.94.0).
- **La démo** : ses offres notées ont une phrase et, sous 60, le niveau au-dessus.
- **Après la fusion** : `make migrate` (0066).

## Vérifié (0.93.0)

- Tests backend : la phrase et le niveau lus et nettoyés (`score-v5`), effacés sans profil ; un manque ajouté devient un bloc et l'offre est renotée, 404 pour une offre inconnue. 620 tests, ruff, mypy.
- Tests de l'interface : le mot, le visage et le chiffre au survol dans la liste, « Pas encore notée » ; la phrase et le niveau dans la fiche ; « Je l'ai » seulement sous une compétence, préremplie ; la jauge (le compte, les segments, le premier manque, cachée quand tout est là). 416 tests, lint, vue-tsc.
- Les trois audits sur la démo à zéro (règles, alignement, accessibilité).

## Écarts (0.93.1 : la note de la démo)

- **Le constat** (ta question du 2026-10-22, « est-ce que la note a du sens pour l'offre ? ») : la démo donnait à toutes ses offres la même phrase (« Ta plateforme Kubernetes colle ») et le même niveau inventé (« huit ans d'expérience ») sous 60. Sur le Data Engineer, rien ne collait : l'offre ne demande pas Kubernetes.
- **La phrase** est tirée de chaque offre : ce qu'elle demande et que le profil a, ce qui manque (« Azure et PowerShell : dans ton profil ; il manque Bicep. »), et « le poste demande plus de développement » seulement quand aucune compétence manquante n'explique une note sous 70.
- **Le Data Engineer** est décrit comme un poste de données : son rôle, sa phrase (« Le poste vise la donnée (Spark, SQL) ; ton parcours est la plateforme et le cloud. »), un seul point fort (les scripts Python), Spark et SQL en manques.
- **Le niveau** seulement sur « SRE junior », dont l'annonce dit « deux ans d'expérience au plus » : « Niveau en dessous ». Plus de niveau ailleurs.
- **Hors démo, rien ne change** : la phrase et le niveau viennent de l'IA, qui lit l'offre.

## Vérifié (0.93.1)

- Test de la démo : la phrase du Data Engineer et du Cloud Engineer (Azure), le niveau seulement sur « SRE junior », toutes les phrases de 140 caractères au plus. 620 tests backend, ruff, mypy. Capture de la fiche du Data Engineer.

## Les questions

1. **A** : l'IA lit le CV pendant l'accueil (environ 0,05 à 0,10 $), un seul écran « Voici ce que j'ai compris » : d'accord ?
2. **A.3** : retirer aussi nom, adresse et date de naissance avant tout envoi à l'IA : d'accord ? (je propose de le livrer seul et tout de suite, c'est une règle déjà promise)
3. **A.2** : les deux nouvelles questions (langues, télétravail) à l'accueil : d'accord, ou seulement préremplies depuis le CV, sans écran en plus ?
4. **B.1** : une table de métiers relue par nous, l'IA en secours pour les autres : d'accord ? Veux-tu relire la liste des métiers ?
5. **B.3** : la relance « rien reçu » à 24 heures au lieu de 3 jours : d'accord ?
6. **C.2** : l'étiquette « Niveau au-dessus / en dessous » : d'accord, ou trop risqué de décourager ?
8. **C.5** (ajoutée) : les quatre seuils (85, 70, 50) et les couleurs (gris chaud pour « À creuser », au lieu de l'orange de la maquette) : d'accord ?
7. **L'ordre** : A, puis B, puis C, en trois versions ?
