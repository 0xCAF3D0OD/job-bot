# jobA1, récapitulatif de tout ce qui est demandé depuis le 10 novembre au soir (PR 25 à 44)

Ce paquet regroupe les 5 prompts du 10 au soir au 11 novembre et toutes les maquettes concernées, **dans leur dernière version**. Installe-le dans `docs/mobile/` par-dessus l'existant. Il prime sur les paquets précédents pour ces points.

## Ce que je te demande

1. **D'abord un état des lieux, sans rien coder.** Pour chaque point numéroté ou chaque puce des sections ci-dessous, dis-moi dans un tableau : `fait` (avec la PR ou le commit), `partiel` (ce qui manque) ou `pas fait`. Regarde le code et les PR fusionnées, pas seulement l'historique de nos échanges.
2. **Attends mon accord sur ce tableau.**
3. **Puis fais ce qui manque**, dans l'ordre des PR, une PR à la fois, avec les captures avant/après à 390 et 1440 px, en clair et en sombre.

Règles :
- Ne refais pas ce qui est déjà fait, sauf si la dernière maquette a changé depuis. Dans ce cas, signale-le dans le tableau comme `à reprendre`.
- **En cas de différence entre un texte et une maquette, la maquette de ce paquet fait foi** : elle est plus récente que certains prompts. Exemples : le formulaire de rendez-vous est maintenant dans un panneau (PR 41) et plus dans la colonne de détail (PR 31) ; les liens « Voir l’annonce » suivent la règle de la PR 25.
- Les captures de `captures/etats/` viennent de paquets successifs : si une capture contredit la maquette, c'est la maquette qui compte.
- Contrôles communs : grille de 4 px, contraste AA, cibles de 44 px sur téléphone, apostrophe ’, espace fine insécable avant : ; ? !, aucun tiret cadratin.

## Points donnés dans nos échanges et pas dans les fichiers

- **Lien vers l’offre en double (rappel de la PR 25)** : un seul lien vers le site dans toute la fiche d'une offre, « Voir l’annonce sur [source] » (section « Le poste » sur téléphone, « L’offre en bref » sur ordinateur). Supprime « Ouvrir l’annonce » de l’encadré, « Postuler sur Indeed/LinkedIn » et tout autre doublon. Le menu « … » garde « Ouvrir l’annonce sur le site ». Test : un seul lien visible vers l'adresse de l'annonce, hors menu « … ».
- **Budget de poids** : tu l'avais commencé pendant les PR 34 à 36. Dis où il en est dans le tableau : budget mesuré compressé (gzip/brotli) et brut, CI en échec au-delà de +5 %, contrôle du CSS inutilisé, budgets JS et images, explications dans `docs/performance.md`.
- **Sources d’offres sans alerte e-mail** : OK pour l'étape 1 (inventaire), Vaud seulement, avec deux ajouts :
  1. mesurer la part de cas 3 (SuccessFactors, Refline, Abacus, Prospective) dans la liste ;
  2. une 2e liste construite à l'envers : les entreprises vaudoises qui ont un flux Personio, Greenhouse, Lever, Recruitee, Workable, SmartRecruiters ou Ashby, quel que soit le métier.
  Dans le tableau, une colonne « conditions d'utilisation : lecture automatique permise / interdite / rien ». Pour l'étape 2, ne garde pas les coordonnées des recruteurs (nom, e-mail, téléphone) au-delà de la durée de l'offre, et note-le dans la politique de confidentialité. Rédige les 3 courriers (Adzuna, JobCloud, SECO), je les relis avant envoi.
- **Coordonnées** : on ne retire pas le volet « Pour les formulaires de candidature ». Voir la PR 44.

## Contenu du paquet

- `maquettes/` : 48 maquettes `.dc.html` dans leur dernière version, et `canvas.json` (titres).
- `captures/` : une capture par maquette, état par défaut, à jour. `captures/etats/` : états ouverts. `captures/cible_*.png` : comparaisons appli / maquette (PR 33).


---

# PR 25 à 28 · 10 novembre, soir

# Prompt Claude Code : annonce illisible, libellés flottants, rendez-vous et contact repliables (10 novembre 2026, soir)

À ajouter par-dessus `docs/mobile/`. Ce paquet ne contient que les fichiers nouveaux ou modifiés, et prime sur les paquets précédents pour ces points.
Captures : `captures/` et `captures/etats/` (téléphone 390 et 360, ordinateur 1440, clair et sombre).

Règle générale nouvelle : **sur téléphone, une tâche courte s’ouvre dans une fenêtre du bas ; sur ordinateur, la carte se déplie sur place** (pas de panneau latéral pour un seul champ). Bouton déclencheur : bouton teinté avec chevron (`aria-expanded`, `aria-controls`).

## PR 25. Annonce illisible : donner le lien de l’employeur

Maquettes : `OffreProvisoire` (+ `Sombre`) téléphone ; `CandidaturesOrdinateurB` (+ `BSombre`, `Ajouter`, `Spontanee`, `Statut`) ordinateur.
- Dans la carte de la note, quand la lecture automatique échoue : une seule ligne « Annonce illisible · Indeed bloque la lecture. » (nom réel de la source) + bouton teinté « Donner l’annonce ».
- Téléphone : le bouton ouvre la fenêtre du bas « Donner l’annonce à jobA1 » : phrase, champ « Lien chez l’employeur » (type url), astuce, bouton plein « Lire l’annonce », séparateur « ou », bouton « Coller le texte de l’annonce » qui ferme cette fenêtre et ouvre la fenêtre de collage.
- Ordinateur : la carte se déplie sur place (état `ann`) : champ + bouton contour « Lire » sur une ligne, astuce, lien « Pas de lien ? Colle le texte ».
- « Lire l’annonce » récupère la page de l’employeur (même moteur que la lecture automatique, PR 13), puis refait la note. Échec : message sous le champ (« Cette page ne contient pas d’annonce lisible »), `aria-live`.
- Fenêtre de collage : phrase « Tout le texte est accepté, même très long. » (aucune limite haute côté interface ; 200 caractères minimum), compteur « n caractères · il en faut au moins 200 » puis, en vert, « 3 482 caractères · assez pour noter », bouton texte « Refaire la note » à la place de la flèche seule (`aria-disabled` sous 200).
- Un seul lien vers le site dans toute la fiche : « Voir l’annonce sur [source] » (section « Le poste » sur téléphone, « L’offre en bref » sur ordinateur). Supprimer « Ouvrir l’annonce » de l’encadré, « Postuler sur Indeed/LinkedIn » et les doublons. Le menu « … » garde « Ouvrir l’annonce sur le site ».
- Menu « … » ordinateur : supprimer « Voir le détail de la note » (doublon de « Voir la compatibilité », et sans effet aujourd’hui).

## PR 26. Filtre « Note »

Maquettes : `Filtres` (téléphone), filtres de `CandidaturesOrdinateurB` (ordinateur).
- Nouveau groupe « Note » : Toutes / Sûres · n / Provisoires · n (choix unique, `role="radio"`), avec la phrase « Provisoire : notée sur l’extrait de l’alerte, sans l’annonce complète. »
- Les nombres sont réels.

## PR 27. Libellés flottants (Material 3, champ « outlined »)

Maquettes : `CoordonneesTel`/`CoordonneesOrdinateur`, `OnboardingProfil`/`OnboardingOrdinateurProfil`, fenêtres « Donner l’annonce », « Prochain rendez-vous ORP », « J’ai contacté quelqu’un » (+ `Sombre`).
- Champ 56 px, bordure 1,5 px #8C8478, radius 12 px.
- Vide : libellé dans le champ (16 px, #596070). Au focus ou rempli : libellé remonte dans la bordure (12 px gras), fond du libellé = dégradé moitié couleur du conteneur / moitié couleur du champ, pour couper la bordure proprement.
- Le libellé est un vrai `<label for>` ; il ne disparaît jamais (WCAG 3.3.2). Pas d’exemple écrit en gris dans le champ : l’exemple va sous le champ (« Ex. : … »).
- Marque « Du CV » : petite pastille dans le libellé.
- Champ désactivé : fond #F2F0EB, bordure #D8D4CA, texte #6E7381.
- Appliquer à tous les formulaires de l’appli, pas seulement aux maquettes listées.

## PR 28. Rendez-vous et contact repliables

- Téléphone, onglet Rendez-vous sans rendez-vous à venir (`RendezVous`, état `vide`) : une carte « Aucun rendez-vous à venir · jobA1 prépare ta feuille la veille. » + bouton teinté « Ajouter ». Le formulaire s’ouvre dans une fenêtre du bas (état `addSheet`) : Date + Heure sur une ligne (1,4 / 1), « Lieu ou lien (facultatif) » + exemple dessous, bouton plein « Ajouter le rendez-vous ». Plus de personnage à capuche ici.
- Ordinateur : déjà compact dans la colonne (« Ajouter »), garder.
- « J’ai contacté quelqu’un » :
  - Ordinateur (onglet Envoyées, historique) : bouton teinté avec chevron, la carte se déplie (état `ct`) : Nom, Rôle (facultatif), Comment, « Annuler » + « Enregistrer ».
  - Téléphone : fenêtre du bas `EnvoyeeDetailContacte` (mêmes champs, bouton plein « Enregistrer »). Le contact enregistré apparaît dans l’historique et adapte la prochaine relance.

## Vérifications
- Téléphone 360 et 390 px ET ordinateur 1440 px, clair et sombre, captures avant/après, pour chaque état listé.
- `outils/audit-grille.js` : 0 écart sur `OffreProvisoire`, `Filtres`, `CoordonneesTel`, `OnboardingProfil`, `RendezVous`, `EnvoyeeDetailContacte`.
- Clavier : la fenêtre du bas garde le focus et se ferme avec Échap ; le bouton dépliant annonce son état.

---

# PR 29 à 33 · 10 novembre, nuit

# Prompt Claude Code : justificatifs remis, « Offres », rendez-vous ordinateur, écarts avec la maquette (10 novembre 2026, nuit)

À ajouter par-dessus `docs/mobile/` (fichiers nouveaux ou modifiés seulement). Prime sur les paquets précédents pour ces points.
Captures : `captures/etats/` et 4 comparaisons « appli / maquette » dans `captures/cible_*.png`.

## PR 29. Justificatifs déjà remis à l’ORP

Maquettes : `BilanOrdinateur` (+ `Sombre`), `Orp` (+ `Sombre`), état `remis`.
- Tant que les justificatifs du mois précédent ne sont pas marqués remis : carte en tête de Bilan › ORP (ordinateur) et du Suivi ORP (téléphone) : « Justificatifs d’octobre à remettre » + « n recherches · échéance (passée) le 5 novembre » + « Exporter le PDF » (contour) + « Déjà remis » (teinté).
- « Déjà remis » enregistre la date de remise ; la carte devient « Octobre remis à l’ORP · le [date] · n recherches » + « Annuler ». Le mois n’est plus bloqué, l’export du mois courant devient le seul visible.
- Aujourd’hui : la ligne « Remettre les justificatifs » mène au Bilan et disparaît dès que le mois est marqué remis.

## PR 30. Onglet « Offres » à la place de « À traiter »

- Libellé de l’onglet : « Offres · Envoyées · Rendez-vous », partout (téléphone et ordinateur, toutes les maquettes ont été mises à jour). Ne pas renommer les statuts internes des filtres.

## PR 31. Rendez-vous ORP sur ordinateur

Maquettes : `CandidaturesOrdinateurB` (+ `BSombre`, `Ajouter`, `Spontanee`, `Statut`), onglet `rv`.
- Supprimer la colonne « Le rendez-vous » à droite (elle répète l’en-tête).
- « Objectif de recherches » et « Mesures décidées » côte à côte, puis « Prochain rendez-vous » en pleine largeur.
- Barre d’action collée en bas de la carte (`position: sticky; bottom: 0`) : bouton plein « Enregistrer » + « L’objectif et le prochain rendez-vous se mettent à jour partout. » Le bouton est toujours visible sans défiler.

## PR 32. Carte « Relance conseillée »

- 8 px entre l’étiquette et le titre, titre 18/24, 4 px entre titre et sous-titre.
- Le message cité est un extrait (4 lignes max, « … ») avec « Modifier » pour le voir en entier ; ne pas afficher la lettre complète dans la carte.

## PR 33. Écarts entre l’appli et les maquettes (à corriger en suivant la maquette)

1. Ordinateur : pas de page « Suivi ORP » séparée avec flèche retour et flèches de mois. Tout est dans Bilan › ORP (`BilanOrdinateur`). Comparaison : `captures/cible_orp_entete.png`.
2. « À déclarer » et « Recherches du mois » utilisent exactement la même ligne : calendrier (mois + jour), entreprise en gras, poste · mode, état coloré + cercle flèche gris. « Déclarer » n’est plus un lien bleu isolé. Comparaison : `captures/cible_orp_listes.png`.
3. Bilan › Résultats sur ordinateur : une seule colonne (chiffres clés, « Le mois en bref », « Ce qui bloque » avec l’action « Relancer les n candidatures »). Supprimer la colonne de droite (« Mois par mois », « Ce qui marche », « Entretiens »). Comparaison : `captures/cible_resultats.png`.
4. Bloc « Entreprise » dans la fiche ORP d’une offre : supprimer l’espace vide en haut (élément vide), pas de bandeau bleu ; lignes « libellé gris au-dessus, valeur en gras dessous », alignées à gauche, bouton copier à droite. Comparaison : `captures/cible_entreprise.png`.
5. Lignes-liens dans une carte (Ce que tu as envoyé, Trouver un contact, menus) : pas de radius ni de bordure propre, pas de soulignement ; seulement un filet 1 px entre les lignes.

## Vérifications
- Téléphone 360 et 390 px ET ordinateur 1440 px, clair et sombre, captures avant/après.
- `outils/audit-grille.js` : 0 écart sur `Orp`, `Candidatures`.

---

# PR 34 à 36 · 10 novembre, fin

# Prompt Claude Code : icônes du Compte, bas de liste, accueil en bandes empilées (10 novembre 2026, fin de soirée)

À ajouter par-dessus `docs/mobile/` (fichiers modifiés seulement). Prime sur les paquets précédents pour ces points.

## PR 34. Icônes dans le Compte (téléphone, et menu « Mon compte » sur ordinateur)
Maquettes : `Compte`, `CompteSombre`.
- Une icône contour 24 px à gauche de chaque ligne (trait 2 px, couleur #3D4250, sombre #C7BFB3), toujours avec le texte, `aria-hidden="true"`.
- Formations = chapeau de diplômé, CV et lettres = document, Critères = loupe, Notifications = cloche, Apparence = lune, Mes données = base de données, Charte IA = bouclier avec coche, Aide = point d’interrogation, Objectif ORP et sites = drapeau, Alertes e-mail = enveloppe. La ligne du profil garde l’avatar.

## PR 35. Bas de la liste des offres (téléphone)
Maquettes : `Candidatures`, `CandidaturesSombre`, capture `etats/*--bas-de-liste.png`.
- Remplacer « Afficher plus (367) » par un bouton contour pleine largeur « Afficher 20 offres de plus · 367 en tout ».
- Puis un groupe « AUTRES OFFRES » (même ligne que le Compte, cercle flèche gris) : « Loin de ton profil · n offres, notées plus bas », « Expirées · n offres, pour mémoire », « Postuler spontanément · À une entreprise sans offre publiée ».
- 24 px de marge sous le dernier élément : rien ne passe sous la barre de navigation.
- Haut de la liste : la première carte ne doit pas passer sous l’en-tête (marge haute = hauteur de l’en-tête collant + 8 px).

## PR 36. Accueil : bandes qui s’empilent au défilement (téléphone)
Maquettes : `AccueilSmile`, `AccueilSombre`, animation `etats/AccueilSmile--bandes-empilees-animation.gif`.
- Bande « ORP » : `position: sticky; top: 0`. Bande « Offres » : `position: sticky; top: 16px` + ombre `0 -10px 24px rgba(27,31,42,.10)`. Bande « À faire » : non collante, passe par-dessus.
- Une bande collante ne dépasse jamais la hauteur de l’écran (sinon elle n’est pas collante).
- Toucher le bord visible d’une bande empilée fait défiler jusqu’à elle.
- `prefers-reduced-motion: reduce` : pas d’empilement (défilement normal).
- Focus clavier : `scroll-margin-top` sur les liens et boutons pour qu’un élément focalisé ne soit jamais caché sous une bande (WCAG 2.4.11).

## Vérifications
- Téléphone 360 et 390 px, clair et sombre ; ordinateur 1440 px pour le menu du compte.
- `outils/audit-grille.js` : 0 écart sur `Compte`, `Candidatures`, `AccueilSmile`.
- Tester l’accueil avec « réduire les animations » activé, et au clavier (Tab) jusqu’en bas de page.

---

# PR 37 à 43 · 11 novembre (et réponses aux questions sur les PR 34 à 36)

# jobA1, PR 37 à 43 (11 novembre 2026)

Paquet à installer dans `docs/mobile/`. Ce fichier remplace les deux prompts PR 37 à 43 envoyés dans le chat le 10 novembre au soir : il les fusionne et ajoute les décisions prises ensuite (rendez-vous dans un panneau, état fermé de l'onglet Rendez-vous).
À faire après les PR 34 à 36. Les réponses à tes questions sur ces PR sont à la fin de ce fichier.

Pour chaque PR : captures avant/après à 390 et 1440 px, en clair et en sombre.
Contrôles communs : grille de 4 px, contraste AA, cibles de 44 px minimum sur téléphone, apostrophe ’ et espace fine insécable avant : ; ? !, aucun tiret cadratin.

## Maquettes de référence

| Sujet | Ordinateur | Téléphone |
|---|---|---|
| Panneau Ajouter (offre, spontanée, annonce lue) | `CandidaturesOrdinateurAjouter` (états `menu=ajouter`, `ajl=true`), `CandidaturesOrdinateurSpontanee` (`ajt=sp`) | `AjouterOffreTel` (inchangé) |
| Filtre des Envoyées | `CandidaturesOrdinateurB` onglet `tab=en` (+ `Sombre`) | `Envoyees` (+ `Sombre`) |
| Rendez-vous : liste, détail, panneau « Nouveau rendez-vous » | `CandidaturesOrdinateurB` `tab=rv`, panneau `ajrv=true` (+ `Sombre`) | `RendezVous` feuille `addSheet=true` (+ `Sombre`) |
| Entraînement à l'entretien | `EntrainementOrdinateur` états `q=0` (réglages) et `q=1` (question) (+ `Sombre`) | `Entrainement` (+ `Sombre`) |

Les captures sont dans `captures/etats/`.

## PR 37 · Composant panneau unique (SidePanel)

- Un seul composant pour : menu du compte, notifications, Ajouter, Nouveau rendez-vous.
- Ordinateur : sous l'en-tête (top 76), largeur 420, coin haut gauche 24, ombre à gauche. En-tête : pastille ronde 48 px avec icône, titre 18 gras, sous-titre 14, bouton X 44 px. Corps qui défile. Pied fixe avec un seul bouton plein (D30).
- Téléphone : le même composant monte du bas (feuille, poignée, coins 24 en haut).
- Fermeture : X, Échap, clic à l'extérieur. role="dialog", aria-labelledby. Focus placé dans le panneau à l'ouverture, bloqué dedans, rendu au bouton d'ouverture à la fermeture (WCAG 2.1.2, 2.4.3).
- Pas de bouton « Annuler » : X et Échap suffisent.
- Tests Playwright : ouvrir, Échap, vérifier fermé et focus sur le bouton d'origine. Même test avec le clic extérieur.

## PR 38 · Panneau Ajouter

- Format du menu du compte (PR 37). Titre « Ajouter », sous-titre « Une offre ou une candidature spontanée ».
- Onglets « Une offre » et « Candidature spontanée ».
- « Une offre » : champ à étiquette flottante « Lien ou texte de l’annonce », coins 12 px. Sous le champ : « Tu peux encore en ajouter {n} aujourd’hui. » (singulier si n = 1). Bouton secondaire « Importer le PDF de l’annonce ».
- Supprime la flèche d'envoi dans le champ et le bouton « Recommencer ». Le seul bouton d'action est « Ajouter l’offre » dans le pied.
- Extraction : garde le contenu principal (type Readability). Retire nav, footer, form, aside, bandeaux cookies et consentement. Test avec une page enregistrée : le texte ne contient ni « cookies » ni « Requis ».
- Annonce lue : le PDF disparaît. Rubrique « CE QUE JOBA1 A LU » : Poste, Entreprise, Lieu, Contrat en champs modifiables. Ligne repliable « Texte lu · {n} caractères · cookies et formulaire retirés » (aria-expanded).
- Doublon : n'affiche pas « Cette offre était déjà là ». Ferme le panneau, ouvre l'offre existante, fais défiler jusqu'à elle, surbrillance 2 s, toast « Elle était déjà dans ta liste ».
- « Candidature spontanée » : Entreprise, Poste visé (aide « Par exemple : Ingénieur DevOps »), « Pourquoi cette entreprise ? (facultatif) ». Bouton « Créer la candidature ».

## PR 39 · Filtre des Envoyées

- Même composant que l'onglet Offres : recherche « Filtrer par titre ou entreprise » et tri « Trier : à relancer d’abord » (aussi « plus récentes », « plus anciennes »).
- Filtres de statut avec leur nombre : Toutes, À relancer, Sans réponse, Entretien, Refusées. Un filtre à 0 est masqué. role="group", aria-pressed.
- Ordinateur : filtres de 36 px sur une ligne. Téléphone : 44 px, sur une ligne qui défile horizontalement.
- Le filtre est gardé dans l'URL (`?statut=relancer&q=`).
- Aucun résultat : « Aucune candidature ne correspond » + bouton « Effacer les filtres ».

## PR 40 · Trait de sélection (ordinateur)

- Le trait et le point qui relient la carte sélectionnée au détail sont calculés à partir de la carte sélectionnée (getBoundingClientRect), et recalculés au défilement, au redimensionnement et au changement de filtre. Aucune position en dur.
- Masqués quand la carte sort de la zone visible.
- Test : après le filtre « À relancer », le centre du point est à ±2 px du centre de la carte sélectionnée.

## PR 41 · Rendez-vous avec une entreprise

- Panneau « Nouveau rendez-vous » (PR 37), sous-titre « jobA1 prépare ta fiche la veille ».
- « Avec qui ? » : « Une entreprise » ou « L’ORP » (radiogroup).
- Entreprise : Candidature (liste des envoyées avec recherche, texte long coupé par « … » avant la flèche), Format (Téléphone, Visio, Sur place), Date, Heure, puis « Lien de la visio », « Numéro » ou « Adresse » selon le format. Phrase : « La candidature passe en « Entretien ». Tu pourras t’entraîner la veille. »
- ORP : Date, Heure, « Lieu ou lien (facultatif) ».
- Date et heure vides par défaut, jamais préremplies avec aujourd'hui.
- Enregistrer : la candidature passe en « Entretien », la fiche de préparation est générée la veille.
- Points d'entrée : bouton « + Nouveau rendez-vous » en haut de la liste Rendez-vous, ligne « Prochain rendez-vous » du détail, détail d'une envoyée (« J’ai un entretien »).
- Modèle de données : `rendez_vous.type = 'orp' | 'entreprise'`, `candidature_id` nullable, `format`, `lieu_ou_lien`.

### Onglet Rendez-vous, panneau fermé (ordinateur)

- En haut de la liste : « Aucun rendez-vous à venir » / « jobA1 prépare ta fiche la veille. » et le bouton « + Nouveau rendez-vous » (plus de deuxième bouton « Ajouter » ambigu).
- Détail : le formulaire « Prochain rendez-vous » (date, heure) est supprimé. À la place, une ligne « Prochain rendez-vous · Pas encore noté. jobA1 prépare ta fiche la veille. » avec un bouton « + Ajouter » qui ouvre le même panneau.
- Texte du pied : « L’objectif et les mesures se mettent à jour partout. »

## PR 42 · Entraînement à l'entretien en page

- Plus de fenêtre : route `/entrainement/:candidatureId`. Point d'entrée : la carte du rendez-vous d'entretien.
- Réglages : « ‹ Rendez-vous », titre « S’entraîner pour l’entretien », poste · entreprise · date.
  - « Avec qui ? » (RH, Manager, Technique) avec une phrase d'aide selon le choix.
  - « Ton du recruteur » (Bienveillant, Exigeant).
  - « Langue » (Français, Anglais, Allemand), par défaut la langue de l'annonce, avec « L’annonce est en … ».
  - Option choisie : bordure 2 px #2445C2, fond #E8ECFB, coche. Une seule par groupe (WCAG 1.4.1 : pas seulement la couleur).
  - « 5 questions · environ 10 minutes · tu peux en passer une. » et le bouton plein « Commencer l’entraînement », sans icône. Sur téléphone, bouton fixé en bas.
- Question (mode concentration, sans la barre de navigation) :
  - Barre : « Quitter » (confirmation si une réponse est en cours), « Question n sur 5 » et 5 segments (role="progressbar"), « Technique · anglais ».
  - « Le recruteur · entreprise », question en 24/34 gras (20/28 sur téléphone), lang de la langue choisie.
  - « Conseil » repliable.
  - Réponse juste sous la question, sans grand vide : étiquette flottante « Ta réponse », coins 12, 168 px de haut (148 sur téléphone), compteur de mots. Aide « Entrée pour envoyer · Maj+Entrée pour aller à la ligne » sur ordinateur seulement ; sur téléphone « Réponds comme à l’oral ».
  - À gauche « Passer la question » (« Passer » sur téléphone), à droite le bouton plein « Envoyer la réponse ».
  - Colonne de 720 px sur ordinateur.
- Prévoir sur l'écran de fin un emplacement pour un lien vers get’emall.ch, masqué par un drapeau de fonctionnalité.

## PR 43 · Contrôle final

- Rejoue les tests des PR 37 à 42 en sombre.
- Vérifie qu'aucun champ ovale (rayon 20 ou plus) ne reste dans les panneaux et formulaires.

## Réponses à tes questions sur les PR 34 à 36

1. OK pour les 8 icônes proposées, prises dans `src/icons.ts`.
2. Ne renomme pas en « Charte d’utilisation de l’IA » : le lien mène à /tes-donnees#ia, la page parle des données envoyées. Nouveau libellé : « L’IA et tes données », icône bouclier avec coche, sur téléphone et ordinateur.
3. OK : ajoute le chapeau de diplômé et la base de données dans `src/icons.ts` avec les tracés de la maquette.
4. OK pour l'icône personne, l'engrenage et le drapeau dans Réglages > Recherche et outils. OK pour 24 px, trait 2 px, #3D4250, 16 px avant le texte, partout (Material 3, listes).
5. OK : 50 au premier chargement, puis +20 par appui. Le bouton annonce le vrai nombre (« Afficher 12 offres de plus »), au singulier « Afficher 1 offre de plus ».
6. État ouvert : même titre, sous-titre « 343 offres affichées », chevron vers le haut, aria-expanded="true". Pas de « touche pour masquer ».
7. Nombre restant. Libellé : « Afficher 20 offres de plus · 367 restantes » (« 1 restante »).
8. OK : ORP collée sous la barre du logo, Offres 16 px plus bas. Hauteur de la barre dans une variable CSS `--header-h`, utilisée pour `top` et `scroll-margin-top`, avec `env(safe-area-inset-top)`. Teste à 390 et 1440, et avec prefers-reduced-motion.

---

# PR 44 · 11 novembre, formulaires de candidature

# jobA1, PR 44 : réponses pour les formulaires de candidature (11 novembre 2026)

Réponse à ta question : on **ne retire pas** le volet « Pour les formulaires de candidature ». Il manquait dans la maquette par oubli. Les données restent (LinkedIn, permis de travail, disponibilité, délai de préavis, prétentions salariales) et leur usage pour remplir les formulaires aussi. Seule la présentation change.

Maquettes : `CoordonneesOrdinateur`, `CoordonneesTel` (+ `Sombre`). États : `cf=li`, `perm`, `dispo`, `preav`, `sal` (panneau ouvert). Captures dans `captures/etats/`.

## Page Coordonnées

- Les champs du haut (nom, e-mail, adresse, téléphone) ne changent pas.
- En dessous, séparée par un trait : la rubrique « POUR LES FORMULAIRES DE CANDIDATURE » (13 px, majuscules, #596070).
- Progression : « {n} réponses sur 5 » à gauche, « Il en manque {5-n} » à droite, puis 5 segments de 6 px (verts #1F7A4D quand la réponse est remplie, #DAD6CC sinon). **La progression disparaît quand les 5 réponses sont remplies.**
- Phrase : « jobA1 les remplit à ta place dans les formulaires des employeurs. »
- 5 lignes de 64 px minimum, séparées par un trait : icône 24 px (#3D4250), libellé 13 px gras gris, valeur 15 px, flèche à droite. La ligne entière est cliquable (aria-haspopup="dialog").
  - Profil LinkedIn : l'adresse du profil.
  - Permis de travail : « Permis C »…
  - Disponible dès : « Tout de suite », « Dans 1 mois » ou la date.
  - Délai de préavis : « 1 mois »…
  - Prétentions salariales : « 95 000 CHF brut par an » + petit cadenas.
- Une réponse vide affiche « À compléter » en orange (#B4542D, sombre #F2A766), sans message d'erreur : une réponse vide n'empêche pas d'enregistrer.
- Phrase du bas : « Ces informations servent à l’en-tête de tes lettres et aux formulaires de candidature. Elles ne sont jamais envoyées à l’IA. »

## Modifier une réponse

- Un appui sur une ligne ouvre le composant panneau de la PR 37 : panneau de droite sur ordinateur, feuille qui monte du bas sur téléphone. Une seule réponse à la fois.
- Le titre est une question, suivie d'une phrase qui explique le mot :
  - « Ton profil LinkedIn ? » : « Copie l’adresse de ton profil depuis LinkedIn. » Un champ « Adresse du profil » (validation : linkedin.com/in/…).
  - « Ton permis de travail ? » : choix à toucher : Nationalité suisse, Permis C, Permis B, Permis G, Autre (Autre ouvre un champ texte).
  - « Quand peux-tu commencer ? » : Tout de suite, Dans 1 mois, Dans 3 mois, Date précise. Le champ « Date » n'apparaît que pour « Date précise ».
  - « Ton délai de préavis ? » : Aucun, 1 mois, 2 mois, 3 mois, Autre.
  - « Tes prétentions salariales ? » : champ « Prétentions salariales (CHF brut par an) », séparateur des milliers à l'espace fine. Sous le champ, avec un cadenas : « Visible seulement par toi. Utilisé seulement si un formulaire le demande, jamais envoyé à l’IA. » Puis le choix « Si un formulaire le demande » : « Le remplir automatiquement » (par défaut) ou « Me demander avant ».
- Choix à toucher : 44 px de haut, une seule réponse (role="radiogroup", aria-checked). Choix sélectionné : bordure 2 px #2445C2, fond #E8ECFB, coche.
- Un seul bouton plein « Enregistrer » dans le pied. Il enregistre et ferme le panneau. Pas de bouton « Annuler » (X, Échap, clic à l'extérieur).

## Données et confidentialité

- Garde le modèle actuel. Ajoute `salaire_mode = 'auto' | 'demander'`, `'auto'` par défaut.
- Avec « Me demander avant », au moment de remplir un formulaire qui demande le salaire, jobA1 s'arrête et demande la valeur pour cette candidature.
- Rien de cette rubrique n'est envoyé à l'IA. Ajoute un test qui le vérifie (aucun de ces champs dans le contexte envoyé au modèle).
- Quand un formulaire demande une réponse vide, jobA1 la demande à ce moment-là, puis propose de l'enregistrer ici.

## Contrôles

- Captures avant/après à 390 et 1440 px, en clair et en sombre, page fermée et chaque panneau ouvert.
- Grille de 4 px, contraste AA, cibles de 44 px, apostrophe ’, espace fine insécable avant : ; ? !, aucun tiret cadratin.
- Test Playwright : ouvrir « Délai de préavis », choisir « 2 mois », enregistrer, vérifier la valeur dans la ligne et la progression qui passe à 5 sur 5 puis disparaît.
