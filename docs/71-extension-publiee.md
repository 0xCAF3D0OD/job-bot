# 71 — L'extension facile à installer (version 0.58.0)

> Statut : **validé** le 2026-10-18.
> Origine : retour du 2026-10-18, après l'essai de la 0.57 sur Job-Room : l'installation (module temporaire ou signature à la main) et la liaison (adresse et jeton à copier) sont trop compliquées.

## 1. Le constat

- **Installer** : dans Firefox, un module temporaire à recharger à chaque redémarrage, ou une signature à faire soi-même en ligne de commande, avec des clés Mozilla. Dans Chrome, le mode développeur.
- **Relier** : créer un jeton dans Réglages, le copier, ouvrir l'extension, y coller l'adresse de la plateforme et le jeton, puis accepter une autorisation (et, dans Firefox, rouvrir le panneau qui s'est fermé).
- **Mettre à jour** : refaire l'installation à chaque version.

## 2. Le principe

- **Installer** : « Ajouter à Firefox » depuis la boutique de Mozilla (addons.mozilla.org). Les mises à jour arrivent ensuite toutes seules. Chrome viendra plus tard, avec le même paquet.
- **Relier** : un clic sur « Relier » dans l'extension, puis un clic sur « Relier ce navigateur » sur ta plateforme. Plus de jeton à copier.
- Ce qui ne change pas : l'extension ne remplit que sur ton clic, n'envoie jamais rien à ta place, et le jeton reste révocable dans Réglages.

## 3. Le parcours

1. Dans Réglages › Outils › Extension du navigateur : **« Installer l'extension »** ouvre sa page dans la boutique. On clique sur « Ajouter à Firefox ».
2. Juste après l'installation, l'extension ouvre d'elle-même un onglet **« Relier jobA1 »**, sans qu'il faille trouver son icône. Il demande une seule chose : l'adresse de ta plateforme (par exemple `https://joba1.exemple.ch`), retenue ensuite.
3. **« Relier »** demande au navigateur l'accès à cette seule adresse, puis ouvre la page **« Relier ce navigateur »** de ta plateforme.
4. Si tu n'es pas connecté, tu passes d'abord par la connexion.
5. La page dit ce que l'extension pourra faire, puis **« Relier ce navigateur »**. L'extension récupère d'elle-même son jeton, l'onglet affiche « C'est relié » et peut être fermé.
6. L'icône jobA1 est prête, sur les formulaires des employeurs comme sur Job-Room.

**Sans la boutique ou en dépannage** : « Relier avec un jeton » (replié) garde la méthode actuelle.

## 4. Relier sans copier de jeton : comment, et pourquoi c'est sûr

- La page « Relier ce navigateur » est une page de ta plateforme, réservée à un compte connecté. Le clic crée un jeton, comme « Créer un jeton » aujourd'hui.
- Le jeton est posé **dans cette page seulement**. L'extension le lit dans **l'onglet qu'elle a elle-même ouvert**, sur l'adresse que tu as autorisée, puis l'efface de la page.
- **Pourquoi c'est sûr** : un site malveillant qui t'enverrait vers cette page ne pourrait pas lire le jeton. Il n'apparaît que dans ton navigateur, et seule ton extension peut le lire. Il ne passe jamais dans une adresse (ni dans l'historique, ni dans les journaux du serveur).
- Si personne ne vient le lire (page ouverte sans l'extension), le jeton disparaît de la page au bout de 2 minutes, et la liste des jetons dans Réglages permet de le révoquer.
- Le jeton porte le nom du navigateur (« Firefox », « Chrome »…), et Firefox est maintenant reconnu.

## 5. Les mises à jour

- La boutique met l'extension à jour toute seule. Ta plateforme, elle, se met à jour quand tu le fais. Les deux peuvent donc ne pas avoir la même version.
- À la liaison, puis à chaque ouverture, l'extension demande la version de la plateforme. Si une fonction manque (par exemple Job-Room avec une plateforme d'avant la 0.57), elle le dit clairement (« Mets ta plateforme à jour pour remplir Job-Room ») au lieu d'une erreur.
- La version de l'extension change seulement quand elle-même change. Chaque nouvelle version passe par la boutique (§6).

## 6. La boutique de Mozilla

**Ce que je prépare (dans le dépôt) :**
- Le **paquet** : seulement ce que l'extension utilise. Le relevé de Job-Room, le script de relevé et le mode d'emploi en sont exclus. Le paquet est produit par `make extension`.
- La **fiche**, dans `extension/fiche-boutique.md` :
  - le nom (« jobA1 — remplir mes candidatures ») ;
  - le résumé, la description et la catégorie ;
  - des captures avec des données fictives : un formulaire d'employeur, Job-Room, la liaison.
- La **politique de confidentialité** de l'extension, à coller dans la fiche. Elle dit ce qui sort du navigateur, et vers où :
  - vers **ta plateforme seulement**, et rien vers moi ni vers un tiers ;
  - l'adresse de l'onglet, pour reconnaître la candidature ;
  - la question d'un formulaire, pour proposer une réponse ;
  - le « J'ai envoyé » et le « C'est déclaré ».
- **La déclaration des données dans le manifeste** :
  - aujourd'hui, elle dit « aucune donnée collectée » ;
  - pour Mozilla, tout ce qui sort du navigateur compte, même vers ton propre serveur ;
  - elle déclarera donc l'adresse des pages (« activité de navigation ») et le texte d'une question (« contenu des sites ») ;
  - Mozilla les affiche à l'installation.
- Le code est lisible tel quel, sans étape de construction : la relecture de Mozilla est plus simple.

**Ce qui est de ton côté :**
- Le compte développeur Mozilla (gratuit), et l'envoi du paquet dans la boutique, en **« listée »** (visible et cherchable) ou en **« non listée »**. Si tu choisis « non listée », Mozilla signe le paquet sans le montrer dans la boutique, et il faut quand même gérer les mises à jour.
- La relecture de Mozilla : de quelques heures à quelques jours, à chaque version.
- **Plus tard, Chrome** : le même paquet sur le Chrome Web Store (5 $ une fois), à cadrer à part.

## 7. Ce qui change dans le code

| Où | Quoi |
|---|---|
| Extension | onglet « Relier jobA1 » ouvert à l'installation ; liaison par la page de la plateforme ; contrôle de version ; déclaration des données ; une page de fond pour suivre l'onglet de liaison (`background`, sans nouvelle permission) |
| Plateforme | page « Relier ce navigateur » (`/extension/relier`) ; Réglages › Extension du navigateur : « Installer l'extension » en premier, la méthode par jeton repliée ; Firefox reconnu dans le nom du jeton ; version exposée à l'extension |
| Dépôt | `make extension` (paquet), `extension/fiche-boutique.md` (fiche et politique de confidentialité), mode d'emploi mis à jour |

Pas de migration : les jetons existent déjà (docs/25).

## 8. Livraison

| Étape | Qui |
|---|---|
| **0.58.0** : liaison en un clic, onglet à l'installation, contrôle de version, paquet, fiche et politique de confidentialité | moi (une PR) |
| Compte Mozilla, envoi du paquet, réponses à la relecture | toi |
| Lien de la boutique ajouté dans Réglages, une fois la fiche en ligne | moi (petite PR) |

Tant que la fiche n'est pas en ligne, « Installer l'extension » renvoie au mode d'emploi actuel.

## Points à valider

1. **Publication dans la boutique de Mozilla**, Chrome plus tard (§2, §6). Listée ou non listée : à toi de choisir.
2. **Liaison en un clic** : le jeton posé dans la page de la plateforme et lu par l'extension dans l'onglet qu'elle a ouvert, puis effacé. La méthode par jeton reste, repliée (§3, §4).
3. **Onglet « Relier jobA1 » à l'installation** (§3).
4. **Contrôle de version** entre l'extension et la plateforme (§5).
5. **Déclaration des données** : activité de navigation et contenu des sites, vers ta plateforme seulement (§6).
6. **Une PR 0.58.0**, sans migration ; la publication est de ton côté (§8).

## Écarts avec le cadrage

- **Signal de la page** : une fois le jeton posé, la page passe à `/extension/relier?etat=pret`. Ce changement d'adresse prévient l'extension ; le jeton, lui, reste dans la page (élément caché `#jobbot-extension-token`). L'extension ne le lit que dans l'onglet qu'elle a ouvert, si l'adresse de cet onglet est toujours celle de la plateforme et la page de liaison (un test le vérifie, et échoue sans ce contrôle). Elle ignore ce qui ne ressemble pas à un jeton (`jbx_…`).
- **Jeton non lu** : au bout de 2 minutes, la page le retire et le **révoque** (pas seulement « révocable »), puis invite à recommencer depuis l'icône.
- **Contrôle de version** : plutôt qu'un numéro de version (« dev » en local), la plateforme annonce ce qu'elle sait faire (`/api/extension/me` : `features`, aujourd'hui `forms` et `job-room`). Sur Job-Room, une plateforme d'avant la 0.57 donne « Mets ta plateforme jobA1 à jour (0.57 ou plus) pour remplir Job-Room ». Une plateforme d'avant la 0.58 n'a pas la page de liaison : l'extension invite alors à relier avec un jeton.
- **Firefox 140 au moins** (au lieu de 128) : c'est la version qui lit la déclaration des données. Firefox pour Android : 142. L'outil de Mozilla (`web-ext lint`) ne signale plus qu'un avertissement attendu : la ligne `service_worker`, gardée pour Chrome, est ignorée par Firefox.
- **Données déclarées** : `browsingActivity` et `websiteContent`, en « requises ».
- **Captures pour la boutique** : non faites dans cette PR. Le panneau a été vérifié avec de fausses données (onglet d'accueil, « C'est relié », Job-Room), mais les captures de la fiche se font mieux depuis l'extension installée, sur une plateforme d'essai. Je les ferai avec toi, ou tu les prends au moment de l'envoi.
- **Réglages** : « Installer l'extension » renvoie au mode d'emploi tant que la fiche n'est pas en ligne (`STORE_URL` vide dans `ExtensionPanel.vue`). Puis les navigateurs reliés, et « Relier avec un jeton » replié.
- **Essayé** : la page « Relier ce navigateur » sur l'instance de test (jeton posé, adresse `?etat=pret`, « C'est relié » une fois le jeton effacé), les Réglages, le panneau de l'extension dans Chrome sans fenêtre (API de l'extension imitée), le paquet (`make extension`, 12 fichiers).
- **Non essayé** : l'extension installée et reliée en vrai (le navigateur de test ne charge pas d'extension). C'est l'essai de ton côté, avant l'envoi à Mozilla.

## Complément 0.58.1 : premier essai réel

- **Installation d'essai** : chargée depuis `~/Documents/job-bot/extension/manifest.json`, la page de fond ne se charge pas (« Échec du chargement pour l'élément <script> … background.js ») ; le même dossier, copié ailleurs, se charge dans un Firefox vierge. macOS ne laisse Firefox lire, dans `~/Documents`, que le fichier choisi (`manifest.json` porte seul l'autorisation `com.apple.macl`). Le **paquet** (`make extension`, un seul fichier) se charge bien : le mode d'emploi et les Réglages l'indiquent désormais. La boutique installera de toute façon un paquet.
- **Job-Room** : avec l'extension chargée depuis le paquet, le remplissage fonctionne sur le vrai Job-Room (date, mode, entreprise… encadrés en violet).
- **Panneau trop large** : une longue candidature dans la liste élargissait le panneau hors de l'écran. Le panneau garde sa largeur (une colonne, champs à 100 %) ; l'intitulé se coupe avec « … » et s'affiche en entier au survol.
- **Champs facultatifs signalés à tort** : Job-Room écrit `required="false"` sur ses champs facultatifs, et la seule présence de l'attribut rend `required` vrai. Seul `aria-required="true"` compte désormais : case postale, personne contactée, courriel, téléphone et lien vides ne sont plus « à faire ».
- Extension 0.58.1.
