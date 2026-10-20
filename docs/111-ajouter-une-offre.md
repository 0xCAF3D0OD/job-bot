# 111 — Ajouter une offre (version 0.81.0)

> Statut : **validé** le 2026-10-20 : pas de branchement à Google Jobs, le texte collé lu par l'IA, « Partager vers jobA1 » dans cette version, l'offre écartée ajoutée avec sa raison, 20 offres par jour ; et la consigne « cohérent avec le poste de l'utilisateur ».
> Origine : ta question du 2026-10-20, « qu'en est-il des offres en dehors de celles des plateformes de recherche ? », puis « écris le cadrage de “Ajouter une offre”, mais n'est-il pas possible de récupérer depuis Google Jobs ? ».
> Se place après la 0.80.0 (les premières offres, docs/104), qui reste à valider.

## Le constat

Une offre n'entre dans jobA1 que par **un e-mail d'alerte** (jobup, Indeed, Job-Room, ou tout site suivi lu par l'IA). Ce qui en reste dehors :

- une annonce vue **sur le site d'une entreprise** qui n'envoie pas d'alertes ;
- **un post LinkedIn**, une annonce **dans un journal**, une offre **transmise par un proche** ;
- une offre trouvée **sur Google**.

Sans offre, il n'y a **ni note, ni lettre et CV préparés, ni ligne ORP pré-remplie**. La candidature spontanée (docs/39) et la candidature notée à la main dans le Suivi existent, mais elles ne remplacent pas une vraie offre.

## Et Google Jobs ?

**Ce que c'est** : le cadre « Emplois » de la recherche Google. Google n'y publie pas ses propres offres : il rassemble celles que les sites (entreprises, sites d'emploi) décrivent avec un balisage standard, `JobPosting` (schema.org).

**Pourquoi jobA1 ne peut pas s'y brancher directement** :

- **Il n'y a pas d'accès prévu pour ça.** Google ne propose aucune interface pour chercher dans Google Jobs depuis une autre application. Son offre « Cloud Talent Solution » sert l'inverse : un employeur qui cherche dans ses propres offres.
- **Lire les pages de résultats Google en automatique est interdit** par ses conditions d'utilisation, et bloqué par ses protections contre les robots. jobA1 ne contourne pas ce genre de protection (c'est déjà la règle pour Indeed, docs/05).
- **Des services payants revendent ces résultats** (par exemple SerpApi, « Google Jobs API ») : de l'ordre de **50 à 75 $ par mois** pour quelques milliers de recherches. Cela marche, mais avec un coût fixe pour toute la plateforme, une dépendance à un tiers et une zone grise juridique (ils font eux-mêmes ce que Google interdit).

**Ce qu'on récupère quand même** : comme Google Jobs se nourrit du balisage `JobPosting` des sites, **« Ajouter une offre » lit ce même balisage**. Une offre trouvée dans Google Jobs se récupère donc **en collant son lien** (le bouton « Postuler sur … » de Google mène à la page de l'entreprise ou du site d'emploi, qui porte ce balisage). jobA1 le fait déjà pour les pages jobup (docs/05).

**Ma recommandation** : pas de branchement à Google Jobs, ni direct ni par un service payant. « Ajouter une offre » couvre le besoin, sans coût fixe ni zone grise.

## La proposition

### 1. Où

- **Candidatures › Offres** : une pilule **« Ajouter une offre »**, à côté de « Candidature spontanée ».
- **Sur téléphone Android**, une fois jobA1 installé sur l'écran d'accueil : jobA1 apparaît dans le menu **« Partager »** du navigateur. On partage la page d'une annonce, et elle arrive dans « Ajouter une offre », lien déjà rempli. L'iPhone ne permet pas cette entrée à une application web : on y copie le lien.

### 2. Deux façons d'ajouter

| | Ce qu'on donne | Ce que fait jobA1 |
|---|---|---|
| **Un lien** | l'adresse de l'annonce (site d'entreprise, jobs.ch, LinkedIn, lien venu de Google Jobs…) | lit la page publique, une fois |
| **Un texte** | le texte de l'annonce, collé (journal, post, e-mail d'un proche) | lit le texte |

### 3. Comment l'annonce est lue, dans l'ordre

1. **Le balisage `JobPosting`** de la page (le même que Google Jobs) : titre, entreprise, lieu, taux, texte complet. Sans IA, sans coût.
2. **Sinon, la page ou le texte passe à l'IA**, qui en tire les mêmes champs : environ **0,01 $**, compté dans le plafond du compte. Rien d'autre ne part à l'IA, et jamais tes coordonnées.
3. **Avant d'enregistrer**, une fiche montre ce qui a été lu (titre, entreprise, lieu, taux) : on corrige au besoin, puis « Ajouter l'offre ».

### 4. Ensuite, comme une offre reçue

- **Le filtre et la note** s'appliquent comme aux autres offres. Une offre écartée par les critères est quand même ajoutée, puisque c'est ton choix, avec la raison affichée.
- **La préparation** (lettre, CV adapté) et **la candidature** fonctionnent pareil.
- **La ligne ORP** se remplit avec le lien comme source de l'annonce.
- **Sur sa carte**, une petite étiquette « Ajoutée par toi » à la place du site d'emploi.
- **Une offre déjà présente** (même entreprise et même titre, ou même lien) n'est pas ajoutée deux fois : jobA1 ouvre celle qui existe.

### 5. Garde-fous

- **Seulement des adresses publiques** (`https`), jamais une adresse privée ou locale, comme pour les logos (docs/exploitation) ; une page de **2 Mo au plus**, **10 secondes** au plus.
- **Une page protégée contre les robots** (Indeed, souvent LinkedIn) n'est pas contournée : jobA1 le dit et propose de **coller le texte** de l'annonce à la place.
- **20 offres ajoutées par jour** et par compte.
- **Dans la démo**, l'ajout est désactivé, comme les autres écritures.

## Cohérent avec ton métier (ta consigne du 2026-10-20)

- **Les exemples des champs viennent de ton métier**, celui choisi à l'accueil (premier mot de « Mon domaine ») : pour « Menuisier », le lien d'exemple est `https://entreprise.ch/emplois/menuisier`, le texte d'exemple commence par « Menuisier (80-100 %) », et le champ « Poste » propose « Menuisier ». Sans métier connu, des exemples neutres (« poste »), jamais un métier inventé.
- **Une annonce qui ne parle pas de ton métier** (ni un mot de « Mon domaine », ni le début d'un de ses mots : « développeur » reconnaît « développeuse ») : la fiche le dit, « Cette annonce ne parle pas de « Menuisier », ton métier. Tu peux l'ajouter quand même : la note dira si elle te correspond. » Rien n'est bloqué.

## Écarts

- **Le lien se garde comme lien de l'offre**, source « l'annonce » : le bouton de l'offre devient « Ouvrir l'annonce » (et non « Postuler sur … »), et la ligne ORP le reprend comme adresse de l'annonce. Une offre ajoutée par son texte n'a pas de lien : rien à ouvrir, la ligne ORP reste à compléter.
- **L'étiquette « Ajoutée par toi »** prend la place de « Spontanée » sur la carte ; elle reste visible dans toutes les vues.
- **Une offre ajoutée n'expire jamais faute d'alerte** (elle n'en reçoit pas) ; on peut toujours la signaler comme expirée.
- **La lecture par l'IA** réutilise le lecteur des alertes (docs/20) : coordonnées retirées du texte, ton nom remplacé par « [nom retiré] », appel compté sous « manual_offer ». Le plafond est vérifié avant (0,02 $ réservés) ; au plafond, ou sans IA, la fiche se remplit à la main.
- **Une page sans annonce lisible** (moins de 200 caractères de texte, par exemple une page de connexion) n'est pas envoyée à l'IA : jobA1 propose de coller le texte.
- **« Remplir la fiche à la main »** apparaît à chaque refus de lecture : l'ajout ne dépend jamais de l'IA.
- **« Partager vers jobA1 »** passe par `/ajouter-une-offre` (manifeste, `share_target` en GET) ; le lien que certains navigateurs glissent dans le texte partagé en est sorti. Il faut jobA1 installé sur l'écran d'accueil d'Android (Chrome) ; l'iPhone ne le permet pas.
- **La limite des 20** compte les offres ajoutées sur les 24 dernières heures ; le formulaire montre « 3 offres ajoutées sur 20 ces 24 heures » et ferme la lecture au maximum.

## Vérifié

- Tests backend : le `JobPosting` (dans un `@graph`, dans une liste, `@type` en liste, description en HTML), le repli sur l'IA pour une page et pour un texte (coordonnées retirées), les adresses refusées (`http`, `localhost`, `127.0.0.1`), la page protégée (403 : coller le texte), la page sans annonce (pas d'IA), le doublon par lien, la limite des 20, l'offre écartée gardée avec sa raison, l'offre notée comme les autres, jamais expirée faute d'alerte, son lien dans la ligne ORP ; le métier reconnu (« développeur » / « développeuse », « Entwickler » / « Entwicklerin »).
- Tests de l'interface : les exemples tirés du métier (et neutres sans métier), la fiche lue puis corrigée, l'annonce hors du métier signalée sans bloquer, la page protégée qui passe au texte et la fiche à la main, l'offre déjà là, le maximum du jour, le partage Android (lien sorti du texte), l'étiquette sur la carte.
- Captures Playwright à 414 et 1280 px : la liste avec les deux boutons (sur téléphone, côte à côte et de même hauteur sous le nombre d'offres), le lien, le texte, la fiche. Largeur de la page mesurée : rien ne dépasse.

## Décisions (2026-10-20)

Tes cinq réponses : « oui pour tout » ; et que ce soit cohérent avec le poste de l'utilisateur.

### Les questions posées

1. **Google Jobs** : d'accord pour ne pas s'y brancher, et récupérer ses offres par leur lien ?
2. **Le texte collé lu par l'IA** (environ 0,01 $ par offre, dans le plafond du compte) : d'accord ?
3. **« Partager vers jobA1 »** sur Android : à faire dans cette version, ou plus tard ?
4. **Une offre écartée par les critères** : l'ajouter quand même (avec la raison), ou demander d'abord ?
5. **20 offres ajoutées par jour** : suffisant ?
