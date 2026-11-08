# 143 — La maquette du 8 novembre 2026 : l'ordinateur et les éléments partagés

> Statut : **validé par Kevin le 2026-11-08** (consigne `docs/mobile/PROMPT_CLAUDE_CODE.md`, maquette
> `jobA1_maquette_2026-11-08.zip`, `docs/mobile/LISEZMOI.md`). La maquette fait foi pour le téléphone et pour
> l'ordinateur, à la place de Figma (exception du 2026-11-08 dans `CLAUDE.md`).

## 1. Les sources

Dans l'ordre, de la plus forte à la plus faible :

1. `docs/mobile/MODIFICATIONS_8_NOVEMBRE_SOIR.md` (lots 11 à 15, envoyé par Kevin le 8 novembre au soir) : il l'emporte
   sur la consigne en cas de conflit ;
2. `docs/mobile/PROMPT_CLAUDE_CODE.md`, en particulier les décisions D18 à D27 (§3 ci-dessous) ;
3. `docs/mobile/LISEZMOI.md` ;
4. les captures `docs/mobile/captures/` et `docs/mobile/captures/etats/` (le rendu) ;
5. le HTML de `docs/mobile/maquettes/*.dc.html` (textes, tailles, espacements) ;
6. `docs/mobile/tokens.css` et `frontend/src/style.css` (jetons) ;
7. `docs/regles-ui-ergonomie.md` et les docs existantes.

Les maquettes Get'emAll (`AutoriserGetemall`, `ConfidentialiteGetemall`, `ReglagesConnexions`, `ReglagesRetirer`)
restent dans `docs/mobile/maquettes/` : elles ne sont pas dans le paquet du 8 novembre et restent la référence de
docs/140.

## 2. Les lots

Une PR par lot, dans cet ordre. Chaque PR vise `main` et contient les lots précédents tant qu'ils ne sont pas
fusionnés : on fusionne dans l'ordre 0, 1, 2… et chaque PR ne montre plus que son lot une fois la précédente fusionnée.

| Lot | Contenu |
|---|---|
| 0 | Mise en place, sans interface : maquettes, captures, LISEZMOI, avatars, ce document, exception de `CLAUDE.md`, décisions dans `regles-ui-ergonomie.md`. |
| 1 | Jetons et mécanique commune : 3 jetons, 4 ombres, keyframes `ja-slide-r`, `ja-slide-l`, `ja-pop`, composable `useDismissLayer`. |
| 2 | Composants partagés : `Composer`, `SuggestionChips`, `CalendarDate`, `DateTimeField` et `DateTimePanel`, `ProfileImage` et `AvatarPicker`. |
| 3 | En-tête et panneaux de l'ordinateur : recherche en bulle, cloche et compte en panneaux non modaux de 420 px, Assistant en panneau de 480 px. |
| 4 | Candidatures sur ordinateur (`CandidaturesOrdinateurB`) : filtres à la place de la liste, menu « … », ajout d'une offre, Envoyées, Rendez-vous. |
| 5 | Aujourd'hui sur ordinateur : bande, H1 d'action, carte Mois ORP à cheval, tâches sur 880 px. |
| 6 | Bilan, Préparer, Profil sur ordinateur. |
| 7 | Notifications, Alertes, Réglages sur ordinateur. |
| 8 | Pages d'état, Connexion, Premiers pas sur ordinateur. |
| 9 | Téléphone : éléments partagés (Assistant, Préparer, Offre provisoire, Ajouter une offre, Envoyées, Rendez-vous, Compte, Alertes, Réglages, Bilan, Extension). |
| 10 | Vérification finale et « Écarts connus ». |
| 11 | Corrections (MODIFICATIONS §3) : champs de formulaire, en-tête de l'ordinateur, Assistant qui écrit, Mes alertes e-mail, nouveau rendez-vous dans le panneau de détail. |
| 12 | Envoyées : détail en deux colonnes (`DetailTwoColumns`). |
| 13 | À traiter : détail en deux colonnes ; lignes de « Ce que je cherche ». |
| 14 | Rendez-vous ORP : sans pastilles « Noté », formulaire en trois parties, colonne « Le rendez-vous ». |
| 15 | Préparer sur ordinateur ; « J'ai déjà postulé ». |

## 3. Les décisions D18 à D27

| N° | Décision | Remplace |
|---|---|---|
| D18 | **Seuil unique 820 px (D8 reste).** Les mentions « < 600 px » et « >= 1024 px » de l'ancien LISEZMOI sont fausses. Téléphone : largeur <= 820 px. Ordinateur : > 820 px. Entre 821 et 1327 px, les conteneurs de 1280 et 880 px prennent `max-width` avec 24 px de marge de chaque côté. | — |
| D19 | **Rayons D7 (8, 18, 34, 999) restent.** Traduction des rayons de la maquette dans le §4 de la consigne. | — |
| D20 | **Couleurs** : traduction obligatoire par le tableau du §3 de la consigne, avec 3 jetons nouveaux (`--line-strong`, `--field-border`, `--text-disabled`) et 4 ombres nouvelles (`--shadow-panel`, `--shadow-menu`, `--shadow-band-card`, `--shadow-composer`). | — |
| D21 | **Barre du bas du téléphone** : elle s'appelle « Bilan », pas « Progresser » (D2 reste), et « Accueil » (D1 reste). Les maquettes affichent encore « Progresser » : ignorer ce mot. | — |
| D22 | **Carte = cliquable.** Une carte (fond `--surface` + bordure) est toujours entièrement cliquable. Une information seule n'a pas de cadre : lignes séparées par `--line-soft`. Dans une carte cliquable, jamais de bouton ni de pastille d'action : un libellé coloré (couleur du ton, 15 px, 700) suivi de « › ». | §4 (cartes), en partie |
| D23 | **Icônes sans fond.** Aucune pastille ou rond coloré derrière une icône décorative, sur téléphone et sur ordinateur. Exception : l'icône Assistant de la barre du bas du téléphone garde son cercle. | — |
| D24 | **Panneaux latéraux non modaux** (cloche, compte, Assistant) sur ordinateur : 420 px (Assistant 480 px), sans voile. Un clic à l'extérieur ferme tout. Les filtres de Candidatures **remplacent la colonne liste** au lieu de s'ouvrir en popover. Le panneau du compte porte Mon compte, Affichage, Aide et Se déconnecter. | docs/32 §2.2 (voile), maquette CandidaturesOrdinateur état `f`, docs/89 (contenu du menu du compte) |
| D25 | **Zone de saisie unique (Composer)** pour tout message libre envoyé tel quel. Les champs de formulaire restent des champs de formulaire. | — |
| D26 | **Date et heure** : déclencheurs en pilule, sélecteur qui prend la place du formulaire (plein écran sur téléphone), icône calendrier qui contient la date (CalendarDate) au lieu des carrés colorés. Remplace les `<input type="date">` et `<input type="time">` natifs (`OrpMeetingForm.vue`, `OrpOutcomeSheet.vue`). | docs/22 en partie |
| D27 | **Personnage sur ordinateur** : 240 px de haut sur les pages d'état, 360 px aux premiers pas. La note « 290 px sur ordinateur » de docs/141 §4 est remplacée. Liste fermée de docs/141 §3 inchangée. | docs/141 §4 |

Autres décisions qui restent valables : D12 (chiffre au centre de l'anneau), D13 (mouvement), D14 (une hauteur par
ligne de liste), D15, D16, D17.

## 4. Écarts connus

Ce qui ne suit pas la maquette, avec la raison. Rempli au fil des lots, complété au lot 10.

| Écran ou élément | Écart | Raison | Lot |
|---|---|---|---|
| En-tête de l'ordinateur | Le menu principal reste centré ; la maquette le place à gauche, après le logo. | §7 de la consigne : ne pas changer le menu principal. Question posée à Kevin dans la PR du lot 3. | 3 |
| Assistant (ordinateur) | Pas de « + » ni de micro dans la zone de saisie, donc pas de pièce jointe (CV) dans la conversation. | Aucun fichier ne part à l'IA sans règle (I-1, E-5) et la dictée est masquée (O-4) ; le serveur de l'Assistant ne reçoit pas de fichier. | 3 |
| Assistant (ordinateur) | La bulle de l'Assistant prend `--panel` au lieu de #F1EFE9. | #F1EFE9 n'est pas un jeton de tokens.css. | 3 |
| Assistant (ordinateur) | Le panneau garde son propre gabarit (classes du SidePanel non modal) au lieu du composant SidePanel. | Le panneau de l'Assistant est aussi la page Assistant du téléphone ; le découper aurait recréé le composant. | 3 |
| Panneau du compte | Les icônes « Réglages » et la roue de la maquette : on garde l'icône Réglages de jobA1 (curseurs). | Iconographie docs/101 : pas de nouvelle icône pour un sens qui en a déjà une. | 3 |
| Titres des panneaux | 20 px dans la maquette, `--font-section` (22 px) ; intertitres 13 px, `--label-caps`. | Échelle de jetons (docs/135). | 3 |
| Ajouter une offre | Pas de menu « + » (Importer le PDF de l'annonce, Importer une capture d'écran). | Aucun fichier ne part à l'IA sans règle (I-1, E-5) ; le serveur ne lit qu'un lien ou un texte. Question posée à Kevin dans la PR du lot 4. | 4 |
| Ajouter une offre | Les exemples propres au métier sous le champ (« Ex. Menuisier à Sion… ») disparaissent. | La zone de saisie commune (Composer) n'a qu'un placeholder, celui de la maquette. | 4 |
| Menu « ⋯ » de la fiche (ordinateur) | Après les entrées dessinées, un trait puis les autres actions de la fiche (J'ai postulé, expirée, Assistant). | Ces actions n'ont pas d'autre place sur ordinateur ; les retirer en supprimerait l'usage. | 4 |
| Envoyées (ordinateur) | Le détail à droite reprend le contenu du panneau de candidature, pas le tableau « Suivi » ni « Ce que dit jobA1 ». | Ces deux blocs n'ont pas de données côté serveur ; question posée à Kevin dans la PR du lot 4. | 4 |
| Rendez-vous (ordinateur) | « À noter » ouvre toujours le dialogue « Ce qui a été convenu » ; la maquette le montre dans le détail, à droite. | Le formulaire est celui de la feuille (OrpOutcomeSheet) ; le déplacer dans le détail est prévu au lot 10 si Kevin le confirme. | 4 |
| Champs date et heure | Il reste des champs natifs ailleurs (entretien, candidature, contacts, entraînement, réglages). | Hors des écrans du lot 4 ; traités au lot 10. | 4 |
| Aujourd'hui (ordinateur) | La phrase sous le titre dit « N offres sont à trier » au lieu de « N nouvelles offres sont arrivées cette nuit ». | Le serveur ne donne pas l'heure d'arrivée des offres ; la phrase dit ce qu'on sait. | 5 |
| Aujourd'hui (ordinateur) | « À retenir » (l'écart du Bilan) et la bande « Tri du jour » disparaissent de l'ordinateur ; le tri devient une tâche « Trier N offres ». | Absents de la maquette. « À retenir » reste lisible dans le Bilan. Question posée à Kevin dans la PR du lot 5. | 5 |
| Aujourd'hui (ordinateur) | Titres sans maquette : « En pause. », « Tout est à jour. » (objectif atteint ou sans objectif), « Commence par les premiers pas. » (sans accent manuscrit). | La maquette ne dessine que le jour de travail et le jour de repos ; mêmes règles (une fin manuscrite au plus). | 5 |
| Aujourd'hui (ordinateur) | Le titre de la page n'est plus « Aujourd'hui » : c'est l'action du jour (exception ajoutée à titles.test.ts). | LISEZMOI : « H1 = action du jour ». | 5 |
| Police manuscrite | Le sous-ensemble de Caveat Brush gagne « à », « y » et « j » (3,8 → 4,6 Ko). | Les fins du titre d'Aujourd'hui ; scripts/regles.py les lit désormais. | 5 |
| Bilan › Résultats et Formations (ordinateur) | Seule la bande change ; le contenu reste celui d'avant (pas encore « Le mois en bref », « Ce qui bloque » ni la bande de trois chiffres à cheval). | « Ce qui bloque » (réponses par site, jamais relancées) demande des données que l'API des résultats ne donne pas sous cette forme. Question posée à Kevin dans la PR du lot 6. | 6 |
| Préparer (ordinateur) | Les réglages à gauche (modèle, langue, mis en avant, longueur), la lettre au centre et « J'ai relu la lettre » en bas à droite ne sont pas repris ; seules les retouches et la zone de saisie le sont. | Refaire la mise en page de Préparer dépasse le lot ; les blocs actuels gardent leurs tests. | 6 |
| Préparer | Pas de menu « + » (Joindre l'annonce complète, Joindre un document) ni de micro. | Aucun fichier ne part à l'IA sans règle (I-1, E-5) ; l'annonce part déjà avec la demande ; la dictée est masquée (O-4). | 6 |
| Profil (ordinateur) | L'en-tête (image, nom, « Changer d'image », « Modifier ») est repris ; les blocs Mon CV, Compétences trouvées et Ce que je cherche restent dans leurs onglets (Critères, Parcours, Coordonnées). | Le sous-titre « Junior DevOps » n'existe pas dans les coordonnées : seule la ville s'affiche. Question posée à Kevin dans la PR du lot 6. | 6 |
| Bilan › ORP (ordinateur) | « Ajouter une recherche » ouvre le formulaire dans le Suivi ORP du mois (/bilan/orp?ajouter=1). | Le formulaire d'ajout vit dans le Suivi ORP ; pas de second formulaire. | 6 |
| Mes alertes e-mail (ordinateur) | Une ligne par recherche et par site (« DevOps · jobup », « DevOps · LinkedIn »…), pas une ligne par recherche ; « … » agit sur toute la recherche (Modifier la recherche, Supprimer la recherche). | Une recherche jobA1 se crée sur chaque site ; la maquette montre un site par recherche. Question posée à Kevin dans la PR du lot 7. | 7 |
| Mes alertes e-mail (ordinateur) | La phrase du bas « jobA1 lit seulement les e-mails d'alerte transférés par ton filtre Gmail. Les autres sont supprimés à la réception. » n'est pas reprise. | Le Transfert Gmail (D) attend encore la validation de Kevin ; la phrase promettrait un traitement des e-mails pas encore en place (R-1, docs/regles-securite-donnees.md). | 7 |
| Mes alertes e-mail (ordinateur) | Sous la liste restent les codes des sites, les alertes reçues et les premières offres. | Absents de la maquette, mais le bandeau « code de vérification » y renvoie ; les retirer couperait cet usage. | 7 |
| Réglages (ordinateur) | Les sections gardent leur contenu actuel : pas de « Rappels ORP », « Relances conseillées », « E-mail en plus des notifications » (résumé du lundi), Langue (Deutsch, English), Taille du texte, ni Canva dans Connexions. | Ces réglages n'existent pas encore ; les ajouter serait les inventer. Question posée à Kevin dans la PR du lot 7. | 7 |
| Réglages (ordinateur) | Les boutons des lignes gardent leur forme actuelle (coins de 8 px) au lieu de la pilule. | Le style commun des boutons secondaires ; le changer touche toutes les pages (lot 10). | 7 |
| Mes alertes e-mail | Titre possessif accepté (exception dans titles.test.ts). | Repris tel quel de la maquette du 8 novembre. | 7 |
| Premiers pas (ordinateur) | L'étape 2 garde les puces des postes et des lieux au lieu des lignes « Postes ›, Lieux ›, Taux d'activité › » ; l'étape 3 montre les offres une à une, pas les trois en liste. | Les lignes à chevron ouvriraient un écran de saisie que la maquette ne dessine pas ; le tri une à une garde « Annuler » après « Écarter ». Question posée à Kevin dans la PR du lot 8. | 8 |
| Premiers pas (ordinateur) | La zone du CV dit « Importer mon CV », pas « Glisse ton CV ici ». | Le glisser-déposer n'existe pas ; la phrase promettrait un geste qui ne marche pas. | 8 |
| Premiers pas (ordinateur) | « 312 offres lues. En trier 3. » reprend le nombre de la maquette, comme le titre du téléphone (« Lire 312 offres »). | Le serveur ne donne pas encore le nombre d'offres lues ; question posée à Kevin dans la PR du lot 8. | 8 |
| Aucune offre (ordinateur) | L'état tient dans la colonne de la liste (560 px), à gauche, au lieu d'être centré sur la page. | La colonne de la fiche reste à sa place ; la maquette montre la page sans fiche. | 8 |
| Connexion (ordinateur) | Aucun changement : la page suivait déjà la maquette (5.11). | — | 8 |
| Coller le texte de l'annonce (téléphone) | Pas de menu « + » (Importer le PDF de l'annonce, Importer une capture d'écran). | Aucun fichier ne part à l'IA sans règle (I-1, E-5) ; le texte collé suffit. | 9 |
| Ajouter une offre (téléphone) | Pas de menu « + », comme sur ordinateur (lot 6). | Même raison (I-1, E-5). | 9 |
| Préparer (téléphone) | Pas d'icône Canva à revoir : le bouton Canva n'existe pas encore dans l'app. | Canva attend l'app de Kevin (5.11). | 9 |
| Compte (téléphone) | Le bouton de l'image est posé sur la carte du profil, à côté du lien, pas dedans ; il se lit « Changer ton image ». | Pas de bouton dans une carte cliquable (§7). | 9 |
| Alertes e-mail (téléphone) | Une ligne par recherche et par site, et pas de phrase Gmail en bas ; les codes des sites, les alertes reçues et les premières offres restent sous la liste. | Mêmes raisons que sur ordinateur (lot 7). | 9 |
| Réglages (téléphone) | Rien à changer : aucune icône décorative n'a de fond, et les icônes des lignes du Compte font déjà 20 px comme la maquette. La page garde ses sections actuelles (voir lot 7). | Les lignes « Exporter mes données » et « Charte d'utilisation de l'IA » avec icône n'existent pas sous cette forme ; les ajouter serait inventer leur page. Question posée à Kevin dans la PR du lot 9. | 9 |
| Bilan › Résultats (téléphone) | Pas encore conforme, et non modifié : la capture montre sous « Résultats » « Le mois en bref », « Ce qui bloque » et « Le carnet », qui vivent aujourd'hui dans l'onglet ORP. | Déplacer ces parties change le contenu des onglets ; « Ce qui bloque » demande des données que l'API des résultats ne donne pas (voir lot 6). Question posée à Kevin dans la PR du lot 9. | 9 |
| Alertes e-mail (téléphone) | « Créer » dans une ligne fait 44 px de haut, pas 40. | Le ⋯ voisin fait 40 × 44 px dans la maquette : une rangée de contrôles a une seule hauteur (docs/94, audit des contrôles), et la cible reste à 44 px. | 9 |
| Poids | Le budget passe à 334 Ko de JavaScript et 71 Ko de CSS. | Les pages Alertes et Compte du téléphone. | 9 |
| Champs date (formulaires) | Les huit champs de date natifs (entretien, suite de l'entretien, contact, date d'envoi, relance, formation terminée, pause) deviennent un DateField : la pilule sans heure, et le sélecteur à la place du champ (pas du formulaire entier). | Le sélecteur prend toute la ligne de la grille ; remplacer tout le formulaire masquerait les autres champs pendant le choix. | 10 |
| Champs date (formulaires) | Pour une date passée (envoi, contact, formation), le sélecteur se borne avec `min` et `max` et n'affiche pas les raccourcis à venir (Demain, Lundi prochain…). Aucun raccourci n'est ajouté. | La maquette ne dessine que le sélecteur d'un rendez-vous à venir. Question posée à Kevin dans la PR du lot 10. | 10 |
| Champs date facultatifs | « Effacer la date » sous la pilule quand une date est choisie (entretien, suite, formation). | Le champ natif permettait de vider la date ; sans ce lien, on ne pourrait plus la retirer. Question posée à Kevin dans la PR du lot 10. | 10 |
| Couleurs en dur | Restent : les feuilles de lettre et de CV (papier blanc, encre #1a1a1a), les logos Google et Microsoft, le fond blanc des logos d'employeur, l'encre foncée du logo pêche des cartes (#1B1F2A dans les deux thèmes), la case à cocher blanche des documents lus (#474C59), la pastille de l'icône IA (#f4a261) et une bulle de la victoire (#a8e6d2). | Papier et logos tiers sont hors du §3 ; aucun jeton ne garde une encre foncée en sombre ; les deux dernières couleurs ne sont pas dans la table du §3. Question posée à Kevin dans la PR du lot 10. | 10 |
| Icônes sur fond | Restent sur fond : les icônes des formations et du financement (maquette Explorer) et la pastille des lignes repliables du Suivi ORP. | Les deux premières sont dessinées ainsi ; la troisième est hors des maquettes du 8 novembre. | 10 |
| Mouvement réduit | Seul reste le fondu lié au défilement de la barre du haut (ordinateur), qui suit la position de la page et non le temps. | Ce n'est pas une animation qui joue seule. | 10 |
| Champs de formulaire | Coins de 8 px. | Champs : 12 px dans l'ancienne maquette, 8 px (D7). | 11 |
| Assistant qui écrit | La ligne « Je consulte tes candidatures… » (outil lu par l'Assistant) disparaît avec l'élément « … » : seuls les trois points restent jusqu'au premier mot. | MODIFICATIONS 11.3 supprime l'élément sous la liste des messages et ne dessine que les trois points. | 11 |
| Mes alertes e-mail (ordinateur) | Le « › » après « Créer l'alerte » est l'icône chevron de 18 px, pas un caractère. | docs/101 : aucun caractère ne sert d'icône (test `iconography`). | 11 |
| Envoyées, détail (ordinateur) | « Entretiens » et « Pour l'ORP », quand ils existent, restent dans la colonne principale, sous « Statut ». | La maquette ne les dessine pas ; les retirer ferait perdre le retour d'entretien et les champs Job-Room. Question posée à Kevin dans la PR du lot 12. | 12 |
| Envoyées, détail (ordinateur) | Dans « Documents », le CV (Word) et « Ouvrir l'annonce » s'ajoutent en liens à la lettre, sans menu « ⋯ ». « Site de l'employeur » reste sous « Trouver quelqu'un » quand le site est connu. | La maquette n'a qu'une lettre et pas de site ; ces liens existaient déjà. | 12 |
| Envoyées, détail | Les deux colonnes commencent à 1024 px, comme la liste et le détail côte à côte ; de 821 à 1023 px, la candidature s'ouvre dans le panneau latéral, en une colonne. | Le détail n'est à droite de la liste qu'à partir de 1024 px (lot 4). | 12 |
| À traiter, détail (ordinateur) | « Le poste » garde ce qui existait : « Résumé par jobA1 », « Voir l'annonce complète », le lien « Postuler… », le menu des autres sites et les réserves sur l'annonce. « Entreprise » et « Contacts » restent en lignes repliables sous « Le poste ». | La maquette montre une offre sans texte ; ces éléments servent dès que l'annonce est lue. | 13 |
| À traiter, détail | « Reçue » dit « par une alerte e-mail » pour toute offre qui n'a pas été ajoutée à la main (« ajoutée par toi »). | Le serveur ne distingue pas encore une offre reçue par alerte d'une offre lue par l'extension ; question posée à Kevin dans la PR du lot 13. | 13 |
| À traiter, détail | Les deux colonnes commencent à 1024 px ; de 821 à 1023 px, la fiche garde une colonne. | Même seuil que la liste et le détail côte à côte (lot 4). | 13 |
| Profil › Critères (ordinateur) | La valeur commence par une majuscule (« Refusé hors de tes lieux »), comme dans la maquette ; le formulaire s'ouvre sur le critère de la ligne. | Lot 13.2. | 13 |
| Premiers pas (ordinateur) | 13.2 ne s'applique pas encore : l'étape 2 garde les puces des postes et des lieux (écart du lot 8). | Les lignes à chevron ouvriraient un écran de saisie que la maquette ne dessine pas. | 13 |
