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

À venir dans la PR B.

## 4. Le formulaire d'alerte (C)

À venir dans la PR C.

## 5. Transfert Gmail (D)

Pas d'écran dans la maquette : à dessiner et à faire valider avant le code.
