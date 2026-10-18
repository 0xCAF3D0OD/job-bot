# Extension jobA1 (docs/25, docs/70)

Remplit le formulaire de candidature de l'employeur avec tes données jobA1 : coordonnées,
CV et lettre en PDF, texte de la lettre, et, sur demande, une proposition de réponse aux
questions libres. **Elle n'envoie jamais rien à ta place** et ne coche aucune case.

Sur Job-Room, elle remplit la saisie d'une recherche d'emploi avec une candidature de ton Suivi.
Là, elle choisit aussi les réponses de la déclaration (mode, assignation, taux, résultat), mais
n'enregistre rien : « Sauvegarder » reste le tien.

## Installer (Chrome, Edge, Brave)

1. Ouvre `chrome://extensions` et active le **mode développeur** (en haut à droite).
2. **Charger l'extension non empaquetée** → choisis ce dossier `extension/`.
3. Épingle l'icône jobA1 dans la barre du navigateur.

## Installer (Firefox 128 et plus)

- **Pour essayer** : ouvre `about:debugging#/runtime/this-firefox` → **Charger un module
  complémentaire temporaire…** → choisis `extension/manifest.json`. Firefox l'enlève à chaque
  redémarrage : recharge-la, puis relie-la à nouveau.
- **Pour la garder** : Firefox n'installe durablement qu'une extension signée par Mozilla. La
  signature est gratuite et l'extension reste privée (non publiée) :
  1. crée un compte sur addons.mozilla.org, puis tes clés dans « Outils › Gérer les clés
     d'API » (garde-les pour toi) ;
  2. dans ce dossier : `npx web-ext sign --channel=unlisted --api-key=… --api-secret=…` ;
  3. ouvre le fichier `.xpi` produit (dossier `web-ext-artifacts/`) dans Firefox.

## Relier à ta plateforme

1. Sur la plateforme : **Réglages › Extension du navigateur › Créer un jeton** ; copie-le
   (il n'est montré qu'une fois).
2. Clique sur l'icône jobA1 : colle l'adresse de ta plateforme (en `https://`, ou
   `http://localhost:…` sur ta machine) et le jeton, puis **Relier**. Le navigateur demande
   l'autorisation de joindre cette adresse, et seulement celle-ci. Si le panneau se ferme
   pendant cette demande (fréquent dans Firefox), rouvre-le : **Autoriser l'accès à ma
   plateforme** reprend là où tu en étais.

## Utiliser

Sur le formulaire de l'employeur (ouvert depuis « Postuler ») : icône jobA1 →
**Remplir le formulaire**. Les champs remplis sont encadrés en violet, les champs obligatoires
restants en orange. Vérifie, envoie depuis le site, puis **J'ai envoyé ma candidature** :
elle arrive dans ton Suivi avec l'adresse du formulaire.

## Sur Job-Room

1. Dans Job-Room, connecte-toi et ouvre la saisie d'une nouvelle recherche d'emploi.
2. Icône jobA1 : le panneau liste les candidatures **à déclarer** (mois précédent et mois en
   cours), la plus ancienne d'abord. Choisis-en une, puis **Remplir dans Job-Room**.
3. Les réponses remplies sont encadrées en violet. Ce qui reste (en orange) est listé dans le
   panneau avec sa valeur et « Copier » ; « NPA / Lieu » se choisit dans les suggestions de
   Job-Room, et l'extension prend celle qui porte le NPA et le lieu.
4. Vérifie, **Sauvegarder** dans Job-Room, puis **C'est déclaré** : la candidature est marquée
   dans ton Suivi, et la suivante est proposée.

Les champs sont reconnus d'après le relevé du formulaire (`fixtures/job-room-formulaire.json`).
Si Job-Room change son formulaire, refais le relevé : colle `releve-formulaire.js` dans la console
du navigateur sur la saisie **vide** (structure seulement, aucune valeur), puis remplace le fichier.

## Permissions

- `activeTab` et `scripting` : agir seulement sur l'onglet où tu cliques sur l'icône, à ce
  moment-là ; aucune lecture des autres sites ni de l'historique.
- `storage` : garder l'adresse de ta plateforme et le jeton dans ce navigateur.
- Accès à ta plateforme : demandé au moment de relier, pour cette seule adresse.

Un formulaire intégré depuis un autre site (cadre) se remplit en l'ouvrant dans son propre
onglet : le panneau propose le lien.
