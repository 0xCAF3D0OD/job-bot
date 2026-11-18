# Table de correspondance planches → app

Paquet de référence : `jobA1_maquettes_2026-11-18.zip` (358 planches, titres dans `maquettes/canvas.json`). Une ligne par écran : la planche claire et, quand elle existe, sa planche *Sombre* (même écran en mode sombre). Taille de capture : 390 × 844 pour le téléphone, 1440 × 900 pour l'ordinateur.

Colonnes : **route** de l'app, **composant** Vue qui dessine l'écran, **état** à préparer (données de démo, onglet, feuille ouverte). « Audit » renvoie au rapport docs/conformite.md.

186 écrans dans l'app, 12 planches sans écran dans l'app (liste à part en bas).

| Planche | Sombre | Appareil | Titre (canvas.json) | Route | Composant | État à préparer | Audit |
|---|---|---|---|---|---|---|---|
| `AccueilV2` | `AccueilV2Sombre` | téléphone | Téléphone · Accueil (bandes, offres à trier) | `/aujourdhui` | TodayView › HomePhone | démo standard (offres à trier, ORP en cours) | à faire |
| `AccueilJustificatif` | `AccueilJustificatifSombre` | téléphone | Téléphone · Accueil, rappel justificatifs (1 fois par jour) | `/aujourdhui` | TodayView › HomePhone, OrpReminder | mois ORP précédent non remis, après le 5 (1 fois par jour) | à faire |
| `AccueilNouveau` | `AccueilNouveauSombre` | téléphone | Téléphone · Accueil, nouveau compte, premiers pas 5 étapes + Google Emplois (v = pas, alerte, ferme, masque) | `/aujourdhui` | TodayView › HomePhone, FirstStepsList | compte neuf : premiers pas ouverts, aucune offre | à faire |
| `AccueilPremiereCandidature` | `AccueilPremiereCandidatureSombre` | téléphone | Téléphone · Accueil (bandes, offres à trier) · Première candidature notée | `/aujourdhui` | TodayView › FirstApplicationCard | première candidature notée (1re offre gardée) | à faire |
| `AujourdhuiOrdinateurV2` | `AujourdhuiOrdinateurV2Sombre` | ordinateur | Ordinateur · Aujourd’hui (retard d’abord, éventail à droite) | `/aujourdhui` | TodayView (ordinateur), OfferFan | démo standard | à faire |
| `AujourdhuiOrdinateurNouveau` | `AujourdhuiOrdinateurNouveauSombre` | ordinateur | Ordinateur · Aujourd’hui, nouveau compte, premiers pas 5 étapes + Google Emplois (v = pas, alerte, ferme, masque) | `/aujourdhui` | TodayView, FirstStepsList | compte neuf : premiers pas | à faire |
| `AujourdhuiOrdinateurPremiereCandidature` | `AujourdhuiOrdinateurPremiereCandidatureSombre` | ordinateur | Ordinateur · Aujourd’hui (retard d’abord, éventail à droite) · Première candidature notée | `/aujourdhui` | TodayView, FirstApplicationCard | première candidature notée | à faire |
| `BarreOrpEtats` | `BarreOrpEtatsSombre` | téléphone | Téléphone · Barre ORP, les états | `/aujourdhui (bande ORP)` | OrpBar | chaque état de la barre (en cours, à remettre, en retard, atteint) | à faire |
| `ObjectifAtteint` | — | téléphone | Téléphone · Objectif ORP atteint | `/candidatures/offres/:id/preparer (fin)` | GoalReached | envoyer la candidature qui atteint l'objectif ORP | à faire |
| `ObjectifAtteintOrdinateur` | — | ordinateur | Ordinateur · Objectif ORP atteint | `/candidatures/offres/:id/preparer (fin)` | GoalReached | idem, ordinateur | à faire |
| `TrierOffresV2` | `TrierOffresV2Sombre` | téléphone | Téléphone · Trier les offres, cartes (états e = carte, garde, longue) | `/candidatures/trier` | TriageView | offres à trier (démo : 5) | à faire |
| `TrierOffresCurseurDroite` | `TrierOffresCurseurDroiteSombre` | téléphone | Téléphone · Trier, curseur glissé à droite (Garder) | `/candidatures/trier` | TriageView | carte glissée à droite (geste en cours) | à faire |
| `TrierOffresCurseurGauche` | `TrierOffresCurseurGaucheSombre` | téléphone | Téléphone · Trier, curseur glissé à gauche (Écarter) | `/candidatures/trier` | TriageView | carte glissée à gauche (geste en cours) | à faire |
| `TrierOffresOrdinateurV2` | `TrierOffresOrdinateurV2Sombre` | ordinateur | Ordinateur · Trier les offres, éventail (e = ferme, etale, dos) | `/candidatures/trier` | TriageView › OfferFan | 3 offres ou plus | à faire |
| `TrierOffresOrdinateurV2Deux` | `TrierOffresOrdinateurV2DeuxSombre` | ordinateur | Ordinateur · Trier, 2 offres (e = ferme, etale, dos) | `/candidatures/trier` | TriageView › OfferFan | 2 offres à trier | à faire |
| `TrierOffresOrdinateurV2Une` | `TrierOffresOrdinateurV2UneSombre` | ordinateur | Ordinateur · Trier, 1 offre (e = ferme, etale, dos) | `/candidatures/trier` | TriageView › OfferFan | 1 offre à trier | à faire |
| `TrierRien` | `TrierRienSombre` | téléphone | Téléphone · Trier, rien à trier pour l’instant | `/candidatures/trier` | TriageView › TriageNone | aucune offre à trier | à faire |
| `TrierOrdinateurRien` | `TrierOrdinateurRienSombre` | ordinateur | Ordinateur · Trier, rien à trier pour l’instant | `/candidatures/trier` | TriageView › TriageNone | aucune offre à trier | à faire |
| `FinDuTri` | `FinDuTriSombre` | téléphone | Téléphone · Fin du tri (scène) | `/candidatures/trier` | TriageView › TriageDone | dernière offre triée, au moins une gardée | à faire |
| `FinDuTriAucune` | `FinDuTriAucuneSombre` | téléphone | Téléphone · Fin du tri, aucune offre gardée | `/candidatures/trier` | TriageView › TriageDone | dernière offre triée, aucune gardée | à faire |
| `FinDuTriOrdinateur` | `FinDuTriOrdinateurSombre` | ordinateur | Ordinateur · Fin du tri (scène) | `/candidatures/trier` | TriageView › TriageDone | idem, ordinateur | à faire |
| `FinDuTriAucuneOrdinateur` | `FinDuTriAucuneOrdinateurSombre` | ordinateur | Ordinateur · Fin du tri, aucune offre gardée | `/candidatures/trier` | TriageView › TriageDone | idem, aucune gardée | à faire |
| `Candidatures` | `CandidaturesSombre` | téléphone | Téléphone · Candidatures, à traiter | `/candidatures/offres` | JobsView › OffersView, OfferCard | démo standard | audité (Candidatures) |
| `CandidaturesAgence` | `CandidaturesAgenceSombre` | téléphone | Téléphone · Candidatures, pastille Agence | `/candidatures/offres` | OffersView › OfferCard | une offre d'agence de placement (absente de la démo) | à capturer : état absent de la démo |
| `CandidaturesGlisser` | `CandidaturesGlisserSombre` | téléphone | Téléphone · Offres, glisser une carte pour l’écarter | `/candidatures/offres` | OffersView › OfferCard | carte glissée vers la gauche (geste en cours) | à capturer : état absent de la démo |
| `CandidaturesVide` | `CandidaturesVideSombre` | téléphone | Téléphone · Candidatures vides, aucune alerte (premier passage) | `/candidatures/offres` | OffersView (offers-none-yet) | compte sans offre ni alerte | à capturer : état absent de la démo |
| `CandidaturesVideAlertes` | `CandidaturesVideAlertesSombre` | téléphone | Téléphone · Candidatures vides, alertes prêtes | `/candidatures/offres` | OffersView (offers-none-alerts) | compte sans offre, alertes créées | à capturer : état absent de la démo |
| `Filtres` | `FiltresSombre` | téléphone | Téléphone · Filtres (feuille du bas) | `/candidatures/offres` | OfferFilterSheet | feuille Filtres ouverte (bouton réglages de l'en-tête) | audité (Candidatures) |
| `AjouterOffreTel` | — | téléphone | Téléphone · Ajouter une offre | `/candidatures/offres` | ManualOfferForm (feuille) | bouton + à côté de la recherche | audité (Candidatures) |
| `AucuneOffre` | — | téléphone | Téléphone · Aucune offre | `/candidatures/offres` | OffersView (offers-empty) | filtres qui ne laissent aucune offre | à faire |
| `AucuneOffreOrdinateur` | — | ordinateur | Ordinateur · Aucune offre | `/candidatures/offres` | OffersView (offers-empty) | idem, ordinateur | à faire |
| `CandidaturesOrdinateurB` | `CandidaturesOrdinateurBSombre` | ordinateur | Ordinateur · Candidatures (à traiter, envoyées, rendez-vous) | `/candidatures/offres/:id` | OffersView › OfferDetail (colonne) | une offre en préparation ouverte | audité (Candidatures) |
| `CandidaturesOrdinateurAucuneOuverte` | `CandidaturesOrdinateurAucuneOuverteSombre` | ordinateur | Ordinateur · Offres, aucune offre ouverte | `/candidatures/offres` | OffersView | aucune offre ouverte | audité (Candidatures) |
| `CandidaturesOrdinateurAgence` | `CandidaturesOrdinateurAgenceSombre` | ordinateur | Ordinateur · Offre d’une agence de placement | `/candidatures/offres/:id` | OfferDetail › AgencyNote | offre d'agence ouverte (absente de la démo) | à capturer : état absent de la démo |
| `CandidaturesOrdinateurEcartee` | `CandidaturesOrdinateurEcarteeSombre` | ordinateur | Ordinateur · Offre écartée, sans note | `/candidatures/offres/:id` | OfferDetail | offre écartée par les filtres, sans note | à faire |
| `CandidaturesOrdinateurAjouter` | — | ordinateur | Ordinateur · Ajouter une offre (panneau) | `/candidatures/offres` | JobsView › ManualOfferForm (panneau) | « + Ajouter » de l'en-tête | audité (Candidatures) |
| `CandidaturesOrdinateurSpontanee` | — | ordinateur | Ordinateur · Candidature spontanée (panneau) | `/candidatures/offres` | SpontaneousForm (panneau) | « + Ajouter » › Candidature spontanée | audité (Candidatures) |
| `CandidaturesOrdinateurVide` | `CandidaturesOrdinateurVideSombre` | ordinateur | Ordinateur · Candidatures vides, aucune alerte (premier passage) | `/candidatures/offres` | OffersView (offers-none-yet) | compte sans offre ni alerte | à capturer : état absent de la démo |
| `CandidaturesOrdinateurVideAlertes` | `CandidaturesOrdinateurVideAlertesSombre` | ordinateur | Ordinateur · Candidatures vides, alertes prêtes | `/candidatures/offres` | OffersView (offers-none-alerts) | compte sans offre, alertes créées | à capturer : état absent de la démo |
| `Offre` | `OffreSombre` | téléphone | Téléphone · Détail d'une offre | `/candidatures/offres/:id` | OfferDetail (sous-page) | offre notée, à traiter | à faire |
| `OffreAgence` | `OffreAgenceSombre` | téléphone | Téléphone · Offre d’une agence de placement | `/candidatures/offres/:id` | OfferDetail › AgencyNote | offre d'agence (absente de la démo) | à faire |
| `OffreCompatibilite` | `OffreCompatibiliteSombre` | téléphone | Téléphone · Compatibilité (feuille) | `/candidatures/offres/:id` | OfferCompatSheet | « Voir la compatibilité » ouvert | à faire |
| `OffreEcartee` | `OffreEcarteeSombre` | téléphone | Téléphone · Offre écartée, sans note | `/candidatures/offres/:id` | OfferDetail | offre écartée, sans note | à faire |
| `OffreExpiree` | `OffreExpireeSombre` | téléphone | Téléphone · Offre signalée expirée | `/candidatures/offres/:id` | OfferDetail (offers-expired) | offre signalée expirée (absente de la démo) | à faire |
| `OffreNonNotee` | `OffreNonNoteeSombre` | téléphone | Téléphone · Offre pas encore notée (Noter maintenant) | `/candidatures/offres/:id` | OfferDetail | offre pas encore notée (démo : 37) | à faire |
| `OffreProvisoire` | `OffreProvisoireSombre` | téléphone | Téléphone · Offre provisoire (lire ou coller l'annonce) | `/candidatures/offres/:id` | OfferDetail › OfferTextNotice | annonce illisible, note provisoire | à faire |
| `OffreAdresseRecherche` | `OffreAdresseRechercheSombre` | téléphone | Téléphone · Adresse de l'entreprise : recherche | `/candidatures/offres/:id` | OfferDetail (company-section) | recherche d'adresse en cours | à faire |
| `OffreAdresseTrouvee` | `OffreAdresseTrouveeSombre` | téléphone | Téléphone · Adresse de l'entreprise : trouvée | `/candidatures/offres/:id` | OfferDetail (company-section) | adresse trouvée au registre | à faire |
| `OffreAdresseNonTrouvee` | `OffreAdresseNonTrouveeSombre` | téléphone | Téléphone · Adresse de l'entreprise : pas trouvée | `/candidatures/offres/:id` | OfferDetail (company-section) | adresse pas trouvée | à faire |
| `ActionsOffre` | `ActionsOffreSombre` | téléphone | Téléphone · Actions sur une offre | `/candidatures/offres/:id` | OfferActionSheet | menu ⋯ d'une offre à traiter | à faire |
| `ActionsOffreGardee` | `ActionsOffreGardeeSombre` | téléphone | Téléphone · Actions sur une offre gardée | `/candidatures/offres/:id` | OfferActionSheet | menu ⋯ d'une offre gardée | à faire |
| `Envoyees` | `EnvoyeesSombre` | téléphone | Téléphone · Candidatures, envoyées | `/candidatures/suivi` | ApplicationsView › SentCard | démo standard | audité (Candidatures) |
| `EnvoyeesStatut` | — | téléphone | Téléphone · Envoyées, statut mis à jour par e-mail | `/candidatures/suivi` | ApplicationsView › UndoToast | statut changé par un e-mail reçu (toast) | à capturer : état absent de la démo |
| `EnvoyeesVide` | `EnvoyeesVideSombre` | téléphone | Téléphone · Envoyées, aucune candidature | `/candidatures/suivi` | ApplicationsView (sent-none) | aucune candidature envoyée | audité (Candidatures) |
| `FiltresEnvoyees` | — | téléphone | Téléphone · Filtres des envoyées (feuille du bas) | `/candidatures/suivi` | SentPhoneFilters | feuille Filtres ouverte | audité (Candidatures) |
| `EnvoyeesOrdinateurAucuneOuverte` | `EnvoyeesOrdinateurAucuneOuverteSombre` | ordinateur | Ordinateur · Envoyées, aucune candidature ouverte | `/candidatures/suivi` | ApplicationsView › SentRows | aucune candidature ouverte | audité (Candidatures) |
| `EnvoyeesOrdinateurVide` | `EnvoyeesOrdinateurVideSombre` | ordinateur | Ordinateur · Envoyées, aucune candidature | `/candidatures/suivi` | ApplicationsView (sent-none) | aucune candidature envoyée | audité (Candidatures) |
| `CandidaturesOrdinateurEpinglee` | `CandidaturesOrdinateurEpingleeSombre` | ordinateur | Ordinateur · Candidatures, carte choisie épinglée (liste défilée) | `/candidatures/suivi?candidature=:id` | SentRows (carte épinglée), SentDetail | une candidature ouverte, liste défilée | audité (Candidatures) |
| `CandidaturesOrdinateurStatut` | — | ordinateur | Ordinateur · Envoyées, statut mis à jour par e-mail | `/candidatures/suivi` | ApplicationsView › UndoToast | statut changé par un e-mail reçu (toast) | à capturer : état absent de la démo |
| `EnvoyeeDetail` | `EnvoyeeDetailSombre` | téléphone | Téléphone · Détail d’une candidature envoyée | `/candidatures/suivi?candidature=:id` | SentDetail | candidature sans réponse, relance conseillée | audité (Candidatures) |
| `EnvoyeeDetailDocuments` | — | téléphone | Téléphone · Détail envoyée, feuille Ce que tu as envoyé | `/candidatures/suivi?candidature=:id` | SentDetail (sent-docs-sheet) | « Ce que tu as envoyé » ouvert | audité (Candidatures) |
| `EnvoyeeDetailContacts` | — | téléphone | Téléphone · Détail envoyée, feuille Trouver un contact | `/candidatures/suivi?candidature=:id` | SentDetail (sent-find-sheet) | « Trouver un contact » ouvert | audité (Candidatures) |
| `EnvoyeeDetailContacte` | — | téléphone | Téléphone · Envoyée, j’ai contacté quelqu’un | `/candidatures/suivi?candidature=:id` | SentDetail › ContactQuickForm | « J'ai contacté quelqu'un » ouvert | audité (Candidatures) |
| `RelanceV2` | `RelanceV2Sombre` | téléphone | Téléphone · Relance | `/candidatures/relances` | FollowUpsView | une relance à envoyer | à faire |
| `RelanceOrdinateurV2` | `RelanceOrdinateurV2Sombre` | ordinateur | Ordinateur · Relance (volet) | `/candidatures/suivi?candidature=:id` | FollowUpPanel (volet) | « Voir et envoyer » la relance | à faire |
| `RendezVous` | `RendezVousSombre` | téléphone | Téléphone · Candidatures, rendez-vous | `/candidatures/rendez-vous-orp` | OrpMeetingView › RendezVousPhone | démo standard | audité (Candidatures) |
| `RendezVousVide` | `RendezVousVideSombre` | téléphone | Téléphone · Rendez-vous, aucun | `/candidatures/rendez-vous-orp` | RendezVousPhone (rdv-none-yet) | aucun rendez-vous | audité (Candidatures) |
| `RendezVousPreparer` | `RendezVousPreparerSombre` | téléphone | Téléphone · Préparer le rendez-vous (feuille) | `/candidatures/rendez-vous-orp` | MeetingPrepSheet | carte du rendez-vous ORP › préparer | audité (Candidatures) |
| `RendezVousFeuilleV2` | `RendezVousFeuilleV2Sombre` | téléphone | Téléphone · Veille de rendez-vous | `/candidatures/rendez-vous-orp` | RendezVousPhone (veille) | rendez-vous ORP le lendemain (absent de la démo : dans 6 jours) | à capturer : état absent de la démo |
| `RendezVousOrdinateurAucunOuvert` | `RendezVousOrdinateurAucunOuvertSombre` | ordinateur | Ordinateur · Rendez-vous, aucun rendez-vous ouvert | `/candidatures/rendez-vous-orp` | RendezVousDesktop | aucun rendez-vous ouvert | audité (Candidatures) |
| `RendezVousOrdinateurVide` | `RendezVousOrdinateurVideSombre` | ordinateur | Ordinateur · Rendez-vous, aucun | `/candidatures/rendez-vous-orp` | RendezVousDesktop (rdv-none-yet) | aucun rendez-vous | audité (Candidatures) |
| `RendezVousFeuilleOrdinateurV2` | `RendezVousFeuilleOrdinateurV2Sombre` | ordinateur | Ordinateur · Veille de rendez-vous (volet) | `/aujourdhui` | TodayView › volet rendez-vous | rendez-vous ORP le lendemain, « Préparer » de À faire | à capturer : état absent de la démo |
| `MaCandidatureV2` | `MaCandidatureV2Sombre` | téléphone | Téléphone · Ma candidature (états e = lettre, attente, email, formulaire, fin, finpreuve) | `/candidatures/offres/:id/preparer` | PreparationView | états lettre, attente, e-mail, formulaire, fin | à faire |
| `MaCandidatureCV` | `MaCandidatureCVSombre` | téléphone | Téléphone · Ma candidature, CV, changements visibles | `/candidatures/offres/:id/preparer` | PreparationView › CvPanel | onglet CV, changements visibles | à faire |
| `MaCandidatureCVPourquoi` | `MaCandidatureCVPourquoiSombre` | téléphone | Téléphone · Ma candidature, CV, pourquoi (feuille) | `/candidatures/offres/:id/preparer` | CvPanel (feuille Pourquoi) | toucher un changement | à faire |
| `MaCandidatureCVRecherche` | `MaCandidatureCVRechercheSombre` | téléphone | Téléphone · Ma candidature, CV, recherche | `/candidatures/offres/:id/preparer` | CvPanel › DocSearch | recherche dans le CV | à faire |
| `PreparerMiseEnPage` | `PreparerMiseEnPageSombre` | téléphone | Téléphone · Mise en page (feuille) | `/candidatures/offres/:id/preparer` | LayoutSheetLink › TemplatePicker | « Changer » la mise en page | à faire |
| `PreparerOrdinateur` | `PreparerOrdinateurSombre` | ordinateur | Ordinateur · Préparer ma candidature | `/candidatures/offres/:id/preparer` | PreparationView | lettre prête | à faire |
| `PreparerOrdinateurGeneration` | `PreparerOrdinateurGenerationSombre` | ordinateur | Ordinateur · Préparer, lettre et CV en cours d’écriture | `/candidatures/offres/:id/preparer` | PreparationView › AiWriting | lettre et CV en cours d'écriture | à faire |
| `PreparerOrdinateurLettreVide` | `PreparerOrdinateurLettreVideSombre` | ordinateur | Ordinateur · Préparer, la lettre n’a pas pu être écrite | `/candidatures/offres/:id/preparer` | AiWritingLetter | échec de la lettre | à faire |
| `PreparerOrdinateurCV` | `PreparerOrdinateurCVSombre` | ordinateur | Ordinateur · Préparer, le CV adapté n’a pas pu être préparé | `/candidatures/offres/:id/preparer` | CvPanel | échec du CV adapté | à faire |
| `PreparerOrdinateurCVPret` | `PreparerOrdinateurCVPretSombre` | ordinateur | Ordinateur · Préparer, CV prêt | `/candidatures/offres/:id/preparer` | CvPanel | CV prêt | à faire |
| `PreparerOrdinateurCVChangements` | `PreparerOrdinateurCVChangementsSombre` | ordinateur | Ordinateur · Préparer, CV : Adapté pour cette offre | `/candidatures/offres/:id/preparer` | CvPanel | CV adapté pour cette offre | à faire |
| `PreparerOrdinateurCVChangementsVus` | `PreparerOrdinateurCVChangementsVusSombre` | ordinateur | Ordinateur · CV, voir les changements | `/candidatures/offres/:id/preparer` | CvPanel | « Voir les changements » | à faire |
| `PreparerOrdinateurCVRecherche` | `PreparerOrdinateurCVRechercheSombre` | ordinateur | Ordinateur · CV, chercher dans le document | `/candidatures/offres/:id/preparer` | CvPanel › DocSearch | recherche dans le CV | à faire |
| `PreparerOrdinateurRelecture` | `PreparerOrdinateurRelectureSombre` | ordinateur | Ordinateur · Préparer, détail de la relecture (panneau) | `/candidatures/offres/:id/preparer` | PreparationView (panneau relecture) | détail de la relecture | à faire |
| `PreparerOrdinateurPostuler` | `PreparerOrdinateurPostulerSombre` | ordinateur | Ordinateur · Préparer, postuler | `/candidatures/offres/:id/preparer` | PreparationView › ApplyActions | étape Postuler | à faire |
| `CandidatureEnvoyeeOrdinateur` | — | ordinateur | Ordinateur · Candidature envoyée | `/candidatures/offres/:id/preparer` | ApplicationSent | candidature envoyée | à faire |
| `ChargementLettre` | `ChargementLettreSombre` | téléphone | Téléphone · Écriture de la lettre en cours | `/candidatures/offres/:id/preparer` | AiWriting / TroupeLoader | lettre en cours d'écriture | à faire |
| `BilanAccueil` | `BilanAccueilSombre` | téléphone | Téléphone · Bilan (feuilles ORP, Résultats, Formations) | `/bilan` | BilanView › BilanPhoneHome | démo standard | à faire |
| `BilanChargement` | `BilanChargementSombre` | téléphone | Téléphone · Bilan, chargement | `/bilan` | BilanView › LoadingBlocks | chargement | à faire |
| `BilanErreur` | `BilanErreurSombre` | téléphone | Téléphone · Bilan, indisponible | `/bilan` | BilanView (erreur) | API indisponible | à faire |
| `BilanResultats` | — | téléphone | Téléphone · Bilan, résultats | `/bilan/resultats` | InsightsView | démo standard | à faire |
| `BilanTropTot` | `BilanTropTotSombre` | téléphone | Téléphone · Bilan, trop tôt pour conclure | `/bilan/resultats` | InsightsView | trop peu de candidatures | à faire |
| `BilanFormations` | `BilanFormationsSombre` | téléphone | Téléphone · Bilan, formations | `/bilan/formations` | TrainingsView | démo standard | à faire |
| `BilanFormationsVide` | `BilanFormationsVideSombre` | téléphone | Téléphone · Bilan, aucune formation | `/bilan/formations` | TrainingsView | aucune formation | à faire |
| `BilanCatalogue` | `BilanCatalogueSombre` | téléphone | Téléphone · Bilan, catalogue des formations | `/bilan/formations` | TrainingsView (catalogue) | « Chercher d'autres formations » | à faire |
| `Orp` | `OrpSombre` | téléphone | Téléphone · Bilan, onglet ORP | `/bilan` | BilanOrpView | onglet ORP | à faire |
| `OrpMois` | `OrpMoisSombre` | téléphone | Téléphone · Bilan ORP, mois déplié | `/bilan` | BilanOrpView › OrpMonth | mois déplié | à faire |
| `OrpMoisPrecedents` | `OrpMoisPrecedentsSombre` | téléphone | Téléphone · Bilan ORP, mois précédents (feuille) | `/bilan` | BilanOrpView (feuille) | « Mois précédents » | à faire |
| `OrpExports` | `OrpExportsSombre` | téléphone | Téléphone · Bilan ORP, autres exports (feuille) | `/bilan` | BilanOrpView (feuille) | « Autres exports » | à faire |
| `OrpRemisV2` | `OrpRemisV2Sombre` | téléphone | Téléphone · ORP, justificatifs remis | `/bilan` | BilanOrpView | justificatifs remis | à faire |
| `OrpFiche` | `OrpFicheSombre` | téléphone | Téléphone · Pour l’ORP (une candidature) | `/bilan/orp/candidature/:id` | OrpFicheView › OrpFiche | une candidature | à faire |
| `FeuilleNom` | `FeuilleNomSombre` | téléphone | Téléphone · Ton nom sur la feuille (enregistré) | `/bilan (feuille ORP)` | OrpSheet / ProfileEditSheet | nom sur la feuille enregistré | à faire |
| `BilanOrdinateur` | `BilanOrdinateurSombre` | ordinateur | Ordinateur · Bilan (ORP, résultats, formations) | `/bilan` | BilanView (ordinateur) | démo standard | à faire |
| `BilanOrdinateurChargement` | `BilanOrdinateurChargementSombre` | ordinateur | Ordinateur · Bilan, chargement | `/bilan` | BilanView › LoadingBlocks | chargement | à faire |
| `BilanOrdinateurErreur` | `BilanOrdinateurErreurSombre` | ordinateur | Ordinateur · Bilan, indisponible | `/bilan` | BilanView (erreur) | API indisponible | à faire |
| `BilanOrdinateurExports` | `BilanOrdinateurExportsSombre` | ordinateur | Ordinateur · Bilan, menu Autres exports | `/bilan` | BilanOrpView (menu) | « Autres exports » | à faire |
| `BilanOrdinateurFiche` | `BilanOrdinateurFicheSombre` | ordinateur | Ordinateur · Pour l’ORP (panneau) | `/bilan` | OrpFiche (panneau) | « Pour l'ORP » d'une candidature | à faire |
| `BilanOrdinateurFormEtats` | `BilanOrdinateurFormEtatsSombre` | ordinateur | Ordinateur · Bilan, formation en texte libre et terminée | `/bilan/formations` | TrainingsView | formation en texte libre et terminée | à faire |
| `BilanOrdinateurFormVide` | `BilanOrdinateurFormVideSombre` | ordinateur | Ordinateur · Bilan, aucune formation | `/bilan/formations` | TrainingsView | aucune formation | à faire |
| `BilanOrdinateurCatalogue` | `BilanOrdinateurCatalogueSombre` | ordinateur | Ordinateur · Bilan, catalogue des formations | `/bilan/formations` | TrainingsView (catalogue) | catalogue | à faire |
| `BilanOrdinateurMois` | `BilanOrdinateurMoisSombre` | ordinateur | Ordinateur · Bilan, mois déplié | `/bilan` | BilanOrpView › OrpMonth | mois déplié | à faire |
| `BilanOrdinateurMoisPrecedents` | `BilanOrdinateurMoisPrecedentsSombre` | ordinateur | Ordinateur · Bilan, menu Mois précédents | `/bilan` | BilanOrpView (menu) | « Mois précédents » | à faire |
| `BilanOrdinateurTropTot` | `BilanOrdinateurTropTotSombre` | ordinateur | Ordinateur · Bilan, trop tôt pour conclure | `/bilan/resultats` | InsightsView | trop tôt pour conclure | à faire |
| `AlertesTel` | `AlertesTelSombre` | téléphone | Téléphone · Alertes e-mail | `/candidatures/alertes` | AlertsView › AlertsPhoneList | démo standard | à faire |
| `AlertesTelAlerte` | `AlertesTelAlerteSombre` | téléphone | Téléphone · Alerte active (feuille) | `/candidatures/alertes` | AlertsPhoneList (feuille) | une alerte active ouverte | à faire |
| `AlertesTelConfirmer` | `AlertesTelConfirmerSombre` | téléphone | Téléphone · Alerte à confirmer (feuille) | `/candidatures/alertes` | AlertsPhoneList (feuille) | une alerte à confirmer | à faire |
| `AlertesTelNePlusSuivre` | `AlertesTelNePlusSuivreSombre` | téléphone | Téléphone · Alertes · Ne plus suivre (toast) | `/candidatures/alertes` | AlertsPhoneList › UndoToast | « Ne plus suivre » | à faire |
| `AlertesOrdinateur` | `AlertesOrdinateurSombre` | ordinateur | Ordinateur · Mes alertes e-mail | `/candidatures/alertes` | AlertsView › AlertsPanel | démo standard | à faire |
| `AlertesOrdinateurRecherche` | `AlertesOrdinateurRechercheSombre` | ordinateur | Ordinateur · Alertes, modifier « Ta recherche » | `/candidatures/alertes` | AlertsSearchPanel | modifier « Ta recherche » | à faire |
| `AlertesOrdinateurSite` | `AlertesOrdinateurSiteSombre` | ordinateur | Ordinateur · Alertes, créer une alerte (panneau) | `/candidatures/alertes` | AlertsWizard (panneau) | créer une alerte | à faire |
| `AlertesOrdinateurVide` | `AlertesOrdinateurVideSombre` | ordinateur | Ordinateur · Alertes e-mail, nouveau compte | `/candidatures/alertes` | AlertsDeskStart | compte sans alerte | à faire |
| `Assistant` | `AssistantSombre` | téléphone | Téléphone · Assistant | `/assistant` | AssistantPanel | assistant disponible (clé IA) | à faire |
| `AssistantOrdinateur` | — | ordinateur | Ordinateur · Assistant (panneau) | `toutes les pages (bouton Assistant)` | AssistantPanel (panneau) | assistant ouvert | à faire |
| `Notifications` | `NotificationsSombre` | téléphone | Téléphone · Notifications | `/notifications` | NotificationsView | démo standard | à faire |
| `NotificationsOrdinateur` | — | ordinateur | Ordinateur · Toutes les notifications | `/notifications` | NotificationsView | démo standard | à faire |
| `NotificationsOrdinateurVide` | — | ordinateur | Ordinateur · Notifications, tout est lu | `/notifications` | NotificationsView | tout est lu | à faire |
| `Compte` | `CompteSombre` | téléphone | Téléphone · Compte | `/compte` | AccountView | démo standard | à faire |
| `CompteImage` | — | téléphone | Téléphone · Compte, choisir son image | `/compte` | AvatarPicker | choisir son image | à faire |
| `ProfilTel` | `ProfilTelSombre` | téléphone | Téléphone · Mon profil, CV à relire (états) | `/profil` | ProfileView | CV à relire (états) | à faire |
| `ProfilTelObjectif` | `ProfilTelObjectifSombre` | téléphone | Téléphone · Profil, objectif du mois | `/profil` | ProfileView (objectif) | objectif du mois | à faire |
| `ProfilTelObjectifMax` | `ProfilTelObjectifMaxSombre` | téléphone | Téléphone · Profil, objectif au maximum | `/profil` | ProfileView (objectif) | objectif au maximum | à faire |
| `ProfilOrdinateur` | `ProfilOrdinateurSombre` | ordinateur | Ordinateur · Mon profil et mon CV | `/profil` | ProfileView › ProfileDesktop | démo standard | à faire |
| `ProfilOrdinateurCV` | `ProfilOrdinateurCVSombre` | ordinateur | Ordinateur · Profil, CV à relire (états) | `/profil` | ProfileDesktop › CvStateBlock | CV à relire | à faire |
| `ProfilOrdinateurObjectif` | `ProfilOrdinateurObjectifSombre` | ordinateur | Ordinateur · Profil, objectif du mois (volet) | `/profil` | ProfileDesktop (volet) | objectif du mois | à faire |
| `Reglages` | `ReglagesSombre` | téléphone | Téléphone · Réglages (notifications, extension, état du service) | `/reglages (téléphone : /compte › Réglages)` | SettingsView | démo standard | à faire |
| `ReglagesLangue` | `ReglagesLangueSombre` | téléphone | Téléphone · Réglages, langue (7 langues) | `/reglages` | LanguagePanel | langue (7 langues) | à faire |
| `ReglagesOutils` | `ReglagesOutilsSombre` | téléphone | Téléphone · Réglages › Recherche et outils | `/reglages` | SettingsView (Recherche et outils) | rubrique ouverte | à faire |
| `ReglagesRythme` | `ReglagesRythmeSombre` | téléphone | Téléphone · Réglages › Rythme | `/reglages` | SettingsView (Rythme) | rubrique ouverte | à faire |
| `ReglagesRythmePause` | `ReglagesRythmePauseSombre` | téléphone | Téléphone · Réglages › Rythme : pause (une seule plage) | `/reglages` | SettingsView (Rythme) | pause en cours | à faire |
| `ReglagesOrdinateur` | `ReglagesOrdinateurSombre` | ordinateur | Ordinateur · Réglages | `/reglages` | SettingsView | démo standard | à faire |
| `ReglagesOrdinateurComplet` | `ReglagesOrdinateurCompletSombre` | ordinateur | Ordinateur · Réglages, page complète | `/reglages` | SettingsView | page complète défilée | à faire |
| `ReglagesConnexions` | `ReglagesConnexionsSombre` | téléphone | Get'emAll · 2. Réglages, connexions | `/reglages` | ConnectionsPanel / GetemallPanel | Get'emAll relié | à faire |
| `ReglagesRetirer` | `ReglagesRetirerSombre` | téléphone | Get'emAll · 3. Retirer l'accès | `/reglages` | GetemallPanel | retirer l'accès | à faire |
| `CoordonneesTel` | `CoordonneesTelSombre` | téléphone | Téléphone · Coordonnées reprises du CV | `/bienvenue ou /profil` | IdentityForm | coordonnées reprises du CV | à faire |
| `CoordonneesOrdinateur` | `CoordonneesOrdinateurSombre` | ordinateur | Ordinateur · Coordonnées reprises du CV | `/bienvenue ou /profil` | IdentityForm | coordonnées reprises du CV | à faire |
| `Entrainement` | `EntrainementSombre` | téléphone | Téléphone · S’entraîner à l’entretien | `/entrainement` | PracticeView | démo standard | à faire |
| `EntrainementOrdinateur` | `EntrainementOrdinateurSombre` | ordinateur | Ordinateur · S’entraîner à l’entretien | `/entrainement` | PracticeView | démo standard | à faire |
| `Connexion` | `ConnexionSombre` | téléphone | Téléphone · Connexion | `/connexion` | LoginView | déconnecté | à faire |
| `ConnexionOrdinateur` | — | ordinateur | Ordinateur · Connexion | `/connexion` | LoginView › AuthSplit | déconnecté | à faire |
| `PageIntrouvable` | `PageIntrouvableSombre` | téléphone | Téléphone · Page introuvable | `/une-adresse-inconnue` | NotFoundView | — | à faire |
| `PageIntrouvableOrdinateur` | — | ordinateur | Ordinateur · Page introuvable | `/une-adresse-inconnue` | NotFoundView | — | à faire |
| `MaintenanceAnnoncee` | — | téléphone | Téléphone · Maintenance annoncée | `toutes les pages` | MaintenanceOverlay | maintenance annoncée (jobbot maintenance on) | à faire |
| `MaintenanceMaj` | — | téléphone | Téléphone · Maintenance, mise à jour | `toutes les pages` | MaintenanceOverlay | mise à jour en cours | à faire |
| `MaintenanceHorsLigne` | — | téléphone | Téléphone · Pas de connexion | `toutes les pages` | NetworkError | réseau coupé | à faire |
| `MaintenanceSombre` | — | téléphone | Sombre · Maintenance | `toutes les pages` | MaintenanceOverlay | maintenance, mode sombre | à faire |
| `MaintenanceOrdinateur` | — | ordinateur | Ordinateur · Maintenance | `toutes les pages` | MaintenanceOverlay | maintenance | à faire |
| `HorsLigneOrdinateur` | — | ordinateur | Ordinateur · Pas de connexion | `toutes les pages` | NetworkError | réseau coupé | à faire |
| `ChargementCV` | `ChargementCVSombre` | téléphone | Téléphone · Lecture du CV en cours | `/bienvenue` | WelcomeView › TroupeLoader | lecture du CV en cours | à faire |
| `ChargementLancement` | `ChargementLancementSombre` | téléphone | Téléphone · Lancement (logo animé) | `premier chargement` | index.html (logo animé) | ouverture de l'app | à faire |
| `PremiersPas1Postes` | `PremiersPas1PostesSombre` | téléphone | Téléphone · Premiers pas, question 1 sur 6 : postes recherchés | `/bienvenue` | WelcomeView › WelcomeQuestions | question 1 sur 6 | à faire |
| `PremiersPas1PostesSansCV` | `PremiersPas1PostesSansCVSombre` | téléphone | Téléphone · Premiers pas · Postes (CV pas lu) | `/bienvenue` | WelcomeView › WelcomeQuestions | question 1 sur 6 | à faire |
| `PremiersPas2Lieu` | `PremiersPas2LieuSombre` | téléphone | Téléphone · Premiers pas, question 2 sur 6 : lieu | `/bienvenue` | WelcomeView › WelcomeQuestions | question 2 sur 6 | à faire |
| `PremiersPas3Taux` | `PremiersPas3TauxSombre` | téléphone | Téléphone · Premiers pas, question 3 sur 6 : taux d’activité | `/bienvenue` | WelcomeView › WelcomeQuestions | question 3 sur 6 | à faire |
| `PremiersPas4Orp` | `PremiersPas4OrpSombre` | téléphone | Téléphone · Premiers pas, question 4 sur 6 : inscription ORP | `/bienvenue` | WelcomeView › WelcomeQuestions | question 4 sur 6 | à faire |
| `PremiersPas5Objectif` | `PremiersPas5ObjectifSombre` | téléphone | Téléphone · Premiers pas, question 5 sur 6 : recherches par mois | `/bienvenue` | WelcomeView › WelcomeQuestions | question 5 sur 6 | à faire |
| `PremiersPas6Langues` | `PremiersPas6LanguesSombre` | téléphone | Téléphone · Premiers pas, question 6 sur 6 : langues | `/bienvenue` | WelcomeView › WelcomeQuestions | question 6 sur 6 | à faire |
| `OnboardingAlerteDebut` | `OnboardingAlerteDebutSombre` | téléphone | Téléphone · Premiers pas, alerte, au début | `/bienvenue?etape=alerte` | WelcomeAlertSteps | au début | à faire |
| `OnboardingAlerteCode` | `OnboardingAlerteCodeSombre` | téléphone | Téléphone · Premiers pas, alerte, code en attente | `/bienvenue?etape=alerte` | WelcomeAlertSteps › JobupCodeBox | code en attente | à faire |
| `OnboardingAlerteCodeRecu` | `OnboardingAlerteCodeRecuSombre` | téléphone | Téléphone · Premiers pas, alerte, code reçu | `/bienvenue?etape=alerte` | WelcomeAlertSteps › JobupCodeBox | code reçu | à faire |
| `OnboardingAlerteCodeExpire` | `OnboardingAlerteCodeExpireSombre` | téléphone | Téléphone · Premiers pas, alerte, code expiré | `/bienvenue?etape=alerte` | WelcomeAlertSteps › JobupCodeBox | code expiré | à faire |
| `OnboardingOrdinateur` | — | ordinateur | Ordinateur · Premiers pas, étape 1 (sans CV) | `/bienvenue` | WelcomeView | étape 1 sans CV | à faire |
| `OnboardingOrdinateurLecture` | — | ordinateur | Ordinateur · Premiers pas, lecture du CV | `/bienvenue` | WelcomeView › TroupeLoader | lecture du CV | à faire |
| `OnboardingOrdinateurCV` | — | ordinateur | Ordinateur · Premiers pas, CV lu | `/bienvenue` | WelcomeView | CV lu | à faire |
| `OnboardingOrdinateurCoupure` | — | ordinateur | Ordinateur · Premiers pas, connexion interrompue | `/bienvenue` | WelcomeView › NetworkError | connexion interrompue | à faire |
| `OnboardingOrdinateurProfil` | `OnboardingOrdinateurProfilSombre` | ordinateur | Ordinateur · Premiers pas, CV non lu : compléter le profil | `/bienvenue` | WelcomeProfileStep | CV non lu : compléter le profil | à faire |
| `OnboardingOrdinateurEtape2` | `OnboardingOrdinateurEtape2Sombre` | ordinateur | Ordinateur · Premiers pas, étape 2 (critères) | `/bienvenue` | WelcomeCriteria | étape 2 (critères) | à faire |
| `OnboardingOrdinateurEtape3` | — | ordinateur | Ordinateur · Premiers pas, étape 4 (premières offres) | `/bienvenue` | FirstOffers | étape 4 (premières offres) | à faire |
| `OnboardingOrdinateurAlerte` | `OnboardingOrdinateurAlerteSombre` | ordinateur | Ordinateur · Premiers pas, étape 3 (alerte) | `/bienvenue?etape=alerte` | WelcomeAlertSteps | étape 3 (alerte) | à faire |
| `OnboardingOrdinateurAlerteCode` | `OnboardingOrdinateurAlerteCodeSombre` | ordinateur | Ordinateur · Premiers pas, alerte, code en attente | `/bienvenue?etape=alerte` | WelcomeAlertSteps › JobupCodeBox | code en attente | à faire |
| `OnboardingOrdinateurAlerteCodeRecu` | `OnboardingOrdinateurAlerteCodeRecuSombre` | ordinateur | Ordinateur · Premiers pas, alerte, code reçu | `/bienvenue?etape=alerte` | WelcomeAlertSteps › JobupCodeBox | code reçu | à faire |
| `OnboardingOrdinateurAlerteCodeExpire` | `OnboardingOrdinateurAlerteCodeExpireSombre` | ordinateur | Ordinateur · Premiers pas, alerte, code expiré | `/bienvenue?etape=alerte` | WelcomeAlertSteps › JobupCodeBox | code expiré | à faire |
| `OnboardingOrdinateurAlerteExt` | `OnboardingOrdinateurAlerteExtSombre` | ordinateur | Ordinateur · Premiers pas, alerte, extension installée | `/bienvenue?etape=alerte` | WelcomeAlertExtension | extension installée | à faire |
| `OnboardingOrdinateurAlerteExtInstaller` | `OnboardingOrdinateurAlerteExtInstallerSombre` | ordinateur | Ordinateur · Premiers pas, alerte, avec l’extension à installer | `/bienvenue?etape=alerte` | WelcomeAlertExtension | extension à installer | à faire |
| `OnboardingOrdinateurAlerteExtSuivi` | `OnboardingOrdinateurAlerteExtSuiviSombre` | ordinateur | Ordinateur · Premiers pas, alerte, extension, suivi en direct | `/bienvenue?etape=alerte` | WelcomeAlertExtension | suivi en direct | à faire |

## Planches sans écran dans l'app

| Planche | Sombre | Titre | Pourquoi |
|---|---|---|---|
| `Emoticones` | — | Système · Émoticônes | référence des émoticônes (pas un écran) |
| `ExtAlerte` | `ExtAlerteSombre` | Extension · Formulaire d'alerte rempli | écran de l'extension de navigateur (dossier extension/), pas de l'app web |
| `ExtAlerteCodeAttente` | `ExtAlerteCodeAttenteSombre` | Extension, alerte, code en attente | extension |
| `ExtAlerteCodeColle` | `ExtAlerteCodeColleSombre` | Extension, alerte, code collé | extension |
| `ExtAlerteCodeSecours` | `ExtAlerteCodeSecoursSombre` | Extension, alerte, code à coller soi-même | extension |
| `ExtAlerteTerminee` | `ExtAlerteTermineeSombre` | Extension, alerte créée | extension |
| `ExtAnnonce` | — | Extension · Envoyer une annonce | extension |
| `ExtAutreSite` | — | Extension · Autre site | extension |
| `ExtNonConnecte` | — | Extension · Non connectée | extension |
| `ModeSombre` | — | Système · Mode sombre | référence du mode sombre (pas un écran) |
| `OnboardingProfil` | `OnboardingProfilSombre` | Téléphone · Premiers pas, CV non lu : compléter le profil · ancienne étape 2, remplacée par Premiers pas 1 à 6 | ancienne étape 2, remplacée par Premiers pas 1 à 6 (titre de la planche) |
| `Systeme` | — | Système · Règles communes | référence des règles communes (pas un écran) |

## Écrans de l'app sans planche (relevés pendant l'audit)

- Ordinateur, Candidatures › Rendez-vous avec un rendez-vous ouvert (colonne de droite : « Voir ma feuille », « Ce que tu apportes », questions). Seules existent les planches « aucun ouvert », « aucun » et le volet de veille ouvert depuis Aujourd'hui.
- Téléphone, Rendez-vous : la carte « Rendez-vous ORP du … / Ce qui a été convenu » et la ligne « Carnet ORP » de la liste.
- Fil d'un écran à l'autre, à compléter au fil de l'audit des autres pages.
