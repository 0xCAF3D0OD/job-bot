# Prompt pour Claude Code : téléphone, version validée du 9 novembre 2026

Remplace `docs/mobile/` par le contenu de `jobA1_maquette_2026-11-08.zip` (maquettes, captures, LISEZMOI, MODIFICATIONS_8_NOVEMBRE_SOIR.md, PROMPT_CLAUDE_CODE.md, outils/). Copie `illustrations/personnage/` dans `frontend/public/personnage/` (mêmes noms ; nouveaux : les 4 bustes et `perso-05-assis`).

Lis `MODIFICATIONS_8_NOVEMBRE_SOIR.md` en entier avant d'écrire du code. Il prime sur tout le reste. La version téléphone est validée par Kevin : applique tout ce qui la concerne, sans rien improviser.

## Ordre des PR (téléphone)

1. **Lot 17** : bug de la zone de saisie (§3).
2. **Lots 11 à 16** (§4 à §9), codés directement avec les règles finales du §2.
3. **Règles transverses** (une PR, avant les écrans) :
   - §2.1 sections et cartes (D28, D29), §2.2 hiérarchie des actions (D30, D34), §2.3 statut (D31), §2.4 champs à recopier (D32), D35 cartes d'information ;
   - §2.5 mode sombre, §2.6 jetons `--action` et `--on-action` ;
   - §2.8 écrans étroits, §2.9 grille et alignement (marges de 20 px, grille de 4, cibles de 44 px, on ne réduit pas le texte), §2.10 cascade.
4. **Écrans du lot 18**, une PR par groupe, clair et sombre :
   - §10.1 détail d'une offre, carte de la note et feuille « Compatibilité », « Écarter » avec message « Annuler » ;
   - §10.2 Suivi ORP et onglet ORP de Bilan ; §10.3 Pour l'ORP ; §10.4 Compte ;
   - §10.7 feuilles du bas : Préparer le rendez-vous, Mise en page, Langue ;
   - §10.8 Alertes e-mail par famille et feuille « Alerte » ;
   - §10.9 Notifications harmonisées, textes allégés, « Tout est lu » avec le personnage assis.
5. Mot « justificatif » partout à la place de « preuve » (§9, 16.4).

L'ordinateur (§10.5, §10.6 pour les pages ordinateur) n'est **pas** dans cette série : ne le touche pas encore.

## Règles de travail

- Toutes les feuilles du bas réutilisent `BottomSheet.vue` (comme Filtres) : jamais une feuille ouverte depuis une autre ; fermeture par croix, voile, glisser, Échap et retour ; focus rendu au déclencheur.
- Chaque PR contient : la liste des points cochés, « Règles vérifiées : … », captures avant et après (clair et sombre, 390 px, et 320 px pour les écrans en liste), une entrée dans `changelog.d/`.
- **Contrôle automatique** : ajoute `outils/audit-grille.js` aux tests de bout en bout. Charge chaque écran téléphone à 390 px avec Playwright, exécute le script avec `page.evaluate`, fais échouer le test s'il renvoie un écart. Une PR n'est verte qu'avec 0 écart. Les 53 maquettes téléphone du zip renvoient 0 écart.
- Valeurs marquées « Choix jobA1 » (axe de la note, cascade, espaces verticaux) : voulues, ne les remplace pas par les valeurs par défaut de Material 3.
- Ajoute à la liste fermée de docs/141 §3 : les 4 bustes (§9, 16.3) et « Notifications, Tout est lu ». Mets à jour `personnage.test.ts`.

## Questions pour Kevin (à reprendre dans tes PR, ne tranche pas seul)

1. `ORP_DEADLINE_DAY = 5` (date limite de remise à l'ORP) à confirmer avec le texte officiel (§10.2).
2. Données de la note : critère, valeur et famille séparés ? Sinon affiche la phrase entière (§10.1).
3. Actions d'une alerte e-mail (§10.8) : proposition à valider.
4. Destinations des notifications « Semaine du 26 oct. » et « 17 nouvelles offres » (§10.9).
5. « Taille du texte » dans Réglages : suivre le téléphone ou garder un choix ? (§10.7)
6. Image de l'écran d'accueil des premiers pas (`OnboardingC`) : garde celle de la production (voir LISEZMOI).

Termine par la vérification du §11.
