# Extension jobA1 (docs/25, docs/70, docs/71)

Remplit le formulaire de candidature de l'employeur avec tes données jobA1 : coordonnées,
CV et lettre en PDF, texte de la lettre, et, sur demande, une proposition de réponse aux
questions libres. **Elle n'envoie jamais rien à ta place** et ne coche aucune case de
consentement ; sur Job-Room, elle choisit les réponses de la déclaration (mode, assignation,
taux, résultat), que tu vérifies avant de sauvegarder.

Sur Job-Room, elle remplit la saisie d'une recherche d'emploi avec une candidature de ton Suivi.
Là, elle choisit aussi les réponses de la déclaration (mode, assignation, taux, résultat), mais
n'enregistre rien : « Sauvegarder » reste le tien.

## Installer

- **Firefox** : bientôt dans la boutique de Mozilla (« Ajouter à Firefox », mises à jour
  automatiques). En attendant, pour essayer : `make extension`, puis
  `about:debugging#/runtime/this-firefox` → **Charger un module complémentaire temporaire…** →
  le fichier `extension/web-ext-artifacts/joba1-<version>.zip`. Firefox l'enlève à chaque
  redémarrage. Firefox 140 ou plus.
  - Charger le **zip** plutôt que `manifest.json` : depuis un dossier de `~/Documents`, macOS ne
    laisse Firefox lire que le fichier choisi, et la page de fond (`background.js`) ne se charge
    pas (« Échec du chargement pour l'élément <script> »).
- **Chrome, Edge, Brave** : `chrome://extensions`, **mode développeur**, **Charger l'extension
  non empaquetée** → ce dossier `extension/`.

À l'installation, un onglet **« Relier jobA1 »** s'ouvre.

## Relier à ta plateforme

1. Dans l'onglet « Relier jobA1 » (ou en cliquant sur l'icône) : l'adresse de ta plateforme
   (`https://…`, ou `http://localhost:5173` sur ta machine), puis **Relier**. Le navigateur
   demande l'accès à cette adresse, et seulement celle-ci.
2. Une page de ta plateforme s'ouvre : **Relier ce navigateur**. L'extension y lit son jeton,
   l'efface de la page, et c'est relié. Le jeton ne passe jamais dans une adresse ; s'il n'est
   pas lu dans les 2 minutes, il est révoqué.
3. Épingle l'icône jobA1 dans la barre du navigateur.

Si le panneau se ferme pendant la demande d'accès (fréquent dans Firefox), rouvre-le et clique
à nouveau sur **Relier**. **Relier avec un jeton** (replié) garde l'ancienne méthode : un jeton
créé dans Réglages › Extension du navigateur, à coller.

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

## Les codes de vérification (docs/112)

Quand jobup ou jobs.ch demande le code envoyé à ton adresse jobA1 (« Entrez votre code de
vérification »), clique sur l'icône : **Remplir mes codes tout seul** donne, une fois, l'accès à
leurs pages de connexion (`auth.jobup.ch`, `auth.jobs.ch`). Ensuite, sur ces pages, l'extension
prévient jobA1 (qui relève la boîte toutes les 15 secondes), attend le code jusqu'à 5 minutes,
le remplit et clique **Continuer**, sans ouvrir le panneau. Sans cet accès, recopie le code
depuis la page Alertes de jobA1.

## Paquet pour la boutique

`make extension` produit `web-ext-artifacts/joba1-<version>.zip`, avec seulement ce que
l'extension utilise. Les textes de la fiche et la politique de confidentialité sont dans
`fiche-boutique.md`. Chaque version envoyée à Mozilla doit avoir un nouveau numéro
(`manifest.json`).

## Permissions

- `activeTab` et `scripting` : agir seulement sur l'onglet où tu cliques sur l'icône, à ce
  moment-là ; aucune lecture des autres sites ni de l'historique.
- `storage` : garder l'adresse de ta plateforme et le jeton dans ce navigateur.
- Page de fond (`background.js`) : ouvrir l'onglet d'accueil à l'installation, et lire le jeton
  dans l'onglet de liaison qu'elle a ouvert, sur l'adresse autorisée.
- Accès à ta plateforme : demandé au moment de relier, pour cette seule adresse.
- Accès aux pages de connexion de jobup et jobs.ch (facultatif) : demandé par « Remplir mes codes
  tout seul », pour y remplir le code de vérification ; rien d'autre n'y est lu.

Un formulaire intégré depuis un autre site (cadre) se remplit en l'ouvrant dans son propre
onglet : le panneau propose le lien.
