# 142 — L'extension : envoyer une annonce, remplir les alertes

> Statut : **demandé** par Kevin le 2026-11-06 (suite de la PR 530, ticket 532). Maquette
> `jobA1_maquette_2026-11-06.zip`, boards `ExtNonConnecte`, `ExtAutreSite`, `ExtAnnonce`, `ExtAlerte` (fenêtre de
> 360 × 480). Livré en trois PR, dans l'ordre : A (la fenêtre), B (envoyer une annonce), C (le formulaire d'alerte).
> D (transfert Gmail) suit à part, après validation de son écran, absent de la maquette.

## 1. La fenêtre (A)

- **En-tête** : logo + « jobA1 » ; à droite, la roue dentée (« Réglages de l'extension ») ouvre les réglages,
  un second clic revient à l'état d'avant.
- **Pastille** : l'hôte de l'onglet ouvert (`www.google.ch`), ou un libellé (« jobup.ch · Créer une alerte »).
  Absente quand l'état ne parle pas de la page (non connectée, réglages).
- **Un état à la fois**, **un seul bouton plein**, en bas. Les confirmations sont en `role="status"`.
- **Couleurs** : les jetons de l'app (`frontend/src/style.css`), recopiés dans `extension/popup.css` (l'extension n'a
  pas d'étape de construction) ; le sombre suit le navigateur (`prefers-color-scheme`). Un test compare les deux.
  Police : Figtree, fournie dans le paquet (`figtree.woff2`, licence OFL), jamais chargée d'un autre site.
- **États** :

| État | Quand | Maquette |
| --- | --- | --- |
| Non connectée | pas de jeton | `ExtNonConnecte` |
| Rien à faire | page sans annonce, ni formulaire d'alerte, ni formulaire de candidature | `ExtAutreSite` |
| Annonce | page d'annonce (B) | `ExtAnnonce` |
| Formulaire d'alerte | « Créer une alerte » de jobup, jobs.ch, LinkedIn (C) | `ExtAlerte` |
| Réglages | roue dentée | absent (contenu d'avant : adresse, jeton, délier) |
| Formulaire de l'employeur, Job-Room, codes | comme avant (docs/25, 70, 112) | absents : contenu d'avant dans la nouvelle fenêtre |

- **Se connecter** : l'adresse de la plateforme connue, la page « Relier ce navigateur » s'ouvre (docs/71 §4) ;
  sinon les réglages s'ouvrent pour la donner (une plateforme jobA1 est auto-hébergée : pas d'adresse par défaut).

### Le jeton (S-5)

Le jeton d'extension existe depuis docs/25 : `jbx_` + 256 bits tirés par `secrets`, seule l'empreinte est gardée,
valable **seulement** sur `/api/extension/…` (le middleware ne l'accepte nulle part ailleurs), révocable. La rubrique
qui le liste passe de Réglages › Agenda et extension à **Réglages › Connexions**, à côté des comptes Apple, Google
ou Microsoft ; « Agenda et extension » devient « Agenda ».

## 2. Ce que l'extension lit, et quand (V-1)

- À l'ouverture de la fenêtre (le clic sur l'icône donne `activeTab`) : l'adresse de l'onglet part à la plateforme
  pour reconnaître une candidature (comme avant) ; dans la page, seul le **nombre** de champs de formulaire est
  compté, pour distinguer un formulaire de candidature d'une autre page. Rien de la page ne part.
- Les autres lectures (annonce, champ e-mail d'une alerte) sont décrites avec leur partie (§3, §4).

## 3. Envoyer une annonce (B)

**Ce qui est lu, et quand** (`extension/annonce.js`, une seule fonction passée à l'onglet actif) :

- À l'ouverture de la fenêtre : le titre, l'entreprise et le lieu du `JobPosting` (schema.org) de la page, pour la
  carte « Annonce sur cette page ». Rien ne part.
- Au clic sur **Envoyer à jobA1** seulement : la description du `JobPosting`, sinon le texte principal
  (`main`/`article`) d'une page qui ressemble à une annonce, et l'adresse de la page. Rien d'autre : ni cookies, ni
  champs de formulaire, ni autres onglets, jamais de lecture en arrière-plan. Permissions : `activeTab` et
  `scripting`, jamais `<all_urls>`.
- **LinkedIn** : seulement l'annonce ouverte (`/jobs/view/<id>` ou `?currentJobId=<id>`) : son titre, son
  entreprise et sa description, par leurs blocs ; jamais un profil, le fil ni la liste des offres. L'adresse envoyée
  est celle de l'annonce, `https://www.linkedin.com/jobs/view/<id>/`.

**Serveur** (`POST /api/extension/announce`, `jobbot/extension/announce.py`, jeton de l'extension) :

1. Le texte est nettoyé comme un texte collé (`manual_offers.clean_pasted` : espaces resserrés, nom de la personne
   remplacé par « [nom retiré] », 20 000 caractères au plus). Moins de 200 caractères : « Je ne trouve pas
   d'annonce sur cette page » (422).
2. Sans `JobPosting` (titre absent), le titre, l'entreprise et le lieu sont lus par l'IA, comme « Ajouter une
   offre » (docs/111).
3. **Même lien** qu'une offre (lien d'alerte, annonce chez l'employeur ou formulaire ; même hôte sans `www`, même
   chemin) : l'offre est complétée (ses champs vides seulement, `manual_offers.fill`).
4. Sinon **même poste chez la même entreprise** (`manual_offers.same_offer`) : réponse « à confirmer », avec le
   poste, l'entreprise, la date d'arrivée et le site de l'alerte. L'extension demande « C'est bien cette offre ? » :
   **Oui, compléter cette offre** (l'id renvoyé doit être celui retrouvé par le serveur, sinon 409) ou **Ajouter
   comme nouvelle offre** (empreinte suffixée, l'empreinte étant unique). Jamais de rattachement silencieux.
5. Sinon : une nouvelle offre (`manual_offers.add`, sa limite de 20 ajouts par 24 heures comprise).
6. Le texte arrivé, l'offre repasse par le filtre et elle est **renotée tout de suite** (`score_offer`). Sans IA
   ou au plafond, la note d'avant reste.
7. **30 envois par jour et par compte** (429, « 30 annonces envoyées aujourd'hui : c'est le maximum. Réessaie
   demain. »). En mémoire, comme les autres limites (`auth.service.Window`) : un redémarrage la remet à zéro. La
   réponse à « C'est bien cette offre ? » ne compte pas.
8. Journal (J-1) : `extension_offer_added`, `extension_offer_filled`, `extension_offer_to_confirm`, avec l'id de
   l'offre et le chemin suivi, jamais le texte.

**Fenêtre** : « Annonce ajoutée à ton offre » + « Note refaite sur l'annonce complète : 76, Proche. » ; « Offre
ajoutée » + « Note : 76, Proche. Elle t'attend dans Candidatures › À traiter. » ; « Ouvrir dans jobA1 ↗ » ouvre
`/candidatures/offres?offre=<id>`. Si l'offre avait déjà son texte : « Offre déjà complète » (absent de la
maquette).

## 4. Le formulaire d'alerte (C)

- **Accès** : `host_permissions` limitées à `www.jobup.ch`, `jobup.ch`, `www.jobs.ch`, `jobs.ch` et
  `www.linkedin.com` (rien d'autre ; ni `*.jobup.ch`, qui donnerait sans accord les pages de code `auth.jobup.ch` de
  docs/112). Rien n'y est lu en arrière-plan : seulement à l'ouverture du panneau, dans l'onglet actif.
- **Sélecteurs** : un seul fichier, `extension/alert-selectors.js` (où est le formulaire, son champ e-mail, les mots
  qui disent « alerte »), et un test par site sur une page type (`extension/fixtures/alertes/`,
  `frontend/src/extensionAlerte.test.ts`). Les pages types sont **reconstituées**, pas relevées sur les sites :
  à vérifier sur les vrais formulaires, et à corriger dans ce seul fichier.
- **Remplir** (`extension/alertes.js`) : quand la fenêtre « Créer une alerte » est ouverte, le champ e-mail reçoit
  l'adresse jobA1 du compte (`GET /api/extension/alerts`, celle de la page Alertes), comme au clavier (setter natif,
  événements `input` et `change`). Le bouton d'envoi du site n'est **jamais** touché, aucune case n'est cochée : la
  personne valide elle-même. Un simple bouton « Créer une alerte » dans la page ne suffit pas : il faut une fenêtre
  ou un formulaire ouvert qui parle d'alerte.
- **Repli** : formulaire ouvert mais champ e-mail introuvable (sélecteurs cassés) → « Copie ton adresse jobA1 »,
  l'adresse avec **Copier**, et la phrase de la maquette (« Le champ n'a pas été rempli ? … »).
- **LinkedIn** : par défaut, rien n'est rempli ; l'adresse est copiée (« Adresse jobA1 copiée »). Le remplissage se
  choisit dans les réglages de l'extension (« Remplir aussi l'adresse dans les alertes LinkedIn », gardé dans le
  navigateur).
- **J'ai créé l'alerte** → `PUT /api/extension/alerts/<site>` : la même fonction que le bouton de l'assistant des
  alertes (`alerts.service.mark_created`), pour les recherches suivies encore à faire sur ce site. Le jeton de
  l'extension ne donne pas accès aux routes de l'assistant (`/api/alert-searches/…`) : la route est sous
  `/api/extension/`, le code est partagé. Confirmation « Alerte jobup enregistrée ». Journal : le site et le nombre
  de recherches, jamais l'adresse.

## 5. Transfert Gmail (D)

Pas d'écran dans la maquette : à dessiner et à faire valider avant le code.
