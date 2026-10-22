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

## Les questions

1. **A** : l'IA lit le CV pendant l'accueil (environ 0,05 à 0,10 $), un seul écran « Voici ce que j'ai compris » : d'accord ?
2. **A.3** : retirer aussi nom, adresse et date de naissance avant tout envoi à l'IA : d'accord ? (je propose de le livrer seul et tout de suite, c'est une règle déjà promise)
3. **A.2** : les deux nouvelles questions (langues, télétravail) à l'accueil : d'accord, ou seulement préremplies depuis le CV, sans écran en plus ?
4. **B.1** : une table de métiers relue par nous, l'IA en secours pour les autres : d'accord ? Veux-tu relire la liste des métiers ?
5. **B.3** : la relance « rien reçu » à 24 heures au lieu de 3 jours : d'accord ?
6. **C.2** : l'étiquette « Niveau au-dessus / en dessous » : d'accord, ou trop risqué de décourager ?
7. **L'ordre** : A, puis B, puis C, en trois versions ?
