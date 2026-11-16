# jobA1, PR 45 à 53 : tri des offres et nouveau visuel (11 novembre 2026, soir)

Ce document complète les prompts précédents (PR 21 à 44). Il ne les remplace pas.

Maquettes dans `maquettes/`, captures dans `captures/` (suffixe `--état` pour un état), images dans `illustrations/tri/`. Les images intégrées dans les maquettes ne servent qu'à l'aperçu : pour le code, prends les fichiers de `illustrations/`.

## 0. Avant de coder

**Ordre.** L'étape 1 passe d'abord et ne change pas : installation du paquet, lien unique et retrait de « Voir le détail de la note », PR 30 élargie, PR 37, PR 38, Entrée et Ctrl+Entrée dans l'Entraînement. Ce lot vient après.

**Pars de l'existant.** Tous les écrans de ce lot réutilisent des composants déjà en place : cercle de note en 4 segments, étiquettes, en-tête, barre du bas, panneau de la PR 37 (volet de droite sur ordinateur, feuille du bas sur téléphone). Ne recrée aucun composant qui existe. Si un composant de la maquette diffère de celui du code, garde celui du code et signale l'écart dans la PR.

**Réponds à ces quatre questions avant la première PR :**
1. Une offre « gardée » existe-t-elle déjà comme état dans les données ? Si non, propose le champ (PR 46).
2. L'objectif mensuel ORP est-il stocké par utilisateur ? Où se lit-il aujourd'hui (constante, configuration, base) ? (PR 50)
3. La note, les points forts et les points à vérifier sont-ils disponibles dans la liste des offres, ou seulement sur le détail ? (PR 45)
4. L'extrait d'annonce est-il disponible avec la position des passages retrouvés, ou seulement en texte brut ? (PR 45, 47)

## 1. Règles communes

- **Mots.** Les deux actions du tri : « Écarter » et « Garder ». Jamais « Pas pour moi » ni « Je garde ». Libellés de note : ceux du code (« Proche », « À creuser »).
- **Texte réel.** Aucun texte dans une image (WCAG 1.4.5).
- **Surlignage.** Fond `#FFE9A8` en clair, `#5C4A14` en sombre, rayon 4 px, marge intérieure 0 4 px, couleur du texte héritée. Toujours accompagné d'une ligne de légende en texte (WCAG 1.4.1). Sur la feuille blanche d'une lettre, garde `#FFE9A8` même en sombre.
- **Marque-page.** Un seul dessin SVG, réutilisé partout : corps `#F2853A`, repli `#C4582A` en haut à gauche, étoile blanche, bas en V. Proportion largeur 1, hauteur 1,82. Ombre `0 4px 5px rgba(27,31,42,.22)`.
- **Écriture manuscrite.** Police « Caveat Brush », graisse 400, déjà utilisée dans « C’est fait ! ». Jamais pour un texte de plus de 5 mots.
- **Cibles.** 44 px au minimum (WCAG 2.5.8).
- **Mouvement.** 250 ms au plus. Avec `prefers-reduced-motion: reduce`, remplace par un fondu de 120 ms (WCAG 2.3.3).
- **Barre du bas.** L'onglet s'appelle « Bilan ». La maquette est corrigée. Rien à faire si le code dit déjà « Bilan ». Le titre de la page reste « Progresser ».
- **Typographie.** Apostrophe ’, espace fine insécable avant : ; ? !, aucun tiret cadratin.
- **Nombres.** Aucun nombre de la maquette n'est à coder en dur (objectif, compteurs, dates). Voir §3.

## PR 45 · Trier les offres

Maquettes : `TrierOffresV2`, `TrierOffresV2Sombre` (états `carte`, `garde`, `longue`), `TrierOffresOrdinateurV2`, `TrierOffresOrdinateurV2Sombre` (états `livre`, `garde`, `longue`), `FinDuTri`, `FinDuTriOrdinateur` (+ `Sombre`).

**Principe.** Les nouvelles offres se trient une par une, triées par note décroissante. Route propre (par exemple `/candidatures/trier`), accessible depuis Accueil et Aujourd'hui (PR 49).

### Téléphone : une carte par offre

- **En-tête de page**, 56 px : flèche retour, titre « Trier les offres » (20 px, graisse 800).
- **Accroche** manuscrite « {n} offres pour toi » : 28 px, `#1A3496`, rotation -2°, marge 4 px 24 px 0.
- **Carte**, marges latérales 22 px, 40 px sous l'accroche :
  - Fond blanc, bordure 3 px `#2445C2`, rayon 22 px, marge intérieure 16 px 16 px 14 px, ombre `0 12px 24px rgba(36,69,194,.18)`.
  - **Pile** derrière la carte, seulement s'il reste des offres : deux bandes de 40 px de haut. La première dépasse de 7 px en haut, en retrait de 10 px de chaque côté, `#9FB0F2`. La seconde dépasse de 14 px, en retrait de 22 px, `#C9D3FA`. Une seule bande s'il reste une offre, aucune sur la dernière.
  - **Marque-page** : 38 px de large, à 18 px du bord droit, dépasse de 14 px au-dessus de la carte.
  - **Ligne 1** : logo 44 px, puis titre (18 px, interligne 23 px, gras, 3 lignes au plus) et entreprise · lieu (14 px, interligne 20 px, `#596070`, 2 lignes au plus). Réserve 50 px à droite pour le marque-page.
  - **Note**, 12 px dessous : cercle existant en 4 segments, 48 px, et son libellé à droite (15 px, gras), écart 10 px.
  - **Étiquettes**, 10 px dessous : hauteur 28 px, marge intérieure 0 10 px, rayon 14 px, fond `#F1EEE7`, texte 13 px graisse 600 `#3D4250`, écart 6 px. Ordre : contrat, taux, trajet.
  - **Extrait**, 12 px dessous : bloc `#FFF8E1`, rayon 14 px, marge intérieure 12 px 14 px. Texte 15 px, interligne 25 px, `#3D4250`, 4 lignes au plus, entre guillemets « ».
  - **Points**, 12 px dessous, écart 9 px : 3 au plus. D'abord les points retrouvés (pastille verte à coche), puis au plus un point à vérifier (pastille brune à point d'interrogation). Texte 15 px.
- **Pied**, collé en bas : trait `#ECE9E1` au-dessus, marge intérieure 14 px 20 px 28 px.
  - Compteur : un trait de 24 × 8 px `#2445C2` pour l'offre courante, des points de 8 × 8 px `#DAD6CC` pour les autres, écart 8 px, puis « {i} sur {n} » (13 px, `#596070`). Affiché une seule fois sur l'écran.
  - Deux boutons, 14 px dessous, écart 12 px, hauteur 52 px, rayon 26 px, 16 px gras : « Écarter » (fond blanc, bordure 1,5 px `#C9C5BA`, icône croix 20 px) et « Garder » (fond `#2445C2`, texte blanc, icône marque-page 20 px).
- La carte grandit avec son contenu. Elle ne défile jamais à l'intérieur. Si l'écran est trop court, c'est la page qui défile et le pied reste collé.

### Ordinateur : un livre ouvert

- **Titre** manuscrit « {n} offres pour toi » (44 px, `#1A3496`, rotation -2°), centré. Dessous : « Tourne les pages : garde celles qui te parlent. » (17 px, `#3D4250`).
- **Livre**, 48 px dessous, centré, largeur 616 px :
  - Couverture : fond `#2445C2`, rayon 18 px, marge intérieure 6 px 8 px 14 px, ombre `0 14px 28px rgba(36,69,194,.22)`.
  - Deux pages blanches de 300 × 430 px, rayon extérieur 12 px, liseré de 3 px `#DCE2F8` autour du bloc. Ombre de pliure sur le bord intérieur de chaque page : `inset 18px 0 16px -12px rgba(27,31,42,.18)`.
  - **Page de gauche**, marge intérieure 24 px : logo 48 px, titre (20 px, interligne 26 px, 3 lignes au plus), entreprise · lieu (16 px, interligne 22 px, `#596070`, 2 lignes au plus), note 14 px dessous, étiquettes 12 px dessous.
  - **Page de droite**, marge intérieure 84 px 24 px 16 px 28 px (le haut laisse la place au marque-page) : extrait (16 px, interligne 26 px, 5 lignes au plus), légende (pastille jaune 22 × 11 px et « {k} points retrouvés », 13 px), trait pointillé `#DAD6CC`, puis les points (écart 8 px).
  - **Marque-page** : 50 px de large, centré sur la pliure, dépasse de 14 px. Trois petits traits bleus `#2445C2` au-dessus.
  - **Personnages**, par-dessus le livre : `orange-tient-le-livre.png` à gauche (hauteur 265 px, son bord droit aligné sur le bord gauche du livre, main sur la couverture), `sourire-tient-le-livre.png` à droite (hauteur 185 px, même principe). `alt=""`, décoratifs.
- **Boutons**, 32 px sous le livre, largeur totale 440 px, hauteur 56 px. Mêmes libellés et styles que sur téléphone.
- **Compteur**, 20 px sous les boutons.
- Le livre a une taille fixe. Il ne grandit pas et ne défile pas.

### Contenu long (état `longue`)

- Titre coupé à 3 lignes, entreprise · lieu à 2 lignes, avec points de suspension.
- **Extrait construit, pas tronqué** : seulement les fragments autour des passages retrouvés, reliés par « (…) ». Jamais un passage surligné coupé en fin de bloc : si le dernier fragment ne tient pas, retire-le en entier.
- Sous l'extrait : lien « Lire toute l’annonce » (15 px, gras, `#1A3496`, souligné, hauteur 44 px), qui ouvre le détail de l'offre (PR 47).
- Le contrat et le taux sont toujours en étiquettes, pour rester lisibles quand le titre est coupé.

### Après « Garder » ou « Écarter » (état `garde`)

- Téléphone : la carte part vers la droite (translation 300 px, rotation 9°, opacité vers 0) en 250 ms, la suivante est déjà dessous. Ordinateur : la page de droite tourne en 250 ms.
- Message en bas, 6 secondes, avec un trait de 3 px `#7D95FF` en bas du message qui se vide de gauche à droite pendant ces 6 secondes (masqué si `prefers-reduced-motion`) : fond `#1B1F2A`, rayon 14 px, hauteur 48 px (52 px sur ordinateur), texte blanc 15 px « Offre gardée dans tes candidatures » ou « Offre écartée », bouton « Annuler » (`#C9D3FA`, gras, cible 44 px). `role="status"`.
- « Annuler » remet l'offre à l'écran et annule le changement en base.
- Le focus passe au titre de l'offre suivante.

### Fin du tri

- Sur le modèle de « C’est fait ! » et « Candidature envoyée » (même mise en page, mêmes boutons).
- Illustration `fin-du-tri.webp` : largeur 290 px sur téléphone, 440 px sur ordinateur. `alt=""`.
- Titre : « C’est » en gras et « trié ! » en manuscrit (`#2445C2`, taille 1,45 em). 34 px, interligne 42 px.
- Phrase : « {g} offres gardées, {e} écartée. » avec les accords. Sur ordinateur, ajoute : « Tu peux préparer les lettres et CV maintenant, ou plus tard depuis Candidatures. »
- Carte des offres gardées : bordure 1 px `#E5E2D9`, rayon 18 px. Une ligne par offre, 68 px au moins : logo 44 px, titre (16 px, gras), entreprise · lieu (14 px, `#596070`), lien « Préparer » (15 px, gras, `#1A3496`, cible 44 px).
- Téléphone : bouton plein « Préparer la première candidature », puis lien « Retour à l’accueil ». Ordinateur : « Retour à l’accueil » (secondaire) et « Préparer la première » (plein).
- Si aucune offre n'est gardée (maquettes `FinDuTriAucune`, `FinDuTriAucuneOrdinateur`, + `Sombre`) : pas de carte, phrase « Aucune offre gardée cette fois. Les prochaines offres arrivent demain matin. », un seul bouton plein « Retour à l’accueil ».
- En sombre, l'illustration a un contour clair : `filter: drop-shadow(0 0 1px #F3EEE6) drop-shadow(0 0 1px #F3EEE6)`. Même règle pour les personnages du livre.

### Accessibilité

- La carte ou le livre est une région nommée « Offre {i} sur {n} ». Ordre de lecture : titre, entreprise, lieu, note, étiquettes, extrait, points.
- Les deux boutons sont de vrais `<button>`. Raccourcis sur ordinateur : flèche gauche pour « Écarter », flèche droite pour « Garder », déclarés avec `aria-keyshortcuts`. Ils sont affichés sous le compteur, 12 px dessous : deux touches dessinées (24 × 24 px, bordure 1 px `#C9C5BA`, rayon 6 px, fond blanc) suivies de leur libellé, 13 px `#596070`. Pas d'affichage sur téléphone.
- Pas de geste obligatoire : le glissement de la carte sur téléphone est un plus, jamais le seul moyen (WCAG 2.5.1).

## PR 46 · Candidatures : offre gardée et étiquettes

Maquettes : `Candidatures`, `CandidaturesSombre`, `CandidaturesOrdinateurB`, `CandidaturesOrdinateurBSombre`, `CandidaturesOrdinateurAjouter`, `CandidaturesOrdinateurSpontanee`, `CandidaturesOrdinateurStatut`.

- **Fonctionnement.** Une offre gardée pendant le tri apparaît dans Candidatures, dans le groupe du jour (téléphone) ou « En préparation » (ordinateur), et quitte la file à trier. Une offre écartée suit le comportement actuel de « Écarter ».
- **Étiquette « Gardée ».** Toujours la première de la rangée. Fond `#FFF1E6`, texte `#8A4A12` (sombre : `#3A2A1C` et `#F2B98E`), 12 px, graisse 700, petit marque-page orange de 9 × 12 px avant le mot, écart 4 px. Même hauteur et même rayon que les autres étiquettes.
- **Étiquettes sous le logo.** La rangée passe sous la ligne logo, titre, note, sur toute la largeur de la carte. La carte devient `flex-wrap: wrap`, `align-items: center`, écart 8 px entre les deux lignes et 14 px entre les colonnes. Le logo et le bloc titre se centrent verticalement sur le cercle de note.
- **Une seule ligne.** `flex-wrap: nowrap`, pas de retour à la ligne, pas de fondu, pas de défilement horizontal. Si la rangée déborde, retire les dernières étiquettes et affiche une pastille « +{k} » (même style, graisse 700) avec le nombre réel. « Gardée » n'est jamais retirée.
- **Ordinateur.** Marge intérieure de la carte 14 px 18,5 px, hauteur minimale 104 px (au lieu d'une hauteur fixe). Retire le masque en dégradé et le `overflow-x: auto` de la rangée.
- **Texte retiré.** Le bouton devient « Afficher 20 offres de plus », sans « · 367 en tout ».

**Contrôles**
- La pastille « +{k} » a le nom accessible « {k} autres étiquettes ».
- Test : une carte avec 6 étiquettes à 390 px affiche « Gardée », les étiquettes qui tiennent, puis « +{k} », sur une seule ligne.

## PR 47 · Détail d'une offre : passages surlignés

Maquettes : `Offre`, `OffreSombre`.

- Dans le texte « Le poste », surligne les passages qui correspondent au profil (règle de surlignage du §1).
- Sous le texte, 12 px dessous : pastille jaune 24 × 12 px, rayon 4 px, puis « {k} passages qui correspondent à ton profil » (13 px). Singulier si k = 1.
- Aucun passage retrouvé : ni surlignage ni légende.
- Le lien « Voir l’annonce complète » ne change pas.
- Les mêmes passages sont surlignés dans le tri et sur le détail : une seule source de données.

## PR 48 · ORP en barre partout

Maquettes : `Orp`, `OrpSombre`, `AccueilV2`, `AujourdhuiOrdinateurV2`, `MaCandidatureV2` (état `fin`), `CandidatureEnvoyeeOrdinateur`, `OrpRemisV2`, `OrpRemisV2Sombre`, `BilanOrdinateur`, `BilanOrdinateurSombre`.

- **Un seul composant** « barre ORP », utilisé partout :
  - Ligne 1 : « Mois ORP · {mois} » à gauche, « {fait} sur {objectif} » à droite, 16 px gras.
  - Barre, 12 px dessous : hauteur 10 px (12 px sur le Suivi ORP), rayon de la moitié, remplie en `#2445C2` (sombre `#7D95FF`). Fond de barre blanc sur une bande bleue `#E8ECFB`, ou `#E8ECFB` sur une carte blanche.
  - Ligne 3, 12 px dessous : « Encore {reste} d’ici le {date} » (14 px, `#3D4250`). Sur Accueil et Aujourd'hui, ajoute « · dans les temps » ou « · en retard » selon le calcul existant.
  - `role="progressbar"`, `aria-valuenow`, `aria-valuemin="0"`, `aria-valuemax`, `aria-label="Recherches du mois"`.
- **Retire** le cercle à vague du Suivi ORP, les pastilles, et les cercles par jour de la semaine.
- **Accueil et Aujourd'hui** : sous la barre, un trait `#CBD3F3`, puis « Cette semaine » à gauche et « {x} sur {y} » à droite (15 px).
- **États** (maquettes `BarreOrpEtats`, `BarreOrpEtatsSombre`) : en cours ; objectif atteint (barre pleine, verte `#17734A`, sombre `#62D497`, ligne 3 « Objectif atteint ») ; objectif dépassé (« 11 sur 10 », barre pleine verte, « Objectif atteint, 1 de plus ») ; en retard (« · en retard » en fin de ligne 3).
- **Octobre remis.** La carte « Octobre remis à l’ORP » devient : fond `#EAF4EE` (sombre `#1C3527`), rayon 20 px, marge intérieure 20 px 24 px, titre manuscrit « {mois} est remis ! » (32 px, `#17734A`, rotation -2°), ligne « Le {date} · {n} recherches » (15 px), bouton texte « Annuler » (cible 44 px), personnage à droite (112 px de haut sur ordinateur, 104 px sur téléphone). Le titre reste un `<h2>`.

## PR 49 · Accueil et Aujourd'hui

Maquettes : `AccueilV2`, `AccueilV2Sombre`, `AujourdhuiOrdinateurV2`, `AujourdhuiOrdinateurV2Sombre`, états `accueil` et `vide`.

- **Accroche.** Manuscrite, sur deux lignes. Si un justificatif est en retard, il passe en premier : « 1 justificatif en retard, » en brun `#8A4A12`, puis « puis 2 candidatures » en `#1A3496`. Dessous : « Commence par l’ORP : 2 minutes. Ensuite, ton rythme du jour. » Sans retard, garde l'accroche actuelle.
- **Tâches numérotées.** Pastille ronde avec le numéro. La tâche en retard est numéro 1 : pastille `#8A4A12` à chiffre blanc, sous-titre en `#8A4A12`. Les autres : pastille `#ECE9E1` à chiffre `#1B1F2A`.
- **Ordinateur.** Deux colonnes. À gauche : accroche, « À faire » (une carte blanche par tâche, hauteur minimale 88 px, rayon 20 px, bouton texte et flèche ronde 44 px à droite), « Quand tu as le temps ». À droite : bande ORP (PR 48), puis « {n} offres à trier ».
- **Entrée vers le tri.**
  - Téléphone : bande « {n} offres à trier », sous-titre « La meilleure d’abord ». Une petite carte (bordure 3 px `#2445C2`, rayon 18 px, pile derrière, marque-page de 30 px) montre la meilleure offre : logo 40 px, titre 16 px, entreprise · lieu · libellé de note. Dessous, bouton blanc « Trier les offres » (hauteur 48 px, rayon 24 px, texte `#1A3496` 16 px gras, flèche).
  - Ordinateur : le livre en petit dans la colonne de droite (pages de 200 × 260 px, texte 13 px), avec « Écarter » et « Garder » dessous (hauteur 48 px, « Garder » en style secondaire `#E8ECFB` / `#1A3496`). On trie sur place. La ligne « Trier {n} offres » de la liste ouvre la page complète.
- **État `vide`.** Titre « Offres à trier ». Bloc à bordure pointillée 2 px `#E3BFA8`, rayon 18 px, marge intérieure 18 px (24 px sur ordinateur) : « Rien à trier pour l’instant » (17 px, gras), « jobA1 cherche chaque matin. Les prochaines offres arrivent demain. » (15 px), contour de marque-page en pointillés à droite. Dessous, lien « Élargir ma recherche » vers les critères. La tâche « Trier {n} offres » disparaît et les suivantes sont renumérotées.
- Les anciens écrans `AccueilSmile`, `AccueilSombre`, `AujourdhuiOrdinateurTravailD` ont été retirés du paquet le 13 novembre (voir la table de remplacement du LISEZMOI). `AujourdhuiOrdinateurReposD` reste, avec l'ancien visuel : ne pas le redessiner.

## PR 50 · Objectif du mois modifiable

Maquettes : `ProfilOrdinateur`, `ProfilOrdinateurObjectif`, `ProfilTel`, `ProfilTelSombre`, `ProfilTelObjectif`, `ProfilTelObjectifSombre`.

- **L'utilisateur fixe lui-même son objectif.** Le 10 des maquettes est un exemple.
- **Profil.** Ligne « Suivi ORP » avec la valeur « {objectif} recherches par mois ». Elle existe sur ordinateur. Ajoute-la sur téléphone, dans « Ce que je cherche », après « Langues », au format des autres lignes.
- **Panneau « Objectif du mois »** (composant de la PR 37) :
  - Phrase : « Le nombre de recherches que ton conseiller ORP te demande chaque mois. » (15 px, interligne 22 px).
  - Compteur, 24 px dessous, centré : bouton rond « moins » (56 px, bordure 1,5 px `#C9C5BA`, fond blanc), le nombre (56 px, interligne 60 px, graisse 800) avec « recherches par mois » dessous (14 px), bouton rond « plus ». Écart 24 px.
  - Encadré, 24 px dessous : fond `#E8ECFB`, rayon 14 px, marge intérieure 12 px 16 px, « S’applique dès {mois courant}. Les mois déjà remis ne changent pas. » (14 px, interligne 20 px).
  - Pied : « Annuler » (secondaire) et « Enregistrer » (plein), hauteur 52 px, écart 12 px.
- **Bornes** : 1 à 99. Aux bornes, le bouton concerné est désactivé (`disabled`, opacité 0,4) et une ligne centrée apparaît sous le compteur : « 99 est le maximum. » ou « 1 est le minimum. » (14 px). Maquette : `ProfilTelObjectifMax`.
- **Accessibilité.** Le compteur est un `role="spinbutton"` avec `aria-valuenow`, `aria-valuemin`, `aria-valuemax`, `aria-label="Recherches par mois"`. Flèches haut et bas au clavier. Les boutons s'appellent « Une recherche de moins » et « Une recherche de plus ».
- **Données.** Un champ par utilisateur, par exemple `orp_objectif_mensuel` (entier, 1 à 99, contrôlé côté serveur et côté interface). Reprends la valeur actuelle comme valeur par défaut pour les comptes existants. À la remise d'un mois, enregistre l'objectif de ce mois avec le mois : un changement ultérieur ne le modifie pas.
- **Lecture.** Tous les écrans qui affichent « {fait} sur {objectif} » lisent ce champ : Accueil, Aujourd'hui, Suivi ORP, Envoyées, Candidatures (ordinateur), Bilan, Préparer, Candidature envoyée, Assistant. Cherche les constantes 10 et 13 dans le code et remplace-les.

**Contrôles**
- Test Playwright : ouvrir Profil, « Suivi ORP », appuyer deux fois sur plus, enregistrer ; vérifier « {objectif+2} recherches par mois » dans la ligne, puis la nouvelle valeur sur Accueil et sur le Suivi ORP sans rechargement.
- Test : un mois déjà remis garde son objectif après le changement.

## PR 51 · Ma candidature et Envoyée

Maquettes : `MaCandidatureV2`, `MaCandidatureV2Sombre` (états `lettre`, `fin`), `PreparerOrdinateur`, `PreparerOrdinateurRelecture`, `PreparerOrdinateurSombre`, `CandidatureEnvoyeeOrdinateur`.

- **Lettre.** Surligne dans la lettre les passages repris de l'annonce. Au-dessus de la feuille, à gauche : pastille jaune 24 × 12 px et « Repris de l’annonce : {k} points » (13 px). Sur ordinateur, la légende est à 16 px du haut et 24 px de la gauche de la zone grise, et la zone gagne 16 px de marge haute.
- Le surlignage est un affichage : il n'apparaît ni dans le PDF, ni dans l'e-mail, ni à l'impression (`@media print`).
- **Envoyée.** Sous « Candidature envoyée. » et la ligne « {poste} chez {entreprise}. », une carte (ordinateur : largeur 480 px, bordure 1 px `#E5E2D9`, rayon 18 px, marge intérieure 16 px 20 px 4 px) :
  - la barre ORP mise à jour (PR 48) ;
  - « Preuve pour l’ORP gardée » et « Ton e-mail du {date} à {heure} », avec une pastille verte à coche de 24 px ;
  - « Relance prévue le {date} » et « jobA1 te la prépare », avec une icône horloge de 24 px.
  - Lignes de 60 px au moins, séparées par un trait `#ECE9E1`.
- Si la preuve manque : la ligne devient « Il manque la preuve pour l’ORP » avec le bouton existant pour l'ajouter (état `finpreuve` de `MaCandidatureV2`).

## PR 52 · Relance et Veille de rendez-vous sur ordinateur

Maquettes : `RelanceOrdinateurV2`, `RendezVousFeuilleOrdinateurV2`. Téléphone : `RelanceV2`, `RendezVousFeuilleV2` (+ `Sombre`).

- Sur ordinateur, ces deux écrans s'ouvrent dans le panneau de la PR 37 : largeur 440 px, à 16 px des bords droit, haut et bas, rayon 24 px, fond `#F7F5F0`, voile `rgba(27,31,42,.38)` derrière.
- En-tête du panneau, 68 px : titre à gauche (22 px, interligne 28 px, graisse 800), bouton rond « Fermer » de 44 px à droite. Pas de flèche retour.
- Contenu : celui du téléphone, marges latérales de 20 à 24 px. Le bouton principal reste collé en bas du panneau.
- Relance s'ouvre par-dessus Candidatures. Veille de rendez-vous s'ouvre par-dessus Aujourd'hui.
- `role="dialog"`, `aria-modal="true"`, focus gardé dans le panneau, rendu à l'élément d'origine à la fermeture, Échap ferme.
- Versions sombres : `RelanceOrdinateurV2Sombre`, `RendezVousFeuilleOrdinateurV2Sombre`. Fond du panneau `#171411`, bordure 1 px `#38322B`, voile `rgba(0,0,0,.55)`, pas d'ombre.

## PR 53 · Textes

| Écran | Avant | Après |
|---|---|---|
| Compte, Réglages | « Charte d’utilisation de l’IA » | « L’IA et tes données » |
| Coordonnées | « jobA1 les remplit à ta place dans les formulaires des employeurs. » | « jobA1 te les donne prêtes à copier quand un formulaire les demande. » |
| Entraînement (ordinateur) | « Entrée pour envoyer · Maj+Entrée pour aller à la ligne » | « Entrée pour aller à la ligne · Ctrl+Entrée pour envoyer » |
| Candidatures | « Afficher 20 offres de plus · 367 en tout » | « Afficher 20 offres de plus » |

La deuxième ligne corrige la PR 44, qui reprenait l'ancienne phrase. Le raccourci de l'Entraînement change avec son texte (déjà prévu à l'étape 1).

## 2. Contrôles pour chaque PR

- Captures avant et après à 390 et 1440 px, en clair et en sombre, pour chaque état cité.
- Grille de 4 px, contraste AA (4,5:1 pour le texte, 3:1 pour les icônes et les bordures de champ), cibles de 44 px.
- `outils/audit-grille.js` sans erreur nouvelle.
- Navigation complète au clavier, annonce au lecteur d'écran vérifiée sur le tri et sur le compteur de l'objectif.
- Tests Playwright demandés dans les PR 45, 46 et 50, plus : trier 3 offres (garder, écarter, garder), arriver sur la fin du tri, vérifier « 2 offres gardées, 1 écartée. » et la présence des deux offres dans Candidatures avec l'étiquette « Gardée ».

## 3. Données de démonstration

Les maquettes utilisent partout : novembre, objectif 10, 7 recherches faites, « encore 3 d’ici le 5 décembre ». Après un envoi : 8 sur 10, encore 2. Octobre : 11 recherches, remis le 10 novembre. Offres d'exemple : « DevOps Engineer », Alpstack, Lausanne, 92 ; « Platform Engineer », Romandie Mobilité, Renens, 84. Ce sont des exemples, pas des valeurs à coder.

## 4. Hors de ce lot

- La variante « fiche » du Bilan n'a pas d'état « remis ».
- Les étapes « 2. CV » et « 3. Postuler » de Ma candidature ne changent pas.
- Le carnet des rendez-vous garde « Objectif : 8 recherches par mois » : c'est ce qui a été convenu en septembre, un historique.
- Envoyées : l'onglet « Toutes » compte toutes les candidatures envoyées, tous mois confondus (14 dans la maquette). La barre ORP ne compte que le mois en cours (7). Les deux nombres sont donc différents, c'est voulu.
- La borne haute de l'objectif est 99 (décision du 9 novembre, confirmée le 11).
