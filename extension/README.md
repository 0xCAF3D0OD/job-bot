# Extension job-bot (docs/25)

Remplit le formulaire de candidature de l'employeur avec tes données job-bot : coordonnées,
CV et lettre en PDF, texte de la lettre, et, sur demande, une proposition de réponse aux
questions libres. **Elle n'envoie jamais rien à ta place** et ne coche aucune case.

## Installer (Chrome, Edge, Brave)

1. Ouvre `chrome://extensions` et active le **mode développeur** (en haut à droite).
2. **Charger l'extension non empaquetée** → choisis ce dossier `extension/`.
3. Épingle l'icône job-bot dans la barre du navigateur.

## Relier à ta plateforme

1. Sur la plateforme : **Réglages › Extension du navigateur › Créer un jeton** ; copie-le
   (il n'est montré qu'une fois).
2. Clique sur l'icône job-bot : colle l'adresse de ta plateforme (en `https://`, ou
   `http://localhost:…` sur ta machine) et le jeton, puis **Relier**. Le navigateur demande
   l'autorisation de joindre cette adresse, et seulement celle-ci.

## Utiliser

Sur le formulaire de l'employeur (ouvert depuis « Postuler ») : icône job-bot →
**Remplir le formulaire**. Les champs remplis sont encadrés en violet, les champs obligatoires
restants en orange. Vérifie, envoie depuis le site, puis **J'ai envoyé ma candidature** :
elle arrive dans ton Suivi avec l'adresse du formulaire.

## Permissions

- `activeTab` et `scripting` : agir seulement sur l'onglet où tu cliques sur l'icône, à ce
  moment-là ; aucune lecture des autres sites ni de l'historique.
- `storage` : garder l'adresse de ta plateforme et le jeton dans ce navigateur.
- Accès à ta plateforme : demandé au moment de relier, pour cette seule adresse.

Un formulaire intégré depuis un autre site (cadre) se remplit en l'ouvrant dans son propre
onglet : le panneau propose le lien.
