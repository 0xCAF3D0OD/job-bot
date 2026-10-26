# jobA1 : règles d'interface et d'ergonomie

Version 1.1 · 23 octobre 2026 (échelles, docs/135)

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
- Pas plus de 3 cartes visibles sans défilement sur téléphone.
- Les listes longues se replient au-delà de 3 éléments (« Tout voir »).

Largeurs, sur ordinateur (1.6.29) :
- **La page** : contenu centré, largeur maximale de **1 020 px** (`--page-max`), marges comprises (GOV.UK Layout).
  Seule exception : **Candidatures › Offres**, avec ses trois colonnes (filtres, liste, détail), garde **1 280 px**
  (`--page-wide`) : à 1 020 px, la liste et le détail n'auraient chacun que 338 px, la largeur d'un téléphone ; à
  1 280 px, ils ont environ 460 px, assez pour une ligne de détail lisible (une soixantaine de caractères).
- **Le texte courant et les phrases de conclusion** : **75 caractères** par ligne au plus (`--measure`, GOV.UK Layout ;
  WCAG 2.2, 1.4.8, niveau AAA visé : 80 au plus). `--measure` vaut 31 em (496 px à 16 px) : mesuré sur toutes les
  pages, aucune ligne n'y dépasse 75 caractères ; un `ch` ne suffit pas, il est plus large que la lettre moyenne.
- **Une colonne des deux tiers** (1.6.30) : sur **Suivi, Alertes et Rendez-vous**, tout le contenu tient dans une seule
  colonne des deux tiers (`--column-two-thirds`), alignée à gauche avec le titre de la page et les onglets, **même
  largeur de haut en bas** ; le tiers de droite reste vide. GOV.UK Layout : « le contenu principal doit toujours être
  dans une colonne des deux tiers », le tiers de droite étant réservé au contenu secondaire ; l'objectif ORP et les
  preuves sont du contenu principal (§1). Nielsen Norman Group : la page se parcourt par la gauche, le contenu le plus
  informatif y va, et un alignement vertical se lit mieux. Le défaut à éviter : deux largeurs l'une sous l'autre.
  Ordre par importance (§1). Suivi : la conclusion ; le mois (navigation, objectif et progression, « Ajouter », ⋯) ;
  les preuves à compléter ; à relancer ; à déclarer ; le détail. Alertes : la conclusion ; les alertes ; le détail.
  Exception : le calendrier du Suivi, ouvert, prend la largeur de la page (une grille de 7 colonnes). Premiers pas
  (Alertes) garde sa pleine largeur.
- **Jamais de « … »** dans une ligne de liste sur ordinateur : le texte passe à la ligne.
- **Les boutons** : la largeur de leur texte sur ordinateur ; toute la largeur seulement sous le point de rupture du
  téléphone (820 px) (NHS Design System ; loi de Fitts : sur téléphone, une cible pleine largeur ; sur ordinateur, une
  cible proche de ce qu'elle concerne).
- **Les champs** : une largeur selon le contenu prévu (GOV.UK Text input) : **nom 20 caractères** (`--field-20`),
  **lieu 30 caractères** (`--field-30`), **date et heure à leur taille naturelle** ; les nombres courts (objectif, note
  sur 100, jour du mois) à 5 caractères (`--field-5`) ; **la recherche peut rester fluide**.
- **Les listes** : le statut ou l'action reste **près du texte** qu'il concerne (loi de proximité) ; aucune ligne de liste
  ne dépasse la largeur maximale de la page.

## 4. Composants (seuls autorisés)

| Composant | Règle |
|---|---|
| **Note d'une offre** | Visage du 1 + un mot, avec une jauge discrète pour la nuance. Pas de pastille, pas de chiffre sur 100 en premier plan. Quatre mots fixes : Très proche · Proche · À creuser · Loin. Jamais de visage triste. « À creuser » en gris chaud (`--score-dig`), jamais l'orange. |
| **Couleur orange** | Réservée à ce qui demande d'agir : notifications, relances, rattrapage. |
| **Rouge** | Uniquement les vraies erreurs. |
| **Progression ORP** | 10 cases, une par candidature. |
| **Semaine** | Points par jour : rempli = candidature, cerclé = aujourd'hui. |
| **Initiales d'entreprise** | Fond accent, menthe ou ciel, jamais l'orange (réservé à ce qui demande d'agir). Contraste ≥ 4,5:1 : `--on-accent` sur l'accent, texte foncé sur la menthe et le ciel. |
| **Offre du jour** | Une à la fois, avec la phrase « pourquoi » et au plus deux manques. Boutons Garder et Écarter, « Annuler » pendant 6 s. Balayage autorisé sur téléphone, en plus des boutons. |
| **Écran vide** | Dit ce que la page fera et quoi faire maintenant, avec une action : un bouton principal plein (§3.3), une éventuelle seconde action en contour. |
| **Premiers pas** | Une carte, une étape à la fois, « 2 sur 5 ». |
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

| Référence | Usage |
|---|---|
| Nielsen Norman Group (nngroup.com) | Navigation, architecture de l'information, heuristiques |
| W3C WCAG 2.2 AA | Accessibilité, norme en vigueur |
| Design System de la Confédération (github.com/swiss/designsystem) | Repères familiers aux utilisateurs suisses |
| GOV.UK Design System | Parcours en étapes, formulaires, messages d'erreur ; Layout (largeur de page de 1 020 px, colonne des deux tiers, lignes de 75 caractères) ; Text input (champs à la taille du contenu prévu, en caractères) |
| NHS Design System (basé sur GOV.UK) | Boutons pleine largeur sur téléphone seulement |
| W3C WCAG 2.2, 1.4.8 (AAA, visé) | 80 caractères par ligne au plus |
| Laws of UX (lawsofux.com) | Hick, Jakob, Fitts ; proximité (l'action près de ce qu'elle concerne) |

On reprend les principes, jamais l'apparence. Toute proposition cite la règle ou la référence qui la justifie.

## 10. Méthode de travail pour Claude Code

1. Avant toute interface : lire ce document, puis le composant ou l'écran correspondant dans Figma (via le connecteur).
2. Utiliser uniquement les composants mappés par Code Connect et les variables Figma (couleurs, espacements, rayons, typographie). Aucune valeur en dur.
3. Si l'écran n'existe pas dans Figma : proposer une maquette ou une structure, attendre la validation, puis coder.
4. Après chaque changement : vérifier les sections 3, 4, 5 et 7, et le signaler dans la PR (« Règles vérifiées : … »).
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
