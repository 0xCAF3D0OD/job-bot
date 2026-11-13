# jobA1, maquette de référence (13 novembre 2026)

**Ce paquet est la seule référence.** Il remplace tous les paquets précédents de `docs/mobile/` (8, 9, 10 et 11 novembre, récapitulatif compris). Il reprend la maquette en ligne, version `1794581776-162e`.

## 1. Installation

- Remplace **entièrement** `docs/mobile/maquettes/` par le dossier `maquettes/` de ce paquet. Toute planche absente de ce paquet est supprimée du dépôt.
- Remplace le LISEZMOI de `docs/mobile/` par celui-ci.
- Les anciens fichiers `MODIFICATIONS_*.md` et `PROMPT_CLAUDE_CODE_*.md` restent comme historique. Ajoute en première ligne de chacun : « Historique. En cas de désaccord, le LISEZMOI du 13 novembre fait foi. »
- Mets `CLAUDE.md` à jour : il doit nommer ce paquet et reprendre la règle du point 2.
- PR de documentation seulement : aucun fichier de l'appli.

## 2. Qui fait foi

1. Une décision de Kevin donnée dans la conversation après le 13 novembre. Note-la dans `docs/mobile/DECISIONS.md` avec la date.
2. Les décisions du point 4 de ce fichier.
3. Le dessin des planches de ce paquet.
4. Le texte des prompts, du plus récent au plus ancien.

Si un écran ou un état n'est dessiné nulle part, ne l'invente pas : demande la maquette.

## 3. Contenu

- `maquettes/` : 150 planches `.dc.html`. Un fichier par écran. Le suffixe `Sombre` est le mode sombre, `Ordinateur` la version ordinateur, sinon c'est le téléphone (390 px).
- `captures/` : 44 PNG des écrans clés. Le suffixe `--état` désigne un état de la planche.
- `illustrations/tri/` : les personnages et la scène de fin du tri.
- `PROMPT_PR_45_A_53_TRI_ET_VISUEL.md` : le prompt du lot « Tri et nouveau visuel », corrigé (objectif de 1 à 99, planches retirées).

## 4. Décisions à jour

- **Objectif du mois** : de 1 à 99, contrôlé côté serveur et côté interface. Le message est « 99 est le maximum. » Toute mention de 30 dans un ancien fichier est fausse.
- **« Garder »** : l'offre gardée porte l'étiquette « Gardée » partout.
- **Menu du bas** : l'onglet s'appelle « Bilan ». Le titre de la page reste « Progresser ».
- **ORP** : toujours en barre, plus de cercle (Suivi ORP, Bilan, Accueil, Aujourd'hui, Envoyées).
- **Trier les offres** : livre sur ordinateur, cartes sur téléphone. Fin du tri : scène avec les personnages et le récapitulatif, pas le livre.

## 5. Planches retirées le 13 novembre et leur remplaçante

| Retirée | Remplacée par |
|---|---|
| `AccueilSmile` | `AccueilV2` |
| `AccueilSombre` | `AccueilV2Sombre` |
| `AujourdhuiOrdinateurTravailD` | `AujourdhuiOrdinateurV2` |
| `AujourdhuiOrdinateurTravailDSombre` | `AujourdhuiOrdinateurV2Sombre` |
| `Preparer` | `MaCandidatureV2` |
| `PreparerSombre` | `MaCandidatureV2Sombre` |
| `CandidatureEnvoyee` | `MaCandidatureV2`, état « fin » (ordinateur : `CandidatureEnvoyeeOrdinateur`) |
| `EnvoyeeDetailRelance` | `RelanceV2` |

Plus anciennes, déjà retirées, à supprimer aussi si elles traînent dans le dépôt : `AujourdhuiOrdinateur`, `AujourdhuiOrdinateurTravail`, `AujourdhuiOrdinateurTravailB`, `AujourdhuiOrdinateurTravailC`, `CandidaturesOrdinateur`, `RendezVousOrdinateur`, `Onboarding1`, `Onboarding2`, `Onboarding3`, `OnboardingB`, `Cercles`, `Main`, `Personnage`.

`AujourdhuiOrdinateurReposD` reste : c'est le jour de repos sur ordinateur, encore dans l'ancien visuel. Ne le redessine pas.

## 6. Ce qui n'est pas dans ce paquet

- Sept planches du lien avec Get'emAll, présentes dans la maquette en ligne et inchangées : `AutoriserGetemall`, `ConfidentialiteGetemall`, `ReglagesConnexions`, `ReglagesRetirer`, `RelierFermee`, `RelierLienInvalide`, `RelierPasTesteur`. Si elles sont dans le dépôt, garde-les telles quelles.
- États pas encore dessinés, à ne pas coder avant la maquette :
  - Assistant : attente de la réponse (avant le premier mot) ;
  - en-tête : cloche sans notification, espacement recherche, cloche, avatar ;
  - écran de fin de candidature : champ « adresse de l'entreprise » ;
  - Alertes reçues : ligne d'une alerte non reconnue.

## 7. Liste des planches

- `AccueilV2`
- `AccueilV2Sombre`
- `ActionsOffre`
- `AjouterOffreTel`
- `AlertesOrdinateur`
- `AlertesOrdinateurSite`
- `AlertesOrdinateurVide`
- `AlertesTel`
- `AlertesTelAlerte`
- `AlertesTelConfirmer`
- `Animations`
- `Assistant`
- `AssistantOrdinateur`
- `AucuneOffre`
- `AucuneOffreOrdinateur`
- `AujourdhuiOrdinateurReposD`
- `AujourdhuiOrdinateurV2`
- `AujourdhuiOrdinateurV2Sombre`
- `BarreOrpEtats`
- `BarreOrpEtatsSombre`
- `BilanOrdinateur`
- `BilanOrdinateurFiche`
- `BilanOrdinateurSombre`
- `BilanResultats`
- `CandidatureEnvoyeeOrdinateur`
- `Candidatures`
- `CandidaturesOrdinateurAjouter`
- `CandidaturesOrdinateurB`
- `CandidaturesOrdinateurBSombre`
- `CandidaturesOrdinateurSpontanee`
- `CandidaturesOrdinateurStatut`
- `CandidaturesSombre`
- `Compte`
- `CompteImage`
- `CompteSombre`
- `Connexion`
- `ConnexionOrdinateur`
- `ConnexionSombre`
- `CoordonneesOrdinateur`
- `CoordonneesOrdinateurSombre`
- `CoordonneesTel`
- `CoordonneesTelSombre`
- `Emoticones`
- `Entrainement`
- `EntrainementOrdinateur`
- `EntrainementOrdinateurSombre`
- `EntrainementSombre`
- `EnvoyeeDetail`
- `EnvoyeeDetailContacte`
- `EnvoyeeDetailContacts`
- `EnvoyeeDetailDocuments`
- `Envoyees`
- `EnvoyeesSombre`
- `EnvoyeesStatut`
- `ErreurConnexion`
- `Explorer`
- `ExtAlerte`
- `ExtAnnonce`
- `ExtAutreSite`
- `ExtNonConnecte`
- `Filtres`
- `FinDuTri`
- `FinDuTriAucune`
- `FinDuTriAucuneOrdinateur`
- `FinDuTriAucuneOrdinateurSombre`
- `FinDuTriAucuneSombre`
- `FinDuTriOrdinateur`
- `FinDuTriOrdinateurSombre`
- `FinDuTriSombre`
- `HorsLigneOrdinateur`
- `MaCandidatureV2`
- `MaCandidatureV2Sombre`
- `MaintenanceAnnoncee`
- `MaintenanceHorsLigne`
- `MaintenanceMaj`
- `MaintenanceOrdinateur`
- `MaintenanceSombre`
- `ModeSombre`
- `Notifications`
- `NotificationsOrdinateur`
- `NotificationsSombre`
- `ObjectifAtteint`
- `ObjectifAtteintOrdinateur`
- `Offre`
- `OffreCompatibilite`
- `OffreCompatibiliteSombre`
- `OffreProvisoire`
- `OffreProvisoireSombre`
- `OffreSombre`
- `OnboardingC`
- `OnboardingOrdinateur`
- `OnboardingOrdinateurCV`
- `OnboardingOrdinateurCoupure`
- `OnboardingOrdinateurEtape2`
- `OnboardingOrdinateurEtape3`
- `OnboardingOrdinateurLecture`
- `OnboardingOrdinateurProfil`
- `OnboardingOrdinateurProfilSombre`
- `OnboardingProfil`
- `OnboardingProfilSombre`
- `Orp`
- `OrpFiche`
- `OrpFicheSombre`
- `OrpRemisV2`
- `OrpRemisV2Sombre`
- `OrpSombre`
- `PageIntrouvable`
- `PageIntrouvableOrdinateur`
- `PageIntrouvableSombre`
- `PreparerMiseEnPage`
- `PreparerMiseEnPageSombre`
- `PreparerOrdinateur`
- `PreparerOrdinateurCV`
- `PreparerOrdinateurCVChangements`
- `PreparerOrdinateurCVPret`
- `PreparerOrdinateurGeneration`
- `PreparerOrdinateurLettreVide`
- `PreparerOrdinateurPostuler`
- `PreparerOrdinateurRelecture`
- `PreparerOrdinateurSombre`
- `ProfilOrdinateur`
- `ProfilOrdinateurCV`
- `ProfilOrdinateurCVSombre`
- `ProfilOrdinateurObjectif`
- `ProfilTel`
- `ProfilTelObjectif`
- `ProfilTelObjectifMax`
- `ProfilTelObjectifSombre`
- `ProfilTelSombre`
- `ProgresserSombre`
- `Reglages`
- `ReglagesLangue`
- `ReglagesOrdinateur`
- `RelanceOrdinateurV2`
- `RelanceOrdinateurV2Sombre`
- `RelanceV2`
- `RelanceV2Sombre`
- `RendezVous`
- `RendezVousFeuilleOrdinateurV2`
- `RendezVousFeuilleOrdinateurV2Sombre`
- `RendezVousFeuilleV2`
- `RendezVousFeuilleV2Sombre`
- `RendezVousPreparer`
- `RendezVousPreparerSombre`
- `RendezVousSombre`
- `Systeme`
- `TrierOffresOrdinateurV2`
- `TrierOffresOrdinateurV2Sombre`
- `TrierOffresV2`
- `TrierOffresV2Sombre`
