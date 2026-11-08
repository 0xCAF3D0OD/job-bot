# jobA1 : règles d'interface et d'ergonomie

Version 1.6 · 6 novembre 2026 (décisions D1 à D11 de la nouvelle identité mobile, docs/139 ; le personnage, docs/141 ; la liste est à la fin)

Ce document fixe la structure de jobA1. Toute interface doit s'y conformer. **Claude Code n'invente aucune structure, aucun composant et aucun mot qui ne figure pas ici ou dans la bibliothèque Figma.** Un besoin nouveau se propose d'abord, il ne se code pas.

---

## 0. Ordre de priorité des sources

1. Ce document.
2. La bibliothèque Figma jobA1 (variables, composants, écrans de référence), reliée au code par Code Connect.
3. Les règles déjà validées dans `docs/` (notamment `docs/interface.md`, `docs/63`, `docs/86`).
4. Les références externes (section 9).

En cas de contradiction, la source la plus haute l'emporte. Si une contradiction est trouvée, la signaler, ne pas trancher seul.

---

## 1. Promesse et hiérarchie

**Phrase guide** : jobA1 tient ton objectif ORP sans y passer tes journées, te montre ce qui obtient des réponses et t'aide à progresser.

| Niveau | Fonctions | Traitement |
|---|---|---|
| 1. Cœur | Objectif ORP du mois · Dose du jour · Bilan | Toujours visibles, premier niveau |
| 2. Progresser | Formations liées aux manques · Assistant jobA1 | Accessibles, jamais en avant |
| 3. Support | Collecte, note, CV et lettre, suivi et relances, retour d'entretien, résumé ORP | Présents au moment utile, discrets |

Une fonction qui ne sert aucun de ces niveaux ne s'ajoute pas.

---

## 2. Structure et navigation

- **Ordinateur : trois entrées, pas une de plus** : Aujourd'hui · Candidatures · Bilan, en haut. Cloche des
  notifications en haut à droite.
- **Téléphone (sous 820 px) : cinq onglets dans la barre du bas** : Accueil · Candidatures · Assistant · Bilan ·
  Compte (D1, 2026-11-02 ; Material 3 : 3 à 5 destinations). « Accueil » est le nom du téléphone pour Aujourd'hui,
  l'adresse reste `/aujourdhui` ; « Bilan » garde son nom, avec trois sous-onglets ORP · Bilan · Formations (D2,
  2026-11-02). Compte réunit Profil et Réglages ; Notifications (`/notifications`) et Assistant (`/assistant`) sont des
  pages sur téléphone (Q4, 2026-11-02). Les adresses actuelles restent.
- **Candidatures** : trois sous-onglets **À traiter · Envoyées · Rendez-vous**, avec les mêmes noms sur téléphone et
  sur ordinateur (Q5, 2026-11-02 ; remplacent Offres · Suivi · Alertes · Rendez-vous). Les Alertes s'ouvrent par le lien
  « Alertes » en haut de Candidatures.
- **Une page, une question** :
  - Aujourd'hui : « Qu'est-ce que je fais aujourd'hui ? »
  - Candidatures : « Où en sont mes candidatures ? »
  - Bilan : « Qu'est-ce qui marche, et quoi améliorer ? »
- Un élément qui ne répond pas à la question de sa page change de page ou disparaît.
- Profondeur maximale : 2 niveaux (page, puis détail). Pas de troisième niveau d'onglets.
- Lien de retour (« ← Offres ») en haut à gauche, au-dessus du titre.
- Chaque page a son titre d'onglet : « Page · jobA1 ».
- Ouvrir un détail change l'adresse ; le bouton Retour le referme.

## 3. Gabarit de page

Ordre fixe, de haut en bas :

1. Titre de la page (**pas de sous-titre**). Exception : une étiquette au-dessus du titre, en style étiquette (majuscules, `--font-caption` 600, `--letter-label`, `--muted`), pour une précision courte comme la date d'Aujourd'hui. Ce n'est pas un sous-titre : quelques mots, jamais une phrase, toujours au-dessus du titre.
2. Conclusion ou état principal en une phrase (ex. « 4 offres à examiner, 6 relances… », « Les offres de jobs.ch obtiennent plus souvent une réponse »).
3. **Au plus une action principale** (bouton plein) ; aucune quand l'écran se parcourt, comme une liste d'offres à ouvrir.
4. Contenu, l'essentiel d'abord ; le détail est replié et s'ouvre au clic.
5. Pied de page : mentions légales, confidentialité, À propos.

Règles :
- Au plus une action principale par écran. Les autres actions sont secondaires (bouton contour ou lien).
- Bande d'action (1.6.48) : une bande accent pleine largeur sous la conclusion, avec une carte posée dessus qui rend explicite l'action la plus importante de la page et porte sa seule action principale. Une seule bande par page. Elle n'apparaît que s'il y a quelque chose à faire. Elle ne répète jamais le contenu de la page (1.6.54) : pas de bande sur Offres, où la liste est déjà la tâche et le nombre déjà dans l'onglet et la conclusion.
- La conclusion (1.6.62) donne l'état général, sans répéter la bande, qui porte l'enseignement transformé en action. Elle reste exacte dans tous les cas : aucune réponse, trop peu de données, rien à comparer (NN/g : être exact, ne pas embellir).
- **Structure des sections (1.6.69, série du 27.10)**, inspirée de la structure des pages des CFF (la structure seulement : ni leurs textes, ni leur police, ni leurs couleurs, ni leurs pictogrammes ; on écrit « inspiré de la structure des pages des CFF », jamais « style CFF ») :
  - un **titre de section sans point final**, puis des **cartes construites pareil** : un titre en gras, une phrase dessous, le contrôle, l'état ou l'action **à droite sur la même ligne** (loi de proximité) ;
  - les éléments liés vont dans **la même carte**, séparés d'un filet (les sites suivis, les sites d'une recherche d'alerte) ;
  - un détail long se **replie** : le repliable porte une icône, un titre et **l'enseignement en une phrase**, visible replié ; chevron vers la droite fermé, vers le bas ouvert (Bilan) ;
  - sur téléphone, un contrôle large (champ et son texte, jours de la semaine) passe sous le texte ; un interrupteur reste à droite. Un contrôle très large (jeton, adresse, zone de texte) passe sous le texte à toutes les tailles ;
  - composants : `SettingCard` et `SettingRow` (Réglages, Alertes), `DisclosureRow` avec `icon` et `description` (Bilan, Suivi, Rendez-vous ; la phrase remplace le compte à droite).
- **Enregistrement immédiat (1.6.65)** : pas de bouton « Enregistrer ». Un interrupteur ou un choix s'applique tout de suite ; un champ chiffré s'enregistre quand on le quitte, pas à chaque frappe. « Enregistré » s'affiche à côté du champ et s'annonce aux lecteurs d'écran (message d'état, WCAG 4.1.3). Une valeur impossible : l'erreur sous le champ, reliée à lui (WCAG 3.3.1), et l'ancienne valeur reste enregistrée. Une désactivation qui se rattrape (un site suivi) propose « Annuler » pendant 6 s (§4).
- **Une confirmation dit ce qui est vraiment fait (1.6.69)** : jamais « c'est fait » si une étape reste à l'utilisateur. Exemple : ajouter une recherche ne crée l'alerte sur aucun site ; la confirmation dit « Recherche ajoutée » et « Il te reste à créer l'alerte sur … », avec l'action en bouton principal.
- Pas plus de 3 cartes visibles sans défilement sur téléphone.
- Les listes longues se replient au-delà de 3 éléments (« Tout voir »).

Largeurs (1.6.32) :
- **La page** : un seul conteneur centré, largeur maximale de **1 020 px** (`--page-max`), marges comprises ; **chaque
  bloc prend toute sa largeur**. 1 020 px est un choix de jobA1, compatible avec la largeur large de Polaris (`inlineSize`
  `large`), recommandée pour les tableaux de bord. Pages concernées : **Aujourd'hui, Suivi, Alertes,
  Rendez-vous et Bilan**. Seule exception : **Candidatures › Offres** garde **1 280 px** (`--page-wide`) pour ses
  deux colonnes, la liste et le détail d'une offre ouverte côte à côte (les filtres sont dans la barre d'outils
  depuis la planche « Barre d'outils Offres ») : à 1 020 px, la liste n'aurait que 462 px et le détail 486 px. Sans
  offre ouverte, la ligne d'offre garde son texte à la mesure (Listes, ci-dessous).
- **Pas de colonne étroite avec le côté droit vide.** Une colonne d'appui (l'`aside` de Polaris) ne reçoit que du
  contenu d'appui : **jamais une commande principale, jamais un contenu requis** (Polaris, mise en page).
- **Le texte courant et les phrases de conclusion** : **75 caractères** par ligne au plus, à toutes les tailles
  d'écran (`--measure`, Baymard Institute : 50 à 75 caractères pour le texte courant ; WCAG 2.2, 1.4.8 : 80 au plus).
  Material Design (40 à 60) vient après Baymard dans l'ordre des références (§9) : il ne s'applique pas ici.
  `--measure` vaut 31 em (496 px à 16 px), relatif à la taille du texte. Un `ch` ne suffit pas, il est plus large que la
  lettre moyenne. La mesure limite le texte, pas le bloc : la carte garde toute la largeur de la page.
- **Réglages** (1.6.65, remplace le modèle de Polaris de la 1.6.35) : une seule colonne, la structure des sections
  ci-dessus (une carte par réglage, le contrôle à droite). Le sommaire des rubriques reste à gauche sur ordinateur.
- **Les tableaux tiennent dans leur carte** (« Toutes les candidatures ») : aucun défilement horizontal sur ordinateur ;
  les colonnes se partagent la largeur et le texte passe à la ligne.
- **Jamais de « … »** dans une ligne de liste : le texte passe à la ligne.
- **Les boutons** : **la largeur de leur texte, à toutes les tailles** (Material Design 3 : la largeur d'un bouton suit
  son libellé). Sur téléphone, une cible d'au moins **44 px** de haut (Apple Human Interface Guidelines : 44 points ;
  Nielsen Norman Group : environ 1 cm). Pas de bouton pleine largeur.
- **Les champs** : une largeur selon le contenu prévu (Baymard Institute : la largeur d'un champ annonce la longueur
  attendue ; un écart fait douter de l'étiquette) : **nom 20 caractères** (`--field-20`), **lieu 30 caractères**
  (`--field-30`), **date et heure à leur taille naturelle** ; les nombres courts (objectif, note sur 100, jour du mois)
  à 5 caractères (`--field-5`) ; **la recherche peut rester fluide**.
- **Les listes** : le statut ou l'action reste **près du texte** qu'il concerne ; aucune ligne de liste ne dépasse la
  largeur de la page. La Ligne d'offre arrête son texte à la mesure (`--measure`) : le verdict et l'action suivent le
  poste, jamais au bord d'une carte large (Offres, Tri du jour). Loi de proximité (Gestalt, NN/g).

## 4. Composants (seuls autorisés)

| Composant | Règle |
|---|---|
| **Note d'une offre** | **Le mot en premier plan**, avec l'anneau gradué tous les 25 % de la maquette comme jauge, coloré selon le mot (D3, 2026-11-02). Quatre mots fixes et leurs seuils inchangés : Très proche (85 et +) · Proche (70 à 84) · À creuser (50 à 69) · Loin (moins de 50) ; `scoreWord` ne change pas. **Pas de chiffre au centre de l'anneau** : le chiffre sur 100 reste dans la fiche de l'offre. Le même composant sur téléphone et sur ordinateur (Q3, 2026-11-02). Jamais de visage triste. « À creuser » en gris chaud (`--score-dig`), jamais l'orange (D5). |
| **Couleur orange** | Réservée à ce qui demande d'agir : « À joindre », notifications, relances, rattrapage (D5, 2026-11-02, confirme docs/135 §5). « À creuser » n'est pas orange. La pêche (`--peach`, `--spark`) est une chaleur de marque, jamais un statut. Une couleur ne porte jamais seule une information. |
| **Rouge** | Uniquement les vraies erreurs et les actions destructives (supprimer, écarter). |
| **Progression ORP** | Un **cercle liquide** qui se remplit vers l'objectif du mois, avec **« x sur y » toujours écrit** (D6, 2026-11-02 ; remplace les 10 cases). Le cercle liquide ne sert qu'à l'objectif ORP (et au contour de l'Assistant), jamais à une note. |
| **Semaine** | Points par jour : rempli = candidature, cerclé = aujourd'hui. |
| **Initiales d'entreprise** | Fond accent, menthe ou ciel, jamais l'orange (réservé à ce qui demande d'agir). Contraste ≥ 4,5:1 : `--on-accent` sur l'accent, texte foncé sur la menthe et le ciel. |
| **Offres du jour** | Sur Aujourd'hui, la carte « Tri du jour » (le nombre d'offres, la meilleure en aperçu, « Commencer le tri ») ; le tri terminé : « Tri terminé · À demain », sans bouton plein. Le tri dans son écran (2e niveau, §2) : une offre à la fois en pile de cartes, avec une phrase « pourquoi » d'une ligne ; les manques sont dans la fiche. Garder et Écarter côte à côte, chacun sur la moitié de la carte : une décision binaire, deux grandes cibles (loi de Fitts) ; c'est la seule exception à « pas de bouton pleine largeur » (§3). « Annuler » pendant 6 s ; à la fin, retour à Aujourd'hui. Balayage autorisé sur téléphone, en plus des boutons. |
| **Écran vide** | **La première fois** (« Pas encore de … ») : ce que la page fera, puis une action principale, un bouton plein (§3.3), une éventuelle seconde action en contour. L'illustration attribuée à l'écran (voir Illustrations), sinon le visage du 1. Titre sans point final. **Réussite** (tout est fait) : l'illustration de la réussite, quand ça revient, pas de bouton plein. **Aucun résultat** (des filtres ne laissent rien) : ni illustration ni visage, une ligne grise à la place de la liste et « Effacer les filtres ». **Vide dans une carte** : une ligne grise « Aucun … pour l'instant. » sous la tête de carte, sans « · 0 » ; l'action reste dans la tête. Inspiré des états vides de Polaris et de NN/g (premier usage, aucun résultat). |
| **Chargement** | **Rien avant 300 ms** (NN/g, Response Time Limits), puis des blocs gris à la forme du contenu (`LoadingBlocks`), la tête de carte déjà affichée. **Une seule annonce « Chargement… » par zone** (WCAG 4.1.3). **Un seul système** (ISO 9241-110, cohérence) : le voile du visage seulement au tout premier chargement de l'application ; un changement de page montre les blocs gris, ou rien sous 300 ms. Animations coupées si le système le demande (`prefers-reduced-motion`). |
| **Action en cours** | Le bouton garde sa place et **sa largeur** (`BusyButton`) : le nom de l'action suivi de « … » (« Rédaction… »), **`aria-disabled="true"` et pas `disabled`**, pour que le focus reste dessus (WCAG 2.4.3), et l'état annoncé (WCAG 4.1.3). **Il garde sa couleur et son contraste** : occupé n'est pas désactivé, pas d'opacité réduite. |
| **Téléchargement en préparation** | Le bouton garde **sa largeur et son libellé** (« Word ») : pendant la préparation, **son icône devient un indicateur** ; prêt, une coche 2 s ; en échec, « Réessayer ». L'état et la taille sont annoncés (`aria-live`, « Word téléchargé, 84 Ko. »), jamais écrits à côté du libellé. L'audit téléphone met ces états en préparation (données simulées, la démo n'a pas d'IA) et refuse un bouton qui change de largeur. |
| **Aération** | WCAG 1.4.12 : **interligne 1,5** pour le texte courant (`--leading-normal`) ; **après un paragraphe, deux fois la taille du texte** (`--paragraph-gap`, `p + p` et les paragraphes de la lettre) ; **un écart fixe entre un libellé et sa valeur** (`--label-gap`, 8 px : champs, listes de faits). |
| **Premiers pas** | Une carte, une étape à la fois, « 2 sur 5 ». |
| **Sélection unique (1.6.58, 1.6.69 ; D4 révisée par Kevin le 2026-11-03)** | Trois styles, chacun avec un sens. **Le segment dit où je suis** : dans un contrôle segmenté (vues d'une page, période, type), le segment choisi est une **carte** (`--surface`, bord 1 px `--line`, léger relief, texte `--text` en 700) posée sur un **rail** `--surface-muted` ; les autres segments n'ont aucun fond, texte `--text-tertiary` en 600. Segments de 44 px, rail de 52 px, coins `--radius-card` pour le rail et `calc(var(--radius-card) - var(--space-1))` pour le segment. **La puce teintée dit ce que j'ai filtré ou choisi** : fond `--primary-soft`, bord `--primary-graphic`, texte `--primary-text` ; une puce non choisie a un bord `--field-border` de 1 px (3:1 sur la carte, WCAG 1.4.11, testé en clair et en sombre). Le menu de l'en-tête sur ordinateur garde la pastille teintée. **Le rond plein est réservé à la barre du bas du téléphone** (D4, 2026-11-02) : l'onglet actif est un rond bleu plein posé dans un creux de la barre, libellés toujours visibles, avec une zone vide de 22 px au-dessus (`--nav-spacer`) ; ailleurs, jamais de sélection pleine, pour ne pas imiter le bouton principal (§3). L'état choisi est aussi annoncé aux lecteurs d'écran : `aria-current="page"` pour des liens, `aria-checked` pour des radios, `aria-selected` pour des onglets. Le survol, une couche neutre à 8 % sans accent ; le focus clavier, un contour accent de 2 px. **Soulignement** : seulement pour un second niveau sous un contrôle segmenté (3 px, accent), jamais au premier niveau. NN/g, cohérence. |
| **Boutons segmentés** | Pour filtrer ou changer l'affichage d'une même carte, ou choisir une option : 2 à 5 choix (Material Design 3, boutons segmentés), dans l'ordre naturel (du plus court au plus long : Un mois, 3 mois, Tout). Jamais pour aller vers un autre contenu : on navigue par le menu et les onglets de page (§2 : pas de troisième niveau d'onglets). La sélection suit la **sélection unique** ci-dessus, sans rail (1.6.69 ; remplace le rail de la 1.6.41). Le texte reste sur une ligne, jamais coupé. Hauteur `--control-h`. Du texte seul. Exemples : la période du Bilan, la Note des Offres. |
| **Recherche globale (1.6.69)** | Ordinateur : un champ visible dans l'en-tête, à gauche de la cloche. Téléphone (D11, 2026-11-02) : **pas de loupe dans l'en-tête** ; la recherche est le champ en haut de Candidatures (maquette `Candidatures`), qui garde le comportement ci-dessous. En attendant ce champ (docs/139, étape 5), pas de recherche globale sur téléphone. Elle cherche dans les données de l'utilisateur (offres, candidatures, entreprises) ; résultats groupés par type, 3 au plus par groupe, puis « Tout voir » ; clavier selon le combobox de l'APG du W3C. En bas : « Suivre cette recherche », en un clic, qui ajoute une recherche d'alerte (la recherche se fait une fois, puis la collecte est automatique, §1) ; la confirmation dit ce qu'il reste à faire (§3). |
| **Repliable (1.6.61)** | Une ligne qui se déplie sur place : titre, et en option une icône dans une pastille et une phrase (l'enseignement, visible replié). Chevron vers la droite fermé, vers le bas ouvert, partout. Jamais un repliable dans un repliable (NN/g). |
| **Pastille d'état (1.6.74)** | Un état en quelques mots, **au bout de la ligne** qu'il qualifie (`StatusPill`). Quatre tons : **neutre** (gris), **à faire** (orange : il y a une action), **réussi** (vert), **erreur** (rouge : seulement une vraie erreur). Le point et le mot disent l'état, jamais la couleur seule (WCAG 1.4.1). Sans point : une étiquette (« Spontanée », « En ligne »), toujours neutre. **Un état dans une phrase, sous un titre, reste du texte coloré** (Ligne d'offre) : la pastille seulement en bout de ligne. |
| **Illustrations (docs/141, Kevin, 2026-11-06 ; remplace 1.6.73 et D10 sur ce point)** | Trois figures, **une seule par écran** : le **logo transformé** (`FaceTransform`) dit où l'on est, dans les transitions de page et les en-têtes ; le **personnage** (`Illustration`, kit `personnage/`) marque un moment ou remplit un écran plein (liste fermée dans docs/141 §3 : premiers pas, connexion, page introuvable, maintenance, pas de connexion, aucune offre, candidature envoyée, objectif ORP atteint, première collecte, Rendez-vous vide, entretien décroché, compte supprimé, refus reçu) ; les **petites mascottes d'humeur** (`MoodAnimation`) disent un état dans un petit espace : chargement, erreur dans la page, notifications. **Jamais le personnage sur un écran de travail** (fiche offre, lettre, CV, formulaires). Personnage : 400 px en 1×, 800 px en 2×, `width`/`height` fixés, décoratif (`alt` vide, `aria-hidden`), chargé à l'affichage sauf sur un écran plein, un fondu de 200 ms coupé par « réduire les animations », aucune autre animation ; 200 px au plus dans une liste, 240 à 280 px sur un écran plein, 400 px au plus sur ordinateur. Garde-fou : `frontend/src/personnage.test.ts`. L'ancienne série (`SceneIllustration`) se retire écran par écran (docs/141 §4). |
| **Tête de carte** | « Titre · nombre » à gauche (`CardHead`), **à hauteur fixe** avec ou sans action ; à droite, **soit** le lien « Tout voir », **soit** une action en taille compacte (« + Ajouter ») suivie de « ⋯ ». **« Tout voir » mène toujours à la page** ; ce qui se déplie sur place s'appelle « Afficher plus (4) », puis « Afficher moins », en bas de la carte (`ShowMore`). Inspirée des en-têtes de carte de Polaris. |
| **Copier** | Un bouton avec la seule icône, **juste à côté de la valeur** (adresse, code, jeton) (`CopyButton`). « Copier » en légende au survol et au focus (WCAG 1.4.13) ; après le clic, la coche verte et « Copié » pendant 2 s, annoncés aux lecteurs d'écran (WCAG 4.1.3). Inspiré du bouton de copie de GitHub (Primer). |
| **Menu « ⋯ »** | **Toujours le dernier élément à droite**, sur une ligne comme dans une tête de carte (`MoreMenu`). Nommé « Plus d'actions » (ou « Plus d'actions sur … ») pour les lecteurs d'écran. Chaque entrée a son icône. **Pas de rouge dans le menu** : une action irréversible (Révoquer) ouvre une confirmation sur place, une suppression qui se rattrape propose « Annuler » pendant 6 s. Une seule action : pas de menu, l'action directement. |
| **Champ de formulaire** | `FormField` : **le libellé au-dessus**, en semi-gras, jamais remplacé par l'exemple grisé (WCAG 3.3.2). **« (facultatif) »** en gris après le libellé d'un champ facultatif, **pas d'astérisque** sur les autres (Material 3, champs de texte). Une aide d'une ligne en gris **sous le libellé** (« jj.mm.aaaa »). **L'erreur sous le champ**, avec une icône, en rouge semi-gras, reliée au champ (`aria-describedby`, `aria-invalid`) : elle dit quoi faire (« Indique l'entreprise. ») ; elle apparaît en quittant le champ puis à l'envoi, la valeur tapée reste, elle disparaît dès que c'est corrigé (WCAG 1.4.1, 3.3.1, 3.3.3 ; Material 3 et Polaris). **La largeur dit la réponse attendue** (Baymard Institute, Form Field Width) : `--field-5` (NPA), `--field-10` (date jj.mm.aaaa), `--field-20` (nom), `--field-30` (lieu) ; une adresse ou un texte jusqu'à la mesure. |
| **Champ (apparence)** | Planche « Champs ». Une seule forme pour les champs de texte, listes, dates et zones de texte : fond `--field-bg` (distinct de la carte), bordure `--field-border` (3,7:1 sur le champ, 4,0:1 sur la carte en clair, 4,06:1 en sombre ; WCAG 1.4.11), rayon `--radius-card` (18 px, celui des cartes, D7), **48 px** de haut (`--field-h`), texte 16 px. États : survol `--field-border-hover` ; **focus** bordure 2 px `--accent` + halo `--accent-soft` 3 px, à la souris comme au clavier (WCAG 2.4.7) ; **erreur** 2 px `--down-text` + message sous le champ avec icône ; désactivé (`--panel`, texte `--muted`) ; lecture seule (pointillés). Liste : la même boîte, chevron de notre jeu d'icônes. Zone de texte : 3 lignes au moins, elle s'agrandit avec le contenu. **Le texte d'exemple ne remplace jamais le libellé ni l'aide.** La recherche de l'en-tête suit les mêmes états, en capsule, à la hauteur des contrôles de l'en-tête (`--control-h` : 40 px, 44 sur téléphone). **48 px seulement dans un formulaire.** Dans une barre de filtres ou d'outils, un ajout rapide, une cellule de tableau ou un menu, la variante compacte `field-compact` (Material 3, puce de filtre avec menu) : toute la rangée prend `--control-h` (40 px, 44 sur téléphone), une liste compacte est une capsule. **La place du chevron vient du composant et n'est jamais écrasée** : aucune règle de page ne fixe le padding d'un champ, et le texte d'une liste ne passe jamais sous son chevron. Les zones de texte **s'agrandissent seules** avec leur contenu, **sans poignée** de redimensionnement (`resize: none`, `field-sizing: content`, `useAutoGrow` sans lui). |
| **Case, radio, interrupteur** | Case et radio **dessinées** : 20 px, cochées en `--accent`, non cochées en `--field-border`, rayon 6 px pour la case ; toute la ligne est l'étiquette, 44 px. **Case** : ce qui s'applique à l'envoi, et les listes à cocher (choix multiple, tâches faites) même enregistrées tout de suite, qui disent alors « Enregistré », annoncé (WCAG 4.1.3). **Interrupteur** (`role="switch"`) : un réglage isolé, enregistré tout de suite (Apple HIG, Material 3). Les jours de recherche : puces à cocher sur une ligne, 44 px de haut, la sélection en pastille teintée. **Un consentement n'est jamais coché d'avance** ; sans lui, l'envoi est bloqué et le message est sous la case, qui reçoit le focus (nLPD, WCAG 3.3.1). |
| **Choisir** | 2 à 5 choix courts qui changent l'affichage tout de suite : **boutons segmentés** ; plus de 5 choix : **liste déroulante** ; oui ou non pris en compte à l'envoi : **case à cocher**, dont **toute la ligne est l'étiquette**, 44 px de haut sur téléphone ; oui ou non enregistré tout de suite : **interrupteur** (Réglages, §3). |
| **Formulaire** | Dans une fenêtre ou une feuille : **un seul bouton principal**, nommé par l'action (« Enregistrer la candidature »), **en bas à gauche**, puis « Annuler ». À l'envoi, le focus va au **premier champ en erreur** ; pas de message global à la place des messages sous les champs. |
| **Structure téléphone (sous 820 px)** | **Un seul seuil, 820 px** (D8, 2026-11-02 ; le seuil de 600 px disparaît). En dessous, **la nouvelle identité mobile** (`docs/mobile/`, docs/139) ; on garde les pièces de structure inspirées de l'application CFF (listes groupées, feuille du bas, action fixée en bas, contrôle segmenté, recherche). Les couleurs, rayons et tailles viennent des variables partagées avec l'ordinateur. **Une colonne**, gouttière de 16 px (`--space-4`), espacement entre cartes par variable (`--space-5`), jamais en dur. À ne pas reprendre : onglets sans libellé, plus de 5 onglets, carte du nom en haut de chaque page, paragraphes longs dans les réglages, rouge pour l'action principale. |
| **Liste groupée** | Apple HIG, *inset grouped* : **le titre de section hors de la carte**, une carte par groupe, les lignes séparées par un filet (décalé sous l'icône). Une ligne : icône facultative, libellé, puis à droite un chevron, une valeur ou une commande ; **toute la ligne est cliquable, 48 px de haut au moins**. Réglages et Profil : titre + une phrase grise + commande à droite ; une radio ou une case : **toute la ligne est l'étiquette** (WCAG 2.5.8). |
| **Feuille du bas** | Material 3, *bottom sheets* : pour les filtres d'Offres, le menu « ⋯ » et le choix d'une date. **Titre à gauche, ✕ rond à droite, action principale en bas.** Filtres : « Afficher N offres » (principal) et « Réinitialiser » (Baymard Institute, filtres). Sur téléphone, le panneau de la cloche s'ouvre **en plein écran** avec la même tête. |
| **Panneau de commande (téléphone)** | Structure d'EasyRide, sous 600 px : **on lit en haut, on agit en bas.** Le tiers du haut ne porte **aucune action principale** ; la navigation (retour « ← Aujourd'hui », en-tête, onglets) y reste. Le panneau (`ActionBar`) est fixé au-dessus de la barre d'onglets, coins du haut arrondis, zone de sécurité respectée (`env(safe-area-inset-bottom)`) ; il porte ce qui décide (la note et son pourquoi, une ligne) et les actions, **pleine largeur sur téléphone seulement** (seule exception à « bouton à la largeur du texte », §3). Deux actions de même poids côte à côte, de même largeur (`.action-bar-row`). Pages : Tri, Relances une à une, Préparer (langue, consigne d'une ligne, « Rédiger » ; « Versions · Télécharger » ouvre une feuille du bas), Fiche (note, « Préparer ma candidature », « Postuler chez l'employeur »). Sur ordinateur, rien ne change sauf le Tri. Pas de geste de balayage. |
| **Progression pas à pas** | Pour traiter une liste un élément à la fois (tri, relances) : « 1 sur 5 » en gris, puis une barre d'un segment par élément, ceux vus en --accent (`StepProgress`) ; au-delà de 10, une barre continue. Pas de phrase « 5 offres à trier. » en plus. Le texte est annoncé (`aria-live`), la barre est décorative. |
| **Raccourcis ← →** | Sous deux actions de même largeur : « ← Écarter » à gauche, « → Garder » à droite, en gris (`KeyHints`), avec clavier et souris seulement. Les flèches agissent hors des champs et des fenêtres ouvertes (`useArrowKeys`) ; les boutons portent `aria-keyshortcuts`. Après chaque choix, « Annuler » pendant 6 s (bandeau `UndoToast`). |
| **Choix d'un seuil dans les filtres** | « Note minimale » : des boutons radio dans la feuille de filtres, ligne entière cliquable (`GroupedRow label`, la radio dans `start`), appliqués avec « Afficher N offres ». |
| **Contrôle segmenté pleine largeur** | Pour 2 ou 3 vues d'une même page sur téléphone : les segments se partagent la largeur, le choix actif en carte sur le rail (Sélection unique). Remplace les onglets du Profil : **Critères, Parcours, Coordonnées** (« Coordonnées » et non « Contact », qui se confond avec les contacts du Suivi). **Un libellé n'est jamais coupé** : le test téléphone de la CI le vérifie en 320 px ; s'il l'est, le libellé court prend sa place (« Contact »). |
| **Réglages** | **Téléphone : une liste** (Ma recherche, Être averti, Compte et aide), chaque entrée ouvre sa sous-page, avec « ← Réglages » en haut. **Ordinateur : liste et détail** (Material 3, *list-detail*) : la liste à gauche, la sous-page à droite, sur le même écran, pas de pages séparées. Le réglage le plus utilisé reste **à un toucher** depuis la liste. Dans une sous-page, les lignes suivent la liste groupée (titre, phrase grise, commande à droite). |
| **Carte avec compteur** | Le nombre en pastille (`CountBadge`) à droite du titre de la carte ou du groupe ; une carte vide suit « Écran vide » (vide dans une carte). |
| **Recherche (téléphone)** | Un champ avec **✕ pour effacer** et « Annuler » à côté ; avant la saisie, les **recherches récentes**, chacune avec une horloge ; les résultats, groupés par type, **séparés des récents**. |
| **Barres de défilement** | Partout, fines (`scrollbar-width: thin`) et de **8 px** : pouce `#C9C5BA`, `#A9A397` au survol, piste transparente (maquettes du 7.11.2026, demande de Kevin ; remplace le curseur de 10 px aux couleurs des champs). En sombre, `#4A433B` et `#6A6157` (pas de maquette sombre : à valider). Firefox et Chrome : `scrollbar-width` et `scrollbar-color` ; Safari : `::-webkit-scrollbar`. **Rien ne change en contraste élevé** (`forced-colors`). Écart connu : le pouce clair fait 1,6:1 sur le fond crème, sous le 3:1 de WCAG 1.4.11. **Une zone horizontale qui cache sa barre** (onglets, rubriques) montre un fondu au bord tant qu'il reste du contenu de ce côté ; sans ce fondu, la barre réapparaît. |
| **Visage du 1** | 16 à 32 px dans l'usage courant. Grande taille réservée aux moments rares. Un seul visage animé à l'écran. |

Un composant absent de cette liste ou de Figma ne se crée pas sans validation.

## 4 bis. Échelles (docs/135)

Toute valeur passe par une variable de `frontend/src/style.css`, reprise telle quelle dans Figma.

| Échelle | Variables | Valeurs |
|---|---|---|
| Espacements (base 4 px) | `--space-1` · `-2` · `-3` · `-4` · `-5` · `-6` · `-8` · `-12` | 4 · 8 · 12 · 16 · 20 · 24 · 32 · 48 px |
| Texte | `--font-caption` · `-small` · `-body` · `-title` · `-section` · `-figure` · `--title-tab` · `--font-page` | 12 · 14 · 16 · 18 · 22 · 26 · 30 · 32 px (`--title-tab`, titre d'un écran d'onglet sur téléphone, D7, 2026-11-02 ; le titre d'une sous-page est `--font-section`, 22 px) |
| Rayons | `--radius-sm` · `--radius-card` · `--radius-block` · `--radius-pill` | 8 · 18 · 34 · 999 px (D7, 2026-11-02 : 18 pour les cartes, 34 pour les blocs de rubrique de l'accueil ; remplace `--radius` 12 ; les cercles restent des cercles) |
| Graisses | `--weight-regular` · `--weight-semibold` · `--weight-bold` | 400 · 600 · 700 |
| Interlignes | `--leading-none` · `--leading-tight` · `--leading-normal` | 1 · 1,3 · 1,5 (styles de texte en % dans Figma) |

- Les titres, boutons et liens actifs sont en 600 ; les liens inactifs du menu en 400.
- Le bouton secondaire se voit à son bord : `--faint`, 3:1 au moins. Le bouton principal désactivé est gris, pas bleu pâle.
- Un seul gris pour le texte secondaire, `--muted` (au moins 4,5:1) ; `--faint` est réservé à ce qui n'est pas du texte (chevrons, soulignés en pointillé, encre des dessins, bord des boutons secondaires, jours vides, cases ORP et points des premiers pas à faire), au moins 3:1 (3,3:1 visé en clair).
- Une seule orange pour l'interface, `--orange`, avec `--orange-text` pour le texte et `--orange-soft` pour les fonds ; `--logo-spark` est réservé au logo et au visage du 1.
- Hors échelle : la lettre, le CV et la feuille ORP (ils imitent le papier et le PDF), les valeurs en `em`, les pourcentages, les réserves de place d'un élément fixe, les textes des graphiques en SVG.
- Les filets : 2 rem de chaque côté sur ordinateur. Les logos d'entreprise : coins de 8 px.

## 5. Mots

- Une chose = un mot, partout.
- Vocabulaire ORP : objectif, preuves, conseiller, rendez-vous.
- Termes validés : Gardées · À préparer · Poste obtenu. *(Compléter avec la liste du cadrage 126.)*
- Les preuves du mois **se remettent** : « Remettre les preuves d'octobre » et son bouton « Remettre » (Aujourd'hui),
  « Marquer comme remis » et « Preuves d'octobre remises » (Suivi). « Compléter » ne sert qu'à une ligne à laquelle
  il manque une information ; « atteint » parle de l'objectif du mois, pas des preuves.
- Un mois après « de » s'élide : « d'octobre », « d'août » (`ofMonth`, `frontend/src/format.ts`).
- Interdits pour l'utilisateur : jargon technique (README, réglage d'installation, lecteur intégré, Diagnostic), anglicismes inutiles, mots ambigus (Retenues, Engagement, Commencées, Progresser). « Progresser » reste interdit, sur téléphone aussi (D2, 2026-11-02) : l'onglet s'appelle « Bilan ».
- Ton : tutoiement, phrases courtes, aucun tiret cadratin.

**Dates (1.6.74)** : une seule façon de les écrire (`frontend/src/dates.ts`, heure de Zurich) :
- dans une liste : « 12 oct. » (avec l'année si elle diffère : « 12 oct. 2025 ») ; « aujourd'hui », « hier » pour les deux derniers jours ;
- dans une phrase : « le 12 octobre », « le 1er octobre » ;
- l'heure seulement quand elle compte : « aujourd'hui à 14 h », « reçu à 14 h 05 » ; un rendez-vous : « jeudi 29 octobre à 9 h 30 » ;
- les durées : « depuis 9 jours », « dans 3 jours » ;
- jamais « il y a 3 h » ;
- seule exception : la feuille ORP imprimée garde le format du formulaire officiel (« 12.10.2026 »).

## 6. Mouvement

- Voile de chargement : au moins 1,2 s (docs/63) ; l'animation de la page se lit dans ce temps, jamais de chargement rallongé pour elle.
- Chargement d'une page (D9, 2026-11-02) : **sur téléphone, le feston d'attente seul** (le visage « attente », qui bouge tant que ça charge) ; **sur ordinateur, le visage du 1 transformé, joué une seule fois** (WCAG 2.2.2, PR 460). Jamais d'animation dans les en-têtes ; entre deux pages, le fondu court de D13.
- Micro-animations seulement sur les gestes clés, celles de `docs/mobile/maquettes/Animations.dc.html` (D9) : candidature envoyée (arche, 1,2 s), objectif atteint (soleil « Fête », 1,8 s), nouvelle offre bien notée (1,1 s), refus reçu (triangle gris, 1,6 s), connexion perdue (hochement, 0,6 s), candidature notée (clin d'œil, 0,45 s), aucune offre (loupe), tout est lu (cloche), pop « Joie » (coches, signet). **Jouées une fois** à l'apparition ; seules l'attente et « Rafraîchir » bougent tant que ça charge.
- Quatre vitesses, rien au-delà de 600 ms pour l'interface (règle 10 des maquettes) : `--t-fast` 200 ms (couleur, appui), `--t-standard` 300 ms (feuille, onglet), `--t-joy` 400 ms (réussite, ressort doux), `--t-party` 600 ms (objectif atteint seulement).
- La séparation sous l'en-tête n'apparaît que quand le contenu défile dessous, en fondu bref de 250 ms (Material Design 3, barre du haut) ; sans fondu si l'appareil demande moins d'animations (WCAG 2.2, 2.3.3 ; Apple HIG, Mouvement).
- Appui et arrivée (D13, 2026-11-05) : tout ce qui se touche s'enfonce à 97 % et ses couleurs passent en fondu (`--t-fast`), sans le rectangle bleu du navigateur ; une page, un onglet de page et le contenu qui remplace les blocs gris arrivent en fondu, 6 px plus bas (`--t-standard`).
- Tout mouvement s'arrête si l'appareil demande moins d'animations.

## 7. Accessibilité (WCAG 2.2 niveau AA, obligatoire)

- Contraste texte ≥ 4,5:1 (≥ 3:1 au-delà de 24 px).
- Cibles tactiles ≥ 24 × 24 px (WCAG 2.5.8) ; **44 px de haut sur téléphone** (sous 820 px ou écran tactile), y compris les liens et boutons texte (« Relancer », « Tout voir », « Modifier ») : une zone invisible agrandie autour du texte, sans changer son aspect. Les zones de deux liens voisins ne se chevauchent pas.
- Sur téléphone, le panneau de la cloche (seul panneau de l'en-tête depuis D11) prend toute la largeur moins 16 px de chaque côté, sous l'en-tête ; rien ne sort de l'écran en 320 px.
- Vrais éléments : `<button>`, `<a href>`, `<label>` ; jamais de clic sur une `div`.
- Lien « Aller au contenu » en premier.
- Une seule étape marquée comme courante dans un parcours.
- Le focus passe au contenu ouvert (détail d'une offre).
- Une couleur ne porte jamais seule une information : toujours un mot ou une forme.

## 8. Confiance

- Pied de page sur chaque page : mentions légales, confidentialité (nLPD), À propos.
- Dire clairement ce qui part à l'IA et ce qui n'y part jamais (coordonnées).
- Pas de lien vers le code dans l'interface utilisateur.

## 9. Références

Par ordre d'autorité : en cas de désaccord, la plus haute l'emporte.

1. **Normes** : WCAG 2.2 AA (W3C) ; ISO 9241, parties 110 (principes de dialogue) et 210 (conception centrée sur l'utilisateur).
2. **Recherche** : Nielsen Norman Group ; Baymard Institute.
3. **Systèmes de design** : Material Design 3 (Google) ; Polaris (Shopify) ; Apple Human Interface Guidelines.
4. **Aide-mémoire** : Laws of UX. Jamais seul pour trancher.

On reprend les principes, jamais l'apparence. Une structure de page empruntée à un site (les pages des CFF pour les sections, 1.6.69) se dit « inspirée de la structure de … », jamais « style … ». **Chaque choix d'interface dans une PR cite au moins une de ces références.**

## 10. Méthode de travail pour Claude Code

1. Avant toute interface : lire ce document, puis le composant ou l'écran correspondant dans Figma (via le connecteur).
2. Utiliser uniquement les composants mappés par Code Connect et les variables Figma (couleurs, espacements, rayons, typographie). Aucune valeur en dur.
3. Si l'écran n'existe pas dans Figma : proposer une maquette ou une structure, attendre la validation, puis coder.
4. Après chaque changement : vérifier les sections 3, 4, 5 et 7, et le signaler dans la PR (« Règles vérifiées : … »), avec la référence de la section 9 qui justifie chaque choix d'interface.
5. Une règle à changer se discute et se met à jour **ici d'abord**, jamais directement dans le code.

---

## Annexe : écarts relevés par l'audit, à reprendre dans Figma

| Écart | Règle concernée | État |
|---|---|---|
| Candidatures surchargée (5 sous-onglets) | 2 | Corrigé en 1.0.0, à refléter dans Figma |
| Suivi et Bilan trop chargés | 3 | Corrigé : conclusion en haut, détail replié (repliables alignés sur le Bilan en 1.3) |
| Vocabulaire ambigu | 5 | Partiellement corrigé, liste à finaliser |
| Contraste des initiales | 4, 7 | Corrigé en 0.99.1 |
| Liens trop petits | 7 | Corrigé en 0.99.1 |
| Pastille de notification rouge | 4 | Corrigé : orange |
| Mentions légales, À propos | 8 | Corrigé en 1.0.1, à refléter dans Figma |
| Écrans vides de la démo | 4 | Prévu au cadrage 128 |

---

## Décisions du 2 novembre 2026 : la nouvelle identité mobile (docs/139)

Prises par Kevin le 2026-11-02, point par point, sur le tableau des conflits entre ce document et les maquettes de
`docs/mobile/` (exception datée dans `CLAUDE.md`). Une décision « suivre la règle » garde la règle ; une décision
« suivre la maquette » la remplace.

| # | Décision | Sections |
|---|---|---|
| D1 | Suivre la maquette sur téléphone : 5 onglets. L'ordinateur garde ses 3 entrées. | §2 |
| D2 | Suivre la règle : l'onglet s'appelle « Bilan » partout (sous-onglets ORP, Bilan, Formations) ; « Progresser » reste interdit. L'accueil s'appelle « Accueil » sur téléphone, adresse `/aujourdhui` inchangée. | §2, §5 |
| D3 | (Revue par D12 le 2026-11-05.) Suivre la règle : 4 mots, seuils 85 / 70 / 50, `scoreWord` inchangé. L'anneau gradué sert de jauge, coloré selon le mot, le mot en premier plan, pas de chiffre au centre. Même composant partout. | §4 |
| D4 | Exception pour la barre du bas seulement : rond bleu plein dans le creux. Ailleurs, pastille teintée. **Révisée le 2026-11-03 (Kevin)** : le segment choisi est une carte sur un rail gris (où je suis), la puce teintée sert aux filtres et aux choix (ce que j'ai filtré), bord des puces non choisies en `--field-border` ; soulignement de 3 px seulement au second niveau. | §4 |
| D5 | Suivre la règle : l'orange reste à ce qui demande d'agir ; « À creuser » en gris chaud. `docs/mobile/tokens.css` et la lecture des maquettes sont corrigés en conséquence. | §4 |
| D6 | Suivre la maquette : cercle liquide, avec « x sur y » toujours écrit. | §4 |
| D7 | Échelle nommée : `--radius-sm` 8, `--radius-card` 18, `--radius-block` 34, `--radius-pill` ; `--title-tab` 30 entre dans l'échelle du texte. | §4 bis |
| D8 | Un seul seuil à 820 px, la nouvelle identité en dessous, avec les pièces de structure CFF. | §4 |
| D9 | Téléphone : feston d'attente seul pour le chargement ; ordinateur : visage transformé joué une fois. Les micro-animations d'`Animations.dc.html` s'ajoutent pour les gestes clés. | §6 |
| D10 | Visages d'humeur dans les écrans vides, les erreurs et le chargement ; la série d'illustrations reste pour les premiers pas et les grandes réussites. | §4 (Illustrations) |
| D11 | Suivre strictement la maquette pour l'en-tête du téléphone : sur l'Accueil, le logo et la cloche ; sur une page d'onglet, le logo et le titre à 30 px (`--title-tab`) ; sur une sous-page, le retour et le titre. Ni loupe ni menu du compte : la recherche va dans Candidatures, le compte est l'onglet Compte. | §4 (Recherche globale), §6 |

Questions du plan, même date : ordinateur, seules les couleurs changent (Q2) ; même anneau partout (Q3) ; adresses
gardées, `/notifications` et `/assistant` en plus (Q4) ; Candidatures en À traiter · Envoyées · Rendez-vous sur les
deux tailles, renommage prévu sur ordinateur (Q5) ; fond crème sur ordinateur aussi (Q6) ; apparence gardée dans le
navigateur pour l'instant (Q7).

## Décisions du 5 novembre 2026 : des interactions plus agréables (Kevin)

| N° | Décision | Remplace |
|---|---|---|
| D12 | La note : « Proche » dès 75 (seuils 85 / 75 / 50) et le chiffre toujours au centre de l'anneau, pour qu'on lise d'emblée une note ; le mot reste dessous. | D3 (seuil 70, pas de chiffre) |
| D13 | Le mouvement : appui animé sur tout ce qui se touche, pas de fond bleu au toucher, fondu court à l'ouverture d'une page et à l'arrivée du contenu chargé. Barre du bas : bords du creux arrondis, ombre plus forte sous le rond, le creux glisse vers l'onglet choisi. | §6 « jamais d'animation entre deux pages » |
| D14 | Une ligne de liste qui mène ailleurs a une seule hauteur : jamais de phrase grise sous le titre, l'aperçu va dans une pastille à droite. La phrase reste pour un réglage ou une action qui s'explique. | §4 (listes groupées) |
| D15 | Un trait sur un seul côté (onglet souligné, séparateur) reste droit, sans coin arrondi qui le fait remonter (contrôlé par `regles.py`). Le bouton bleu sous un champ ajoute aussi ce qui y est tapé. | — |
| D16 | Sur téléphone, la liste des Candidatures suit la maquette : pas de phrase « n offres à traiter » au-dessus (le nombre est sur la pastille de « À traiter ») et pas de « Il te manque » sur la carte (il est dans la fiche). Kevin, 2026-11-05. | §3.2 (phrase de conclusion), sur téléphone seulement |

## Décision du 6 novembre 2026 : le personnage (Kevin, docs/141)

| N° | Décision | Remplace |
|---|---|---|
| D17 | Trois figures, une seule par écran : le logo transformé (où l'on est : transitions, en-têtes), le personnage (moments et écrans pleins, liste fermée de docs/141 §3), les petites mascottes d'humeur (chargement, erreur dans la page, notifications). Jamais le personnage sur un écran de travail. Contrôlé par `personnage.test.ts`. | §4 Illustrations (1.6.73), D10 en partie |


## Décisions du 8 novembre 2026 : la maquette ordinateur et les éléments partagés (Kevin, docs/143)

Validées par Kevin le 2026-11-08 (consigne `docs/mobile/PROMPT_CLAUDE_CODE.md`, `docs/mobile/LISEZMOI.md`). La
maquette du 8 novembre fait foi pour le téléphone et pour l'ordinateur (exception datée dans `CLAUDE.md`).

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

D12, D13, D14, D15, D16 et D17 restent valables.

### Décisions du 8 novembre 2026 au soir : le style « blocs » (Kevin, D28 à D34)

Validées par Kevin le 2026-11-08 (`docs/mobile/MODIFICATIONS_8_NOVEMBRE_SOIR.md` §2, version finale). Elles valent
pour les lots 11 à 18 (docs/143) et partout où ce fichier ne dit pas autre chose.

| N° | Décision | Remplace |
|---|---|---|
| D28 | **Un bloc est une section, jamais cliquable en entier.** Une page de lecture est une pile de blocs `--surface`, sans bordure ni ombre, rayon `--radius-card`, sur le fond `--page-blocks`. Écart entre blocs : 8 px (téléphone), 16 px (ordinateur). Marge intérieure : 22 px en haut et en bas, 20 px sur les côtés (téléphone) ; 24 px (ordinateur). Sur-titre 13 px 700 en capitales ; titre 18/24 700 ; phrase d'aide 14/21 `--text-secondary`. | D22 « carte = cliquable » |
| D29 | **Une ligne à flèche est cliquable en entier.** Fond `--row-blocks`, rayon `--radius-sm`, 72 px (56 px sur une ligne), `padding: 14px 12px 14px 16px`, 10 px entre deux lignes. À droite, un cercle à contour de 40 px (36 px dans les réglages sur ordinateur), flèche → `--primary-text`, décoratif. Un seul arrêt de tabulation. | D22, en partie |
| D30 | **Hiérarchie des actions.** Tout ce qui est cliquable est bleu, d'autant plus intense que l'action compte : niveau 1 plein (`--action`, texte `--on-action`), niveau 2 à contour (`--surface`, contour 1,5 px `--primary-graphic`, texte `--primary-text`), niveau 3 cercle (lignes D29), lien texte (`--primary-text`, 15 px, 700). Plus aucun contour gris sur un bouton. L'orange n'est jamais une couleur d'action. | — |
| D31 | **Statut = un mot coloré après le titre** (14 px, 700, 8 px après, couleur de ton). Plus de pastille de statut à droite sur téléphone ; sur ordinateur, dans les listes à traits, le statut reste à droite en texte coloré, suivi du cercle D29. | — |
| D32 | **Champs à recopier** : libellé 13 px au-dessus de la valeur 16 px 700, bouton copier de 44 px (niveau 2) nommé « Copier <libellé> », annonce « Copié ». Case à cocher externe : étiquette grise « ☐ case à cocher dans Job-Room ». Valeur absente : « Non renseigné ». | — |
| D33 | **Mode sombre** : ce qui est devant est plus clair. Fond des écrans en blocs `--bg`, blocs `--surface`, lignes `--surface-muted` ; éléments pleins interactifs en `--action` / `--on-action`. Les logos, points non lus, barres de progression, miniatures, pastilles de compte et bulle de l'utilisateur gardent `--primary`. | — |
| D34 | **Au plus un bouton plein visible par écran**, en plus du bouton central de la barre du bas et du bouton Envoyer du Composer. Un second bouton plein passe au niveau 2. | — |

Jetons ajoutés (§2.6) : `--action`, `--on-action`, `--page-blocks`, `--row-blocks`, dans `docs/mobile/tokens.css` et
`frontend/src/style.css`. Les numéros D33 et D34 suivent l'ordre du §2 (le texte de Kevin nomme D28 à D34 sans
numéroter le mode sombre).
