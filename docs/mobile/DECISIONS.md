# Décisions données après la maquette du 13 novembre

Une décision de Kevin donnée dans la conversation après le 13 novembre passe avant le paquet (LISEZMOI §2, CLAUDE.md).

**Ce fichier est assemblé : ne le modifie pas.** Une décision se note dans son propre fichier,
`docs/decisions/AAAA-MM-JJ-HHMM-sujet.md` (l'heure est facultative), qui commence par un titre `## …`
(docs/decisions/README.md). Sur main, `scripts/decisions.py` assemble ce fichier après chaque fusion,
trié par date puis par heure, la plus récente en bas.

## Décisions du 13 novembre

| Date | Décision | Remplace |
|---|---|---|
| 2026-11-13 | Texte en #8C8478 dans la maquette : erreur de contraste (3,69:1). En texte, utiliser le gris secondaire. La maquette sera corrigée. | Le #8C8478 des planches, pour du texte. |
| 2026-11-13 | Le point 6 du LISEZMOI (planches Get'emAll gardées) passe avant le point 1 : les quatre planches Get'emAll et `maquettes/canvas.json` restent dans le dépôt. | La suppression de toute planche absente du paquet. |
| 2026-11-13 | Raccourcis de la préparation de candidature (lettre et CV lancés ensemble, bouton unique "J'ai relu, continuer", "Tout télécharger") : déjà dans main (PR #597, #600), conservés. | La ligne « raccourcis 1, 2 et 4 » du §6 du LISEZMOI, retirée (erreur du paquet). |
| 2026-11-13 | Téléphone, Ma candidature : la ligne "modèle · langue · Changer" de PreparerMiseEnPage est conservée. MaCandidatureV2 sera complétée. | L'absence de cette ligne sur MaCandidatureV2. |
| 2026-11-13 | Téléphone, échec de l'écriture de la lettre ou du CV : même carte et même texte que PreparerOrdinateurLettreVide (« La lettre n'a pas pu être écrite », l'explication, « Réessayer »). Pas de nouveau dessin. | L'état d'échec, dessiné nulle part sur téléphone. |
| 2026-11-13 | Ordinateur, étape Postuler : la ligne du certificat dans « À joindre » est conservée. PreparerOrdinateurPostuler sera complétée. | L'absence de cette ligne sur PreparerOrdinateurPostuler. |
| 2026-11-13 | Chaque PR d'interface est vérifiée contre le paquet du 13 novembre et porte une section « Conformité maquette du 13.11 » (règle dans CLAUDE.md). | — |
| 2026-11-13 | Attente de l'Assistant, cloche sans notification, espacement de l'en-tête : version de #574 conservée, la maquette sera alignée dessus. | Les deux premières lignes des « États pas encore dessinés » du §6 du LISEZMOI. |
| 2026-11-13 | Largeur des volets (code gardé tel quel). 420 px : petit volet ancré à un bouton, avec pastille, sans voile (Nouveau rendez-vous, Ajouter, Pour les formulaires, Compte, Notifications). 440 px : volet standard sur toute la hauteur ; c'est le cas par défaut pour tout nouveau volet. 480 px : réservé à l'Assistant, Pour l'ORP et Compléter le profil ; pas de nouveau volet à 480 sans l'accord de Kevin. | Les largeurs des planches quand elles diffèrent. |
| 2026-11-13 | Panneau des Alertes sur ordinateur (fiche d'un site, Ajouter une recherche) : 440 px. La planche AlertesOrdinateurSite dit 480, c'est une erreur de la maquette, elle sera corrigée. | Les 480 px de AlertesOrdinateurSite. |
| 2026-11-13 | Rendez-vous ORP, « Ce qui a été convenu » : le champ « Mesures décidées » grandit avec le texte au lieu de le couper, dans le volet et dans la fiche (ordinateur, à partir de 1024 px). | Le champ d'une ligne des planches. |
| 2026-11-13 | La planche RendezVous dessine l'ancien champ (48 px, libellé au-dessus) : le champ commun de 56 px à libellé flottant fait foi. La planche sera corrigée. | Le champ de 48 px à libellé au-dessus de la planche RendezVous. |
| 2026-11-13 | Lot de corrections du 13.11 au soir (LISEZMOI_CORRECTIONS.md), §1 Premiers pas : nouvelle étape « Alerte ». Ordre : CV, critères, alerte, premières offres. Téléphone (OnboardingC, étape 3) : barre de 5 segments, « Chercher » barré et « Recevoir. » à la main ; phrase « Crée une alerte sur jobup : ses offres arrivent ici chaque matin, déjà triées. Environ 2 minutes. », rappel de la recherche et les trois étapes numérotées du panneau Alertes ; étape 2 : « Copie-la, puis colle-la dans le champ e-mail de l’alerte. ». Pied : « J’ai créé l’alerte », puis « Plus tard » en bouton texte de 44 px ; les deux mènent à l'étape suivante. Le bouton de l'étape des critères devient « Continuer ». Ordinateur (OnboardingOrdinateurAlerte) : « Étape 3 sur 4 », surtitre « Tes prochaines offres », titre « Une alerte, et elles arrivent seules », trois étapes dans une carte, Orange à droite (260 px) ; pied « Retour » à gauche, « Plus tard » et « J’ai créé l’alerte » à droite. Les huit autres planches OnboardingOrdinateur* passent à « sur 4 », avec 4 points. Un seul site : jobup. Après « Plus tard », la carte « Premiers pas » d'Aujourd'hui garde l'étape ouverte. Compteur « Recherches par mois » : 1 à 99. | Les premiers pas en 3 étapes (4 segments sur téléphone), « Voir mes offres » à l'étape des critères. |
| 2026-11-13 | Lot de corrections du 13.11 au soir (LISEZMOI_CORRECTIONS.md), §2 Alertes sur ordinateur : AlertesOrdinateurVide sans l'illustration de l'ancienne série ; Orange (112 px de haut) à gauche du titre, puis 24 px, puis la carte « Ta recherche ». AlertesOrdinateurSite : même page derrière, panneau à 440 px. Bouton « Copier l’adresse » : 44 × 44 px. | L'illustration de l'ancienne série des Alertes vides. |
| 2026-11-13 | Lot de corrections du 13.11 au soir (LISEZMOI_CORRECTIONS.md), §3 Gris #8C8478 interdit en texte : « Pas encore notée » et le mois de la petite icône de calendrier en #596070 (clair) et #ABA398 (sombre). #8C8478 reste permis pour les bordures et les traits d'icônes. | Le #8C8478 en texte des planches. |
| 2026-11-13 | Lot de corrections du 13.11 au soir (LISEZMOI_CORRECTIONS.md), §4 Ma candidature sur téléphone, état « lettre » : ligne « Moderne · Français » et lien « Changer » entre les onglets et la légende (la ligne déjà codée). | L'absence de cette ligne sur MaCandidatureV2. |
| 2026-11-13 | Lot de corrections du 13.11 au soir (LISEZMOI_CORRECTIONS.md), §5 Rendez-vous, feuille « Ce qui a été convenu » (RendezVous et RendezVousSombre, état noter) : les deux champs suivent le champ commun (56 px, rayon 12 px, bordure 1,5 px, libellé flottant de 12 px gras), avec une aide de 13 px : « Ex. : cours, stage, programme » et « Ex. : ce que ton conseiller t’a demandé ». Un filet, le titre centré « Prochain rendez-vous », puis « Date » et « Heure » ; « jobA1 le met dans tes Rendez-vous. » centré. Alignement de la maquette sur le code. | Le champ de 48 px à libellé au-dessus. |
| 2026-11-13 | Lot de corrections du 13.11 au soir (LISEZMOI_CORRECTIONS.md), §6 Objectif du mois atteint (état « atteint » de AccueilV2, AujourdhuiOrdinateurV2 et leurs versions sombres) : plus de carte à part avec une image de l'ancienne série. Titre manuscrit « Objectif du mois atteint, » en vert (#17734A, #62D497 en sombre), « la suite est en plus » en bleu, puis « Tes 10 recherches de novembre sont faites. Ce que tu envoies maintenant compte en plus. » ; barre ORP « 10 sur 10 », pleine et verte, « Objectif atteint » (BarreOrpEtats) ; « À faire » sans « Envoyer N candidatures ». L'écran plein « C’est fait ! » (ObjectifAtteint) reste, au moment où l'objectif est atteint. | La carte à part de l'objectif atteint. |
| 2026-11-13 | Lot de corrections du 13.11 au soir (LISEZMOI_CORRECTIONS.md), §7 Notifications, « Tout est lu » : le personnage de l'ancien kit est remplacé par le Sourire (140 px de haut) ; en sombre, liseré clair `drop-shadow(0 0 1px #F3EEE6)` deux fois. | Le personnage de l'ancien kit. |
| 2026-11-13 | Lot de corrections du 13.11 au soir (LISEZMOI_CORRECTIONS.md), §8 Adresse de l'entreprise manquante sur l'écran de fin (état finadresse de MaCandidatureV2 et sombre, état adr de CandidatureEnvoyeeOrdinateur) : sous « Relance prévue », icône d'épingle brune, « Il manque l’adresse de l’entreprise », « Il la faut pour ton suivi ORP », lien « Ajouter » à droite (zone de 44 px). Seulement si l'adresse manque ; « Ajouter » ouvre le champ d'adresse existant de la fiche entreprise ; jamais bloquant. | — |
| 2026-11-13 | Lot de corrections du 13.11 au soir (LISEZMOI_CORRECTIONS.md), §9 Surlignage en sombre : le texte surligné hérite de la couleur du texte (`color: inherit`) sur le fond #5C4A14 (sinon noir, 2,4:1). | La planche de surlignage sombre précédente. |
| 2026-11-13 | Trier les offres, ordinateur : les flèches des deux touches sous le compteur sont des caractères (← →) dans `kbd`, lus « flèche gauche » et « flèche droite » par un lecteur d'écran. | La règle « une icône à la place de tout caractère » (docs/101), pour ces deux touches seulement. |
| 2026-11-13 | Trier les offres, ordinateur : marges du livre autour des pages à 8 px en haut et 16 px en bas, retrait droit du message « Annuler » à 8 px (grille de 4 px). Les planches seront alignées. | Les 6 et 14 px du livre et les 6 px du message sur TrierOffresOrdinateurV2. |
| 2026-11-13 | Panneau « Alerte <site> » sur ordinateur (AlertesOrdinateurSite) : même composant que les autres volets latéraux, pas de nouveau composant ; le focus entre dans le panneau et y reste, Échap ferme et rend le focus au bouton du site, le titre est annoncé ; le bouton de copie confirme « Adresse copiée », visible et annoncé (état non dessiné, demandé par Kevin) ; la page derrière ne change pas (sa planche corrigée viendra) ; rien ne change sur téléphone. | L'absence de l'état « adresse copiée » sur la planche. |
| 2026-11-13 | Panneau « Alerte <site> », plusieurs recherches pour un même site : un bouton « Ouvrir <site> : <recherche> » par recherche, et le rappel « Recherche : » les liste toutes (comportement actuel gardé). | L'absence de cet état sur AlertesOrdinateurSite. |
| 2026-11-13 | Panneau « Alerte LinkedIn » : le second bouton « Ouvrir LinkedIn en télétravail » reste sous le premier. | L'absence de cet état sur AlertesOrdinateurSite. |
| 2026-11-13 | Panneau « Alerte <site> » : bouton « Copier l'adresse » de 44 × 44 px dans le champ de 48 px. | Les 40 px de AlertesOrdinateurSite. |
| 2026-11-13 | Première alerte pendant les premiers pas (accueil) : accord sur le principe. Planche livrée le 13 novembre au soir (OnboardingC étape 3, OnboardingOrdinateurAlerte ; LISEZMOI_CORRECTIONS §1). « J'ai créé l'alerte » est le bouton principal, « Plus tard » le bouton secondaire. | — |
| 2026-11-13 | Première alerte pendant les premiers pas : un seul site dans l'étape, jobup. Les autres sites se créent ensuite depuis Mes alertes. | Les quatre sites enchaînés de l'assistant des alertes, pour cette étape. |
| 2026-11-13 | Première alerte pendant les premiers pas : après « Plus tard », la carte « Premiers pas » d'Aujourd'hui garde l'étape ouverte et ramène au même écran. | — |
| 2026-11-13 | « Des offres dès maintenant » reste affiché jusqu'à la première offre reçue. | — |

`tokens.css` reste la source des couleurs et des tailles : il n'est pas dans le paquet du 13 novembre et n'est pas remplacé.

## Décisions du 14 novembre

| Date | Décision | Remplace |
|---|---|---|
| 2026-11-14 | Style ou comportement (règle dans CLAUDE.md) : un changement de style seul dessiné sur une planche se code directement, la section « Conformité maquette » de la PR sert d'inventaire ; un changement de comportement, de données ou de parcours s'annonce d'abord en cinq lignes au plus et attend l'accord de Kevin ; si la planche ferait retirer ou modifier une fonction qui marche dans main, s'arrêter et demander, ne rien retirer. Application au lot du 13.11 au soir : §2, 3, 6, 7, 8, 9 = style ; §4 et 5 = vérification seule ; §1 = parcours, annoncé d'abord. | Les demandes « donne-moi la liste sans coder » du 13.11 pour des points de style. |
| 2026-11-14 | Premières offres trouvées sur le web (sans planche) : le composant « premières offres » existant est repris, avec le texte « Pas encore notées. Les notes arrivent avec les offres de tes alertes. » Ces offres ne sont pas notées ; seules celles de moins de 14 jours sont gardées quand la date est connue ; titre, entreprise et lieu sont repris tels quels du résultat de recherche. | — |
| 2026-11-14 | Jour de repos : la planche `AujourdhuiOrdinateurReposD` est retirée. Le jour de repos suit le gabarit commun, état « repos » des planches `AccueilV2`, `AccueilV2Sombre`, `AujourdhuiOrdinateurV2` et `AujourdhuiOrdinateurV2Sombre` : « Jour de repos. » à la main, « Ta semaine est faite. Si tu veux avancer, N choses t'attendent. », la liste « Si tu veux avancer », la barre ORP avec « Cette semaine : 3 sur 3, faite » (plus de ronds par jour), « Offres à trier » s'il y en a. Sur téléphone, en attendant le tour du téléphone, seuls les textes vont sur la page Accueil actuelle. | `AujourdhuiOrdinateurReposD` |
| 2026-11-14 | Alertes sur ordinateur, rien en place (AlertesOrdinateurVide) : l'assistant en trois étapes est gardé sous l'en-tête (Orange, titre, phrase de la planche). La planche sera alignée dessus. | La carte « Ta recherche » et la liste « À créer » de la planche, quand rien n'est en place. |
| 2026-11-14 | Écran de fin, adresse de l'entreprise manquante (§8) : la ligne « Il manque l'adresse de l'entreprise », sous la relance, dans la carte « Mois ORP » de la planche (corrigé le 14.11 par Kevin : cette ligne visait la ligne d'adresse, pas la carte ; la carte est ajoutée, sans la ligne « Preuve pour l'ORP gardée »). « Ajouter » ouvre « Modifier la candidature » envoyée, le curseur dans l'adresse, parce que le suivi ORP lit l'adresse de la candidature, pas celle de l'offre. | « Ajouter » qui ouvre le champ d'adresse de la fiche entreprise. |
| 2026-11-14 | Étape « Alerte » des premiers pas (§1) : le rappel montre la recherche enregistrée de la personne (pas « Lausanne et 30 km » écrit en dur) ; une seule recherche, la première, les autres se créent depuis Mes alertes ; rouverte depuis Aujourd'hui, « Retour » et « Plus tard » ramènent à Aujourd'hui ; l'écran téléphone « Des offres dès maintenant » est inchangé. | Le texte des planches OnboardingC (étape 3) et OnboardingOrdinateurAlerte sur ces points. |
| 2026-11-14 | Bilan sur ordinateur : « Mois précédents » et « Autres exports », sous les rendez-vous ORP, sont gardés (ajoutés le 11.11, PR 33). | Leur absence sur BilanOrdinateur. |
| 2026-11-14 | Bilan sur ordinateur, « Prochain rendez-vous » déjà fixé : sa date dans le calendrier bleu, comme les autres dates à venir. Pas encore fixé : le calendrier vide en pointillés de la planche. | L'état « fixé », dessiné nulle part. |
| 2026-11-14 | Panneau « Pour l'ORP » sur ordinateur, « Compléter » à côté d'une adresse manquante : même mécanisme que « Ajouter » de l'écran de fin (§8 : modification de la candidature envoyée, champ adresse prêt). La déclaration n'est jamais bloquée. | Le lien sans destination de BilanOrdinateurFiche. |
| 2026-11-14 | Bilan › Formations sur ordinateur : d'abord la carte « L'ORP peut financer une formation », « En cours » et « Gardées » ; le catalogue et ses filtres, inchangés, derrière « Chercher d'autres formations ». Téléphone inchangé. | Le code ouvrait le catalogue ; la planche BilanOrdinateur (état Formations) montre la vue d'ensemble. |
| 2026-11-14 | Bilan › Résultats, « Ce que jobA1 conseille » : codé sans IA ni migration, bloc caché s'il n'y a rien. Seuil : un conseil sur un site ou une façon de postuler demande au moins 5 candidatures concernées ; une compétence manquante doit apparaître dans au moins 5 offres. En dessous, pas de conseil. Chaque conseil affiche sa base (« d'après 8 offres »). Le texte exact des deux types de conseil est montré à Kevin avant la fusion. | Le bloc de la planche BilanOrdinateur, absent du code. |
| 2026-11-14 | « Ce que jobA1 conseille », textes validés par Kevin (PR #694). Formulaires en ligne : « Les formulaires en ligne ne répondent pas » / « Essaie l'e-mail direct au service RH quand l'annonce en donne un. » E-mails directs : « Les e-mails directs ne reçoivent pas de réponse » / « Essaie le formulaire en ligne de l'annonce quand il y en a un. » Lettres : « Les lettres par la poste ne reçoivent pas de réponse » / « Essaie le formulaire en ligne ou l'e-mail quand l'annonce en donne un. » Site : « Les offres de {site} ne répondent pas » / « Garde plus de temps pour les sites qui te répondent. » Compétence : « {Compétence} revient dans {n} offres sur {total} » / « Une formation peut compter pour l'ORP : à voir avec ton conseiller. », lien vers Formations gardé. Une candidature compte 14 jours après son envoi ; aucun conseil quand rien n'a répondu. | La seconde ligne du conseil de compétence de la planche (« La formation peut être financée par l'ORP. ») est remplacée. |
| 2026-11-14 | Écran qui a sa planche : son visuel est refait à partir de zéro d'après la planche (gabarit, styles, mise en page), au lieu de corriger l'existant ; la logique ne change pas (stores, services, routes, types, textes non dessinés, tests). La PR montre l'avant et l'après, Kevin décide alors ; les fonctions de main absentes de la planche sont listées et gardées sans son accord. Règle 4 de CLAUDE.md, section maquette. | La correction de l'écran existant, point par point. |
| 2026-11-14 | Écran de fin sur ordinateur (CandidatureEnvoyeeOrdinateur) : la carte « Mois ORP » de la planche est affichée (titre et mois, « 8 sur 10 », barre, « Encore 2 d'ici le 5 décembre », relance prévue, adresse manquante), sans la ligne « Preuve pour l'ORP gardée », dont la donnée n'existe pas (voir « Fonctions manquantes »). « Je n'ai pas postulé » reste en lien sous les boutons. | L'écran sans carte. |
| 2026-11-14 | Relance (RelanceOrdinateurV2) : le message s'écrit à la première ouverture, puis il est gardé ; rouvrir le panneau ne refait pas d'appel à l'IA, un lien « Réécrire » en demande un nouveau. Objet et message restent visibles en lecture ; « Modifier le message » les rend modifiables ; rien ne part sans que la personne ait pu le lire. « Relancer par e-mail » : bouton principal, avec l'illustration. « Marquer comme relancée » : lien sous le bouton. Si l'écriture échoue : la carte « Réessayer » de la lettre. | « Rédiger la relance » à cliquer, champs ouverts, « Marquer comme relancée » en bouton plein. |

## Fonctions manquantes

Fonctions dessinées sur une planche que jobA1 ne sait pas encore faire. Rien n'est codé : chaque entrée dit ce qu'il faudrait pour l'avoir, et Kevin décide. Une entrée par fonction, la plus récente en bas.

| Date | Fonction (planche) | Ce qu'il faudrait |
|---|---|---|
| 2026-11-14 | « Preuve pour l'ORP gardée — Ton e-mail du 11 nov. à 11 h 52 » (écran de fin, carte « Mois ORP », CandidatureEnvoyeeOrdinateur) | Une preuve rattachée à la candidature, qui n'existe pas aujourd'hui. Trois sources possibles : 1) l'e-mail de candidature que la personne a envoyé, retrouvé dans son dossier « Envoyés » (lecture seule, comme la lecture des alertes), rapproché par l'adresse du destinataire ou le domaine de l'entreprise ; 2) l'accusé de réception de l'employeur ou du site, reçu dans sa boîte et rapproché de la même façon ; 3) une capture ou un PDF de la page de confirmation, déposé par la personne. Dans tous les cas : une migration (date, expéditeur ou destinataire, objet, pas le corps), l'accord de la personne pour lire ses envois, et les règles de docs/regles-securite-donnees.md (conservation, effacement, journal). La 1) est la seule qui correspond au texte de la planche (« Ton e-mail »). |
| 2026-11-14 | Bouton micro dans la zone de demande (Préparer, PreparerOrdinateur ; PR #695) | La dictée vocale. Soit l'API du navigateur (Web Speech) : sans serveur, mais absente de Firefox, et Chrome envoie la voix à Google ; soit un enregistrement envoyé à un service de transcription : un coût par minute, la voix devient une donnée de la personne (règles de sécurité des données, conservation nulle). Il faut choisir la voie avant de coder. |
| 2026-11-14 | Surlignage « Repris de l'annonce : 3 points » dans la lettre (PreparerOrdinateur ; PR #695) | Que l'écriture de la lettre par l'IA rende aussi les passages repris de l'annonce (leur position dans chaque paragraphe), dans le même appel, sans coût en plus, comme les citations de la note du tri ; les garder avec chaque version de la lettre (champ ajouté aux paragraphes, donc migration ou format JSON étendu) ; les recalculer à chaque retouche par l'IA, et les retirer d'un paragraphe modifié à la main. |
| 2026-11-14 | Bouton d'envoi bleu même quand la zone de demande est vide (PreparerOrdinateur ; PR #695) | Aucune donnée : un choix de comportement. Aujourd'hui le bouton reste grisé tant que rien n'est écrit, ce qui dit qu'il n'y a rien à envoyer. Bleu en permanence, un clic à vide devrait mettre le curseur dans la zone. Changement du seul écran, une fois choisi. |

## Maquette finale du 14 novembre (docs/maquette/2026-11-14)

Décisions de Kevin du 14.11.2026 (20 h 05) sur les questions posées avant l'étape 2. Elles passent avant les planches du paquet et avant `docs/design/regles.md`.

| Date | Décision | Remplace |
|---|---|---|
| 2026-11-14 | Le paquet du 14 novembre compte 89 planches modifiées : les fichiers font foi, pas la phrase « 63 planches » du LISEZMOI (écrite avant les sections 6 à 9). | La phrase d'ouverture du LISEZMOI. |
| 2026-11-14 | Envoyées, tri : le tri passe dans le volet Filtres, comme les puces de statut. Choix « À relancer d'abord » (par défaut) / « Plus récentes d'abord ». Les groupes « À relancer » / « Cette semaine » de la liste restent. | Le tri retiré sans remplacement (§3, §6). |
| 2026-11-14 | Carte Relance : le libellé du bouton principal suit le canal de la candidature. E-mail → « Relancer par e-mail » (PR #699). LinkedIn → « Copier et ouvrir LinkedIn » (la planche montre une candidature LinkedIn). Même bouton, même place, texte selon le canal. | « Copier et ouvrir LinkedIn » pour toutes (§8). |
| 2026-11-14 | Champ de recherche sur téléphone : « Poste, entreprise, lieu » est le texte visible (placeholder) ; « Rechercher une offre » / « une candidature » / « un rendez-vous » est le nom pour les lecteurs d'écran (aria-label). Le champ est aussi sur Rendez-vous, à la même place. | Le texte « Rechercher une… » visible des planches. |
| 2026-11-14 | « Partager l'annonce » reste dans le menu ⋯ de l'offre (la planche ne montre pas le menu ouvert). Seule l'icône Partager de la barre du haut de l'offre provisoire disparaît. | L'absence de « Partager » sur ActionsOffre. |
| 2026-11-14 | Réglages, notifications : pas d'interrupteur pour un envoi qui n'existe pas. Quatre interrupteurs, téléphone et ordinateur : Nouvelles offres, Relances, Objectif ORP, E-mail en plus des notifications. La planche sera corrigée. | « Actualités et formations » de ReglagesOrdinateur et de §6. |
| 2026-11-14 | Cercle liquide : remplacé par la barre dans la PR de chaque page concernée (accueil du téléphone, Bilan), sans attendre la PR 48 du lot Tri. Une page refaite d'après sa planche ne garde pas un élément retiré. | Le cercle ORP de l'accueil réservé à la PR 48. |
| 2026-11-14 | Planches retirées par Kevin (Animations, AujourdhuiOrdinateurReposD, RelierFermee, RelierLienInvalide, RelierPasTesteur) : supprimées du dépôt. Seule `Animations` y était encore. | — |
| 2026-11-14 | Réglages, notifications : trois interrupteurs pour l'instant (Nouvelles offres, Relances, Objectif ORP). « E-mail en plus des notifications » attend qu'un envoi d'e-mail existe : jobA1 n'en envoie aucun aujourd'hui. Remplace le quatrième interrupteur de la ligne précédente. | « E-mail en plus des notifications » de Reglages et ReglagesOrdinateur. |

## Candidatures sur téléphone, réponses du 15 novembre

Décisions de Kevin du 15.11.2026 sur les questions du fil « Candidatures sur téléphone ». Elles passent avant les planches.

| Date | Décision | Remplace |
|---|---|---|
| 2026-11-15 | Lien vers le détail de la note : « Voir la compatibilité » sur téléphone comme sur ordinateur, le même libellé partout, note provisoire ou non. | « Le détail de la note » (prompt du 10 novembre, PR 15 ; planche OffreProvisoire). |
| 2026-11-15 | Envoyées, feuille Filtres du téléphone : alignée sur la planche FiltresEnvoyees (§10) : titre « Filtres des envoyées », statut choisi coché, tri en contrôle segmenté. | La feuille « Filtres » à pastilles de #711. |
| 2026-11-15 | Rendez-vous sur téléphone : pas d'icône Filtres sur cet onglet ; la recherche reste. | — |
| 2026-11-15 | Offres sur téléphone : « + Ajouter » est gardé à côté de la recherche, place définitive : bouton rond 48 × 48 px (hauteur du champ), contour 1,5 px bleu (#2445C2, sombre #7D95FF), fond carte, icône « + » de 22 px, nommé « Ajouter une offre », 8 px entre le champ et le bouton. Le titre garde 30 px, « Alertes » ne bouge pas. Sur un écran vide où la recherche est masquée, le « + » l'est aussi (le bouton « Ajouter une offre » de l'écran vide le remplace). Sa planche arrive avec le prochain lot. | « Ajouter » compact à côté de la recherche (C10). |
| 2026-11-15 | Offre provisoire sur téléphone : « L'entreprise » reste, sous « Le poste », dans le même style de section (titre 16/700, texte 15 px), masquée si on n'a aucune information sur l'entreprise ; pas de carte en plus. | L'absence de « L'entreprise » sur OffreProvisoire. |

## Code jobup dans l'étape Alertes (Kevin, 14 et 15.11.2026)

- 14.11 : le code de vérification de jobup s'affiche dans l'étape Alertes des Premiers pas (choix « Code dans l'étape Alertes »).
- 14.11 : format d'adresse avec sous-adressage, `JOBBOT_ALERT_DOMAIN=alertes@joba1.ch` → `alertes+nom-code@joba1.ch` ; Kevin règle le serveur.
- 15.11 : la relecture toutes les 5 s ne tourne que pendant l'attente et quand l'écran est visible ; elle s'arrête dès que le code arrive ou au bout de 10 minutes sans code (état expiré, « Renvoyer »).
- 15.11 : la route ne renvoie que le dernier code du compte connecté, sans contenu de l'e-mail ; le code n'est pas journalisé.
- 15.11 : durée de validité lue dans l'e-mail de jobup, 10 minutes par défaut ; l'étape du code seulement pour jobup.
- 15.11 : l'état expiré réutilise les jetons existants `--peach-soft` / `--peach-text` (valeurs claires de la planche).
- 15.11 (réponses de Kevin sur #725) : l'état expiré garde `--peach-soft` / `--peach-text` aussi en sombre (#3A281E / #F2B98E, contraste 8,1:1) ; le libellé reste « Renvoyer », aria-label « Renvoyer le code depuis jobup » (la capture sombre du téléphone était périmée). Poids : l'allègement est fusionné d'abord, puis #723 et #725, sans toucher à la limite.

## Liaison carte → détail (ordinateur), réponses du 15 novembre

| Date | Décision | Source |
|---|---|---|
| 2026-11-15 | Liaison carte → détail (§11) : deux jetons propres à la liaison, `--linked-line` (#D5D1C7, sombre #4E473E) pour le trait de la zone et de l'encoche, `--linked-selected-bg` (#EEF1FC, sombre #232B45) pour la carte choisie de la liste reliée. La sélection ailleurs garde `--selected-bg`. | Kevin, réponse 3 du 15.11 |
| 2026-11-15 | Pastilles d'information : une valeur absente ou inconnue ne donne pas de pastille (règle dans le composant de carte, téléphone et ordinateur), au lieu d'une liste de libellés interdits. | Kevin, réponse 4 du 15.11 |
| 2026-11-15 | Sombre : « À creuser » garde #B39A82 (la planche BSombre avec #6B6157 est périmée sur ce point). | Kevin, réponse 2 du 15.11 |

## Liaison rail (§18, paquet jobA1_maquette_2026-11-15_rail)

| Date | Décision | Remplace |
|---|---|---|
| 2026-11-15 | La section 18 remplace la liaison de §11 et §14 : colonne de 504 px, cartes de 480, plus de prolongement de 28 px, flèche 22 × 60 au contact de la pointe du rail (1,5 px, 9 px après la colonne), détail entièrement en cartes, carte compacte épinglée (CandidaturesOrdinateurEpinglee) sur les trois onglets. | Liaison de #722 (§11, §14). |
| 2026-11-15 | Pointe du rail : la formule du LISEZMOI fait foi (centre de la flèche − haut de la zone − 30, contact exact) ; le dessin de la planche (1,5 px plus haut) est une imprécision. | Kevin, réponse 1 sur #731 |
| 2026-11-15 | Carte épinglée de Rendez-vous : la date dans le carré de 40 px du logo (même rayon, fond neutre), jour en gras, mois abrégé dessous ; « <Entreprise> · Sélection affichée » (l'ORP pour ses rendez-vous) ; nom du bouton « Revenir au rendez-vous du 12 novembre, <Entreprise>, dans la liste ». | Kevin, réponse 2 sur #731 |
| 2026-11-15 | La barre de recherche et de filtres sort de ce qui défile : seules les cartes défilent, la barre de défilement commence sous les filtres ; la carte épinglée reste à 12 px sous la barre de recherche. | Kevin, réponse 3 sur #731 |

## États vides, Offres (Kevin, 15.11.2026, 10 h 25 et 10 h 34)

- a) Dès qu'au moins une recherche est suivie : titre « Tes alertes sont prêtes », bouton principal « Ajouter une offre », secondaire « Voir mes alertes ». « Créer mes alertes » n'apparaît que si aucune recherche n'est suivie (l'en-tête dit alors « Aucune recherche suivie »). Heure de la prochaine collecte inconnue : pastille « Offres collectées chaque jour », jamais une heure inventée.
- b) Vide parce qu'il n'y a encore rien : pas de recherche ni de filtres (ordinateur et téléphone, bouton « + » compris). Vide à cause des filtres : la barre de filtres reste, avec les filtres actifs en pastilles retirables. Dans les deux cas, la scène est centrée sur toute la largeur, sans rail ni colonne de détail.
- Poids : limite CSS relevée une seule fois de 0,5 Ko (total 117,5 Ko, Candidatures 69,5 Ko) pour les états vides et la liaison rail (section 18).

## Aujourd'hui ordinateur, l'éventail remplace le livre (Kevin, 15.11.2026, 11 h 03)

- Deux PR à la suite : la première fait Aujourd'hui (§20) et le composant éventail réutilisable (OfferFan) ; la seconde refait Trier ordinateur (§12) avec ce composant, puis retire le dernier livre (composant, CSS, images, signet, pages) et renomme l'état is_livre en is_ferme. Entre les deux, le livre reste sur Trier ordinateur.
- Couleurs des cartes : bleu = `--primary` (existant) ; deux jetons nouveaux, `--fan-orange` (#F2853A) et `--fan-yellow` (#FFE07A), les mêmes en clair et en sombre (aucun jeton existant n'avait ces valeurs).
- Police manuscrite : sous-ensemble élargi à toutes les majuscules, « · », les lettres accentuées et l'apostrophe ’, sans ligatures (Kevin, 15.11, 12 h 00 : 16 Ko au lieu de 39 Ko ; sans ligature, les deux « f » se touchent par la barre comme dans le « ff » lié). « ↗ » n'existe pas dans Caveat Brush : le lien du dos des cartes de Trier le dessine en icône SVG (Kevin, 15.11, 11 h 46).
- « livreu » (détection du métier de livreur, formulaire de profil) reste, avec un commentaire qui le protège du nettoyage.

## Pied de page et changement de page (Kevin, 15.11.2026, 11 h 09)

- Pied de page « sticky footer » sur le gabarit commun, pas page par page : `#app` en colonne, `min-height: 100dvh` (repli `100vh`), `main` en `flex: 1 0 auto`, pied de page en `flex-shrink: 0`. Page longue : le pied de page suit le contenu ; page courte : il touche le bas de l'écran. Jamais fixe ni collant : il ne recouvre pas le contenu.
- Avec des barres de défilement classiques (Windows, Linux, Mac avec souris), leur place reste réservée, vide (`scrollbar-gutter: stable`, classe `scrollbars-classic` posée par main.ts) : le logo et l'en-tête ne bougent plus entre une page courte et une page longue, ni pendant le chargement d'une page. Pas de `overflow-y: scroll`, qui laisserait une barre vide en permanence (Kevin, 11 h 31).
- Bouton « Assistant » : au moins 12 px entre lui et les liens du pied de page ; la marge du bas du pied de page (hauteur du bouton + 16 px, règle existante) suffit.
- Carte de formation : l'avancement s'écrit « Module 6 sur 12 », comme sur la planche BilanOrdinateur, y compris quand il a été noté en texte libre « module 6/12 » (affichage seulement).

## Trier ordinateur, l'éventail remplace le livre (Kevin, 15.11.2026, 11 h 44)

- Chaque carte est un bouton (`aria-pressed` faux à l'endroit, vrai au dos), nommé « poste, entreprise. notes entières. Retourner pour voir l'extrait ». Focus : contour de 2 px `--primary-graphic`, décalé de 3 px, qui suit l'arrondi de la carte.
- Clavier : ← Écarter et → Garder inchangés ; Tab et Maj+Tab passent d'une carte à l'autre ; Entrée ou Espace retourne la carte ; Entrée sur « Voir l'annonce complète » ouvre l'annonce sans retourner la carte (le lien est à côté du bouton, pas dedans).
- Mouvement réduit : ni étalement animé ni rotation 3D, un fondu de 150 ms au plus.
- « Écarter » affiche « Offre écartée » et « Annuler », le même bandeau et la même durée que « Garder ».
- Badge « Gardée » : le style de la puce de la liste Candidatures, icône signet orange #F2853A ; fond et texte `--peach-soft` / `--peach-text`.
- Signet : gardé sur la carte du téléphone ; fichier, composant et classes renommés « signet » (SignetMark). L'écran « Rien à trier » est refait à part (#735).
- La ligne des touches ← → sous le compteur est retirée (Kevin, 15.11, 12 h 40) : les boutons portent `aria-keyshortcuts` et le titre « Écarter (←) » / « Garder (→) ».

## Carte Google Emplois, nouveau compte sans offre (Kevin, 15.11.2026, 11 h 46, 12 h 17 et 12 h 27)

- Tant qu'aucune offre n'est arrivée et qu'un métier (ou une alerte) donne une recherche : carte « Des offres pour toi, en attendant » sur Aujourd'hui, ordinateur et téléphone (planches AujourdhuiOrdinateurNouveau et AccueilNouveau, §22). Sous les premiers pas s'ils sont visibles, en premier s'ils sont fermés, jamais au-dessus. Sans métier, pas de carte ; elle part à la première offre.
- Sous-titre « Métier · Lieu » seulement : ni « 4 derniers jours » ni « récemment », la recherche ne filtre pas par date. Bouton « Voir sur Google Emplois », aria-label « Voir les offres sur Google Emplois (nouvel onglet) ».
- La requête garde le mot « emploi », qui ouvre le panneau Google Emplois ; il n'est pas affiché.
- « Masquer » : message « Carte masquée » + « Annuler » 6 s, puis retenu pour le compte, sans réglage pour la réafficher. Il ne cache que la carte d'Aujourd'hui.
- Candidatures vide, avec ou sans alerte : lien « Voir les offres sur Google Emplois » au-dessus de « Faire une candidature spontanée », jamais caché par « Masquer ».

## Contour des boutons secondaires (Kevin, 15.11.2026, 11 h 57)

- `--line-strong` (#D8D4CA) ne change pas : contours de champs, barre de recherche, séparateurs.
- Nouveau jeton `--button-outline` : #C9C5BA, sombre #4E473E, pour tous les boutons secondaires à contour gris (« Plus de filtres », « Retirer l’accès », « Annuler », pastilles, boutons ronds, « + Ajouter » en pointillé).
- « Plus de filtres » : le demi-pixel restant (espace 8 au lieu de 6, icône 16,5 au lieu de 18) est accepté.

## Jour de repos et tri (Kevin, 15.11.2026, 12 h 24)

- Le jour de repos ne bloque jamais une action choisie par l'utilisateur (planche AujourdhuiOrdinateurV2, état is_repos). Il change seulement le ton d'Aujourd'hui (« Jour de repos. Ta semaine est faite. Si tu veux avancer, N choses t'attendent. ») et coupe les rappels et les notifications de ce jour-là.
- Trier n'a pas d'écran « Jour de repos ». Aujourd'hui, Trier et l'assistant comptent les offres à trier avec la même règle (useDailyDose : pickDose, isTriagePending).
- Rappels d'échéance obligatoire (remise des preuves ORP, veille d'un rendez-vous ORP) : jamais coupés par le jour de repos. Un jour de repos, ils partent si l'échéance tombe au plus tard le prochain jour normal ; sinon ils sont décalés au prochain jour normal, à la même heure (Kevin, 15.11.2026, 12 h 45).
- Trier à 0 offre : « Rien à trier pour l'instant » sur l'état vide commun (§13) : mascotte de FinDuTriAucune, titre manuscrit, pastille « Offres collectées chaque jour », boutons « Voir mes candidatures » (principal) et « Gérer mes alertes » (contour) ; ni éventail vide ni Écarter / Garder (Kevin, 15.11.2026, 12 h 45).

## Formations ordinateur, plus de « Module terminé » (Kevin, 15.11.2026, 16 h 33)

- Dans « En cours » de la vue d'ensemble Formations sur ordinateur, « Module terminé » et ses boutons − et + sont retirés : « Module N sur 12 » avec la barre suffit, comme sur la planche BilanOrdinateur.
- « Marquer comme terminée » (au dernier module) et « Noter l'avancement » restent. Le téléphone (Suivies) garde le compteur jusqu'à sa propre page.
- Le compte se note dans le panneau « Noter l'avancement » : champ « Modules faits » (nombre, de 0 au nombre de modules, libellé visible), sous « Nombre de modules ». Au-delà du total, rien n'est enregistré et « Pas plus de N modules » s'affiche sous le champ. La carte montre ensuite « Module N sur 12 » (Kevin, 15.11.2026, 18 h 01).

## Offre ajoutée à la main, notée comme les autres (Kevin, 15.11.2026, 16 h 33 et 16 h 39)

- Une offre ajoutée à la main est notée comme les autres, quel que soit son statut (écartée par les critères, gardée, en préparation, envoyée). La note part dès l'ajout.
- Pendant la notation, la carte de la liste ordinateur montre le cercle vide en pointillés et la pastille « Pas encore notée » (§21, paquet jobA1_maquette_2026-11-15_reglages), puis la note s'affiche sans recharger la page.
- Les offres ajoutées à la main avant le 16 novembre et jamais notées ne sont pas reprises au passage automatique : une commande ponctuelle, idempotente, donne d'abord leur nombre et le coût estimé, puis les note sur accord.
- Téléphone (Kevin, 15.11.2026, 17 h 25) : même traitement que l'ordinateur. Cercle vide en pointillés de 48 px à la place de l'anneau (aria-label « Pas encore notée ») et pastille neutre « Pas encore notée » en première position. Les pastilles qui ne tiennent pas sur la ligne passent dans « +N » (planche Candidatures), jamais coupées.
- « Donner l'annonce pour la noter › » (§18) : plus tard, pas dans la PR de la notation manuelle.

## Carte épinglée de Rendez-vous, date en icône calendrier (Kevin, 15.11.2026, 16 h 42)

- Remplace la décision « la date dans le carré de 40 px du logo » (Liaison rail) : la carte épinglée de Rendez-vous montre la même icône calendrier que les cartes de la liste et la carte d'en-tête (mois abrégé en capitales en haut, jour dessous), à 40 px comme le logo de la carte épinglée d'Offres.
- Même ton que la carte représentée, comme dans la liste : orange pour un rendez-vous ORP, bleu pour un entretien, gris pour un rendez-vous passé déjà noté.
- Le nom du bouton garde la date complète ; variante du bas à 12 px du bas de la zone de liste, comme les 12 px sous les filtres en haut.

## Modèles de la lettre et du CV (Kevin, 15.11.2026, 17 h 33 et 19 h 07)

- Classique : la police Georgia est gardée ; c'est la police du document, pas celle de l'interface (la planche indique Fraunces, non chargée).
- Bandeau : pêche partout (#F3B08A, la teinte du PDF et de la planche PreparerMiseEnPage). La vignette « Bandeau » de la carte Mise en page sur ordinateur passe du bandeau foncé des planches PreparerOrdinateur (et du bandeau clair de PreparerOrdinateurSombre) au pêche, avec le trait du nom en #1B1F2A. En sombre, le bandeau reste pêche : c'est la couleur du document.

## Premiers pas d'Aujourd'hui en cinq lignes (Kevin, 15.11.2026, 17 h 39)

- Option B pour la section 22 (planche AujourdhuiOrdinateurNouveau) : cinq lignes dans le style de la planche, compteur « N sur 5 », au lieu des trois lignes « 2 sur 3 » dessinées. Un seul composant de ligne pour les cinq étapes ; l'ancienne carte « 2 sur 5 » à une seule action est supprimée.
- Étapes : 1 « Ton CV est lu » (« N compétences reprises ») ; 2 « Tes critères sont réglés » (« Métier · Lieu · taux ») ; 3 « Créer ta première alerte » (« jobup : 2 minutes », bouton « Créer mon alerte ») ; 4 garder des offres ; 5 préparer et envoyer.
- Avant la première offre, les étapes 4 et 5 sont grisées, sous-titre « Dès ta première offre », sans bouton, aria-disabled="true".
- Trois étapes faites sans offre : « 3 sur 5 », l'étape 4 dit « Ta première offre arrive après la prochaine collecte », sans bouton.
- L'écran « C'est fait ! » reste à la fin des cinq étapes.
- Serveur : CV et critères séparés ; /api/today renvoie compétences, métier, lieu et taux. Les étapes gardées pour le compte, l'équipe et les applications partenaires ne changent pas.
- Poids : pas de relèvement de limite ; fusion seulement après le retrait du livre de Trier.
- Téléphone : plus tard, avec la nouvelle page d'accueil. La mise en page attend la planche mise à jour.

## Préparer, carte « Ce CV » (Kevin, 15.11.2026, 17 h 57)

- « N changements, à vérifier » prend l'orange d'alerte `--warning` (clair #A8540E, sombre #F2A766) : c'est une action à faire, pas une réussite. Remplace le vert de la planche PreparerOrdinateurCVPret.
- Les lignes de « Ce CV » (et de « Ta candidature », qui partage les mêmes lignes) tiennent dans la carte : largeur 100 %, sans marge négative ; la carte n'a pas de marge sur les côtés, le titre et les lignes portent les 18,5 px. Un texte long est coupé sur une ligne avec points de suspension ; dans « Ce CV », le texte complet est dans l'aria-label de la ligne.

## Code jobup : relevé partagé de la boîte tant qu'une page attend (Kevin, 15.11.2026, 18 h 24 et 18 h 49)

- L'étape « Recopie le code de jobup » signale son attente dès son affichage, puis chaque minute tant qu'elle attend et que l'onglet est visible, 10 minutes au plus ; l'attente finit 75 s après la dernière relance, ou dès que le code du compte est arrivé. « J'attends un code » et l'extension attendent 5 minutes.
- Un seul relevé partagé lit la boîte toutes les 15 s tant qu'au moins une attente est en cours, et range chaque code selon son adresse. Plafond : 240 relevés rapides par heure, un toutes les 15 s, quel que soit le nombre d'attentes ; pas de plafond par compte.
- La boîte des invités est lue même si la boîte Gmail de l'exploitant échoue, et inversement ; l'erreur est relancée après.
- Ligne d'état de l'étape : « on vérifie toutes les 15 s » (la vraie fréquence du serveur).
- Retiré : le message « Déjà six relevés rapides cette heure-ci », qui ne pouvait plus s'afficher (Kevin, 19 h 02).
- La boîte jobA1 ne répond pas (Kevin, 19 h 02) : après 3 lectures ratées de suite de la boîte des invités (Infomaniak indisponible, erreur IMAP), la ligne d'état de l'étape 3 devient « La boîte jobA1 ne répond pas. On réessaie dans 1 minute. », même style, icône d'alerte orange. Le relevé ne relit plus la boîte qu'une fois par minute tant qu'elle ne répond pas. La ligne revient à l'attente dès qu'une lecture réussit. Aucun détail technique affiché ; dans les journaux, le type d'erreur seulement, ni adresse ni code.

## Premiers pas : compléments du §23 (Kevin, 15.11.2026, 18 h 24)

- Croix « Masquer les premiers pas » gardée : 44 × 44 px à droite du compteur, bandeau « Premiers pas masqués » + « Annuler ».
- Téléphone : la liste dans une carte, en attendant la nouvelle page d'accueil.
- Sous-titre du bloc d'accueil : « Crée ta première alerte : jobA1 s'occupe du reste. » avant l'alerte ; « Ton alerte est créée. La prochaine collecte t'apporte tes premières offres. » après.
- ORP : la phrase commune (« Encore N d'ici le <date> »), pas celle de la planche.
- Un seul bouton, sur l'étape en cours : 3 « Créer mon alerte », 4 « Trier mes offres », 5 « Préparer une candidature ». Étapes faites : « Fait », sans bouton ; à venir : grisées, sans bouton. Pas les mots de l'ancienne carte.
- Bandeau à trait de compte à rebours partout où il y a « Annuler » (Gardée, Écartée, Carte masquée, Premiers pas masqués, Navigateur retiré) : un seul composant, dans la feuille commune ; coût à mesurer.

## Offres sur téléphone, réponses du 16 novembre (Kevin, 16.11.2026)

- « Voir la compatibilité » est bleu (`--primary-text`) partout, offre provisoire comprise : un lien garde la même couleur sur tous les écrans (Nielsen, heuristique 4). La planche OffreProvisoire, qui le dessinait foncé, avait tort ; Kevin la corrige.
- La flèche d'envoi grise quand le champ est vide est voulue sur tous les champs à flèche (Ajouter, assistant) : même état désactivé partout, flèche toujours visible et annoncée avec `aria-disabled`.

## Offres jamais notées, A2 : écartée et note impossible (Kevin, 16.11.2026, 8 h 18)

- Une offre écartée par les critères et sans note n'a pas d'anneau et n'affiche jamais « Pas encore notée » : pastille neutre « Écartée » dans la rangée de pastilles, à la place. Une offre ajoutée à la main reste notée même écartée (décision du 15.11) et garde le cercle d'attente.
- Note impossible (trois échecs de l'IA, ou annonce sans texte) : sur la carte, le même cercle gris en pointillés sans chiffre et une pastille neutre « Pas de note ».
- Dans la fiche, une ligne selon la cause : annonce sans texte → « L’annonce est trop courte pour être notée. » ; échec de l'IA → « La note n’a pas pu être calculée. » avec un bouton « Réessayer », parce que le serveur ne réessaie plus après le 3e échec (« Nouvel essai demain » écarté).

## Étape 3, trajet du code en 3 points et scène de la boîte aux lettres (Kevin, 16.11.2026, 9 h 16)

- Sections 24 et 25 du paquet du 15.11 appliquées à l'étape « Alerte » des premiers pas, ordinateur et téléphone ; la scène de la boîte aux lettres sur ordinateur seulement.
- 10 minutes sans code : pas d'état « code expiré ». L'étape reste en attente (point 1 sans coche, point 2 « on écoute », aide « Toujours rien ? » visible) et la relecture s'arrête. « Code expiré » seulement pour un code reçu puis périmé.
- Boîte qui ne répond pas : point 2 en orange, « ne répond pas », même icône que « expiré » ; la ligne d'état dit « La boîte jobA1 ne répond pas. On réessaie dans 1 minute. » et « Toujours rien ? » est masqué.
- Le trajet est aussi dans le panneau « Alerte jobup » de la page Alertes (même boîte, variante ordinateur), sans planche propre.
- Écarts acceptés : bordure `--card-line` (#CFCBC1) au lieu de #C9C5BA ; fonds sombres des coches et de l'icône « expiré » repris des jetons existants. Les images orange-salut, devenues inutiles, seront retirées dans une PR de nettoyage à part.

## Bilan ordinateur, menus ouverts, mois déplié et fiche sombre (Kevin, 16.11.2026, 9 h 00 et 9 h 25)

- Les planches du paquet jobA1_maquette_2026-11-16_bilan (§29, recopié dans docs/maquette/2026-11-16/) font foi pour le Bilan sur ordinateur. Elles remplacent la règle provisoire de 9 h 00 (« sans planche, style du menu ⋯ »).
- Menus « Mois précédents » et « Autres exports » (planches BilanOrdinateurMoisPrecedents et Exports) : 300 px, rayon 16, lignes de 44 px, ouverts vers le haut, chevron du bouton qui se retourne ; « À remettre » en orange sur le mois dont les justificatifs restent à remettre.
- Mois déplié (planche BilanOrdinateurMois) : « Voir les N autres » devient « Replier le mois » une fois toutes les recherches affichées ; la carte du mois montre un chevron vers le haut et replie aussi.
- Fiche « Pour l'ORP » (planches BilanOrdinateurFiche et FicheSombre) : lignes de 64 px au lieu de 56 ; palette sombre commune.

## Tâche « Envoyer N candidatures » d'Aujourd'hui, fonction manquante (Kevin, 16.11.2026, 9 h 41)

| Date | Fonction (planche) | Ce qu'il faudrait |
|---|---|---|
| 2026-11-16 | Tâche « Envoyer N candidatures · Lettres et CV déjà prêts » dans « À faire » d'Aujourd'hui (AujourdhuiOrdinateurV2 et AccueilV2, états « accueil » et « repos ») | Savoir quelles candidatures ont leur lettre et leur CV prêts, offre par offre, et en tirer N. Ce calcul n'existe pas : jobA1 montre seulement « Préparer N candidatures » (offres gardées sans lettre). Rien n'est codé : la marge de poids JS est presque épuisée. La tâche reste sur la planche comme objectif, marquée « à venir » par Kevin. |

## Bilan ordinateur, Résultats : chargement par les blocs gris existants (Kevin, 16.11.2026, 10 h 15)

- Le chargement de Résultats reprend LoadingBlocks tel quel (trois blocs gris avec reflet), sans la forme dessinée sur la planche BilanOrdinateurChargement : la limite de CSS n'est pas relevée. Erreur et Trop tôt suivent la planche.

## Bilan ordinateur, Formations : « Noter l'avancement » sur toutes les formations en cours (Kevin, 16.11.2026, 10 h 15)

- « Noter l'avancement » reste sur toutes les cartes « En cours », avec ou sans nombre de modules. La planche BilanOrdinateurFormEtats, qui ne le montre que sur la carte sans modules, sera corrigée dans ce sens.

## Coordonnées trouvées dans le CV : dans la relecture du CV (Kevin, 16.11.2026, 10 h 33)

- Bloc « Tes coordonnées » en tête du panneau « Repris de … » (relecture du CV, Profil › Mon CV › « Choisir les éléments »), au style des cartes existantes du panneau. Pas de planche à attendre : Kevin la dessine d'après la capture de la PR.
- Seulement les champs encore vides du profil (nom, rue, NPA, localité, téléphone, e-mail), déjà remplis et modifiables ; un champ déjà rempli n'est jamais proposé ni écrasé.
- Enregistrés avec « Ajouter N éléments » (le bloc compte pour un élément), jamais avant ; « Annuler » ou le bloc décoché n'enregistre rien. La règle « Rien n'est enregistré avant » reste.
- Rien ne part à l'IA : les coordonnées sont repérées sur le serveur, sans IA.
- Pas dans les premiers pas (ils sont déjà longs).

## Agences de placement, détection (Kevin, 16.11.2026, 10 h 34)

- Section 35 du paquet du 16.11 : plan validé. Détection sans IA, avec la liste des agences connues (titre « Agence de placement ») et les phrases de l'annonce comme « pour notre client » (titre « Probablement une agence de placement »).
- « Ce n'est pas une agence » : la correction est gardée par compte, pour l'entreprise, et passe avant la détection.
- Alerte doublon : si une candidature a été envoyée ces 90 derniers jours à un poste proche (titre proche, même ville), chez l'employeur ou via une autre agence, la ligne de la fiche le dit.
- Le répertoire SECO des entreprises autorisées n'est pas utilisé tant que le SECO n'a pas donné son accord écrit. Lui écrire est une bonne idée, mais ça ne bloque pas le reste.

## Taille des cibles dans les filtres (Kevin, 16.11.2026, 11 h 50)

- Ordinateur : les pastilles du panneau Filtres gardent 36 px de haut, comme sur la planche. WCAG 2.2 AA (2.5.8)
  demande 24 px ; les 44 px valent pour le tactile.
- Téléphone : 44 px au moins.
- Pas de règle CSS en plus pour ça.

## Agences de placement, fiche et « Annuler » (Kevin, 16.11.2026, 12 h 10)

- Pour une agence, la fiche ne montre plus le doute « Employeur caché : annonce d'agence » : la ligne « Agence de placement » suffit.
- Après « Ce n'est pas une agence », le bandeau commun « Correction enregistrée. Annuler » s'affiche, avec le trait du compte à rebours, comme « Offre écartée ».
- Les 2 octets de CSS de trop ne sont pas regagnés dans cette PR : une PR « Allègement CSS » à part regroupe les règles en double de toute l'app, pour les PR #764, #770 et #771 ensemble.

## Voile derrière les panneaux : noir à 60 % en sombre (Kevin, 16.11.2026, 12 h 10)

- En sombre, le voile derrière les panneaux latéraux, les feuilles ouvertes en panneau sur ordinateur et la confirmation Get'emAll devient rgb(0 0 0 / 60%), comme sur la planche BilanOrdinateurFicheSombre (paquet du 16.11). En clair, il reste rgb(27 31 42 / 45%). Une variable commune, --voile, porte les deux valeurs.

## Cartes « À venir » de Rendez-vous sur deux lignes (Kevin, 16.11.2026)

- Ordinateur et téléphone : deux lignes au plus, comme la planche RendezVous. Ligne 1 : le titre (« Rendez-vous ORP » ou l’intitulé du poste) et sa pastille sur la même ligne ; « Ta feuille est prête » devient « Feuille prête » (vert). Ligne 2 : l’heure et le délai (« 9 h · dans 3 jours »), puis le lieu s’il existe, coupée par « … ».
- L’icône calendrier garde la date. Le surtitre (« Dans 3 jours », « Entretien d’embauche ») disparaît : le délai est en ligne 2.
- Même hauteur que les cartes Offres sur ordinateur (104 px).
- Sur téléphone, toute la carte ORP ouvre la feuille de préparation, comme la planche (lien vers RendezVousPreparer) et comme la carte entretien ; le bouton « Préparer le rendez-vous » sort de la carte, le « ⋯ » reste.
- Le détail de droite sur ordinateur garde « Ta feuille est prête » à côté des boutons.

## Réponses des entreprises transférées (Kevin, 16.11.2026, 12 h 36)

- Option retenue : la personne transfère à la main la réponse d'une entreprise vers son adresse d'alertes habituelle (docs/146). Pas de connexion à sa boîte, pas de filtre automatique pour l'instant.
- Le serveur garde ce transfert, retrouve la candidature d'après l'expéditeur puis le nom de l'entreprise, et range la réponse en entretien, refus ou autre avec des mots-clés, sans IA.
- Rien ne change tout seul : une notification « Ivy Partners t'a répondu : entretien ? » ouvre la candidature et la personne confirme. « Il faut une vraie transparence sur ce que fait l'IA. »

## « Avant ta lettre » préremplie depuis le CV (Kevin, 16.11.2026, 12 h 51)

- La feuille « Avant ta lettre › Coordonnées » (Préparer) remplit ses champs vides avec les coordonnées lues dans le CV, sans IA, sans rien demander.
- Un champ n'est rempli que si la lecture est sûre : NPA = quatre chiffres suivis d'une localité ; un seul téléphone ; un seul e-mail en tête du CV. Sinon il reste vide. La règle vaut aussi pour Profil › Coordonnées et la relecture du CV (même lecture côté serveur).
- Marque « Du CV » à côté du libellé, qui disparaît dès que l'utilisateur modifie le champ ; le champ est décrit par « Repris de ton CV, vérifie-le. » (aria-describedby).
- Jamais d'écrasement d'un champ déjà rempli dans le profil.
- « Enregistrer » met aussi à jour Profil › Coordonnées, comme la relecture du CV (#769) ; rien n'est enregistré avant.

## Réponses des entreprises : le téléphone pour les invitations seulement (Kevin, 16.11.2026, 13 h 08)

- Exception au jour de repos pour les invitations à un entretien uniquement : une notification sur le téléphone, une seule fois, sans rappel.
- Refus, accusés de réception et autres réponses restent dans la cloche (jamais sur le téléphone).
- Précise docs/decisions/2026-11-16-1236-reponses-employeurs.md (docs/146 §2.6).

## Roue d'attente sur « Refaire la note » (Kevin, 16.11.2026, 13 h 20)

- Fenêtre « Coller le texte de l’annonce » : pendant que jobA1 enregistre le texte et refait la note, une roue tourne
  devant « Refaire la note », pour qu’on voie que la plateforme traite l’annonce. La planche OffreProvisoire ne dessine
  pas cet état ; c’est la roue de lecture de l’annonce (18 px), dans la couleur du texte du bouton, et le bouton
  garde sa couleur pleine pendant l’attente (gris seulement tant que le texte est trop court).

## Ligne « Pourquoi » du CV, partie serveur et IA (Kevin, 16.11.2026, 13 h 37)

- Le prompt cv-v2 (une raison par changement) ne sert qu'à `make mesure-pourquoi` ; cv-v1 reste en service. La bascule se fera dans une petite PR après la mesure de Kevin.
- La vérification des citations compare des mots ou expressions entiers (frontières de mot), sans accents ni majuscules, pas des sous-chaînes : « Go » ne valide pas « Google », « Java » ne valide pas « JavaScript ».
- Les mots cités restent dans la langue de l'annonce, entre guillemets, même si la raison est en français.
- Un changement demandé par l'utilisateur via « Demander une modification du CV » n'a pas de raison de l'IA : l'API renvoie `origin: "user"` et l'interface affiche « Demandé par toi ».
- `make mesure-pourquoi` utilise 5 CV fictifs (aucune donnée de compte réel) et n'affiche que des chiffres : jetons et prix par CV, total, différence v1/v2.

Précisions de Kevin (16.11.2026, 13 h 52) :

- Un bloc ajouté a lui aussi une raison, même règle (mots de l'annonce, vérifiés). Son contenu vient toujours des blocs existants de l'utilisateur, jamais inventé.
- « Demandé par toi » suit le changement : gardé si la nouvelle version contient encore la demande. Sinon, l'interface affiche une fois « N de tes demandes ne sont pas reprises dans cette version » avec un bouton « Les réappliquer » (PR d'affichage). Le serveur garde la liste des demandes de l'utilisateur pour pouvoir les réappliquer.

## Offre renotée hors des filtres (Kevin, 16.11.2026, 13 h 39)

- Après « Refaire la note » (texte collé, lien donné ou lecture de l’annonce), une offre dont la nouvelle note sort des
  filtres de la liste ne disparaît plus : elle reste ouverte et en tête de liste, avec la pastille neutre « Hors de tes
  filtres », jusqu’au prochain changement de filtre ou au départ de la page.
- Dans la fiche, sous la note : « Nouvelle note : {n}. Elle sort de ton filtre « {seuil} ». », avec le libellé du filtre
  de note en vigueur ; la phrase est annoncée (aria-live="polite").
- Si on change ensuite le statut de l’offre (écarter, garder…), la règle commune revient.

## Bilan sur téléphone : trop tôt, erreur, aucune formation (Kevin, 16.11.2026, 13 h 50)

- Les trois états du Bilan sur téléphone suivent les planches BilanTropTot, BilanErreur et BilanFormationsVide (§37 du paquet du 16.11) : scène, titre, pastille et bouton, avec l'état vide commun, à la place des paragraphes simples.
- Pastilles raccourcies : « Il se remplit avec tes candidatures », « Tes candidatures ne sont pas touchées », « Garde-en une avec son signet ». Titre de l'erreur : « Bilan indisponible ».
- Chargement : trois blocs de 96, 160 et 256 px.
- L'ordinateur ne change pas (§29).

## Réglages « Objectif ORP et sites » (Kevin, 16.11.2026, 13 h 51)

Pas de planche pour cette page : la référence est le message de Kevin. Ordinateur et téléphone, clair et sombre.

1. En-tête : « ← Retour aux réglages » passe au-dessus du titre, pas à côté. Le lien, le titre et les cartes commencent au même bord gauche. Même en-tête sur toutes les sous-pages de Réglages.
2. Les champs chiffrés forment une colonne fixe, alignée d'une carte à l'autre. Grille de la carte : texte 1fr, champ 72 px, unité de largeur fixe (assez pour « du mois suivant »), écart 12 px. Le « le » devant le jour est retiré : « [5] du mois suivant ».
3. Les champs prennent le rayon standard des champs de saisie de l'app (12 px, celui du champ à libellé flottant), pas la pilule. Hauteur 44 px, chiffre centré.
4. Description de « Date limite des justificatifs » : « À rendre chaque mois avant ce jour. » « Objectif mensuel de l'ORP » garde « Les candidatures demandées chaque mois. »

## Colonne de droite sans élément ouvert, sur ordinateur (§36, Kevin, 16.11.2026, 13 h 52)

- Offres, Envoyées et Rendez-vous sur ordinateur : rien d'ouvert à l'arrivée ; la colonne de droite montre la scène
  « Choisis une offre », « Choisis une candidature » ou « Choisis un rendez-vous » (scènes choisis-* du paquet du 16.11).
  La première carte ne s'ouvre plus d'elle-même.
- `?offre=`, `?candidature=` et `?rdv=` ouvrent toujours l'élément.
- Après « Écarter » : l'offre quitte la liste, aucune autre ne s'ouvre, la scène « Choisis une offre » s'affiche avec
  la confirmation commune « Offre écartée · Annuler » (bandeau à trait). « Annuler » remet l'offre à sa place,
  choisie, son détail ouvert.

Précisions de Kevin (16.11.2026, 15 h 10), sur les écarts de la #798 :

- Pastille en sombre : #AEBDFF (`--primary-text`), comme les autres états vides, et non le #C9D3FF de la planche.
- Pastille : la grille de 4 l'emporte ; marges de 8 px (6 sur la planche).
- Bandeau « Offre écartée · Annuler » en bas à droite, comme partout dans l'application ; la planche sera corrigée.
- Nouvelle scène d'erreur du Bilan (§36) : dans une PR à part.

## Formations : catalogue vide pour « Mon domaine » (Kevin, 16.11.2026, 13 h 53)

- Quand le catalogue vérifié n'a rien pour « Mon domaine », avant tout filtre : titre « Rien dans le catalogue pour {domaine} », pastille « Le catalogue couvre surtout l'informatique pour l'instant », bouton principal « Chercher des formations en {domaine} » (la recherche web existante). {domaine} est le premier mot-clé de « Mon domaine ».
- « Aucune formation avec ces filtres » reste seulement quand ce sont les filtres qui vident la liste.
- Le catalogue des soins viendra d'une liste sourcée fournie par Kevin : aucune formation inventée.

## Offre écartée sans note : la date de mise à l'écart, « Remettre dans le tri » (Kevin, 16.11.2026, 13 h 53)

- §30 du paquet du 16.11 : dans la fiche, « Écartée le 12 nov. » à la place de « Écartée » seul ; lien « Remettre dans le tri » (téléphone : dernière ligne de la carte de note ; ordinateur : à droite de la ligne de note) ; plus de bouton « Écarter » sur une offre déjà écartée (téléphone : « Préparer ma candidature » prend toute la largeur).
- Option A : une colonne `offers.set_aside_at`, posée à chaque mise à l'écart (la personne, Trier, l'assistant, les critères). Pas de rattrapage : une offre écartée avant la colonne affiche « Écartée » seul.
- « Remettre dans le tri » vide la date ; une nouvelle mise à l'écart pose la nouvelle date.
- Format de date habituel : « 12 nov. », l'année seulement si ce n'est pas l'année en cours.

## Bilan › Formations sur téléphone (Kevin, 16.11.2026, 14 h 06)

- « Mes formations » d'abord (carte de l'ORP, En cours, Gardées), le catalogue derrière « Voir le catalogue » et « Chercher d'autres formations », comme sur ordinateur. Les onglets Catalogue / Suivies disparaissent ; « ← Mes formations » ramène depuis le catalogue (planches BilanFormations et BilanCatalogue, §37).
- Le compteur « − N + » quitte la carte « En cours » : « Noter l'avancement » ouvre une feuille du bas qui le contient. Même chose sur ordinateur. Sans nombre de modules, « Noter l'avancement » ouvre le panneau de la formation, comme avant.
- Le titre de la carte « En cours » ouvre le panneau de la formation (notes, financement, profil), pour que ces fonctions restent accessibles.
- Catalogue sur téléphone : lignes sur deux lignes (titre ; « organisme · format » et le prix), sans icône, signet rond de 44 px. L'avancement et le financement restent dans le panneau.

## Bilan › ORP sur téléphone (Kevin, 16.11.2026, 14 h 06)

- La carte « Mois ORP · novembre · 7 sur 10 », avec sa barre et son chevron, remplace l'anneau ; elle déplie et replie le mois.
- Cartes de recherche sur 2 lignes : entreprise + pastille d'état, puis poste · date.
- Replié : les trois premières à déclarer. Déplié : toutes, puis les recherches du mois, puis « Replier le mois ». Plus de « Afficher l'autre ».
- En bas, deux pilules « Mois précédents » et « Autres exports », chacune ouvre sa feuille du bas ; « Exporter le formulaire (PDF) » passe dans « Autres exports ».
- Règle : hors d'une carte, seulement un titre ou un lien. Une phrase vraiment utile devient une pastille. Les phrases sous les intertitres sont retirées.

## Ma candidature › CV sur téléphone (Kevin, 16.11.2026, 14 h 06)

- Kevin : « pas besoin de proposition, code-le selon les planches MaCandidatureCV, MaCandidatureCVPourquoi, MaCandidatureCVRecherche, dans une PR à part » (§37 du paquet du 16.11).
- Sous les étapes : « Changements · N » (pilule, surligne les passages changés), la loupe ronde de 44 px, le lien « Modèle » (la feuille Mise en page et langue). La recherche remplace la rangée.
- Le CV entier s'affiche tout de suite, sans aperçu à toucher ; la page suit le thème clair ou sombre.
- Toucher un passage surligné ouvre « Changement N sur M » : Avant, Maintenant, Pourquoi (la raison du serveur, mots de l'annonce surlignés ; « Demandé par toi » pour une demande de l'utilisateur), « Annuler ce changement », précédent et suivant.
- La retouche est le champ « Demander une modification du CV » ; le bouton du bas devient « J'ai relu, continuer » (note la relecture, puis Postuler), comme sur ordinateur.
- Retirés du téléphone parce qu'absents des planches : l'aperçu à toucher, les mots mis en avant sous l'aperçu (ils restent en gras dans le CV), la case « J'ai relu le CV » (remplacée par le bouton du bas), « Modifier le texte avec l'Assistant » (remplacé par le champ).
- Kevin, 16.11 à 15 h 51 : les quatre fonctions retirées du téléphone (l'aperçu à toucher, les mots sous l'aperçu, la case « J'ai relu le CV », « Modifier le texte avec l'Assistant ») sont enlevées pour de bon ; les planches les remplacent.
- Kevin, 16.11 à 15 h 51 : le surlignage de « Pourquoi » ne dépend pas des guillemets. Avec chaque raison, l'IA donne à part la liste des mots tirés de l'annonce (`words`, prompt cv-v2) ; le serveur les vérifie dans le texte de l'offre et les renvoie dans `quotes` ; le téléphone les surligne avec la même fonction que « Mon domaine » (`highlight`, sans majuscules, mots entiers).

## Un seul relèvement du CSS pour #764, #770 et #771 (Kevin, 16.11.2026, 14 h 08)

- Avant ces trois PR, un allègement à part (#777) : 47 groupes de règles identiques de `style.css` réunis, −189 octets gzip, 138 captures sans un pixel d'écart. L'objectif de 470 octets n'est pas atteignable par regroupement (plafond mesuré ≈ 390 octets).
- Mesures sur main du 16.11 : #764 ajoute 413 octets de CSS, #770 397, #771 168. Les trois avec #777 : css-total 119 403 octets.
- Décision : css-total passe de 118 780 à 119 450 octets, une seule fois, dans #777, pour les trois PR ensemble. Pas de relèvement PR par PR.
- #770 garde le contour du résultat courant (sans lui, seule la couleur distingue le résultat courant, WCAG 1.4.1).
- JS : pas de relèvement de js-total sans que Kevin ait vu les chiffres. Avant de fusionner la troisième PR, mesurer l'apport JS de chacune et proposer un découpage (chargement à la demande des parties absentes du premier écran).

## Cartes de rendez-vous en 2 lignes : réponses de Kevin (16.11.2026)

- Le délai figure aussi sur la carte entretien, en ligne 2, jamais sur une 3e ligne.
- La pastille de l’entretien reste « À préparer » (orange), sur ordinateur comme sur téléphone ; pas de « Entretien » neutre, le titre le dit déjà.
- À 320 et 360 px, le titre peut être coupé par « … », à trois conditions : le titre complet est dans le nom accessible et dans le détail ; l’heure et le délai ne sont jamais coupés (ils passent en tête de la ligne 2, seuls l’entreprise et le lieu se coupent) ; la zone du « ⋯ » fait au moins 24 × 24 px (elle fait 44 × 44).

## Formations en soins : diplômes acceptés et vérification des liens (Kevin, 16.11.2026, 14 h 11)

- 14 formations de Suisse romande entrent au catalogue vérifié, d'après la liste sourcée de Kevin ; aucune n'est inventée. Un lien mort = la fiche n'entre pas.
- Chaque fiche porte la liste des diplômes acceptés (vide = sans diplôme) : soins infirmiers, Bachelor HES santé, Bachelor HES travail social. La fiche HE-Arc accepte les deux Bachelor.
- Le diplôme de la personne vient de ses blocs : Bachelor, diplôme ES ou HES en soins infirmiers, « Diplôme d'État infirmier », ou « infirmier·ère » dans le titre d'une expérience. « J'ai ce diplôme » corrige la détection.
- Vérificateur de liens : 404, 410 ou page « 404 / page non trouvée » = mort ; erreur 5xx, délai, page « Cookie not accepted » = à revérifier dans 24 h, jamais mort. Une fiche du catalogue ne s'affiche qu'une fois son lien vérifié. Les fiches orientation.ch (1, 2, 3) attendent ainsi la fin de la panne du site.
- Remplacements : 6, 7 et 8 par les pages officielles de La Source (la brochure PDF de la 7 renvoie vers une page 404) ; 14 par la fiche du CHUV.

## Notes de l'éventail sur une ligne (Kevin, 16.11.2026, 8 h 56 et 14 h 19)

- Chaque carte garde ses 3 notes, sur 1 ligne chacune avec « … », qu'elle ait une forme courte (score-v9) ou non
  (PR #755).
- Entre la dernière note et le poste : 24 px au moins (`--space-6`), le même écart qu'entre l'en-tête et les notes.
- Les notes restent centrées. Une note coupée garde une marge de chaque côté, comme une note courte : Kevin avait
  demandé « environ 88 % de la largeur de la carte ».
- Écart retenu, validé par Kevin à 14 h 19 : 16 px de chaque côté (`--space-4`), soit une ligne de 240 px sur les
  272 px de la zone de texte (88 %). Raisons :
  - 88 % de la carte entière (282 px) dépasserait la zone de texte, qui fait 272 px à cause du padding de 24 px ;
  - `max-width: 88%` donnait des marges de 16,3 px, hors de la grille de 4 (l'audit grille relevait 48 écarts).

## Un seul relèvement du JS pour #764, #770 et #771, puis l'issue « Budget JS » (Kevin, 16.11.2026, 14 h 19)

- Mesures sur main du 16.11 (js-total 428 054 octets gzip, limite 428 780) : #764 ajoute 715 octets (AlertSiteSteps, code jobup), #770 1 544 (PreparationView, recherche dans le CV), #771 916 (OffersView, agences de placement). Les trois ensemble : 431 252 octets.
- Le chargement à la demande des trois composants a été mesuré : js-total + 1 840 octets, js-candidatures − 250 seulement. Il n'est pas retenu.
- Décision : js-total passe de 428 780 à 431 500 octets, une seule fois, dans une petite PR à part, pour les trois PR ensemble. Pas de découpage.
- Après la fusion de #764, #770 et #771 : ouvrir une issue « Budget JS » qui (1) mesure le JS chargé au premier écran de chaque page (gzip), (2) propose une limite par page en plus de js-total, (3) liste les 5 plus gros modules avec des pistes d'allègement chiffrées.
- Plus aucun relèvement de css-total ou de js-total sans passer par cette issue.

## Audit de poids quand main dépasse déjà (Kevin, 16.11.2026, 14 h 25)

- Quand main dépasse déjà une limite de poids (JS ou CSS), une PR dont la mesure baisse ou reste égale passe en vert ; seule une PR qui ajoute du poids à cette mesure reste bloquée.
- Mise en œuvre : `frontend/scripts/poids-ci.sh` (CI et `make audits-ci`) mesure la branche ; si une mesure dépasse, il construit la base (HEAD^1 dans la CI, le main sur lequel la PR est fusionnée ; origin/main en local) et compare avec `poids.mjs --base`.
- Les limites ne changent pas, et la règle des illustrations en WebP reste bloquante.
- Suite : issue « Budget JS et CSS » (JS et CSS du premier écran par page, limite par page, 5 plus gros modules avec des pistes chiffrées, écarts expliqués). Plus aucun relèvement de css-total ou de js-total sans passer par cette issue.

## Préparer, bouton « ↑ » du champ de demande (Kevin, 16.11.2026, 14 h 48)

- Champ de 56 px. Bouton visible de 40 × 40 px, à 8 px du bord du champ en haut, à droite et en bas : sur la grille de 4, sans exception dans l'audit.
- Zone tactile de 48 × 48 px par un pseudo-élément qui déborde de 4 px dans le retrait (modèle des boutons-icônes de Material 3).
- Rayon du champ = rayon du bouton + retrait = 20 + 8 = 28 px, pour des arrondis concentriques. Icône « ↑ » de 20 px.
- Le texte saisi s'arrête à 12 px du bouton, il ne passe jamais dessous.
- Vaut pour « Que changer ? » (téléphone) et « Demander une modification de la lettre / du CV » (ordinateur).
- Remplace la première demande du même jour (14 h 18 : bouton de 44, retrait de 6), qui sortait de la grille de 4.

## Limites de poids par page (Kevin, 16.11.2026, 15 h 10 et 15 h 18, issue #797)

- Règle : le JS et le CSS ont des limites **par page**, fixées une seule fois et jamais relevées. Une PR qui dépasse compense sur sa propre page ou attend. Seule exception : une décision écrite dans docs/decisions/ avec l'accord de Kevin.
- Valeur : pour chaque page, la plus basse entre (a) une référence publique de budget pour un téléphone moyen en 4G et (b) la mesure de main du 16.11 + 5 %, arrondie à la centaine d'octets inférieure.
- Référence (a) : Alex Russell, « The Performance Inequality Gap, 2024 » (https://infrequently.org/2024/01/performance-inequality-gap-2024/). Pour un téléphone de milieu de gamme (Galaxy A51, Pixel 4a) sur un réseau P75 (7,2 Mbit/s, 94 ms), interactif en 3 secondes : environ 730 Kio compressés par page, dont 365 Kio de JS au plus, soit 373 760 o de JS et 373 760 o pour le reste (HTML, CSS, images, polices). Aujourd'hui (b) est plus basse partout : la page la plus lourde, Candidatures › Suivi, charge 168 Ko de JS et 70 Ko de CSS.
- Pages : les 30 vues de router.ts (avec leur page parente), plus Aujourd'hui avec le bloc qu'elle charge à part sur téléphone (HomePhone) et sur ordinateur (TriageMini) : 32 pages. Une vue ou un bloc chargé à part sans limite fait échouer le budget : une nouvelle page reçoit ses limites dans la PR qui la crée.
- js-total et css-total sont affichés dans chaque PR mais ne bloquent plus. css-premier et js-premier disparaissent : c'est la page Aujourd'hui (accueil).
- Chaque PR affiche le poids avant/après des pages qu'elle touche : résumé de l'exécution de la CI et note sur la PR (scripts/poids-ci.sh).
- Voie 1 retenue : la voie 3 (couper du contenu utile pour gagner du poids) est exclue, la voie 2 seule (relever css-total) ne réglait rien.
- Suite, une PR chacun, captures identiques au pixel près, gain mesuré par page : (a) sortir de style.css le CSS propre aux pages ; (b) premiers pas, une étape par fichier chargée à son tour ; (c) Préparer, panneaux secondaires à la demande.

## Pastilles neutres sur le fond beige (Kevin, 16.11.2026)

- La pastille « Case à cocher dans Job-Room » de « Pour l'ORP » garde son fond aligné sur le bord gauche du texte au-dessus, comme sur la planche BilanOrdinateurFiche.
- Une pastille neutre posée sur le fond beige (volets, feuilles) se distingue de ce fond : fond blanc #FFFFFF et trait de 1 px #CFCBC1 (`--card-line`) ; en sombre, fond #2C2722 et trait #4E473E. Jeton `--pill-on-bg`. Le trait est dessiné à l'intérieur : la pastille garde sa taille et son alignement.
- Relevé du 16.11 sur toutes les pages des audits et leurs volets et feuilles, à 1440 et 390 px : seule cette pastille était concernée (volet du Bilan sur ordinateur, fiche « Pour l'ORP » sur téléphone). Posée sur une carte blanche (volet d'une candidature), elle ne change pas.

## Coche après le téléchargement de la lettre et du CV (Kevin, 16.11.2026, 16 h 44)

- Dans « 3. Postuler », la pastille Lettre.pdf (et CV.pdf) remplace son icône de téléchargement par une coche verte (icône `done`, couleur `--ok-text`, celle de la coche passagère des téléchargements) une fois le fichier téléchargé. « Tout télécharger » coche les deux. Sur téléphone, où la pastille n'a pas d'icône, la coche s'ajoute de la même façon.
- La pastille reste un lien cliquable pour retélécharger. Son nom accessible devient « Lettre.pdf, téléchargée » (« CV.pdf, téléchargé »), pas l'icône seule.
- La coche est posée quand le fichier est bien arrivé : les liens de téléchargement passent déjà par `useFileDownloads`, qui récupère le fichier lui-même et montre une coche 2 secondes ; il prévient maintenant la page (`file-done`). Un échec ne coche rien. Elle est gardée dans ce navigateur (`localStorage`, clé `jobA1.telecharges`, 100 entrées au plus), par version du document : une lettre ou un CV refait repart sans coche. Rien n'est envoyé au serveur. La clé est effacée à la déconnexion (règle A-7).
- Aucune planche ne dessine cet état : cette décision en tient lieu. Les certificats joints et les liens « Partager » du téléphone ne sont pas concernés.

## Filtres des Offres gardés jusqu'à la fermeture de l'onglet (Kevin, 16.11.2026, 16 h 44)

- Constat : le filtre choisi (par exemple « Nouvelles ») retombait sur « Toutes » après une candidature, parce que les filtres vivent dans l'adresse (`?statut=to_review`) et que « Retour aux offres » (écran « C'est fait ! »), l'onglet Offres et les autres liens pointent sur `/candidatures/offres` sans filtre.
- Les filtres des Offres (statut, tri, note, taux, sites, cantons, télétravail, agences, écartées, expirées, recherche) sont gardés pour l'onglet du navigateur (`sessionStorage`, clé `jobA1.offres-filtres`) et remis quand on revient sur Offres par un lien qui n'en porte aucun. Ils durent jusqu'à la fermeture de l'onglet et sont effacés à la déconnexion (règle A-7).
- Un lien qui porte un filtre précis (par exemple « Tout voir » de Top du jour → note 75 et plus) l'emporte sur les filtres gardés.
- Le statut choisi devient une pastille, « Statut : Nouvelles » (Gardées, En préparation), comptée dans le nombre du bouton Filtres ; « Tout effacer » apparaît dès qu'un filtre est actif et retire aussi le statut (avant, il le gardait). Le tri n'a pas de pastille et reste en place, sauf « Dernière action », propre à En préparation.
- Complément (Kevin, 17.11.2026, 0 h 29 et 0 h 33) : « Tout effacer » retire aussi le statut, à condition que le statut soit dans le panneau Filtres et compté dans le nombre de filtres actifs ; après « Tout effacer », le nombre affiché est 0. Sur téléphone, la feuille Filtres reçoit en tête un groupe « Statut » (fieldset et légende, `role="radiogroup"`, un seul choix) : Toutes · n, Nouvelles · n, Gardées · n, En préparation · n, avec les nombres de l'ordinateur et le style de « Type de note » (puces de 44 px, coche sur le choix actif). Le statut est le même des deux côtés. La planche Filtres ne le dessine pas : cette décision en tient lieu.

## Offres déjà postulées et doublons (Kevin, 16.11.2026, 16 h 45)

Une offre déjà postulée ne doit plus encombrer le fil Offres, sans jamais cacher en silence une vraie nouvelle offre
(Nielsen n° 1). On distingue le sûr du probable.

- **Même lien = doublon sûr.** Même site (sans www), même chemin, même identifiant d'annonce dans l'adresse (Indeed :
  `jk`). L'offre est rattachée à l'offre envoyée et sort de la liste. Une candidature saisie dans Envoyées avec ce
  lien reçoit l'offre comme fiche.
- **Même titre chez la même entreprise = doublon probable.** L'offre reste visible avec la pastille neutre
  « Déjà postulé le … », et c'est toi qui décides. Une entreprise peut republier le même poste des mois plus tard, ou
  ouvrir deux postes au même titre. Titre comparé sans taux ni genre ; entreprise sans SA, Sàrl, AG, GmbH, casse,
  accents ni ponctuation, comme pour « Autres offres chez X ».
- **Agences** : le même titre via deux agences différentes reste un cas probable : la pastille seulement, jamais de
  fusion automatique.
- Spontanées et candidatures saisies dans Envoyées comprises.
- Ajout d'une offre (à la main, par l'extension, en spontanée) : la fiche existante s'ouvre avec les nouveaux liens ;
  « Créer quand même » reste visible à côté, pas dans un menu (seconde PR).
- Conséquence acceptée : les offres déjà cachées derrière une offre envoyée seulement par leur titre reviennent dans
  le fil avec la pastille (3 sur le compte de Kevin le 16.11).

## Fenêtre de l'extension sur « Créer une alerte » de jobup (Kevin, 16.11.2026, 21 h 25)

Section 42 de la maquette (planches ExtAlerte, ExtAlerteCodeAttente, ExtAlerteCodeColle, ExtAlerteTerminee,
ExtAlerteCodeSecours, et leurs versions Sombre). Quatre règles strictes :

1. L'extension remplit des champs mais ne clique jamais sur un bouton de jobup (ni créer, ni confirmer). Cela
   remplace, pour jobup seulement, le clic sur « Continuer » de la page du code (docs/112 §3, validé le 21.10) :
   le code est rempli, la personne clique. jobs.ch garde le clic.
2. Elle n'agit que sur la page d'alerte ouverte par la personne : l'onglet où la fenêtre a été ouverte sur le
   formulaire, et lui seul, jusqu'à l'alerte créée.
3. Le code n'est jamais écrit dans les logs, ni dans l'extension ni sur le serveur. Il passe du serveur à l'extension
   par la requête authentifiée existante (`GET /api/extension/codes?site=jobup`) et n'est pas gardé après usage
   (ni stockage du navigateur, ni message à la page jobA1).
4. Si le formulaire jobup change (sélecteurs introuvables), la fenêtre passe à l'état secours (code affiché et
   « Copier le code ») au lieu d'échouer.

Le contrat avec la page jobA1 (détection et suivi en direct) est dans
`2026-11-16-2130-extension-contrat-page.md` (PR du choix « Avec l'extension / À la main »).

Précisions de Kevin (16.11.2026, 23 h 05, sur #805) :
- Le résumé « Formulaire rempli » n'affiche que ce qui est stocké (mots et lieu, sans rayon).
- « Copier l'adresse jobA1 » seulement si le champ e-mail est resté vide, avec le libellé
  « Le champ e-mail est vide ? » + lien « Copier l'adresse jobA1 ».
- Plus tard, dans une PR à part : quand la fenêtre jobs.ch passera à la liste en 4 étapes, retirer aussi le clic
  automatique sur « Continuer » pour jobs.ch. LinkedIn garde sa fenêtre actuelle avec « J'ai créé l'alerte »
  jusqu'à nouvel ordre.

## Extension et page jobA1 : détection et suivi de l'alerte (Kevin, 16.11.2026, 21 h 30)

Section 42 de la maquette : à l'étape « Crée ton alerte sur jobup » des premiers pas, sur ordinateur seulement, le
choix « Avec l'extension · environ 1 minute » / « À la main · environ 2 minutes ». Le contrat entre l'extension
(`extension/page-joba1.js`) et la page (`useJobA1Extension`), sans requête au serveur pour la détection :

1. **Détection.** Sur l'adresse de la plateforme reliée, au chargement (`document_start`), l'extension pose
   `data-joba1-extension="x.y.z"` sur `<html>` et envoie
   `postMessage({ source: "joba1-extension", type: "ready", version }, location.origin)`. La page lit d'abord
   l'attribut, puis écoute `ready` (extension installée pendant que la page est ouverte). Par défaut, le choix est
   « Avec l'extension » si l'extension est détectée (« installée · environ 1 minute »), sinon « À la main ».
2. **Suivi.** L'extension envoie
   `postMessage({ source: "joba1-extension", type: "alert-progress", site: "jobup", step })`, avec `step` parmi
   `filled`, `sent`, `code-pasted`, `fallback`, `created`. Jamais le code, jamais l'adresse.
3. **Demande.** La page peut demander l'étape courante :
   `postMessage({ source: "joba1-page", type: "alert-progress?" }, location.origin)`. Des deux côtés, un message ne
   compte que si `event.source === window`, la même origine et le bon `source`.
4. **Alerte créée.** À `created`, l'extension appelle `PUT /api/extension/alerts/jobup` (route existante
   `mark_created`). La page passe d'elle-même à l'étape suivante, sans bouton « J'ai créé l'alerte ». En secours,
   quand on revient sur l'onglet, la page relit `/api/alert-searches` et avance si jobup est noté créé.
5. **Ouvrir jobup.** Le bouton « Ouvrir jobup avec ma recherche » garde l'adresse `cells[].url` de
   `/api/alert-searches`.
6. **Secours.** `fallback` (champ du code introuvable sur jobup) : la ligne « Code collé dans jobup » devient
   « Le code est dans la fenêtre de l'extension ».

Le suivi en direct affiche : Formulaire rempli, Alerte envoyée à jobup, Code collé dans jobup, En attente de ta
confirmation sur jobup. Changer d'option garde l'avancée de chaque parcours. Téléphone : pas de choix, parcours à la
main seul. Ordinateur (Kevin, 16.11, 23 h 29) : l'extension n'existe que pour Firefox, donc le choix ne s'affiche que sur
Firefox, ou sur tout navigateur où l'extension est détectée ; ailleurs, parcours à la main seul. Texte : « Gratuite,
pour Firefox. ». Les règles de l'extension elle-même sont dans `2026-11-16-2125-extension-alerte-jobup.md`.

## « C'est une agence de placement » (Kevin, 16.11.2026, 23 h 33)

- Pour marquer à la main une offre que la détection n'a pas repérée : un choix « C'est une agence de placement » dans le menu de la fiche (« … »), à côté de « Signaler une erreur dans l'offre ». Pas de bouton visible sur la fiche.
- Effet immédiat : la pastille « Agence » sur la carte et la ligne « Agence de placement » sur la fiche (texte de la section 35), sans recharger la page.
- La correction est gardée pour cette entreprise, dans ce compte, et vaut pour ses autres offres, comme « Ce n'est pas une agence » dans l'autre sens. La dernière correction de la personne l'emporte sur la détection automatique.
- « Ce n'est pas une agence » reste un lien visible, affiché seulement quand la ligne Agence est là.
- Rien n'est envoyé au répertoire SECO, qui n'est pas lu automatiquement sans son accord écrit.

## Ajouter une offre déjà là (Kevin, 17.11.2026, 0 h 29)

Retour de Kevin sur la #818. On ne crée plus directement une offre déjà présente.

1. Pas d'encadré. Le message va sous le champ « Lien ou texte de l'annonce » (icône et texte, `role="alert"`), puis
   ses boutons. Tant qu'il est affiché, ces boutons remplacent « Ajouter l'offre » du bas.
2. Doublon sûr (même lien) : « Cette offre est déjà dans tes candidatures (ajoutée le {date}). » Un seul bouton plein,
   « Ouvrir l'offre ». Pas d'« Ajouter quand même » : le serveur ouvre l'offre déjà là même si on le lui demande.
3. Doublon probable (même titre et même entreprise, lien différent) : « Une offre très proche est déjà là : {titre}
   chez {entreprise}, ajoutée le {date}. » Bouton plein « Ouvrir l'offre », bouton contour « Ajouter quand même ».
   L'offre ajoutée quand même porte la pastille « Déjà postulé le … » si une candidature a été envoyée, comme dans le
   fil (#810).
4. Changer le lien ou le texte du champ fait disparaître le message et revenir « Ajouter l'offre ».

## Préparer : l'étape CV chargée à son ouverture (Kevin, 17.11.2026, 0 h 29)

- L'étape CV de Préparer se charge à son ouverture. Elle est préchargée au survol ou au focus de l'onglet « CV », sinon quand le navigateur est au repos (`requestIdleCallback`).
- Si le chargement dépasse 300 ms, un squelette de l'onglet s'affiche (les blocs de chargement communs), jamais un écran vide.
- Le gain réel est mesuré et donné dans la PR.
- Candidatures prend 1,4 Ko de JS depuis la #816 (les panneaux de Préparer y deviennent des blocs séparés) : on le laisse, sans PR de compensation, puisque la page reste 7,8 Ko sous sa limite.

## Ajouter une offre déjà là : icône info et « Annuler » (Kevin, 17.11.2026, 8 h 31)

Deux retours de Kevin sur la #818.

1. Icône : une icône « info » rejoint le jeu d'icônes. C'est un cercle de rayon 9, avec un trait vertical de y = 11 à
   y = 16 et un point à y = 8, de la même épaisseur que les autres icônes. Elle prend la couleur du texte secondaire, le jeton `--text-secondary` (#596070, et #ABA398 en sombre : précision
   de Kevin du 17.11 à 10 h 09, à la place du #A39C90 d'abord écrit).
   Le cercle « ! » reste réservé aux alertes, par exemple un code expiré.
2. Champs complétés : la phrase « Ouvrir l'offre complète aussi les informations qui lui manquent. » revient dans le
   message sous le champ, avant les boutons. Elle s'affiche seulement si l'ajout apporte au moins un champ vide à
   remplir. Après l'ouverture, si au moins un champ a été complété, un message bref s'affiche en bas :
   « {n} information(s) ajoutée(s) à l'offre », avec « Annuler ». C'est le même composant que le message d'Écarter
   (6 s). « Annuler » remet les champs comme avant.

## Extension : « Toute la Suisse » quand l'alerte jobup n'a pas de lieu (Kevin, 17.11.2026, 9 h 09)

- Lieu, option B : jamais de pastille sur Lieu, « Toute la Suisse » si le lieu est vide, la recherche s'écrit
  « {mots} · {lieu} ».
- Dans la fenêtre de l'extension sur jobup « Créer une alerte », la recherche lue dans l'adresse jobup s'affiche donc
  « {mots} · Toute la Suisse » quand l'adresse n'a pas de lieu (`searchSummary`, extension/popup.js).

## « Logitech · 12 nov. » sur la carte « Première candidature notée » (Kevin, 17.11.2026, 10 h 07)

- « Logitech · 12 nov. » va sur la carte « Première candidature notée » (section 44, planches AccueilPremiereCandidature et AujourdhuiOrdinateurPremiereCandidature), en ligne « {Entreprise} · {date courte} » entre le titre et la barre du mois ORP.
- Rien sur l'écran « C'est fait ! ».
- (17.11, 12 h 02) La carte ne se ferme jamais seule : elle reste ouverte jusqu'à « Fermer » ou jusqu'à ce que la personne quitte la page, sans minuteur caché, parce qu'elle contient une action (« Voir ») (WCAG 2.2.1 Timing Adjustable ; Material 3, snackbars avec action).

## Journal d'accès de Caddy sans identifiant (Kevin, 17.11.2026, 11 h 07)

- Le journal d'accès de Caddy masque les identifiants dans toutes les adresses : `/api/<ressource>/<nombre>` devient
  `/api/<ressource>/:id`.
- La query string n'est jamais journalisée, pour qu'aucun code ni jeton ne s'y retrouve.
- La durée de conservation reste de 7 jours.
- Test : `GET /api/interviews/123?x=1` apparaît dans le journal comme `/api/interviews/:id`, sans paramètre
  (`make test-journal-caddy`). Kevin vérifie lui-même en production après le déploiement.
- Mise en œuvre : le champ `request>uri` est retiré et un champ `path` (le chemin seul) le remplace, avec le filtre
  `regexp`. Le filtre `query` ne peut retirer que des paramètres nommés un à un, et Caddy n'enchaîne pas deux filtres
  sur un même champ. Le Referer est retiré aussi, car il peut contenir une adresse avec ses paramètres.

## Tableau des retours d'entretien, données (Kevin, 17.11.2026, 11 h 10)

- Une PR serveur seule, sans écran. L'écran attend la planche de Kevin : volet à droite sur ordinateur, page entière
  sur téléphone. Accès provisoire : une ligne « Retours d'entretien » dans Bilan › Résultats.
- Deux états par ligne :
  - `point` : `a_venir` | `a_faire` | `fait` (le retour « Faire le point ») ;
  - `issue` : `en_attente` | `retenu` | `pas_retenu` (la réponse de l'entreprise).
- La liste donne : entreprise, poste, date, type, ressenti, stress, suite, prochaine étape, remerciement envoyé
  (oui/non), point, issue et le nombre de questions notées. Aucun texte libre dans la liste : notes et questions
  seulement dans le détail.
- Lecture seule : aucune écriture en base, rien envoyé à l'IA, rien journalisé (ni contenu, ni identifiant
  d'entretien dans les journaux).
- Seulement les entretiens de la personne connectée : un autre compte reçoit 404 (test).
- Tri du plus récent au plus ancien, pages de 20.
- Une ligne ouvre le retour complet ; pour le modifier, on repasse par « Faire le point ».
- Le bloc « Entretiens » retiré de Bilan › Résultats sur ordinateur est voulu (point 3 du récapitulatif du
  11 novembre, #651) : pas de régression, pas d'issue.

## Barre du bas : icône Assistant et disque actif à l'encre (Kevin, 17.11.2026, 11 h 51)

- Kevin lance la PR « barre du bas » (§50 + §55 du LISEZMOI_CORRECTIONS du 17.11), petite et à faire vite, en parallèle des feuilles du bas.
- §50 : l'onglet Assistant inactif est une bulle au trait (24 px, même trait que les 4 autres icônes) avec une étincelle pêche #E8B48A (`--spark`) au centre ; icône `assistant` de icons.ts.
- §55 : le disque de l'onglet actif passe à l'encre #1B1F2A, icône blanche, ombre 0 4px 12px rgba(27,31,42,.25) ; en sombre, crème #F3EEE6, icône #171411, ombre rgba(0,0,0,.4) (jeton `--nav-dot-shadow`). Libellé actif à l'encre (#F3EEE6 en sombre), gras. Le bleu plein reste aux actions.
- Onglet Assistant actif (Kevin, 17.11.2026, 12 h 41) : pas de mascotte ni de rond couleur surface ; même règle que les 4 autres onglets : dans le disque, la bulle de la barre en 26 px, trait 2,2 px, currentColor, étincelle #E8B48A ; clair disque #1B1F2A, icône #FFFFFF ; sombre disque #F3EEE6, icône #171411, ombre 0 4px 12px rgba(0,0,0,.4). Planches Assistant et AssistantSombre.

## Écrans de chargement, LISEZMOI §53 (Kevin, 17.11.2026, 12 h 03)

- Lecture du CV : écran plein de la planche ChargementCV seulement dans les premiers pas, juste après l'envoi du CV (la personne n'a rien d'autre à faire). Sur téléphone, « Continuer » était déjà grisé pendant la lecture : rien de ce qui marchait ne disparaît. Sur ordinateur, les premiers pas laissaient continuer pendant la lecture : ce parcours reste, avec le style seul.
- Partout ailleurs (relire le CV depuis Profil, changer de CV) : le parcours actuel, qui ne bloque pas, avec seulement le style (titre manuscrit, barre de progression, étapes cochées) dans la carte existante.
- Lancement : un ajout, affiché seulement pendant le vrai chargement à froid. Jamais de délai artificiel, environ 1,2 s d'animation au plus (la planche en dessine 1,4 s : les étapes sont resserrées). Avec prefers-reduced-motion, le logo est fixe.
- Écriture de la lettre : écran plein seulement si l'attente bloque déjà l'écran. Elle ne le bloque pas (elle occupe la zone de la lettre dans Préparer) : style seul, dans cette zone.
- Complément (Kevin, 17.11.2026, 14 h 43, point 6) : l'avancement estimé est validé. À la réponse, la barre et les étapes finissent en moins de 0,5 s (ici 0,3 s, puis le bloc laisse la place 0,4 s après). Au-delà de la durée habituelle + 50 %, la barre est remplacée par « Ça prend un peu plus de temps que d'habitude » (role="status"), jamais une barre figée.

## « M’avertir dès » : seuils de main gardés (Kevin, 17.11.2026)

- Le LISEZMOI §56 dessine Très proche « 90 et plus », Proche « 75 et plus », À creuser « 60 et plus ». Kevin garde les seuils de main, alignés le 16.11 sur « Note minimale » des filtres : 85, 75 et 50. Les valeurs enregistrées ne changent pas.
- Seuls la forme et les libellés suivent le §56 : les mots (Très proche, Proche, À creuser) en libellé, « 85 et plus », « 75 et plus », « 50 et plus » en précision, dans la feuille à boutons radio (téléphone) et le menu (ordinateur).

## Rappel des justificatifs en haut de l'Accueil (Kevin, 17.11.2026, 13 h 21)

- §57 du LISEZMOI_CORRECTIONS du 17.11, planches AccueilJustificatif et AccueilJustificatifSombre : une PR à part.
- Îlot avec les jetons des feuilles en îlot de la #828, sans nouveau CSS d'îlot : 8 px des bords, rayon 24 px, ombre 0 12px 32px rgba(27,31,42,.2) ; en sombre, fond #221E1A et trait #38322B (la planche sombre n'a pas de trait : la décision de Kevin passe avant).
- role="status", pas de prise de focus. Bouton « Exporter », qui ouvre la page ORP du mois, et croix « Fermer pour aujourd'hui ».
- Au plus une fois par jour, seulement quand des justificatifs sont à remettre ou en retard ; disparaît dès que le mois est marqué remis (case cochée §58/§61 ou « Déjà remis »). Lecture retenue : le rappel se montre à la première ouverture de l'Accueil du jour, puis plus avant le lendemain ; la date est gardée dans le navigateur (`jobA1.rappel-orp`), rien sur le serveur.
- Téléphone seulement : aucune planche ordinateur ne le dessine ; Kevin (17.11.2026, 14 h 07) : rien sur ordinateur.
- Texte non dessiné : avant l'échéance, « À remettre avant le 5 décembre » (« À remettre aujourd'hui » le jour même), la phrase de la tâche n° 1. Le rond de l'icône prend --peach-soft (#FDEDE3 ; #3A281E en sombre) au lieu du #FDF0E2 de la planche, qui garde ce fond clair en sombre.
- Précision (Kevin, 17.11.2026, 13 h 43) : avant l'échéance, le rappel ne s'affiche que pendant les 5 derniers jours (« À remettre avant le 5 décembre »), comme la tâche en tête de « À faire » ; après l'échéance, chaque jour à la première ouverture.
- Poids (Kevin, 17.11.2026, 14 h 07) : pas de compensation pour les +464 o de CSS les jours de rappel, la page reste sous sa limite.

## Filtres et bouton retour (Kevin, 17.11.2026, 13 h 27)

Bug : sur téléphone, un choix fait dans la feuille Filtres (Statut, Note minimale…) était annulé à la fermeture. La
feuille ajoute une entrée d'historique à l'ouverture et revenait en arrière en se fermant, ce qui ramenait l'adresse
d'avant, donc les filtres d'avant.

Option choisie : garder l'entrée d'historique quand un filtre a changé. Règles précisées par Kevin (13 h 27), pour tous
les filtres (Offres, Envoyées), sur téléphone et sur ordinateur :

1. Une seule entrée d'historique par application (« Afficher N offres » ou une fermeture qui applique), avec les
   filtres dans l'adresse. Pas une entrée par case cochée. Retour ramène les filtres d'avant.
2. Feuille ouverte + retour (bouton retour Android ou du navigateur) : la feuille se ferme sans appliquer, la liste
   revient à l'état d'avant, aucune nouvelle entrée.
3. « Tout effacer » suit la règle 1 : une entrée quand on applique.

Précision de Kevin (17.11, 13 h 43), qui remplace la règle 2 : toute fermeture applique (croix, glisser, voile, bouton
retour ; sur ordinateur aussi Échap et le clic à l'extérieur), avec le même effet que « Afficher N offres » et une seule
entrée d'historique par application. Annuler = « Tout effacer », ou retour après la fermeture, qui ramène aux filtres
d'avant. Les pastilles sous la barre et « Effacer les filtres » des listes vides appliquent tout de suite : une entrée
chacun.

Réponses de Kevin (17.11, 14 h 07) :

- Le tri d'Envoyées est une préférence du compte : il n'entre pas dans l'historique (replaceState, jamais pushState).
  Retour = page précédente. L'adresse et la liste montrent toujours le même tri : revenir à une entrée d'avant
  remet aussitôt le tri choisi dans l'adresse. Les filtres de statut gardent la règle : une entrée par application.
- Pas de clignotement : la liste affichée reste jusqu'à ce que la liste filtrée soit prête, puis elle est remplacée
  d'un coup. Retour pendant l'ouverture : l'entrée choisie est remise avant que le routeur ne lise l'adresse, la liste
  ne repasse jamais par les filtres d'avant.

## Accueil : la scène des 4 personnages (Kevin, 17.11.2026, 13 h 21 et 13 h 27)

- §59 du LISEZMOI_CORRECTIONS du 17.11 : la scène des 4 personnages du logo remplace le rond orange de l'accroche.
- Image définitive (13 h 27), à la place de l'image provisoire choisis-candidature : accueil-orp, clair et sombre. Fichier de 840 px des planches AccueilV2 et AccueilV2Sombre, tel quel (les fichiers de 480 px ne sont pas dans le zip ; avec eux, les images dépassaient leur limite).
- Téléphone : centrée au-dessus du titre, 110 px de haut. Ordinateur : à droite du texte dans le bandeau pêche, 340 px de large, hauteur auto (au lieu de 150 px de haut). alt="".
- Une seule constante, `HOME_SCENE` (frontend/src/troupe.ts) : remplacer l'image tient en une ligne (plus le fichier dans public/troupe/).
- Un seul des trois par écran (docs/141) : le petit visage du 1 à côté de « Rien à trier » sur l'Accueil du téléphone est retiré, la scène le remplace (« Il n'y a plus d'autre personnage dans l'app », §59). L'image orange-liste.webp, qui ne servait qu'à l'accroche, est retirée.
- Retrait du petit visage à côté de « Rien à trier » validé par Kevin (17.11.2026, 14 h 07).

## jobA1 en sept langues : plan validé (Kevin, 17.11.2026, 13 h 30)

- Langues : français (par défaut), allemand, italien, anglais, albanais, portugais, espagnol. Cadrage : docs/147-langues-plateforme.md.
- Plan accepté sur le principe : fonction maison `t()`, pas de vue-i18n ; catalogues chargés par page ; français inchangé (texte du code) ; une PR par écran ; une langue reste grisée « Bientôt » tant qu'une personne dont c'est la langue maternelle ne l'a pas relue.
- Ordre : l'outil et le sélecteur (PR 1) après #833 et le fil Compte et Réglages ; les écrans sur lesquels un autre fil travaille passent en dernier.
- Ajouts obligatoires avant le premier jet :
  1. Glossaire figé par langue, versionné dans le dépôt (docs/i18n/), utilisé pour tous les écrans : ORP / RAV / URC, justificatifs, recherches d'emploi, gain intermédiaire, formulaire de preuves de recherches, conseiller. Termes officiels du SECO et des cantons. Le contrôle automatique vérifie que le glossaire est respecté.
  2. Dates, nombres et montants par Intl, jamais traduits à la main, avec la variante suisse (de-CH, fr-CH, it-CH ; « 1'000 » en allemand).
  3. Pluriels et accords par Intl.PluralRules, pas par phrases concaténées.
  4. Deux réglages séparés : langue de l'interface et langue des documents (lettre, CV). Changer l'interface ne change jamais la langue des documents.
  5. Notifications et réponses de l'IA dans la langue de l'interface, dans la PR de l'écran concerné, pas dans une PR à part plus tard.
  6. Captures en allemand avant fusion sur les écrans où le texte s'allonge : onglets dossier, boutons pleine largeur, pastilles des offres, titre manuscrit de l'Accueil, feuilles du bas. Jamais de « … » dans un onglet ou un bouton.
- Réponses aux questions du plan :
  1. Premier lancement : langue du navigateur si elle fait partie des sept, sinon le français ; un choix enregistré passe toujours avant. Texte dans une autre langue que l'interface (annonces, lettres affichées) : attribut `lang` sur le bloc (WCAG 3.1.2). Pages légales : traduction relue et mention « la version française fait foi ».
  2. La langue est enregistrée sur le compte (S1), pour les notifications.
  3. Poids : voir 2026-11-17-1330-poids-catalogues-langues.md.
  4. Kevin redessine la planche ReglagesLangue avec les sept langues (nom dans sa propre langue, grisées « Bientôt » tant qu'elles ne sont pas relues). La PR 1 l'attend.
  5. Variantes : fr-CH, de-CH (sans ß), it-CH, en-GB, pt-PT, es-ES, sq.
  6. Relecture : qui relit, à compléter par Kevin. Une langue n'est activée qu'après relecture ; l'allemand et l'italien d'abord.
  7. Italien dans les lettres : pas maintenant.

## Poids des catalogues de langue (Kevin, 17.11.2026, 13 h 30)

- La limite de chaque page reste celle d'aujourd'hui, mesurée en français (docs/decisions/2026-11-16-1518-limites-par-page.md). Elle ne change pas avec les traductions.
- Chaque catalogue (une page × une langue) reçoit sa propre limite dans la PR qui le crée : sa mesure gzip + 5 %, arrondie à la centaine d'octets inférieure, jamais relevée ensuite, comme les autres limites.
- Le code d'une page et son catalogue le plus lourd restent ensemble sous le budget public de 365 Kio gzip (téléphone moyen en 4G, The Performance Inequality Gap 2024).
- `poids.mjs` mesure les catalogues à partir de la PR 1 ; chaque PR d'écran affiche le poids avant et après de la page et de ses catalogues.

## Tâches à cocher et bandeau des justificatifs du Bilan (Kevin, 17.11.2026, 13 h 39)

- Bilan sur ordinateur (§63, nouveau, remplace « ordinateur inchangé » du §58) : la carte « Justificatifs d’octobre à remettre » devient un bandeau pêche sans bordure, « Exporter le PDF » en bouton plein, « Déjà remis » en lien.
- Jamais de texte barré pour une tâche finie, nulle part (§61 remplace ce que disait le §58) : cercle vert, sous-titre « Remis / Déclarée le … » et « Annuler ».
- Accueil et Aujourd’hui : seule la tâche « Remettre les justificatifs » a un cercle à cocher ; les autres gardent leur numéro.
- En attente de sa décision, pas codé : l’icône de « À déclarer à l’ORP » sur le Bilan ordinateur (calendrier actuel ou cercle à cocher).

## « Ta recherche » des Alertes : l'écran de la planche, une seule source, les critères du Profil (Kevin, 17.11.2026, 13 h 39 à 13 h 43)

- Option A (13 h 39) : sur ordinateur, Alertes vides avec au moins une recherche = l'écran des planches AlertesOrdinateurVide et AlertesOrdinateurSite. Carte « Ta recherche » (postes · lieux), puis « À créer » avec une ligne par site (jobup, LinkedIn, jobs.ch, Indeed, Job-Room), chaque ligne ouvre le volet du site.
- Texte de la carte : les 3 premiers postes puis « +n », les 2 premiers lieux puis « +n », « Toute la Suisse » sans lieu ; le texte complet pour les lecteurs d'écran. La ligne « Recherche : … » du volet d'un site reprend exactement ce texte.
- « Modifier » ouvre un volet à droite, « Ta recherche » : postes (pastilles à choix multiple, 3 au plus, « + Autre poste »), lieux (champ « Ville ou région » et pastilles), taux (pastilles, choix unique), « Enregistrer » et « Annuler ».
- Une seule source (13 h 41) : les critères du Profil (postes, lieux, taux). Enregistrer met à jour les critères, puis recalcule les recherches : chaque poste × lieu qui manque est créé, chaque recherche dont le poste ou le lieu a été retiré est supprimée. Aucun lieu = une recherche par poste, sans lieu.
- Plus de 8 recherches : « Enregistrer » désactivé, message « 8 recherches au maximum. Retire un poste ou un lieu. » relié par aria-describedby. Encadré d'information (style §62) : « Ces critères servent aussi à trier tes offres. »
- Recherche supprimée alors qu'elle était créée sur un site : toast « Pense à supprimer aussi l'alerte sur {site}, sinon il continuera de t'écrire » avec « Ouvrir {site} ». Ignorer les e-mails d'une recherche supprimée : PR serveur séparée, juste après.
- Réponses du 13 h 43 : pastilles cochées = postes recherchés ; cantons comptés comme lieux, écrits en entier (« Vaud ») ; « + Ajouter une recherche » ajoute son poste et son lieu aux critères ; taux = 7 valeurs (Tous, Dès 50 %, Dès 60 %, Dès 70 %, Dès 80 %, Dès 90 %, 100 %), mêmes pastilles dans premiers pas, Profil et volet, le filtre de liste garde ses 4 valeurs ; volet construit avec les éléments des premiers pas en attendant sa planche ; téléphone inchangé.
- Profil (ligne « Postes » en tête de « Ce que je cherche », recalcul à l'enregistrement avec la même limite) et libellés « Dès … % » des premiers pas : PR séparée, ouverte quand la planche Profil arrive.

### Réponses aux écarts de la PR (Kevin, 17.11.2026, 14 h 27)

- « Ne plus suivre » ne touche pas au Profil : l'exclusion de la combinaison poste × lieu est enregistrée (la recherche reste en base, en pause) et un recalcul ne la recrée pas. Les critères du Profil ne changent pas. Toast « Tu ne suis plus {poste}. Tes critères du Profil ne changent pas. » avec « Annuler » (le même que dans Envoyées). Retirer un poste ou un lieu partout passe par « Ta recherche ».
- Démo réduite à 3 postes × 2 lieux = 6 recherches. Aucun volet ne s'ouvre avec « Enregistrer » désactivé sans que la personne ait agi.
- Au-delà de 8 : pastille orange (fond #FDF0E2, texte #8A4A16) « {n} recherches · 8 au maximum : retire un poste ou un lieu », bouton désactivé.
- Calcul : une ville comprise dans un canton coché ne compte pas en plus (Lausanne avec Vaud = 1 lieu) ; « Toute la Suisse » remplace tous les autres lieux.

## Feuille « Actions sur une offre » : les lignes en plus de la planche (Kevin, 17.11.2026, 13 h 43)
- On garde les 3 lignes absentes de la première planche ActionsOffre ; la planche est mise à jour.
- « Remettre dans Nouvelles » : seulement si l'offre est gardée ou écartée (plus pour une offre en préparation).
- « C'est une agence de placement » et « Demander à l'assistant » : toujours (quand l'action a un sens : entreprise connue
  et pas déjà marquée agence ; assistant disponible).

## Poids des premiers pas pour les écrans de chargement (Kevin, 17.11.2026, 13 h 54)

- Exception écrite à la règle des limites de poids (issue #797) : la limite `js-bienvenue-etapes` (premiers pas, toutes
  étapes) passe de 119 200 à 119 400 octets (gzip). Montant exact : +200 o, pas plus.
- Raison : les écrans de chargement du §53, validés par Kevin. À la réponse, la barre et les étapes finissent tout de
  suite (0,3 s) et le bloc est retiré à 0,4 s ; au-delà du temps prévu + 50 %, une phrase remplace la barre. L'écart
  restait après compensation dans la PR (marques en CSS, « : fait » en CSS, lancement sans JavaScript).
- Pour la suite : tout autre dépassement de cette limite, ou de n'importe quelle autre, demande une nouvelle décision
  écrite de Kevin. Pas de nouvelle hausse silencieuse.

Précision du 17.11, 16 h : l'exception n'a pas servi. Entre-temps, l'allègement des premiers pas fusionné sur main
(un fichier par étape, page téléphone à part) a ramené la page à environ 108 Ko : avec les écrans de chargement, elle
reste sous 119 200 o. La limite n'a donc pas été relevée et reste à 119 200 o. La règle pour la suite s'applique
toujours.

## Assistant chargé à la demande (Kevin, 17.11.2026, 14 h 01)

- Pour compenser le poids de la PR 1 des langues (docs/147, environ +240 o par page), Kevin choisit une PR à part, avant elle : le bouton flottant de l'Assistant reste dans le socle et s'affiche tout de suite ; le panneau (AssistantPanel) ne se télécharge qu'à la première ouverture (bouton, question posée d'ailleurs, page Assistant du téléphone).
- Poids : environ −10 Ko gzip sur chaque page. Nouvelle page mesurée « assistant » (page Assistant du téléphone, mesure + 5 %) et pire cas « suivi-assistant » (Suivi avec le panneau ouvert), qui garde les limites de Suivi d'avant l'allègement.

## Poids des pages traduites : la page avec son catalogue le plus lourd (Kevin, 17.11.2026, 14 h 17)

Remplace 2026-11-17-1330-poids-catalogues-langues.md (limite propre à chaque catalogue et budget public de 365 Kio).

- Pour chaque page : sa taille, plus ce qu'elle charge hors du français (i18n.ts, son catalogue et le catalogue `commun`), dans la langue la plus lourde. Toutes les langues sont mesurées et on prend le maximum ; la langue n'est jamais fixée en dur, elle peut changer d'une page à l'autre.
- On compare aux limites actuelles des pages. Pas de nouvelle limite.
- En CI, un échec indique la page, la langue et l'écart en octets.
- La description de chaque PR de traduction contient un tableau page / langue la plus lourde / taille / limite / marge (`poids.mjs` l'imprime).
- Une page qui dépasse dans une langue suit la règle d'aujourd'hui : une décision écrite dans docs/decisions/, jamais une hausse silencieuse.

## Premiers pas sur téléphone : taux et lieu (Kevin, 17.11.2026, 14 h 43)

- Taux (question 3 du §60) : un seul choix parmi les 7 valeurs déjà enregistrées, sans migration : « Tous, Dès 50 %,
  Dès 60 %, Dès 70 %, Dès 80 %, Dès 90 %, 100 % ». Le minimum choisi est enregistré tel quel (« Tous » = peu importe).
  Plus de fourchettes « 60 à 80 % ». Mêmes pastilles dans le Profil et le volet « Ta recherche » ; le filtre « Taux
  d'activité » de la liste garde ses 4 valeurs. Remplace la réponse « Tous, Dès 60 %, Dès 80 %, 100 % » donnée juste avant.
- Lieu (question 2) : une ville tapée devient une pastille cochée sous le champ et « Toute la Suisse » se décoche ;
  toucher « Toute la Suisse » efface les villes. Lieu vide = « Toute la Suisse », jamais tiré du CV (§43).

## Premiers pas sur téléphone : CV pas lu et aide du taux (Kevin, 17.11.2026, 15 h 07)

- Question 1 : si le CV n'a pas été lu, la pastille orange « Ton CV n'a pas pu être lu » remplace « Depuis ton CV », même
  forme et même place. Pas de phrase hors pastille. Planche à venir : PremiersPas1PostesSansCV (+ Sombre).
- Question 3 (§64, planche PremiersPas3Taux à jour) : sous-titre « Le taux minimum que tu acceptes. Les offres au-dessus
  restent affichées. » à la place de « Choisis-en un. ».

## E-mails d'une recherche retirée : garder une trace et filtrer (Kevin, 17.11.2026, 15 h 25)

- Une recherche d'alerte supprimée garde sa ligne, marquée retirée (`alert_searches.removed_at`, migration 0091), en pause et cachée de la page. Recréer la même recherche (mêmes mots, même lieu) reprend la ligne.
- À la collecte, une alerte dont le libellé ou l'objet contient les mots d'une recherche retirée ou en pause (« Ne plus suivre »), et ceux d'aucune recherche suivie, reste au journal mais ne donne aucune offre ; elle ne compte ni comme alerte reçue ni comme preuve ORP.
- Un e-mail qu'on ne peut rattacher à aucune recherche est gardé, par prudence.
- Option écartée : ignorer tout e-mail qui ne correspond à aucune recherche active, sans migration (risque d'ignorer à tort un libellé flou).

## Échelle de note unique 50 / 75 / 85 (Kevin, 17.11.2026, 16 h 36)

- Couleur de la note : vert (#17734A) dès 75, « Proche », et 85 et + « Très proche » ; orange (#A8540E, sombre
  #F2A766) de 50 à 74, « À creuser » ; gris en dessous de 50, « Loin » (LISEZMOI §65, planche Système).
- Une seule constante de seuils (`SCORE_SCALE`, frontend/src/format.ts), partagée par le cercle de score, les mots,
  Réglages « M'avertir dès » et le filtre Note. Test aux limites : 49, 50, 74, 75, 84, 85.
- Remplace D5 pour la note : « À creuser » n'est plus en gris chaud. L'orange reste aussi à ce qui demande d'agir.

Précision de Kevin (17.11.2026, 16 h 46) :
- Migration ciblée de « M'avertir dès » (0092) : 50, 75 et 85 ne bougent pas ; toute autre valeur va au niveau le
  plus proche, le plus haut à égalité (70 → 75, 55 → 50, 80 → 85). Nouveau défaut : 75. Pas de message à la
  personne. Compter les valeurs enregistrées avant la migration.
- Bilan › Résultats : tranches « Proches » dès 75, « À creuser » de 50 à 74, « Loin » en dessous de 50, même
  constante (`jobbot.scoring.scale`).
- La recherche employeurs (70) reste hors périmètre : ce seuil n'est affiché qu'en chiffre, jamais avec un mot.

## Réglages : retour sur la ligne d'origine, retour aux réglages, Formule sans limite (Kevin, 17.11.2026, 21 h 05)

Réponses de Kevin aux changements de comportement de l'audit du 17.11 (lot 2, Réglages) :

- Ordinateur : « Retour au compte » (État du service) devient « Retour aux réglages » et mène à la page Réglages (K43).
- Réglages : en quittant une rubrique, on revient sur la ligne d'origine ; le focus clavier est posé sur cette ligne et la position de défilement est restaurée (K39).
- Formule sans limite : afficher « Sans limite » et l'utilisation du mois (ex. « 42 utilisés ce mois »), sans barre de progression (K38, N2).

## Retour d'une candidature et bouton rond flottant (Kevin, 17.11.2026, 21 h 05)

- Téléphone : une candidature ouverte a sa propre adresse (`?candidature=ID`). Le retour du navigateur et le retour de l'app ferment la fiche et ramènent à la liste, à la même position de défilement (audit du 17.11, N25).
- Bouton rond flottant (Candidatures sur téléphone, Assistant sur ordinateur) : il ne se masque pas au défilement. La page a un `scroll-padding-bottom` égal à la hauteur du bouton plus sa marge : un élément qui reçoit le focus ne passe jamais dessous (WCAG 2.4.11), et le dernier élément de la page reste entièrement visible au-dessus du bouton.

## Choix Permis, Disponibilité et Préavis : motif « Radio Group » (Kevin, 17.11.2026, 21 h 47)

- Les choix des feuilles Coordonnées sont dans un `role="radiogroup"` : chaque choix a `role="radio"` et
  `aria-checked`, jamais `aria-pressed` (ARIA APG, motif « Radio Group »). Le `aria-pressed` de la maquette §66 était
  une erreur ; Kevin corrige les deux planches Coordonnées (claire et sombre).
- Clavier : Tab entre dans le groupe sur le choix actif (ou le premier) puis en sort ; les flèches passent d'un choix à
  l'autre et le cochent, Début et Fin vont aux extrémités (FormAnswerSheet.vue, test FormAnswerSheet.test.ts).
- Inchangé : la coche sur le choix actif, et un second appui qui retire le choix (la réponse peut redevenir vide).

## Une offre qui change d'état reste à sa place (Kevin, 17.11.2026, 21 h 50)

- Réponse à Q4 de l'audit du 17.11 (K5) : quand une offre de la liste Offres change d'état (gardée, écartée, remise dans Nouvelles), elle reste à sa place avec son nouvel état (pastille « Gardée » ou « Écartée ») jusqu'à ce qu'on quitte la liste : changement de filtre ou de statut, ou départ de la page.
- Un toast l'accompagne : « Déplacée dans Gardées », avec « Voir » (ouvre la liste Gardées) et « Annuler » (choix de Kevin du 17.11 au soir, carte de décision : « Annuler » est gardé). « Remise dans Nouvelles » a aussi « Voir ». Une offre écartée garde son message actuel, sans « Voir » : elle n'a pas de liste dans Offres.
- Le détail se referme comme avant (§36 du 16.11 sur ordinateur).

## Adresse du registre copiée seulement dans un champ vide (Kevin, 17.11.2026, 22 h 05)

- Quand le registre IDE connaît déjà l'entreprise (cache), « Chercher l'adresse » copie son adresse dans l'offre, seulement si le champ adresse est vide.
- Une adresse saisie par l'utilisateur, ou trouvée ailleurs, n'est jamais écrasée.
- Un test couvre les deux cas : champ vide, adresse copiée ; champ rempli, adresse inchangée.
- Origine : audit du 17.11, K6 (la fiche disait « Adresse trouvée » et restait « Non renseignée »).

## Fichier dans « Refaire la note » et titres d'offres lisibles (Kevin, 17.11.2026, 22 h 49)

- Q1 : « Refaire la note » accepte un fichier : un PDF, un PNG ou un JPG, un seul à la fois. L'usage compte dans la formule.
  - Le PDF est lu par le serveur, sans IA. La capture PNG ou JPG est recopiée par l'IA. L'image n'est pas gardée.
  - Le texte arrive dans le champ. La personne le relit, puis « Refaire la note » enregistre et renote, comme un texte collé.
  - La planche OffreProvisoire dit « PDF ou Word, 10 Mo » : Kevin a choisi PDF, PNG ou JPG. La limite reste 5 Mo, celle du PDF de « Ajouter une offre ».
- Q2 : « Noter maintenant » sur une offre « Pas encore notée » est accepté, mais attend sa planche.
- Q3 : à l'affichage seulement, un titre tout en majuscules passe en casse normale, « | » devient « · », et les sigles connus restent intacts (AWS, DevOps, SRE, CI/CD…). Aucune donnée n'est modifiée.

## Filtre Distance : numéros postaux GeoNames au lieu de swisstopo (Kevin, 18.11.2026)

Remplace la source de la partie « Distance » de 2026-11-18-0847-filtre-contrat-distance.md (swisstopo) :
- Source : les numéros postaux suisses avec coordonnées du dépôt GitHub zauberware/postal-codes-json-xml-csv (données
  GeoNames, licence CC BY 4.0). Une seule copie, commitée dans le dépôt, avec un README : source (URL du dépôt et
  commit exact), date, licence et l'attribution « Données : GeoNames (geonames.org), CC BY 4.0 ».
- L'attribution figure aussi dans « À propos ».
- Aucun appel externe depuis l'application, ni au démarrage ni plus tard. Mise à jour : une commande manuelle
  documentée (`make geonames-maj COMMIT=…`).
- La demande d'accès à swisstopo est annulée (aucun réglage d'environnement n'avait été changé).

Les autres règles de Distance restent : vol d'oiseau, libellé « Distance depuis Renens », choix 15, 30 et 50 km,
« Lieu non précisé » avec son nombre, jamais d'offre exclue en silence, nombre sous chaque choix.

Mise en œuvre (à valider par Kevin dans la PR) :
- La copie vit dans `backend/src/jobbot/data/geonames/` : le dossier `data/` de la racine est ignoré par git (données
  des personnes).
- « Renens » vient des coordonnées de la personne (numéro postal, sinon commune) : le libellé suit la commune saisie.
  Sans commune reconnue, le groupe ne s'affiche pas.
- Un lieu d'annonce n'a un point que s'il est sans ambiguïté : numéro postal connu, ou nom de localité dans un seul
  endroit (le canton cité tranche). « Buchs » sans canton, « Neuchâtel / Berne » ou « Suisse romande » vont dans
  « Lieu non précisé ».
- Choix par défaut « Toutes » (la planche s'ouvre sur 30 km et « Tout effacer » y revient à 50 km) : un défaut en km
  retirerait des offres de la liste de main.

## Nombres des filtres : graisse, ordinateur, choix à 0, Contrat et Distance (Kevin, 18.11.2026, 8 h 32)

Réponses aux trois questions de #851 :

- Le nombre sous un choix est en 12 px, graisse 500, #596070. Figtree est chargée en variable, donc le 500 existe
  (jeton `--weight-medium`). Si ce n'était pas le cas, il faudrait prendre 400. On n'ajoute pas de fichier de police.
- Le panneau Filtres de l'ordinateur montre aussi les nombres, avec le même calcul que le téléphone : les autres
  filtres actifs sont pris en compte, et le choix actif égale « Afficher n offres ». Au-delà de 99 999 : « 100 k+ ».
- Un choix à 0 offre reste visible et sélectionnable. Il est grisé (#596070, fond inchangé), jamais masqué.
- Contrat (plusieurs choix) s'affichera « CDI · 120 », comme Statut. Distance (un seul choix) aura son nombre sous le
  choix, comme Note et Taux.

Ordre choisi le 18.11 à 8 h 42 (issue #468) : le serveur de Contrat d'abord, puis celui de Distance, dans deux PR
séparées.

Précision de Kevin (18.11.2026, 9 h 31, choix a) : sur téléphone, les nombres sous les choix excluent les offres
« Loin » tant que la liste les cache, comme « Afficher n offres ». Règle : le nombre du choix actif égale toujours
celui de « Afficher n offres ». Un test compare les deux, avec et sans offres « Loin ».

Contrôle avec la planche (règle de Kevin du 18.11.2026, 9 h 25 : planche à gauche, app à droite, écarts entourés) :
la feuille Filtres du téléphone s'écartait de la planche sans décision écrite. Elle la reprend dans cette PR : titres
de groupe en capitales 13 px gris (docs/design/regles.md §4), aide en pastille et plus courte (« À quel point l'offre
correspond à ton profil », « Provisoire : notée sur l'extrait de l'alerte »), contour des puces à 1,5 px
`--button-outline`. Le panneau de l'ordinateur garde l'aide longue, comme sa planche.

## Planches de la fiche d'une offre du 18.11 (Kevin, 18.11.2026, 8 h 05)

- Le paquet jobA1_maquettes_2026-11-18.zip remplace celui du 17.11. Son §70 dessine les écrans de la section 6 de l'audit du 17.11.
- K2, planche OffreNonNotee : une offre « Pas encore notée » montre l'anneau pointillé, « Noter maintenant » et la pastille « Environ 10 secondes · compte dans ta formule ». Elle n'apparaît ni sur une offre écartée, ni sur une note impossible, ni quand le profil est vide. La note compte dans la formule ; le coût de l'appel n'est visible que pour Kevin (Q2 du 17.11).
- K6, planches OffreAdresseRecherche, OffreAdresseTrouvee et OffreAdresseNonTrouvee : la recherche d'adresse s'affiche à la place de l'adresse, l'adresse trouvée tient sur deux lignes avec « Trouvée au registre du commerce », une recherche vaine garde « Non renseignée » avec « Pas trouvée au registre ». « Modifier l'adresse » ou « Ajouter l'adresse » est une ligne sous l'adresse.
- K9, planche OffreExpiree : attend la réponse de Kevin sur « Voir des offres proches ».
- Restent sans planche, à ne pas inventer : Alertes reçues (K20, K21), Préparer le rendez-vous (K26, K30), Faire le point (K27), la page Aide.

## « Ton nom sur la feuille » (Kevin, 18.11.2026, 8 h 39 et 8 h 50)

- Une page à part, « Ton nom sur la feuille » (planches FeuilleNom et FeuilleNomSombre, §70), avec trois champs enregistrés dans le compte : le nom ; le conseiller ORP, pré-rempli depuis le rendez-vous s'il est connu ; l'office régional, nouvelle donnée.
- Sous chaque champ : « Enregistrement… » (role="status"), puis « Enregistré » quand on le quitte ; si l'enregistrement échoue, « Pas enregistré · Réessayer », et la saisie reste dans le champ.
- Entrée : la ligne « Ton nom sur la feuille › » dans la carte « La feuille » de « Préparer le rendez-vous » (planche PreparerRendezVous, §71).
- Ordinateur : la case actuelle reste, avec le même retour.
- L'office régional peut être vidé ; ces champs partent avec l'export et la suppression du compte, comme les autres données.

## Accueil téléphone d'après AccueilV2 (Kevin, 17.11.2026 et 18.11.2026, 8 h 44)

- 17.11 : l'Accueil du téléphone est refait d'après AccueilV2 dans une seule PR : §40 (titre écrit à la main, ordre À faire → ORP → Top du jour → offres à trier, barre « Mois ORP », feuille « Top du jour », « N offres à trier »), §54 (feuilles empilées au défilement) et §61 (cercle orange sur « Remettre les justificatifs », les autres tâches gardent leur numéro). La colonne « offre ouverte » suit dans une PR serveur à part.
- 18.11, 8 h 44 : visuels validés sur les captures côte à côte, à l'exception des notes mal alignées (corrigé : la règle globale `.close` décalait de 8 px les notes « Proche »).
- Écarts gardés et montrés à Kevin : « Préparer 2 candidatures · 2 offres gardées attendent leur lettre » (texte de l'ordinateur) au lieu de « Envoyer · Lettres et CV déjà prêts » ; les relances restent dans « À faire » (fonction de main gardée) ; l'anneau de note garde ses graduations (composant commun) ; un jour sans retard reprend le titre de l'ordinateur (« 1 candidature à envoyer. ») ; « Pas encore vues » = pas encore triées jusqu'à la colonne « offre ouverte ».
- « Top du jour » : jusqu'à 3 offres notées 75 et plus parmi les offres à trier, gardées ou en préparation (jamais envoyées) ; ces offres ne sont jamais dans « N offres à trier ».
- Après le tri du jour, la feuille « N offres à trier » disparaît (aucune offre n'est plus « à trier ») ; les meilleures restent visibles dans « Top du jour ». Avant, les cartes « Offres » restaient après le tri : à Kevin de dire s'il veut une feuille pour ce cas, aucune planche ne le dessine.
- « Relire ton CV » devient une ligne numérotée comme les autres (verbe « Relire », « ton CV ») ; l'ancienne icône document disparaît, la planche n'en dessine pas.

## Filtres Contrat et Distance : les règles (Kevin, 18.11.2026, 8 h 47)

Issue #468, choix A : Contrat d'abord, puis Distance, une PR chacun. La limite de 4 PR ouvertes s'applique.

Contrat :
- Une catégorie par offre : CDI, CDD, Stage, Temporaire ou Non précisé. Ni Apprentissage ni Autre.
- Pas de devinette : si l'annonce ne le dit pas clairement, l'offre est « Non précisé ».
- Une migration ajoute la catégorie et classe les offres existantes.
- Une facette donne les nombres, comme Statut : « CDI · 120 ». « Non précisé » apparaît aussi, avec son nombre.
- Un choix à 0 reste visible, grisé et sélectionnable.

Distance :
- Une table des communes tirée de la liste officielle des localités de swisstopo (open data, avec coordonnées). On
  l'importe une seule fois, sans appel à un service externe.
- La distance se mesure à vol d'oiseau depuis la commune de Kevin (Renens), avec `max_km`. Libellé : « Distance
  depuis Renens », comme la maquette.
- Une offre sans lieu reconnu va dans le choix « Lieu non précisé », avec son nombre. Elle n'est jamais exclue en
  silence.
- Un nombre sous chaque choix, comme Note et Taux.

Tests : un filtre sur une valeur inconnue ne doit jamais faire disparaître d'offres sans le dire.

## Contrôle visuel avant toute PR d'interface (Kevin, 18.11.2026, 9 h 25)

Trop de bugs d'affichage arrivaient jusqu'à Kevin (dernier en date : les pastilles qui débordent dans Envoyées). Une PR qui touche l'interface n'est prête que si ces quatre points sont faits.

1. Règle permanente (CLAUDE.md, section Interface) : partir de la planche de la maquette (dossier maquettes/ du zip), jamais d'un composant existant qui « ressemble » ; ne jamais livrer un écran sans l'avoir vu en capture ; une information n'apparaît qu'une fois par carte.
2. Captures obligatoires avant d'ouvrir la PR : Playwright, chaque écran touché, en 390×844 et 1440×900, en clair et en sombre ; pour chaque écran, une image côte à côte, planche à gauche, app à droite, dans la description de la PR, écarts entourés en rouge ; un écart volontaire dit pourquoi.
3. Test automatique de l'affichage, qui fait échouer la CI : toHaveScreenshot sur Accueil, Candidatures (Offres, Envoyées, Rendez-vous), fiche d'une offre, Bilan, Réglages, Profil, téléphone et ordinateur, clair et sombre ; et un script de contrôle sur ces écrans qui échoue si : (a) un élément dépasse de sa carte ou de l'écran, ou un texte est coupé sans « … » ; (b) une pastille fait plus de 32 px de haut, ou un élément s'étire (align-self: stretch non voulu) ; (c) le même texte d'état apparaît deux fois dans une carte ; (d) une police autre que Figtree apparaît ; (e) un contraste de texte est sous 4,5:1 (3:1 dès 18 px) ; (f) une zone cliquable fait moins de 24×24 px ; (g) un bouton ou un lien n'a pas d'action, ou une icône cliquable n'a pas de nom ; (h) un texte noir sur fond sombre, ou un fond blanc en mode sombre. Ce test arrive dans une PR à part, avant toute autre PR d'interface.
4. Avant d'écrire « prêt à relire », relire ses captures et répondre dans la PR : « J'ai comparé chaque écran à sa planche : oui / non, écarts : … ».

## Détail d'une candidature envoyée sur téléphone (Kevin, 18.11.2026, 9 h 26)

Suivre la planche EnvoyeeDetail (+Sombre) :

- Plus de carte « Pour l'ORP » (titre « Pour l'ORP » et lien « Pour l'ORP › » : le même texte deux fois). L'état ORP va dans la carte du haut, sur la ligne d'état : déclarée, « ✓ Déclarée à l'ORP » en vert #17734A ; pas encore déclarée, « À déclarer à l'ORP › », lien vers la déclaration du mois, en bleu #1A3496.
- Historique : titre en casse normale « Historique » (§67), ligne repliable avec résumé (« 3 étapes · dernière le 31 oct., déclarée à l'ORP ») et chevron ; le détail des étapes s'ouvre au toucher (aria-expanded).
- « Ce que tu as envoyé / Trouver un contact » : une seule carte, lignes séparées par un trait 1 px #EFECE5, pas de bloc arrondi à l'intérieur (jamais de carte dans une carte).

## Réglages, Rythme et pause (§70, Kevin, 18.11.2026, 9 h 39)

- « Dès qu'elles arrivent » est le premier choix de la feuille « Heure du message » ; quand il est choisi, il s'affiche comme valeur de la ligne.
- Sur ordinateur, les champs Du / Jusqu'au restent en attendant la planche ordinateur, qui reprendra le même calendrier à plage unique dans une fenêtre accrochée à la ligne.
- La pause n'est enregistrée qu'au toucher d'« Enregistrer », sur téléphone comme sur ordinateur.
- La section « Extension du navigateur » de la planche Reglages viendra plus tard, dans une autre PR.

## Accueil téléphone : une tâche bloquante ou en retard a un rond orange, pas de numéro (Kevin, 18.11.2026, 10 h 15)

- Écart 1 de la #858 : la version de la PR est gardée. Après le tri du jour, seulement « Top du jour » (75 et plus), en liste, comme AccueilV2. Le carrousel « Offres » de main disparaît.
- Écart 2 de la #858 : une tâche bloquante ou en retard n'a pas de numéro. Elle a un rond orange vide (#B4631F, en sombre la couleur pêche), comme « Remettre les justificatifs » dans AccueilV2. « Relire ton CV » a donc ce rond, puis 2, 3, 4… pour les autres tâches. Son sous-titre reste en orange, « · 30 secondes » inclus.
- Ordinateur (même règle, planche AujourdhuiOrdinateurV2, qui dessine le rond pour les justificatifs) : « Relire ton CV » perd son « 1 » sur fond orange et prend le même rond vide de 26 px, aligné au pixel avec le cercle à cocher des justificatifs.

## Offres : pas de compteur au-dessus de la liste ; bandeau « Annuler » au-dessus du bouton central (Kevin, 18.11.2026, 10 h 48)

- Point 6 : « 8 offres » au-dessus de la liste (ordinateur) est retiré. Remplace la décision du 15.11 sur ce compteur. Les nombres restent sur les groupes et dans « Afficher n offres ».
- Point 7 : sur téléphone, le bandeau « Annuler » se place au-dessus de la barre du bas et du bouton central, 8 px au-dessus du bouton, sans jamais le couvrir. Précise §10.8 (12 px au-dessus de la barre), qui faisait recouvrir le haut du bouton.
- Ordinateur (planche CandidaturesOrdinateurEcartee, appliquée dans la même PR) : le bandeau en bas à gauche, aligné sur le contenu, 400 × 56, couleurs inversées en sombre.

## Ligne d'état ORP à trois états dans le détail d'une envoyée (Kevin, 18.11.2026, 10 h 48)

Le bandeau « Il manque … / Compléter » quitte le détail d'une envoyée. La ligne ORP de la carte du haut (la ligne d'état de l'en-tête) a trois états :

- « ✓ Déclarée à l'ORP » en vert, si la déclaration est faite et complète ;
- « À déclarer à l'ORP › » en bleu, avec un lien vers la fiche ORP de la candidature ;
- « À compléter pour l'ORP › » en orange, si la déclaration manque d'informations, avec un lien vers la même fiche.

L'orange est celui de la maquette : #B4631F en clair, #F2B98E en sombre, le même orange partout (Kevin, 18.11.2026, 14 h 38, après qu'on lui a proposé #8A4A16). En clair, #B4631F n'atteint que 4,43:1 sur la carte blanche (mesuré par le script de contrôle), sous le minimum de 4,5:1 de la règle e du test d'affichage : c'est un écart connu et voulu, noté dans frontend/e2e/ecarts-connus.json avec cette décision comme raison.

Même correction sur ordinateur : la carte « Pour l'ORP » disparaît, et la ligne d'état ORP va dans l'en-tête du détail.

## Pause sur ordinateur : fenêtre centrée (§71, Kevin, 18.11.2026)

- La planche ReglagesOrdinateurPause (§71, zip du 18.11) remplace les champs Du / Jusqu'au de la carte « Une pause » : un bouton ouvre une fenêtre centrée de 760 px avec le même calendrier de plage que le téléphone, deux mois côte à côte.
- Rien n'est enregistré avant « Enregistrer » ; « Effacer » puis « Enregistrer » retire la pause. « Terminer la pause » reste sur la carte.
- Ceci remplace le point « les champs Du / Jusqu'au restent » de la décision de 9 h 39.

## Aujourd'hui ordinateur : « 1 candidature à envoyer » écrit à la main, sans point final (Kevin, 18.11.2026, 10 h 48)

- Sur ordinateur, le titre d'un jour de rythme s'écrit comme ses variantes (« tes offres arrivent bientôt », « la suite est en plus ») : une seule ligne manuscrite, même style, sans point final. Pluriel : « 2 candidatures à envoyer ».
- Le téléphone ne change pas.

## Poids de la fiche d'une offre : blocs chargés à part, mesurés un à un (Kevin, 18.11.2026, 13 h 37)

- « Autres offres chez … » (planche Offre) et la feuille de la compatibilité se chargent à part de Candidatures.
- Chaque bloc est mesuré avec la page, sous les limites de Candidatures (175 500 o en JS, 72 500 o en CSS) : pages candidatures-autres-offres et candidatures-compatibilite de frontend/scripts/poids.mjs. Aucune limite n'est relevée.
- Les deux blocs ouverts ensemble dépassent la limite de la page (176 727 o mesurés le 18.11) : accepté, parce que la page s'ouvre plus légère et que le surplus ne se charge qu'après un geste sur la fiche.

## Texte d'une offre sur téléphone : « Coller » d'abord, puis « Importer une capture ou un PDF », pas de raccourci iPhone (Kevin, 18.11.2026, 14 h 13)

Fil « Simplifier l'ajout du texte d'une offre ». Options proposées : A (captures lues par l'IA), B (raccourci iPhone
depuis Safari), C (bouton « Coller »). Kevin choisit **C puis A, pas B**.

- **« Coller » en premier** : le bouton qui ouvre le collage (« Coller le texte de l'annonce » sur téléphone,
  « Pas de lien ? Colle le texte » sur ordinateur) lit le presse-papiers (`navigator.clipboard.readText`), avec la
  demande d'autorisation du système. Le texte copié arrive dans la fenêtre de collage existante, à vérifier avant
  « Refaire la note ». Si l'accès est refusé (ou le presse-papiers vide, ou un simple lien) : la fenêtre s'ouvre vide,
  et on colle à la main. Un texte déjà commencé n'est jamais remplacé. Aucun élément ajouté : les libellés et la
  fenêtre restent ceux de la planche OffreProvisoire (paquet du 16.11).
- **Ensuite « Importer une capture ou un PDF »** : PNG, JPG ou PDF, un fichier à la fois, compté dans la formule
  (comme Q1). Le menu « + » de la planche OffreProvisoire (« Importer le PDF de l'annonce », « Importer une capture
  d'écran ») sert de dessin. PR à part.
- **Pas de raccourci iPhone.**

## Alertes : « J'ai créé l'alerte » ne suffit plus, il faut un e-mail du site (Kevin, 18.11.2026, 15 h 13)

- Constat de Kevin (compte factice d'infirmier, 18.11) : l'alerte jobup s'affichait « Active · en attente du premier envoi » et l'étape « Ta première alerte est créée » était cochée, alors que l'alerte n'avait jamais été créée sur jobup. Le bouton « J'ai créé l'alerte » suffisait à tout cocher.
- Règle : une alerte n'est active qu'avec un e-mail du site arrivé dans la boîte jobA1 du compte (code de vérification, message ou alerte), au plus un jour avant la déclaration. Sinon, elle est « À confirmer », dans la famille « À confirmer » de la planche AlertesTel (et AlertesOrdinateur), avec « Coller le code » pour jobup, qui ouvre le panneau du site où le code s'affiche.
- Premiers pas : l'étape 3 n'est faite qu'avec cette preuve, ou une alerte reçue. Remplace la règle du 14.11 (« J'ai créé l'alerte » ou reçue). La fonction de l'exploitant `first_steps_progress` suit (migration 0094).
- Rappel : 24 h après la déclaration sans alerte reçue, « Vérifier 1 alerte » sur Aujourd'hui, que l'alerte soit à confirmer ou non.
- Le reste du plan de Kevin du 18.11 (bouton unique « Créer ma première alerte », parcours en 3 étapes hors des premiers pas, valeurs à copier, une action par état, bandeau au premier e-mail, rappel « Vérifier mon filtre Gmail ») vient dans une PR à part.

## « Ajouter une offre » : « Coller » et « Capture ou PDF » dans la barre du champ, téléphone et ordinateur (Kevin, 18.11.2026, 14 h 38, corrigé à 15 h 21)

§72 du LISEZMOI (paquet jobA1_maquettes_2026-11-18), planche AjouterOffreTel, corrigée par §72d (15 h 20) et la
réponse de 15 h 21 :

- Pas de boutons tonals au-dessus du champ. « Coller » et « Capture ou PDF » vont dans la barre du bas du champ, à
  gauche de la flèche d'envoi : boutons texte bleus (#1A3496), 44 px de haut, sans fond, icône + texte. Le + est retiré.
- Indication du champ : « Lien ou texte de l'annonce ». Pas de phrase d'intro. Pastille « Capture ou PDF : compte
  dans ta formule ».
- Ordinateur : « Capture ou PDF » remplace « Importer le PDF », même libellé et même place que sur téléphone. Même
  contenu partout, seule la taille change.
- « Coller » lit le presse-papiers sur ce toucher, avec la demande d'autorisation du système ; refusé : le curseur va
  dans le champ, où l'on colle à la main (décision du 18.11, 14 h 13).
- « Capture ou PDF » suit la règle de « Refaire la note » (Q1 du 17.11, #873) : PDF lu sans IA, capture PNG ou JPG
  recopiée par l'IA, un fichier, 5 Mo au plus, 20 par heure, formule épuisée = capture refusée avant tout appel.
  Route `POST /api/offers/manual/file`.

## « J'ai contacté quelqu'un » : Rôle et Comment en pastilles (Kevin, 18.11.2026, 14 h 38, §72)

- « Son rôle · facultatif » : Recrutement, Responsable du poste, Équipe, Autre. « Comment » : LinkedIn, E-mail, Téléphone, En personne, Autre.
- Ce sont des pastilles `role="radio"` dans un `role="radiogroup"`, avec `aria-checked` et une hauteur d'au moins 44 px. Cliquer de nouveau sur la pastille choisie la désélectionne.
- « Autre » ouvre un champ « Précise ». Son texte est gardé dans la note du contact (« Rôle : … », « Moyen : … »).
- « En personne » est un nouveau moyen de contact (`in_person`). La colonne n'a pas de contrainte : aucune migration n'est nécessaire.
- Cette décision remplace le point 2 du 18.11 à 10 h 48 (listes de choix de l'app, avec « Autre » et un champ libre).
- 16 h 20 : « Ancien de ton école » est retiré des choix, validé par Kevin ; ce cas passe par « Autre ». La phrase sous le titre de la fenêtre (« jobA1 le note dans l'historique… ») est retirée (§72g).

## Pause sur ordinateur : flèches de mois (Kevin, 18.11.2026, 14 h 38)

- Sur ordinateur, la fenêtre de la pause montre deux mois et des flèches « < » et « > » de 44 × 44 px (« Mois précédent » / « Mois suivant ») de chaque côté des deux noms de mois, sans défilement.
- Sur téléphone, les mois défilent verticalement, comme sur la planche ReglagesRythmePause.
- La planche ReglagesOrdinateurPause sera mise à jour en ce sens.

## Rendez-vous sur téléphone sans bouton Filtres (Kevin, 18.11.2026, 14 h 38, §72)

- L'onglet Rendez-vous n'a pas de bouton Filtres. Les rendez-vous sont seulement regroupés en « À venir » et « Passés ».
- La place du bouton (44 px) reste à droite de l'en-tête pour l'alignement du titre. « Alertes » est ainsi au même endroit sur les trois onglets (planches RendezVous et RendezVousPreparer, clair et sombre).

## Filtre Distance : « Toutes » par défaut (Kevin, 18.11.2026, 14 h 39)

Le groupe « Distance depuis Renens » s'ouvre sur « Toutes », et « Tout effacer » y revient. La planche, qui s'ouvre
sur 30 km et revient à 50 km, sera corrigée. Raison : un défaut en km retirerait des offres de la liste de main.

## Filtres : plus de phrase d'aide sous la note ni sous le type de note (Kevin, 18.11.2026, 16 h 20, §72g)

Sur téléphone et sur ordinateur, en clair et en sombre, on retire « À quel point l'offre correspond à ton profil »
(sous « Note minimale, sur 100 ») et « Provisoire : notée sur l'extrait de l'alerte » (sous « Type de note »).
Règle générale du même message : on comprend l'écran en 3 secondes, un seul bouton plein, aucune phrase qui répète
le titre ou l'image ; un texte que la planche n'a pas se retire. Le switch « Télétravail possible » reste en place
(filtres en direct, pas de bouton « Appliquer »).
