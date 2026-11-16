Historique. En cas de désaccord, le LISEZMOI du 13 novembre fait foi.

# Prompt pour Claude Code : version ordinateur (9 novembre 2026)

```
Tâche : appliquer la version ordinateur validée de jobA1 (largeur > 820 px).

Sources, dans cet ordre de priorité :
1. MODIFICATIONS_9_NOVEMBRE_ORDINATEUR.md (ce lot, prime sur tout pour l'ordinateur)
2. MODIFICATIONS_8_NOVEMBRE_SOIR.md (règles D24, D28 à D35, §2.9, §2.10)
3. Les maquettes de maquettes/ (index ordinateur dans LISEZMOI.md) et leurs captures dans captures/
4. captures/commentees/ : ce qui ne va pas aujourd'hui sur app.joba1.ch, numéroté

Ne change pas la mise en page en 2 colonnes. Les feuilles du bas du téléphone deviennent des panneaux latéraux (BottomSheet.vue garde la logique, un composant SidePanel.vue l'affiche à droite au-delà de 820 px).

Ordre des PR (une par ligne, chacune avec ses tests) :
1. Composants communs : carte (bordure 1,5px #CFCBC1, rayon 18, padding 20), SidePanel, champ et zone de texte (un seul contour au focus, texte à 20 px), bouton copier 40 px, mot d'état coloré. Supprimer tout défilement interne : seule la page défile, colonne de droite sticky.
2. Préparer, Lettre et CV : page A4 toujours visible dans le modèle choisi, état "pas encore généré" avec le bouton au centre de la page, vignettes de modèle, carte "Cette lettre" (Relecture et Versions en lignes qui ouvrent un panneau), panneau Relecture, zone de saisie sticky sans "+", suppression de la puce "En allemand".
3. Préparer, Postuler : carte "Où postuler" en haut (À joindre : lettre ET CV, bouton à la largeur du contenu, "J'ai déjà postulé"), formulaire à recopier en lignes de 56 px, carte Entreprise et "Après l'envoi" à droite.
4. Candidatures : note en carte d'information + "Voir la compatibilité" (panneau), "Écarter" immédiat + snackbar "Annuler", bouton "+ Ajouter" avec panneau à 2 onglets (Une offre / Candidature spontanée), suppression du lien "Postuler spontanément" en bas de liste, état vide des filtres avec le lien vers la candidature spontanée.
5. Bilan ORP : famille "À déclarer à l'ORP" en cartes, mois en cours, panneau "Pour l'ORP" (libellé au-dessus de la valeur, "Non renseigné", "Compléter", Ouvrir Job-Room, Marquer comme déclarée), plus de débordement horizontal.
6. Alertes, Profil, Réglages : familles d'alertes et panneaux, une carte par préférence, Langue et Taille du texte en lignes + panneau, textes des notifications alignés sur le téléphone.
7. Envoyées (§8) : détail en cartes séparées à 8 px, carte d'en-tête avec statut et Suivi en 5 étapes alignés sur le titre, carte de relance avec message prêt et bouton d'envoi, colonne « Ce que tu as envoyé » / « Trouver un contact », Historique sans carte, trait de liaison qui suit la carte sélectionnée ; mise à jour du statut depuis un e-mail reconnu avec snackbar « Voir » / « Annuler ». Même PR pour le nouvel écran téléphone EnvoyeeDetail (sans avatar ni graphique de suivi, relance compacte, 3 feuilles du bas : Relance, Ce que tu as envoyé, Trouver un contact) et l'état EnvoyeesStatut.
8. Simplifications (§10) : cercles-flèches gris partout sauf notifications (même taille et position que le §2.9), Bilan « Encore 9 d’ici le 30 novembre ».
9. Mode sombre ordinateur (§12) : table de couleurs, page A4 blanche, 4 maquettes de référence ; échéance ORP « d’ici le 5 décembre » (ORP_DEADLINE_DAY = 5, report au jour ouvrable) ; scène connexion-perdue dans la coupure des premiers pas (§13). Seuil des cibles ordinateur : 24 px.
10. Textes : apostrophe ’, accords au singulier pour 0 et 1, noms en français (CICR, Genève), téléphone espacé à l'affichage, "LinkedIn" avec majuscules.

Notifications ordinateur : ne pas toucher.

Tests obligatoires (Playwright, 1024 et 1440 px) :
- l'action principale de chaque écran est visible sans défiler ;
- aucune page n'a de défilement interne ni horizontal (scrollWidth == clientWidth) ;
- outils/audit-grille.js ne remonte que des cibles de 24 px ou plus ;
- les panneaux se ferment par Échap et rendent le focus au déclencheur ;
- Envoyées : le trait de liaison est au centre vertical de la carte sélectionnée (tolérance 1 px) et le bord gauche du statut et du premier cercle du Suivi est celui du titre (tolérance 1 px).

Questions à me poser avant de coder si tu en as besoin : §3 de MODIFICATIONS_9_NOVEMBRE_ORDINATEUR.md (24 ou 44 px, maquettes sombres, ORP_DEADLINE_DAY, bande bleue d'Aujourd'hui).
```
