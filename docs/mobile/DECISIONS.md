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

## Formations : catalogue vide pour « Mon domaine » (Kevin, 16.11.2026, 13 h 53)

- Quand le catalogue vérifié n'a rien pour « Mon domaine », avant tout filtre : titre « Rien dans le catalogue pour {domaine} », pastille « Le catalogue couvre surtout l'informatique pour l'instant », bouton principal « Chercher des formations en {domaine} » (la recherche web existante). {domaine} est le premier mot-clé de « Mon domaine ».
- « Aucune formation avec ces filtres » reste seulement quand ce sont les filtres qui vident la liste.
- Le catalogue des soins viendra d'une liste sourcée fournie par Kevin : aucune formation inventée.

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
