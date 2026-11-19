# Tes droits : les règles

Le seul endroit où vit le contenu juridique de la page « Tes droits » (§72r, §72t, §72v) et des réponses de
l'Assistant sur les droits au chômage. Le serveur lit ce fichier (`jobbot/droits/regles.py`) : les nombres du calcul,
les phrases affichées et leur source viennent d'ici, nulle part ailleurs. Une règle qui n'est pas ici, l'Assistant ne
la donne pas : il renvoie à l'ORP.

Chaque ligne a sa source et sa date de vérification. Les textes de loi ont été lus le 19.11.2026 dans leur version
en vigueur au 1er janvier 2026 (copies de Fedlex sur juriup.ch ; le texte de Fedlex fait foi).

Format, lu par le programme :

- `## clé` ouvre une rubrique ; ses champs sont des lignes `- Champ : valeur` ;
- les tableaux gardent leurs colonnes dans l'ordre donné ;
- `{n}` dans un texte est remplacé par un chiffre du compte au moment de l'affichage.

## sources

| Clé | Nom | Adresse |
|---|---|---|
| laci | Loi sur l'assurance-chômage (LACI, RS 837.0) | https://www.fedlex.admin.ch/eli/cc/1982/2184_2184_2184/fr |
| oaci | Ordonnance sur l'assurance-chômage (OACI, RS 837.02) | https://www.fedlex.admin.ch/eli/cc/1983/1205_1205_1205/fr |
| lpga | Loi sur la partie générale du droit des assurances sociales (LPGA, RS 830.1) | https://www.fedlex.admin.ch/eli/cc/2002/510/fr |
| opga | Ordonnance sur la partie générale du droit des assurances sociales (OPGA, RS 830.11) | https://www.fedlex.admin.ch/eli/cc/2002/569/fr |
| seco | SECO, fiche « L'assurance-chômage » | https://www.seco.admin.ch/dam/seco/fr/dokumente/Arbeit/ALV/Grundlagen/Faktenblatt_Die_Arbeitslosenversicherung.pdf.download.pdf/FR_Faktenblatt_Die_Arbeitslosenversicherung.pdf |
| travail | travail.swiss, « Questions financières » | https://www.arbeit.swiss/secoalv/fr/home/menue/stellensuchende/arbeitslos-was-tun-/finanzielles.html |
| ge | GE.ch, « Droits, obligations et sanctions » | https://www.ge.ch/indemnites-chomage/droits-obligations-sanctions-lies-assurance-chomage |
| vd | Vaud, « Jours sans contrôle » | https://www.vd.ch/static/module_droits_devoirs/story_content/external_files/jours_sans_controle_explications.pdf |
| be | OAC Berne, carte « Maladie » | https://www.weu.be.ch/content/dam/weu/dokumente/awi-ava/fr/wirtschaft-arbeit/arbeitslosigkeit/Krankheit-Karte-AVA-fr.pdf |
| formulaires | travail.swiss, « Formulaires pour les chômeurs » (IPA en ligne, attestation de gain intermédiaire 10018 f) | https://www.arbeit.swiss/secoalv/fr/home/service/formulare/formulare-fuer-arbeitslose.html |
| jobroom | Job-Room (SECO), services en ligne de l'assurance-chômage | https://www.job-room.ch/home/job-seeker |
| atas579 | Cour de justice GE, ATAS/579/2023 (cite l'art. 10 OPGA) | https://justice.ge.ch/apps/decis/en/atas/file//2023/0005/ATAS_000579_2023_A_1358_2023.pdf |

## paramètres

| Clé | Valeur | Règle | Source | Vérifié |
|---|---|---|---|---|
| taux_plein | 80 | L'indemnité pleine est de 80 % du gain assuré. | art. 22 al. 1 LACI | 2026-11-19 |
| taux_reduit | 70 | 70 % sans enfant de moins de 25 ans à charge, avec une indemnité pleine de plus de 140 francs par jour, et sans rente AI d'au moins 40 %. | art. 22 al. 2 LACI | 2026-11-19 |
| seuil_journalier | 140 | Au-delà de 140 francs par jour à 80 %, le taux passe à 70 % (montant adapté en général tous les deux ans). | art. 22 al. 2 let. b et al. 3 LACI | 2026-11-19 |
| jours_par_mois | 21.7 | Jours indemnisés par mois : 140 × 21,7 / 0,8 = 3 797 francs, le seuil mensuel donné par le SECO. | seco | 2026-11-19 |
| delai_cadre_mois | 24 | Le délai-cadre d'indemnisation dure deux ans, dès le premier jour où toutes les conditions sont réunies. | art. 9 al. 1 et 2 LACI | 2026-11-19 |
| vacances_jours | 5 | Après 60 jours de chômage contrôlé, cinq jours consécutifs sans contrôle. | art. 27 al. 1 OACI | 2026-11-19 |
| vacances_tranche | 60 | Une tranche de 60 jours de chômage contrôlé donne 5 jours. | art. 27 al. 1 OACI ; ge | 2026-11-19 |
| vacances_annonce | 14 | Annoncer au moins 14 jours avant ; les jours se prennent par semaines entières. | art. 27 al. 3 OACI | 2026-11-19 |
| maladie_jours | 30 | Le droit persiste au plus jusqu'au 30e jour de l'incapacité. | art. 28 al. 1 LACI | 2026-11-19 |
| maladie_max | 44 | 44 indemnités au plus pendant le délai-cadre. | art. 28 al. 1 LACI ; be | 2026-11-19 |
| opposition_jours | 30 | Opposition dans les 30 jours. | art. 52 al. 1 LPGA | 2026-11-19 |

## indemnités

Nombre maximum d'indemnités selon la situation (art. 27 al. 2 et 5bis LACI, vérifié le 2026-11-19). Moins de
25 ans sans enfant à charge : 200 au plus, quelle que soit la cotisation (al. 5bis). 520 seulement dès 55 ans et
22 mois cotisés (al. 2 let. c).

| Âge | Enfants | Mois cotisés | Indemnités | Source |
|---|---|---|---|---|
| moins_25 | non | 12_17 | 200 | art. 27 al. 5bis LACI |
| moins_25 | non | 18_21 | 200 | art. 27 al. 5bis LACI |
| moins_25 | non | 22_24 | 200 | art. 27 al. 5bis LACI |
| moins_25 | oui | 12_17 | 260 | art. 27 al. 2 let. a LACI |
| moins_25 | oui | 18_21 | 400 | art. 27 al. 2 let. b LACI |
| moins_25 | oui | 22_24 | 400 | art. 27 al. 2 let. b LACI |
| 25_54 | * | 12_17 | 260 | art. 27 al. 2 let. a LACI |
| 25_54 | * | 18_21 | 400 | art. 27 al. 2 let. b LACI |
| 25_54 | * | 22_24 | 400 | art. 27 al. 2 let. b LACI |
| 55_plus | * | 12_17 | 260 | art. 27 al. 2 let. a LACI |
| 55_plus | * | 18_21 | 400 | art. 27 al. 2 let. b LACI |
| 55_plus | * | 22_24 | 520 | art. 27 al. 2 let. c LACI |

## page

- Source affichée : Selon la LACI et travail.swiss
- Vérifié : 2026-11-19
- Restants : d’indemnités restants sur {n}
- Montant : Montant
- Montant valeur : {n} % du gain assuré
- Fin : Fin estimée
- Fin aide : La date exacte est sur la décision de ta caisse
- Fin source : art. 9 al. 2 LACI
- AVS : Quelques années avant l’âge AVS, tu peux avoir droit à plus d’indemnités. Demande à ton ORP.
- AVS source : art. 27 al. 3 LACI
- À compléter : À compléter

## vacances

- Titre : Vacances
- Phrase : 5 jours payés tous les 60 jours
- Phrase source : art. 27 al. 1 OACI ; ge
- Mot-clé : {n} jours
- Sous le mot-clé : disponibles maintenant
- Mot-clé sans solde : {n} jours acquis
- Sous le mot-clé sans solde : Complète Ta situation pour le solde exact
- Source affichée : Selon la LACI et travail.swiss
- Vérifié : 2026-11-19
- Action : Annoncer mes vacances

| Comment ça marche | Précision | Source |
|---|---|---|
| 5 jours tous les 60 jours d’indemnités | Tu peux les garder et les cumuler | art. 27 al. 1 OACI ; vd |
| Pendant ces jours | Pas de recherches ni de rendez-vous | art. 27 al. 1 OACI ; ge |
| Annonce-les 14 jours avant | À ta conseillère ou ton conseiller | art. 27 al. 3 OACI |
| Pas pris à la fin du délai-cadre | Ils sont perdus | ge |

## formation

- Titre : Formation payée
- Phrase : Cours ou stage, avec l’accord de l’ORP
- Phrase source : art. 59b al. 1 et 60 al. 3 LACI ; ge
- Mot-clé : Payée
- Sous le mot-clé : par l’assurance, avec l’accord de l’ORP
- Source affichée : Selon la LACI et travail.swiss
- Vérifié : 2026-11-19
- Action : Demander une formation

| Comment ça marche | Précision | Source |
|---|---|---|
| Demande d’abord à ta conseillère | Avant toute inscription | art. 60 al. 3 et 59b al. 1 LACI ; ge |
| Le cours doit servir ta recherche | Il améliore tes chances de retrouver un poste | art. 59 al. 2 LACI ; seco |
| Tes indemnités continuent | Pendant le cours | art. 59b al. 1 LACI ; seco |

## gain

- Titre : Gain intermédiaire
- Phrase : Travailler un peu, l’assurance complète
- Phrase source : art. 24 al. 1 LACI
- Mot-clé : Plus d’argent
- Sous le mot-clé : ton salaire + un complément de l’assurance
- Source affichée : Selon l’art. 24 LACI et le SECO
- Vérifié : 2026-11-19
- Action : Déclarer un gain
- Lien : https://www.job-room.ch/home/job-seeker
- Lien libellé : Formulaire IPA sur Job-Room
- Lien source : formulaires ; art. 29 al. 2 OACI (vérifié le 2026-11-19 : « Indications de la personne assurée » est un eService de la caisse dans Job-Room ; sans compte, la caisse l’envoie sur papier chaque mois)
- Attestation : https://www.arbeit.swiss/secoalv/fr/home/service/formulare/formulare-fuer-arbeitslose.html
- Attestation libellé : Attestation de gain intermédiaire (formulaire 10018 f)
- Attestation source : formulaires ; art. 29 al. 2 let. b OACI

| Comment ça marche | Précision | Source |
|---|---|---|
| Un petit travail, même à temps partiel | Il doit être payé au tarif usuel | art. 24 al. 1 et 3 LACI |
| L’assurance complète la différence | 70 ou 80 % de l’écart, 12 mois au plus en général | art. 24 al. 1, 3 et 4 LACI ; seco |
| Déclare-le chaque mois | Sur le formulaire IPA, avec l’attestation de gain intermédiaire, à ta caisse | art. 29 al. 2 OACI ; formulaires |

## frais

- Titre : Frais de déplacement
- Phrase : Remboursés pour une mesure de l’ORP
- Phrase source : art. 59cbis al. 3 LACI
- Mot-clé : Remboursés
- Sous le mot-clé : pour une mesure demandée par l’ORP
- Source affichée : Selon l’art. 59cbis LACI
- Vérifié : 2026-11-19
- Action : Ajouter un justificatif

| Comment ça marche | Précision | Source |
|---|---|---|
| Cours, stage ou programme de l’ORP | Les frais nécessaires sont remboursés | art. 59cbis al. 3 LACI ; art. 85 al. 1 et 2 OACI |
| Garde tes billets et reçus | Ils servent de justificatifs | art. 85 al. 1 OACI |
| Envoie-les à ta caisse de chômage | Avec le formulaire du mois | art. 86 al. 1 OACI |

## maladie

- Titre : Maladie
- Phrase : Jusqu’à 30 jours, avec un certificat
- Phrase source : art. 28 al. 1 et 5 LACI
- Mot-clé : Jusqu’à 30 jours
- Sous le mot-clé : par arrêt, avec un certificat médical
- Source affichée : Selon l’art. 28 LACI
- Vérifié : 2026-11-19
- Action : Annoncer un arrêt

| Comment ça marche | Précision | Source |
|---|---|---|
| Préviens ta conseillère tout de suite | Le jour où tu es malade | be ; art. 42 al. 1 OACI (au plus tard dans la semaine) |
| Envoie un certificat médical | À la caisse de chômage | art. 28 al. 5 LACI ; be |
| 44 jours au plus | Sur tout ton délai-cadre | art. 28 al. 1 LACI |

## opposition

- Titre : Faire opposition
- Phrase : Par écrit et signée, dans les 30 jours
- Phrase source : art. 52 al. 1 LPGA ; art. 10 al. 2 et 4 OPGA (atas579)
- Mot-clé : 30 jours
- Sous le mot-clé : pour contester une décision
- Source affichée : Selon l’art. 52 LPGA et l’art. 10 OPGA
- Vérifié : 2026-11-19
- Action : Préparer ma lettre

| Comment ça marche | Précision | Source |
|---|---|---|
| Par écrit, motivée et signée | Explique pourquoi tu n’es pas d’accord | art. 10 al. 1, 2 et 4 OPGA (atas579) |
| À l’autorité qui a décidé | Son adresse est sur la décision | art. 52 al. 1 LPGA |
| Compte à partir de la réception | Le lendemain du jour où tu la reçois | art. 38 al. 1 LPGA (les féries de l’al. 4 l’allongent) |

## devoirs

- Recherches : Recherches du mois
- Recherches phrase : Pour garder tes indemnités
- Recherches source : art. 17 al. 1 LACI
- Rendez-vous : Rendez-vous ORP
- Rendez-vous source : art. 17 al. 3 LACI
- Annoncer : Annoncer tes vacances
- Annoncer phrase : 14 jours avant, à ta conseillère
- Annoncer source : art. 27 al. 3 OACI

## assistant

Règles que l'Assistant peut donner en plus de celles des rubriques ci-dessus. Il ne reçoit jamais les chiffres du
compte : il écrit `{{clé}}` et le serveur met le chiffre à l'affichage.

| Règle | Source |
|---|---|
| Une rente AI d’au moins 40 % donne aussi droit à 80 % du gain assuré. | art. 22 al. 2 let. c LACI |
| Sans conditions de cotisation remplies mais libéré de ces conditions (formation, maladie de plus de 12 mois…), 90 indemnités au plus. | art. 27 al. 4 LACI ; seco |
| Le délai-cadre continue de courir pendant une maladie ; il n’est pas prolongé. | be |
| Un jour de vacances annoncé puis non pris sans motif valable compte quand même comme pris. | art. 27 al. 3 OACI |
| Une incapacité annoncée plus d’une semaine après son début, sans excuse, fait perdre les indemnités des jours d’avant. | art. 42 al. 1 et 2 OACI |
| Les frais de transport remboursés sont ceux des transports publics en 2e classe ; la voiture seulement par exception. | art. 85 al. 2 et 3 OACI |
