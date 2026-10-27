# jobA1 : règles d'interface et d'ergonomie

Version 1.2 · 26 octobre 2026 (références, §9)

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

- **Trois entrées, pas une de plus** : Aujourd'hui · Candidatures · Bilan.
- Téléphone : barre d'onglets en bas. Ordinateur : navigation en haut. Cloche des notifications en haut à droite.
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
  - composants : `SettingCard` et `SettingRow` (Réglages, Alertes), `DisclosureRow` avec `icon` et `description` (Bilan).
- **Enregistrement immédiat (1.6.65)** : pas de bouton « Enregistrer ». Un interrupteur ou un choix s'applique tout de suite ; un champ chiffré s'enregistre quand on le quitte, pas à chaque frappe. « Enregistré » s'affiche à côté du champ et s'annonce aux lecteurs d'écran (message d'état, WCAG 4.1.3). Une valeur impossible : l'erreur sous le champ, reliée à lui (WCAG 3.3.1), et l'ancienne valeur reste enregistrée. Une désactivation qui se rattrape (un site suivi) propose « Annuler » pendant 6 s (§4).
- **Une confirmation dit ce qui est vraiment fait (1.6.69)** : jamais « c'est fait » si une étape reste à l'utilisateur. Exemple : ajouter une recherche ne crée l'alerte sur aucun site ; la confirmation dit « Recherche ajoutée » et « Il te reste à créer l'alerte sur … », avec l'action en bouton principal.
- Pas plus de 3 cartes visibles sans défilement sur téléphone.
- Les listes longues se replient au-delà de 3 éléments (« Tout voir »).

Largeurs (1.6.32) :
- **La page** : un seul conteneur centré, largeur maximale de **1 020 px** (`--page-max`), marges comprises ; **chaque
  bloc prend toute sa largeur**. 1 020 px est un choix de jobA1, compatible avec la largeur large de Polaris (`inlineSize`
  `large`), recommandée pour les tableaux de bord. Pages concernées : **Aujourd'hui, Suivi, Alertes,
  Rendez-vous et Bilan**. Seule exception : **Candidatures › Offres**, avec ses trois colonnes (filtres, liste,
  détail), garde **1 280 px** (`--page-wide`) : à 1 020 px, la liste et le détail n'auraient chacun que 338 px.
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
  largeur de la page.

## 4. Composants (seuls autorisés)

| Composant | Règle |
|---|---|
| **Note d'une offre** | Visage du 1 + un mot, avec une jauge discrète pour la nuance. Pas de pastille, pas de chiffre sur 100 en premier plan. Quatre mots fixes : Très proche · Proche · À creuser · Loin. Jamais de visage triste. « À creuser » en gris chaud (`--score-dig`), jamais l'orange. |
| **Couleur orange** | Réservée à ce qui demande d'agir : notifications, relances, rattrapage. |
| **Rouge** | Uniquement les vraies erreurs. |
| **Progression ORP** | 10 cases, une par candidature. |
| **Semaine** | Points par jour : rempli = candidature, cerclé = aujourd'hui. |
| **Initiales d'entreprise** | Fond accent, menthe ou ciel, jamais l'orange (réservé à ce qui demande d'agir). Contraste ≥ 4,5:1 : `--on-accent` sur l'accent, texte foncé sur la menthe et le ciel. |
| **Offres du jour** | Sur Aujourd'hui, la carte « Tri du jour. » (le nombre d'offres, la meilleure en aperçu, « Commencer le tri ») ; le tri terminé : « Tri terminé · À demain », sans bouton plein. Le tri dans son écran (2e niveau, §2) : une offre à la fois en pile de cartes, avec une phrase « pourquoi » d'une ligne ; les manques sont dans la fiche. Garder et Écarter côte à côte, chacun sur la moitié de la carte : une décision binaire, deux grandes cibles (loi de Fitts) ; c'est la seule exception à « pas de bouton pleine largeur » (§3). « Annuler » pendant 6 s ; à la fin, retour à Aujourd'hui. Balayage autorisé sur téléphone, en plus des boutons. |
| **Écran vide** | Dit ce que la page fera et quoi faire maintenant, avec une action : un bouton principal plein (§3.3), une éventuelle seconde action en contour. |
| **Premiers pas** | Une carte, une étape à la fois, « 2 sur 5 ». |
| **Sélection unique (1.6.58, 1.6.69)** | Un seul style de sélection partout : le menu de l'en-tête, la barre du bas sur téléphone, les sous-onglets et les sélecteurs. Le choix actif porte une **pastille teintée** (fond `--accent-soft`, texte accent en 600, coins entièrement arrondis) ; les autres n'ont **aucun fond** ; le survol, une couche neutre à 8 % sans accent ; le focus clavier, un contour accent de 2 px. Pas de soulignement, pas de rail gris, et jamais de pastille pleine, pour ne pas imiter le bouton principal (§3). Sur la barre du bas, la pastille de 64 × 32 se place derrière l'icône (Material 3, indicateur actif). NN/g, cohérence. |
| **Boutons segmentés** | Pour filtrer ou changer l'affichage d'une même carte, ou choisir une option : 2 à 5 choix (Material Design 3, boutons segmentés), dans l'ordre naturel (du plus court au plus long : Un mois, 3 mois, Tout). Jamais pour aller vers un autre contenu : on navigue par le menu et les onglets de page (§2 : pas de troisième niveau d'onglets). La sélection suit la **sélection unique** ci-dessus, sans rail (1.6.69 ; remplace le rail de la 1.6.41). Le texte reste sur une ligne, jamais coupé. Hauteur `--control-h`. Du texte seul. Exemples : la période du Bilan, la Note des Offres. |
| **Recherche globale (1.6.69)** | Ordinateur : un champ visible dans l'en-tête, à gauche de la cloche. Téléphone : la loupe seule, nommée « Rechercher » (légende au survol et au focus, WCAG 1.4.13), qui ouvre la recherche en plein écran. Elle cherche dans les données de l'utilisateur (offres, candidatures, entreprises) ; résultats groupés par type, 3 au plus par groupe, puis « Tout voir » ; clavier selon le combobox de l'APG du W3C. En bas : « Suivre cette recherche », en un clic, qui ajoute une recherche d'alerte (la recherche se fait une fois, puis la collecte est automatique, §1) ; la confirmation dit ce qu'il reste à faire (§3). |
| **Repliable (1.6.61)** | Une ligne qui se déplie sur place : titre, et en option une icône dans une pastille et une phrase (l'enseignement, visible replié). Chevron vers la droite fermé, vers le bas ouvert, partout. Jamais un repliable dans un repliable (NN/g). |
| **Visage du 1** | 16 à 32 px dans l'usage courant. Grande taille réservée aux moments rares. Un seul visage animé à l'écran. |

Un composant absent de cette liste ou de Figma ne se crée pas sans validation.

## 4 bis. Échelles (docs/135)

Toute valeur passe par une variable de `frontend/src/style.css`, reprise telle quelle dans Figma.

| Échelle | Variables | Valeurs |
|---|---|---|
| Espacements (base 4 px) | `--space-1` · `-2` · `-3` · `-4` · `-5` · `-6` · `-8` · `-12` | 4 · 8 · 12 · 16 · 20 · 24 · 32 · 48 px |
| Texte | `--font-caption` · `-small` · `-body` · `-title` · `-section` · `-figure` · `-page` | 12 · 14 · 16 · 18 · 22 · 26 · 32 px |
| Rayons | `--radius-sm` · `--radius` · `--radius-pill` | 8 · 12 · 999 px (les cercles restent des cercles) |
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
- Interdits pour l'utilisateur : jargon technique (README, réglage d'installation, lecteur intégré, Diagnostic), anglicismes inutiles, mots ambigus (Retenues, Engagement, Commencées, Progresser).
- Ton : tutoiement, phrases courtes, aucun tiret cadratin.

## 6. Mouvement

- Voile de chargement : au moins 1,2 s (docs/63) ; l'animation de la page se lit dans ce temps, jamais de chargement rallongé pour elle.
- Une animation par page, propre à la page (visage du 1 transformé).
- Micro-animations seulement sur les gestes clés : candidature envoyée, réponse reçue, objectif atteint.
- La séparation sous l'en-tête n'apparaît que quand le contenu défile dessous, en fondu bref de 250 ms (Material Design 3, barre du haut) ; sans fondu si l'appareil demande moins d'animations (WCAG 2.2, 2.3.3 ; Apple HIG, Mouvement).
- Tout mouvement s'arrête si l'appareil demande moins d'animations.

## 7. Accessibilité (WCAG 2.2 niveau AA, obligatoire)

- Contraste texte ≥ 4,5:1 (≥ 3:1 au-delà de 24 px).
- Cibles tactiles ≥ 24 × 24 px (viser 44 px sur téléphone).
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
| Suivi et Bilan trop chargés | 3 | À faire : conclusion en haut, détail replié |
| Vocabulaire ambigu | 5 | Partiellement corrigé, liste à finaliser |
| Contraste des initiales | 4, 7 | Corrigé en 0.99.1 |
| Liens trop petits | 7 | Corrigé en 0.99.1 |
| Pastille de notification rouge | 4 | À passer en orange |
| Mentions légales, À propos | 8 | Corrigé en 1.0.1, à refléter dans Figma |
| Écrans vides de la démo | 4 | Prévu au cadrage 128 |
