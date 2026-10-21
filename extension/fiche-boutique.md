# Fiche de la boutique de Mozilla (docs/71 §6)

Les textes à coller sur addons.mozilla.org à l'envoi du paquet (`make extension`). Ce fichier
n'entre pas dans le paquet.

## Nom

jobA1 — remplir mes candidatures

## Résumé (250 caractères au plus)

Remplit les formulaires de candidature des employeurs, la saisie des recherches d'emploi de Job-Room et les codes de vérification de jobup avec tes données jobA1. Tu vérifies, tu envoies : l'extension n'envoie jamais de candidature à ta place.

## Description

jobA1 est une plateforme de recherche d'emploi pour la Suisse, que tu héberges toi-même. Elle suit tes offres et tes candidatures, et prépare lettres, CV et preuves ORP. Cette extension la relie à ton navigateur.

**Sur le formulaire d'un employeur**
- Tes coordonnées, ton CV et ta lettre (en PDF) sont mis dans les bons champs.
- Sur demande, une réponse est proposée aux questions libres (« Pourquoi nous ? »), à relire.
- Les champs remplis sont encadrés en violet ; ceux qui restent à faire, en orange.
- « J'ai envoyé » enregistre la candidature dans ton Suivi.

**Sur Job-Room (preuves de recherches d'emploi)**
- Choisis une candidature de ton Suivi : la saisie se remplit (date, entreprise, adresse, poste, mode, taux, résultat).
- Tu vérifies et tu sauvegardes toi-même ; « C'est déclaré » la marque dans ton Suivi.

**Les codes de vérification (jobup, jobs.ch), si tu le veux**
- Quand jobup ou jobs.ch demande le code envoyé à ton adresse jobA1, l'extension le remplit dès qu'il arrive sur ta plateforme, puis clique « Continuer ».
- Elle ne le fait qu'après ton accord, donné une fois dans son panneau (« Remplir mes codes tout seul »), et seulement sur les pages de connexion `auth.jobup.ch` et `auth.jobs.ch`. Sans cet accord, tu recopies le code toi-même.

**Ce qu'elle ne fait jamais**
- Elle n'envoie ni n'enregistre aucune candidature à ta place, et ne coche aucune case de consentement. Seule action faite pour toi : « Continuer » après un code de vérification, si tu l'as autorisé.
- Elle n'agit que sur l'onglet où tu cliques sur son icône, au moment où tu cliques ; exceptions : la page « Relier ce navigateur » de ta plateforme, ouverte par elle, où elle lit son jeton, et, si tu l'as autorisé, les pages de code de jobup et jobs.ch.
- Elle ne parle qu'à ta plateforme jobA1, à l'adresse que tu as donnée.

Il faut une plateforme jobA1 (code ouvert : https://github.com/0xCAF3D0OD/job-bot). Pour relier l'extension, indique son adresse, puis clique sur « Relier ce navigateur » sur la page qui s'ouvre.

## Catégorie

Autre (et, si proposé : Productivité).

## Site et code source

- Page d'accueil : https://github.com/0xCAF3D0OD/job-bot
- Code de l'extension : dossier `extension/` du dépôt, lisible tel quel (pas d'étape de construction).

## Politique de confidentialité

> **jobA1 — remplir mes candidatures : politique de confidentialité**
>
> L'extension relie ton navigateur à **ta propre plateforme jobA1**, à l'adresse que tu lui donnes. Elle n'envoie aucune donnée à l'auteur de l'extension ni à un tiers, n'utilise ni publicité, ni mesure d'audience, ni traceur.
>
> **Ce qui va de ton navigateur à ta plateforme**, seulement quand tu cliques sur l'icône de l'extension :
> - l'adresse de l'onglet ouvert, pour reconnaître la candidature correspondante ;
> - le texte d'une question libre d'un formulaire, quand tu demandes « Proposer une réponse » ;
> - l'adresse du formulaire, quand tu cliques sur « J'ai envoyé » ;
> - la marque « C'est déclaré », sur Job-Room.
>
> **Ce qui va de ta plateforme à la page**, seulement quand tu cliques sur « Remplir » : tes coordonnées, ta lettre et ton CV, ou les données d'une candidature (Job-Room). Elles sont mises dans les champs du formulaire ; rien n'est envoyé ni enregistré à ta place.
>
> **Les codes de vérification**, seulement si tu as donné l'accès aux pages de connexion de jobup et jobs.ch : sur la page qui demande un code, l'extension prévient ta plateforme (qui relève sa boîte), lui demande le code de ce site arrivé pour toi, le remplit et clique « Continuer ». Rien d'autre n'est lu sur ces pages.
>
> **Ce qui reste dans le navigateur** : l'adresse de ta plateforme et le jeton qui relie l'extension à ton compte (stockage local de l'extension). « Délier » les efface ; le jeton peut aussi être révoqué dans les Réglages de ta plateforme.
>
> Ce que ta plateforme fait de tes données est décrit sur sa page « Données personnelles » (`/tes-donnees`).

## Notes pour la relecture de Mozilla

- L'extension a besoin d'une plateforme jobA1. Pour l'essayer : cloner le dépôt, `make setup`, `make migrate`, `make dev` (macOS, PostgreSQL 17), puis relier l'extension à `http://localhost:5173`.
- Accès demandé à une seule adresse, celle de la plateforme, au moment de relier (`optional_host_permissions`).
- `fill.js` (formulaires des employeurs) est injecté dans l'onglet actif au clic, dans l'espace isolé ; la fonction de `fill-job-room.js` est passée à la page de Job-Room (`world: "MAIN"`, `func`) au clic, car Job-Room (Angular) ne voit pas une saisie faite depuis l'espace isolé de Firefox ; elle ne reçoit que la candidature à saisir, jamais le jeton, et ne laisse rien dans la page.
- `background.js` ouvre l'onglet d'accueil à l'installation, et lit le jeton de liaison dans l'onglet de la plateforme que l'extension a elle-même ouvert, sur l'adresse autorisée.
- Données déclarées : `browsingActivity` (adresse de l'onglet) et `websiteContent` (texte d'une question), vers la plateforme de l'utilisateur seulement.
- 0.59.0, les codes de vérification (docs/112 §3) : accès facultatif à `https://auth.jobup.ch/*` et `https://auth.jobs.ch/*`, demandé par un bouton du panneau (`permissions.request`). Sur une page de code de ces hôtes, `background.js` appelle la plateforme de l'utilisateur (`/api/extension/codes/expect`, puis `/api/extension/codes?site=…` toutes les 5 s pendant 5 minutes au plus), puis injecte `fillCode` (remplit le champ du code, clique sur le bouton d'envoi du formulaire). Rien n'est lu ni envoyé d'autre depuis ces pages.
