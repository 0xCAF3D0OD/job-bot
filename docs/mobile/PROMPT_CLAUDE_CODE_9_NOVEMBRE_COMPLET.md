# Prompt pour Claude Code : lot complet du 9 novembre 2026 (téléphone et ordinateur)

Copie tout le bloc ci-dessous dans Claude Code.

```
Tâche : appliquer à jobA1 toutes les décisions de design validées par Kevin le 9 novembre 2026, sur téléphone (≤ 820 px) et ordinateur (> 820 px), en clair et en sombre.

## 0. Sources et priorité

Ajoute le contenu de jobA1_maquette_2026-11-09.zip par-dessus docs/mobile/ (fichiers du même nom remplacés), sans supprimer le reste : tokens.css reste la source de vérité des couleurs (CLAUDE.md), le logo et les écrans Get'emAll (AutoriserGetemall, ConfidentialiteGetemall, Relier*, ReglagesConnexions, ReglagesRetirer) restent, ils appartiennent à un autre chantier.
Ordre de priorité (le premier gagne en cas de contradiction) :
1. Ce prompt.
2. MODIFICATIONS_9_NOVEMBRE_ORDINATEUR.md (§1 à §13 ; il couvre aussi des écrans téléphone : §4, §8.3, §9, §10).
3. MODIFICATIONS_8_NOVEMBRE_SOIR.md (règles D24, D28 à D35, §2.9, §2.10).
4. Les maquettes de maquettes/ et leurs captures (captures/, captures/etats/, captures/commentees/).
Lis les documents 2 et 3 en entier avant d'écrire du code. N'improvise rien : si une maquette et un texte se contredisent, demande-moi.

Copie aussi :
- illustrations/scenes/*.webp et connexion-perdue.svg dans frontend/public/illustrations/scenes/ ;
- illustrations/personnage/ dans frontend/public/personnage/ (mêmes noms).

## 1. Décisions qui remplacent des règles plus anciennes

Applique-les partout, même si un ancien document dit autre chose :
- Cercles-flèches des cartes cliquables : même composant (cercle 36 ou 40 px, flèche 18 px, à 20 px du bord droit) mais contour et flèche en #596070 (sombre #ABA398), plus en bleu. Seule exception : les notifications (inchangées). Ne jamais éclaircir ce gris.
- Cibles cliquables : 24 px minimum sur ordinateur (WCAG 2.5.8), 44 px sur téléphone. Boutons principaux 40 à 48 px.
- Bande bleue d'Aujourd'hui (ordinateur) : gardée, pleine largeur, c'est le point focal. Aucune autre page n'a de bande bleue.
- ORP_DEADLINE_DAY = 5 : les recherches d'un mois se remettent au plus tard le 5 du mois suivant (art. 26 al. 2 OACI), reporté au premier jour ouvrable si le 5 tombe un samedi, un dimanche ou un jour férié du canton de l’ORP de la personne. Tous les textes « d’ici le … » utilisent cette échéance (ex. « Encore 9 d’ici le 5 décembre »).
- Jamais de carte dans une carte (D29). Un seul bouton plein par écran ou par feuille (D30). Statut = mot coloré, pas de pastille (D31).
- Notifications téléphone et ordinateur : ne pas toucher.

## 2. Ordre des PR

Une PR par ligne. Chaque PR contient : la liste des points cochés, « Règles vérifiées : … », captures avant et après (clair et sombre ; 390 px et 320 px pour les listes téléphone ; 1024 et 1440 px pour l'ordinateur), une entrée dans changelog.d/.

### PR 1. Composants communs
- Carte : blanche, bordure 1,5 px #CFCBC1, rayon 18, marge intérieure 20 px (18,5 + bordure). Carte d'information : même style, sans flèche.
- Cercle-flèche gris (§1 ci-dessus), chevron de 24 px #596070 pour les lignes de liste et de feuille.
- Mot d'état coloré : vert #17734A, orange #8A4A16, bleu #1A3496, gris #596070 (sombre : #62D497, #F2B98E, #AEBDFF, #ABA398).
- SidePanel.vue (ordinateur, 440 à 480 px, voile rgba(27,31,42,.45), animation 250 ms, fermeture croix, Échap, clic sur le voile, focus rendu au déclencheur). BottomSheet.vue reste la logique commune ; SidePanel l'affiche à droite au-delà de 820 px.
- Champs : pilule (rayon 24 ou 28), texte à 20 px du bord, bordure 1,5 px #8C8478, au focus un seul contour 2 px #2445C2. Zones de texte rayon 20.
- Bouton copier 40 px (cercle, bordure 1,5 px #CFCBC1, aria-label « Copier : <libellé> »), lignes de 56 px, libellé 13 px au-dessus de la valeur 16 px.
- Snackbar : fond #1B1F2A, actions en #AEBDFF, 6 secondes, role="status".
- Une seule zone défile : la page. Plus aucun défilement interne (colonne, carte, liste). Colonne de droite sticky, tient dans 900 px.

### PR 2. Mode sombre ordinateur (MODIFICATIONS_9 §12)
- Table de couleurs du §12 (identique au téléphone sombre) appliquée par jetons CSS, pas écran par écran.
- Bouton plein sombre : fond #7D95FF, texte #171411.
- La page A4 de la lettre et du CV reste blanche en sombre (ombre plus marquée).
- Avatars aux initiales inversés (fond clair, lettres foncées).
- Références : AujourdhuiOrdinateurTravailDSombre, CandidaturesOrdinateurBSombre (onglets tr, en, rv), PreparerOrdinateurSombre, BilanOrdinateurSombre. Les autres écrans suivent la même table.

### PR 3. Préparer
Ordinateur (MODIFICATIONS_9 §2.2 à §2.4, §7) :
- « Préparer ma candidature » lance tout de suite l'écriture de la lettre ; le CV adapté se prépare en même temps (PreparerOrdinateurGeneration : bandeau « J’écris ta lettre… environ 20 secondes », lettre qui apparaît, puces et saisie grisées, bouton désactivé).
- Page A4 toujours visible dans le modèle choisi ; 4 vignettes de modèle ; carte « Ta candidature » (Relecture 7 sur 7, Versions · 3, CV adapté) ; bouton « J’ai relu, continuer ».
- PreparerOrdinateurLettreVide et PreparerOrdinateurCV : uniquement en cas d'échec, avec « Réessayer ».
- Étape CV quand le CV est prêt (MODIFICATIONS_9 §14, PreparerOrdinateurCVPret et PreparerOrdinateurCVChangements) : même structure que la Lettre, sélecteur FR / DE / EN (« Langue du CV », par défaut celle de la lettre), carte « Ce CV » (Adapté pour cette offre, Versions, CV d’origine), panneau qui liste chaque changement avec « Annuler ce changement ».
- Postuler : carte « Où postuler » en haut, « Tout télécharger » à contour (2 fichiers séparés), lignes à copier de 56 px, carte Entreprise à droite.
Téléphone (MODIFICATIONS_9 §9, maquettes Preparer, PreparerSombre, PreparerMiseEnPage, PreparerMiseEnPageSombre) :
- Retirer l'anneau de note de l'en-tête, la carte « Mise en page » et le sélecteur FR / DE / EN (téléphone seulement : sur ordinateur, FR / DE / EN reste en haut du document).
- Sous le titre du document : « Moderne · Français » en gris et le lien « Changer » (44 px) qui ouvre la feuille « Mise en page et langue » (4 modèles, « Tient sur une page A4. », Langue de la lettre en 3 boutons Français / Deutsch / English, ligne « Retoucher dans Canva »).
- Aperçu du document : 384 px de haut.
- Puces de retouche cachées par défaut ; elles apparaissent au-dessus de la zone de saisie quand elle a le focus, l'aperçu passe à 300 px (captures/Preparer--saisie-active.png). Plus de libellé « Retoucher la lettre ».
- « Retoucher dans Canva » uniquement dans la feuille.
- Plus de case « J’ai relu la lettre » : un seul bouton « J’ai relu, continuer ».

### PR 4. Candidatures, À traiter et Ajouter (ordinateur, MODIFICATIONS_9 §2.1, §2.6, §2.7)
- Note en carte d'information avec « Voir la compatibilité » (panneau `cmp`).
- « Écarter » immédiat (état `ec`) + snackbar « Offre écartée » / « Annuler ».
- Un seul bouton « + Ajouter » : panneau à 2 onglets « Une offre » / « Candidature spontanée » (`ajt` = of, sp). Supprimer le lien « Postuler spontanément » en bas de liste.
- Aucune offre : lien « Faire une candidature spontanée › » sous un trait de 420 px.

### PR 5. Candidatures, Envoyées (MODIFICATIONS_9 §8)
Ordinateur (CandidaturesOrdinateurB, onglet `en`) :
- Plus de grand cadre autour du détail : cartes blanches séparées sur le crème, 8 px entre toutes les cartes, 20 px avant Historique.
- Carte d'en-tête : avatar 56 px, titre, entreprise · ville, menu « … » ; statut en mots colorés (« Sans réponse · 57 jours », « ✓ Déclarée à l’ORP ») ; Suivi en 5 étapes (Préparée, Envoyée, Déclarée ORP, Relance, Réponse) avec date ou état sous chaque libellé.
- Alignement : statut et Suivi décalés de 72 px (avatar 56 + 16) ; titre, entreprise, statut et bord gauche du premier cercle sur le même bord. Libellés alignés à gauche sous leur cercle. Traits entre étapes de 8 px après un cercle à 8 px avant le suivant ; verts jusqu'à l'étape en cours, gris ensuite. Dernière étape sur la marge droite.
- Carte de relance (colonne gauche) : « Relance conseillée » dans la carte, « Ton message est prêt », message en citation, destinataire et canal avec « Changer », bouton plein « Copier et ouvrir LinkedIn » (ou « Ouvrir l’e-mail » selon le canal) et lien « Modifier ». Dessous : « Quand tu reviens, le statut passe à « Relancé » et la prochaine relance est proposée dans 10 jours. »
- Colonne droite 280 px : « Ce que tu as envoyé » (Lettre, CV adapté, L’annonce) et « Trouver un contact » (Recrutement, L’équipe du poste, Anciens de 42 Lausanne), lignes de 56 px.
- Historique sur le crème, puis « J’ai contacté quelqu’un ».
- Trait vertical 2 px #E5E2D9 entre liste et détail ; trait bleu 2 px + point de 8 px du bord droit de la carte sélectionnée vers ce trait, centré verticalement sur la carte sélectionnée, aria-hidden, disparaît sans sélection.
Téléphone (nouvel écran EnvoyeeDetail + feuilles EnvoyeeDetailRelance, EnvoyeeDetailDocuments, EnvoyeeDetailContacts) :
- Ouvert depuis une carte de la liste Envoyées. Barre « ‹ Envoyées » et « … », sans barre d'onglets. 12 px entre les cartes.
- Pas d'avatar ni de graphique de suivi : titre, entreprise · ville, statut en mots colorés.
- Carte de relance compacte avec bouton plein pleine largeur « Voir et envoyer » (ouvre la feuille Relance : destinataire + « Changer », message entier, note, pied fixe « Ouvrir l’e-mail » + « Modifier le message »).
- Une carte de 2 lignes de 72 px avec chevron : « Ce que tu as envoyé » et « Trouver un contact », chacune ouvre sa feuille.
- Historique sur le crème.
Statut mis à jour par e-mail (CandidaturesOrdinateurStatut, EnvoyeesStatut) :
- Réponse reconnue dans un e-mail : la carte passe tout de suite à « Refus » (icône croix, #596070), pastille « Réponse reçue hier », snackbar « Réponse de [entreprise] : refus. » / « Depuis l’e-mail du 8 nov. » avec « Voir » et « Annuler ». La carte reste en place tant que la snackbar est visible.

### PR 6. Bilan et Suivi ORP
- Ordinateur (MODIFICATIONS_9 §2.5, §10.3) : « À déclarer à l’ORP » en cartes, panneau « Pour l’ORP », carte du mois « Novembre » / « 4 sur 13 » / barre / « Encore 9 d’ici le 5 décembre · dans les temps ».
- Téléphone (Orp, OrpSombre, Explorer, ProgresserSombre) : à côté de l'anneau 8/10, « Novembre » puis « Encore 2 d’ici le 5 décembre ». Retirer « 2 recherches à faire » et « Objectif fixé par ta conseillère… ».

### PR 7. Rendez-vous ORP (téléphone, RendezVous et RendezVousSombre)
- Une seule action dans la carte : bouton plein « Préparer le rendez-vous » qui ouvre la feuille (elle contient « Imprimer ou télécharger en PDF »). Retirer le lien séparé et « Voir ma feuille ». La pastille « Ta feuille est prête » reste.

### PR 8. Compte (téléphone, Compte et CompteSombre)
- Une carte par groupe (profil ; Mon parcours ; Préférences ; Confidentialité et aide ; Se déconnecter), lignes séparées par un trait de 1 px #EFECE5 (sombre #38322B), comme Réglages. Plus de trait entre les groupes, 12 px au-dessus et au-dessous de chaque groupe.
- « Se déconnecter » en rouge #B4371F (sombre #FF9B85), avec l'adresse e-mail dessous.

### PR 9. Alertes, Profil, Réglages, Aujourd'hui (ordinateur, MODIFICATIONS_9 §2.8 à §2.10)
- Alertes : familles À confirmer / Actives / À créer, une carte par alerte, panneaux `al` et `cf`.
- Profil : une carte par préférence.
- Réglages : groupes avec bordure, Langue et Taille du texte en lignes + panneau.
- Aujourd'hui : bande bleue gardée, cercles-flèches gris sur les cartes d'action.

### PR 10. Premiers pas et nouveau compte (MODIFICATIONS_9 §5, §6, §13)
- Grille commune des 3 étapes, scènes de la page de présentation (SceneIllustration) en colonne droite : étape 1 offres-profils ; lecture du CV lecture-calme ; CV lu formations-vide ; étape 2 lieux-carte ; étape 3 reussite ; alertes d'un nouveau compte alertes-carte.
- Coupure pendant la lecture du CV : scène connexion-perdue (illustrations/scenes/connexion-perdue-800.webp), en couleur, plus de lecture-calme grisée. Version provisoire sans personnage : garde ce nom de fichier, il sera remplacé.
- Images décoratives : alt="" et aria-hidden="true".
- docs/141 §4 : la série SceneIllustration n'est plus « à retirer ».
- Lecture du CV asynchrone (202 + job_id), étape enregistrée côté serveur, écran de maintenance uniquement sur 503 + X-Maintenance.

### PR 11. Textes
- Apostrophe typographique ’ partout, accords au singulier pour 0 et 1, noms en français (CICR, Genève), téléphone affiché espacé et copié brut, « LinkedIn » avec majuscules, « justificatif » à la place de « preuve ».

## 3. Ne pas toucher
- Notifications (téléphone et ordinateur).
- La mise en page en 2 colonnes de l'ordinateur.
- Les valeurs marquées « Choix jobA1 » dans MODIFICATIONS_8 (axe de la note, cascade, espaces verticaux).

## 4. Tests obligatoires (Playwright)
- Téléphone 390 px : outils/audit-grille.js renvoie 0 écart sur chaque écran (seuil des cibles 44 px). Écrans ajoutés le 9 novembre : EnvoyeeDetail et ses 3 feuilles, EnvoyeesStatut, Preparer, PreparerMiseEnPage, Compte, Orp, RendezVous (clair et sombre).
- Ordinateur 1024 et 1440 px : audit-grille.js en mode ordinateur (seuil des cibles 24 px) ; aucune page avec défilement interne ni horizontal (scrollWidth == clientWidth) ; action principale visible sans défiler.
- Envoyées ordinateur : trait de liaison au centre vertical de la carte sélectionnée (tolérance 1 px) ; bord gauche du statut et du premier cercle du Suivi = bord gauche du titre (tolérance 1 px).
- Feuilles et panneaux : fermeture par Échap, focus rendu au déclencheur, jamais une feuille ouverte depuis une autre.
- ORP_DEADLINE_DAY : tests unitaires pour un 5 en semaine, un 5 un samedi, un 5 un dimanche, un 5 jour férié vaudois et un 5 jour férié d’un autre canton.
- Contraste : textes et icônes en sombre ≥ 4,5:1 (texte) et ≥ 3:1 (icônes).

## 5. Décisions
1. Objectif ORP : c'est un accord entre la personne et sa conseillère, l'app ne le devine jamais. Il est saisi dans les premiers pas (« Recherches par mois », boutons − et +, de 1 à 99 (pas de plafond bas : la valeur est celle convenue avec la conseillère), départ à 10), modifiable dans Profil, et redemandé après chaque rendez-vous ORP (« Objectif de recherches »). Une seule source dans l'app : tous les écrans (accueil, Suivi ORP, Bilan, Envoyées, Préparer) lisent cette valeur. Les chiffres des maquettes ne sont que des exemples.
2. Jours fériés pour le report du 5 : ceux du canton de l'ORP de la personne (canton enregistré dans son profil, Vaud par défaut).
```
