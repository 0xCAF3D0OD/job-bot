# jobA1 : modifications du 8 novembre au soir (lots 11 à 15)

À exécuter **après** les lots 0 à 10 de `PROMPT_CLAUDE_CODE.md`, ou à la place de toute correction locale faite entre-temps sur les mêmes points.
Validé par Kevin le 2026-11-08. Les maquettes et les captures du zip sont déjà à jour : elles font foi.
Ce document reprend et détaille les §8 à §12 de `PROMPT_CLAUDE_CODE.md`. En cas de doute entre les deux, **ce document gagne**.

---

## 0. Règles (rappel, non négociables)

1. **Ne rien improviser.** Ce qui n'est ni ici, ni dans le LISEZMOI, ni dans une capture, va dans « Questions pour Kevin » de la PR.
2. **Couleurs** : uniquement les jetons (table du §3 de `PROMPT_CLAUDE_CODE.md`). **Rayons** : 8, 18, 34 ou 999 (D7).
3. **Seuil** : téléphone <= 820 px, ordinateur > 820 px (D8). Sauf mention « téléphone aussi », tout ce document concerne l'ordinateur.
4. **Une PR par lot**, dans l'ordre 11, 12, 13, 14, 15. Chaque PR contient :
   - la liste des points cochés un par un ;
   - « Règles vérifiées : … » ;
   - les captures avant et après, en clair et en sombre, à 1440 px (et à 390 px quand le téléphone change) ;
   - une entrée dans `changelog.d/`.
5. Ajoute chaque écart à la maquette dans « Écarts connus » de `docs/143-maquette-8-novembre.md`.
6. Les maquettes ne s'ouvrent pas seules (`support.js` absent). Le rendu se lit dans les PNG. L'état d'une maquette se lit dans son script (objet `s`).

---

## 1. Vue d'ensemble

| Lot | Écran | Ce qui change | Maquette et état | Captures |
|---|---|---|---|---|
| 11.1 | Tous les formulaires | Style unique des champs | RendezVous, CandidaturesOrdinateurB, Connexion | `etats/CandidaturesOrdinateurB--tab-rv-ajouter.png` |
| 11.2 | En-tête ordinateur | Groupe de 16 px, 44 px, cloche sans notification | toutes les pages ordinateur, état `lu` | `etats/CandidaturesOrdinateurB--cloche-sans-nouvelle.png` |
| 11.3 | Assistant | Indicateur « écrit », plus de bulle vide | AssistantOrdinateur `attente`, Assistant `phase: ecrit` | `etats/AssistantOrdinateur--attente.png`, `etats/Assistant--ecrit.png` |
| 11.4 | Mes alertes e-mail | Retour, liste sans cadre, libellés | AlertesOrdinateur, AlertesTel | `AlertesOrdinateur.png`, `AlertesTel.png` |
| 11.5 | Nouveau rendez-vous | Formulaire sans carte autour | CandidaturesOrdinateurB `tab: rv, ajrv: true` | `etats/CandidaturesOrdinateurB--tab-rv-ajouter.png` |
| 12 | Envoyées, détail | Deux colonnes | CandidaturesOrdinateurB `tab: en` | `etats/CandidaturesOrdinateurB--tab-en.png`, `--tab-en-bas.png` |
| 13.1 | À traiter, détail | Deux colonnes, « L'offre en bref » | CandidaturesOrdinateurB `tab: tr` | `CandidaturesOrdinateurB.png`, `etats/CandidaturesOrdinateurB--tab-tr-bas.png` |
| 13.2 | Profil, Premiers pas | Libellé au-dessus de la valeur | ProfilOrdinateur, OnboardingOrdinateur | `ProfilOrdinateur.png` |
| 14 | Rendez-vous, détail | Sans pastille « Noté », 3 sections, colonne « Le rendez-vous » | CandidaturesOrdinateurB `tab: rv` | `etats/CandidaturesOrdinateurB--tab-rv.png`, `--tab-rv-bas.png` |
| 15.1 | Préparer | En-tête, Mise en page, Pour cette offre | PreparerOrdinateur | `PreparerOrdinateur.png`, `etats/PreparerOrdinateur--colonne-bas.png` |
| 15.2 | À traiter | Bouton « J'ai déjà postulé » | CandidaturesOrdinateurB `tab: tr` | `CandidaturesOrdinateurB.png` |

Les chemins de captures partent de `captures/`.

---

## 2. Gabarit commun « deux colonnes » (lots 12, 13, 14)

Défini une fois, réutilisé trois fois. Crée un composant `DetailTwoColumns.vue` (slots `main` et `aside`, prop `asideLabel`) plutôt que de recopier le CSS.

- Au-dessus des colonnes, sur toute la largeur : l'en-tête du détail (logo ou CalendarDate, H2 24 px 800 en `var(--text)`, sous-titre 15 px `var(--text-secondary)`, menu « … »), les étiquettes, puis les boutons d'action s'il y en a.
- Puis un trait `1px solid var(--line-soft)` et la grille :
  - `display: grid; grid-template-columns: minmax(0, 1fr) 240px; column-gap: 48px;`
  - lot 14 seulement : `minmax(0, 560px) 240px` avec `justify-content: space-between`.
- **Colonne principale** : sections empilées, chacune `padding: 32px 0 36px`, séparées par `border-top: 1px solid var(--line-soft)`. La première n'a pas de trait.
- **Colonne d'appui** : `<aside aria-label="…">`, `padding-left: 40px`, `border-left: 1px solid var(--line-soft)`, mêmes paddings de section.
- **Titres de section** : 18 px, 700, line-height 24 px, 16 px dessous. **Sur-titres** (« Premier message », « Trouver quelqu'un », « Ce qui a été convenu ») : 13 px, 700, capitales, `letter-spacing: .06em`, `var(--text-secondary)`.
- **Listes « clé : valeur »** de la colonne d'appui : `<dl>`. Chaque ligne a `padding: 12px 0` et un trait entre les lignes. Le libellé `<dt>` (14 px, `var(--text-secondary)`) est au-dessus de la valeur `<dd>` (16 px, 700, marge 2 px). Une valeur absente s'écrit « Non précisé ».
- **Liens** de la colonne d'appui : `min-height: 44px`, `var(--primary-text)`, 15 px, 600 ou 700. Icône de lien externe (15 px) pour un lien qui sort de jobA1.
- **Ordre du DOM** : toute la colonne principale, puis toute la colonne d'appui (WCAG 1.3.2). Pas d'`order` CSS.
- **Formulaires** : toujours une seule colonne de champs (NN/g, Baymard).
- **Téléphone** : le gabarit ne s'applique pas ; une seule colonne, ordre inchangé.

---

## 3. Lot 11 : corrections

### 11.1 Champs de formulaire (téléphone aussi)

- **Où** : la règle de base des champs dans `frontend/src/style.css` (vers la ligne 563 au commit `271fae29`). Cherche le sélecteur qui vise `input`, `select` et `textarea`.
- **Quoi** :

  | Propriété | Valeur |
  |---|---|
  | `height` (input, select) | 48 px |
  | `border` | `1.5px solid var(--text-secondary)` |
  | `background` | `var(--surface)` |
  | `border-radius` | `var(--radius-sm)` (8 px) |
  | `padding` | `0 14px` (textarea : `12px 14px`) |
  | `font-size` | 16 px (évite le zoom sur iOS) |
  | focus | anneau existant, inchangé |

- S'applique à tous les formulaires, y compris ceux qui ne sont pas dessinés (Coordonnées, Réglages, Pour les formulaires de candidature).
- **Ne touche pas** au Composer (zone de saisie de l'Assistant) ni à la bulle de recherche : ce ne sont pas des champs de formulaire.
- **Écart connu** : « Champs : 12 px dans l'ancienne maquette, 8 px (D7). »
- **Fini quand** : Coordonnées, Lieu ou lien, Mesures décidées et Connexion ont le même champ ; le contraste de la bordure est d'au moins 3:1 en clair et en sombre (WCAG 1.4.11).

### 11.2 En-tête ordinateur

- **Où** : `AppHeader.vue`, `NotificationBell.vue`, `GlobalSearch.vue`, `AccountMenu.vue`.
- **Quoi** :
  - recherche, cloche et avatar dans **un seul conteneur** `display: flex; align-items: center; gap: 16px` ;
  - l'écart de 32 px reste entre logo, menu principal et ce groupe ;
  - les trois éléments font **44 x 44 px** (bulle de recherche fermée, cloche, avatar) ;
  - cloche **sans** notification : rond 44 px, fond `var(--surface)`, bordure `1.5px solid var(--line-strong)`, icône 20 px `var(--text)`, nom accessible « Notifications, aucune nouvelle » ;
  - cloche **avec** notifications : capsule pêche (`var(--peach-soft)`, texte `var(--peach-text)`), hauteur 44 px, `padding: 0 14px`, icône 18 px + compte (« 9+ » au-delà de 9), nom accessible « Notifications, n nouvelles » ;
  - avatar : 44 px, rayon `--radius-pill`.
- **Fini quand** : les deux états de la cloche correspondent aux captures ; rien ne bouge quand on passe de l'un à l'autre, à part la largeur de la capsule.

### 11.3 Assistant qui écrit (téléphone aussi)

- **Où** : `AssistantPanel.vue` et le composant qui affiche un message de l'Assistant.
- **Quoi** :
  - à l'envoi, ajoute le message de l'utilisateur, **mais aucune bulle de réponse** tant qu'aucun texte n'est arrivé ;
  - à la place, une ligne d'attente : le logo de l'Assistant **sans cercle** (28 px), puis une bulle de 46 px de haut (48 px sur téléphone) avec 3 points de 8 px en `var(--text-secondary)`, espacés de 6 px ;
  - la bulle a la même forme que celle d'une réponse (ordinateur : fond `var(--surface-muted)`, rayon 18 18 18 4 ; téléphone : fond `var(--surface)`, bordure `var(--line)`, rayon 20 20 20 6) ;
  - animation `ja-dot` : 1,2 s, `ease-in-out`, infinie, décalages 0, 0,15 et 0,3 s ; opacité .25 vers 1 et `translateY(-3px)` (keyframes dans `maquettes/AssistantOrdinateur.dc.html`) ;
  - `role="status"`, `aria-live="polite"`, texte masqué visuellement « L'Assistant écrit… » ;
  - au premier morceau de texte reçu, la bulle de réponse remplace la ligne d'attente ;
  - **supprime** l'élément « … » placé sous la liste des messages ;
  - `prefers-reduced-motion: reduce` : points fixes, opacité .6 ;
  - la carte d'étapes « Je rédige ta lettre… » (`AiWriting`) reste réservée aux tâches longues (rédaction d'une lettre ou d'un CV).
- **Fini quand** : plus aucune bulle vide à aucun moment ; les points disparaissent dès que le texte commence ; un lecteur d'écran annonce une seule fois « L'Assistant écrit… ».

### 11.4 Mes alertes e-mail (téléphone : point 3 seulement)

- **Où** : `AlertsView.vue`, `AlertsPanel.vue`, `AlertSearchCard.vue`, et le composable ou la garde du routeur qui retient la dernière page de Candidatures.
- **Quoi** :
  1. `/candidatures/alertes` **n'est plus retenue** comme dernière page de Candidatures. Un clic sur « Candidatures » dans le menu ramène à la liste.
  2. Ordinateur : lien « ‹ Candidatures » **au-dessus du H1** (`min-height: 44px`, 15 px, 600, `var(--primary-text)`, chevron 18 px). Il ramène à la liste de Candidatures, avec l'onglet qui était ouvert.
  3. Liste des recherches suivies **sans cadre** : plus de fond, de bordure ni de rayon autour ; un trait `var(--line-soft)` en haut, en bas et entre les lignes ; marge gauche 4 px.
  4. « Créer l'alerte » devient un **libellé** `var(--primary-text)`, 15 px, 700, suivi de « › », cible de 44 px. Plus de bouton à contour par ligne.
  5. « + Ajouter une recherche » reste le seul bouton à contour de la page.
- **Fini quand** : on peut toujours revenir aux offres en un clic, depuis le menu comme depuis le lien.

### 11.5 Nouveau rendez-vous sur ordinateur

- **Où** : `RendezVousDesktop.vue`, `OrpMeetingForm.vue`.
- **Quoi** : « Ajouter » (à côté de « Aucun rendez-vous à venir ») ouvre le formulaire **dans le panneau de détail**, avec l'animation `ja-slide-l`.
  - **Pas de carte autour** : pas de fond, de bordure ni de rayon propres au formulaire.
  - Contenu : titre « Prochain rendez-vous ORP » (26 px, 800), phrase « jobA1 prépare ta feuille la veille et te le rappelle le matin. », DateTimeField (libellés « Date » et « Heure »), « Lieu ou lien (facultatif) », « Ajouter le rendez-vous » (bouton plein, 52 px) et « Annuler » (bouton texte `var(--primary-text)`).
  - `max-width: 560px`.
  - Le bouton « Ajouter » porte `aria-expanded`.
  - Sur téléphone, la carte du formulaire reste.

---

## 4. Lot 12 : Envoyées, détail en deux colonnes

- **Où** : le composant du détail d'une candidature envoyée (Statut, Documents, Contacts, Premier message, Prises de contact). Gabarit du §2.
- **En-tête** : H2 **24 px, 800, `var(--text)`** (aujourd'hui gris clair et fin en production : à corriger), entreprise et lieu, étiquettes, menu « … ».
- **Colonne principale**, dans cet ordre :
  1. **Statut** : liste déroulante de 200 px (« En attente »…), puis « Sans réponse depuis n jours. » en `var(--peach-text)` suivi du lien « Relancer › », puis « Relance à faire · Changer ».
  2. **Premier message** (sur-titre) : « Écrire à » puis « Canal », **l'un sous l'autre**, pleine largeur, 20 px entre les deux, 8 px entre libellé et champ ; puis le bouton à contour « Rédiger un message » (48 px, `--radius-pill`, icône crayon 18 px, 24 px au-dessus).
  3. **Prises de contact** (sur-titre) : « Aucun contact pour l'instant. » (`var(--text-secondary)`), puis le lien « J'ai contacté quelqu'un › ».
- **Colonne d'appui** (`aria-label="Documents et contacts"`) :
  1. **Documents** : « Lettre (Word) » avec l'icône de téléchargement.
  2. **Contacts** : sur-titre « Trouver quelqu'un », puis Recrutement, L'équipe du poste, Anciens de 42 Lausanne, chacun avec l'icône de lien externe. Le libellé est raccourci en « L'équipe du poste », sans l'intitulé entre parenthèses.
- Tous les boutons du détail ont des bords ronds (`--radius-pill`) : plus de bouton rectangulaire à 8 px.
- **Téléphone** : inchangé. Une colonne : Statut, Documents, Contacts, Premier message, Prises de contact.

---

## 5. Lot 13

### 13.1 À traiter, détail en deux colonnes

- **Où** : `OfferDetail.vue` (offre de l'onglet À traiter), `OfferTextNotice.vue`. Gabarit du §2.
- **Au-dessus des colonnes**, dans cet ordre :
  - logo, H2, entreprise et lieu, menu « … » ;
  - étiquettes ;
  - les boutons « Préparer ma candidature » (plein), « Écarter » (contour), « J'ai déjà postulé » (contour, lot 15.2).
- **Colonne principale** :
  1. **La note** : anneau (chiffre au centre, D12), verdict et étiquette « Provisoire » si besoin, explication ; puis les critères en ligne (coche + mot), avec retour à la ligne (`flex-wrap: wrap; gap: 12px 24px`) ; puis, si l'annonce manque, le bandeau en **bloc** : fond `var(--peach-soft)`, bordure `1px solid var(--peach)`, rayon `--radius-card`, `padding: 18px 20px`, le texte au-dessus et les boutons dessous (« Lire l'annonce » tonal et « Coller le texte » à contour, 44 px, 10 px entre eux) ; puis le lien « Le détail de la note › », 16 px au-dessus.
  2. **Le poste** : titre puis le texte de l'annonce (15 px, line-height 23 px, `var(--text-tertiary)`). La largeur de la colonne garde les lignes sous 80 caractères (WCAG 1.4.8).
- **Colonne d'appui** (`aria-label="L'offre en bref"`) : titre « L'offre en bref », `<dl>` avec Lieu, Contrat, Taux d'activité et Reçue (« Hier, par une alerte e-mail »), puis le lien « Voir l'annonce sur le site » avec l'icône de lien externe.
- Les étiquettes « Contrat non précisé » et « Reçue hier » restent en haut, même si l'information est aussi dans « L'offre en bref ».

### 13.2 « Ce que je cherche » (Profil et Premiers pas)

- **Où** : `ProfileView.vue` et la section équivalente des premiers pas sur ordinateur.
- **Quoi** :
  - dans chaque ligne cliquable, le libellé (14 px, `var(--text-secondary)`) est **au-dessus** de la valeur (16 px, 700, `var(--text)`), alignés à gauche, 2 px entre eux ;
  - hauteur de ligne 68 px, chevron à droite ;
  - la valeur n'est plus collée au bord droit (Laws of UX, proximité).
- Bilan : ne change pas (chiffres courts alignés à droite). Téléphone : ne change pas.

---

## 6. Lot 14 : rendez-vous ORP

1. **Pastilles « Noté » et « Pas encore noté » supprimées** (téléphone aussi), dans la liste et dans le détail. Les groupes « À noter » et « Passés » donnent l'information. Garde les titres de groupe comme titres de liste (`<h3>`).
2. **En-tête du détail** : CalendarDate 56 px, H2, « Vendredi 30 octobre, 11 h · EPFL », menu « … ». Aucune ligne vide dessous.
3. **Grille** : gabarit du §2, en `minmax(0, 560px) 240px` avec `justify-content: space-between`.
4. **Colonne principale** : un `<form>` qui contient :
   - le sur-titre « Ce qui a été convenu » ;
   - trois `<fieldset>`, chacun `padding: 28px 0 32px`, trait `var(--line-soft)` au-dessus sauf pour le premier. Dans chacun : un `<legend>` (18 px, 700), une phrase d'aide (14 px, `var(--text-secondary)`, 4 px au-dessus et 16 px dessous), puis le contrôle :

     | Legend | Phrase d'aide | Contrôle |
     |---|---|---|
     | Objectif de recherches | Le nombre de recherches que l'ORP te demande chaque mois. | compteur − n + (boutons 44 px) et « Comme le mois dernier » |
     | Mesures décidées (facultatif) | Un cours, un stage ou un programme proposé par ta conseillère. | champ texte (style 11.1) |
     | Prochain rendez-vous (facultatif) | jobA1 prépare ta feuille la veille et te le rappelle le matin. | DateTimeField, libellés « Date » et « Heure » |

   - « (facultatif) » : 15 px, 400, `var(--text-secondary)`, dans le legend ;
   - en bas, après un trait : « Enregistrer », bouton plein de 52 px.
5. **Colonne d'appui** (`aria-label="Le rendez-vous"`) : titre « Le rendez-vous », `<dl>` avec Date, Heure, Lieu et Objectif jusqu'ici (« 13 recherches par mois »).
6. **Date dans la pilule** : format court « Mar. 10 nov. 2026 » dès que la pilule fait moins de 280 px, `white-space: nowrap`, jamais sur deux lignes. Le format long reste dans le sélecteur et dans « Le rendez-vous ». Utilise `dates.ts`.
7. Le sélecteur de date (`dp = cal`) remplace toujours tout le contenu sous l'en-tête, comme avant.

---

## 7. Lot 15

### 15.1 Préparer sur ordinateur

**Décision** : on garde la disposition de la production (lettre à gauche, colonne d'aide à droite). La maquette `PreparerOrdinateur` a été refaite dans ce sens et remplace l'ancienne (réglages à gauche).

- **Où** : `PreparationView.vue` et ses sous-composants.
- **En-tête** : une seule ligne de 64 px, `align-items: center`, 20 px entre les blocs, dans cet ordre :
  1. « ‹ Retour à l'offre » (44 px, 15 px, 700, `var(--primary-text)`) ;
  2. trait vertical 1 x 32 px `var(--line)` ;
  3. logo de l'entreprise 44 px ;
  4. **H1 = intitulé du poste** (24 px, 800), entreprise et lieu dessous (15 px, `var(--text-secondary)`) ;
  5. **anneau** de 48 px (piste `var(--line)`, arc de la couleur du verdict, trait 4 px), le chiffre au centre (15 px, 800, D12), et à droite le verdict (15 px, 700, couleur du verdict D5 : Proche `var(--success)`, À creuser `var(--score-dig)`, Loin `var(--neutral)`) avec « de ton profil » dessous (13 px) ;
  6. les étapes « 1. Lettre », « 2. CV », « 3. Postuler » (SegmentedControl existant).
  - Le texte « Ma candidature » **disparaît de l'écran**. Il reste dans le `<title>` : « Ma candidature, <poste>, jobA1 ».
- **Grille** : `grid-template-columns: minmax(0, 1fr) 360px; gap: 24px`. La colonne de droite défile seule (`overflow-y: auto`).
- **Colonne de gauche, la lettre** : une carte (`var(--surface)`, bordure `var(--line)`, `--radius-card`) avec :
  - un en-tête de 16 px x 24 px : « Lettre de motivation » (18 px, 700) à gauche, SegmentedControl FR, DE, EN à droite, trait dessous ;
  - l'aperçu de la page sur fond `var(--surface-muted)`, centré, défilant ;
  - la ligne « Consigne : Plus court » **disparaît**.
  - À l'étape CV, même carte avec « CV » et l'aperçu du CV.
- **Colonne de droite**, trois cartes (`padding: 20px 24px`, `--radius-card`, 16 px entre elles), dans cet ordre :
  1. **Mise en page** :
     - « Le modèle s'applique à la lettre et au CV. » ;
     - pastilles Sobre, Moderne, Bandeau, Classique (40 px, `aria-pressed`, sélection en `var(--primary-soft)` avec bordure `var(--primary-graphic)`) ;
     - trait, puis « Tient sur une page A4 · n mots » ;
     - visible aux étapes Lettre **et** CV ;
     - réutilise les modèles existants du téléphone, mêmes noms ; le nom interne « serif » s'affiche « Classique ».
  2. **Pour cette offre** :
     - sous le titre, « n points forts · n à vérifier » ;
     - **plus de verdict** dans cette carte, ni l'ancien onglet « À creuser » souligné ;
     - groupe « Points forts (n) » (titre 14 px, 700), éléments avec une coche 18 px `var(--success)` ;
     - groupe « À vérifier (n) », éléments avec un point d'attention 18 px `var(--peach-text)` ;
     - chaque élément : le sujet en gras (15 px), le détail dessous (14 px, `var(--text-tertiary)`), `padding: 10px 0`, 10 px entre l'icône et le texte ;
     - le sujet est la partie avant les deux-points dans les données actuelles (« Kubernetes : K3s, Helm… » donne « Kubernetes » et « K3s, Helm… ») ;
     - plus de « Afficher moins » : tout est visible, la colonne défile.
  3. **Nouvelle version** : « Repartir de zéro avec l'annonce et ton CV. », bouton à contour « Rédiger la nouvelle version » (48 px, `--radius-pill`, icône crayon), puis le lien « Ce qui part à l'IA › ».
- **Bas de page** : grille `minmax(0, 1fr) 360px`, alignée sur la grille du dessus. À gauche, les suggestions (Plus court, Plus formel, Insister sur <compétence>, En allemand) puis le Composer (« Demander une modification de la lettre ») ; à droite, « J'ai relu la lettre » (bouton plein, 52 px) aligné à droite.
- La pastille « Insister sur <compétence> » vient d'une compétence du profil présente dans l'annonce. Sans cette donnée, n'affiche que les trois autres et signale-le.

### 15.2 « J'ai déjà postulé » (téléphone aussi)

- **Où** : le détail d'une offre de l'onglet À traiter, sur ordinateur (`OfferDetail.vue`) et sur téléphone (écran Offre, à côté de « Ignorer »).
- **Quoi** :
  - bouton à contour « J'ai déjà postulé » (44 px, `--radius-pill`), à droite de « Écarter » ;
  - au clic, réutilise le parcours existant « Marquer comme envoyée » : écran `ApplicationSent`, puis l'offre passe dans Envoyées avec la date du jour, modifiable ;
  - « Préparer ma candidature » reste le seul bouton plein de l'écran.
- **Fini quand** : l'offre quitte À traiter et apparaît dans Envoyées ; l'objectif ORP compte la candidature comme les autres.

---

## 8. Vérification finale (après le lot 15)

1. À 1440 px, en clair et en sombre, compare chaque écran du §1 à sa capture.
2. `grep` dans `frontend/src` :
   - aucun « Pas encore noté » ni « Noté » en pastille ;
   - aucun « Ma candidature » affiché dans Préparer (le `<title>` seul est permis) ;
   - aucun bouton rectangulaire à 8 px dans les détails ;
   - aucun `border-radius: 12px`.
3. Au clavier seul : dans chaque détail en deux colonnes, la tabulation parcourt la colonne principale puis la colonne d'appui.
4. Lecteur d'écran : chaque `<aside>` a son nom ; chaque `<fieldset>` du rendez-vous annonce son `<legend>` ; l'Assistant annonce « L'Assistant écrit… » une seule fois.
5. Entre 821 et 1327 px : les grilles ne débordent pas ; la colonne d'appui garde 240 px (360 px dans Préparer), la colonne principale rétrécit.
6. `prefers-reduced-motion: reduce` : aucune animation (points de l'Assistant fixes).
7. Les tests listés au §0.7 de `PROMPT_CLAUDE_CODE.md` sont verts. Ajoute un test pour `DetailTwoColumns.vue` (ordre du DOM, nom de l'aside) et pour la ligne d'attente de l'Assistant (pas de bulle vide).
