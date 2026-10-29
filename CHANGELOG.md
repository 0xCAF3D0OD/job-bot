# Historique des versions

Une ligne par version, la plus récente en bas. Le détail de chaque version (ce qui change, ce
qui est vérifié) est dans le document de cadrage qu'elle cite.

**Ce fichier est assemblé : ne le modifie pas.** Une PR dépose `changelog.d/<sujet>.md`, sans
numéro (la première ligne : le contenu ; une ligne « État : … » facultative, sinon « livrée ») ;
sur main, `scripts/changelog.py` lui donne le numéro suivant à la fusion et assemble ce tableau.

| Version | Contenu | État |
|---|---|---|
| 0.1.0 | Squelette : API, worker, base, page État | livrée |
| 0.2.0 | Collecte Gmail, journal des recherches, dédoublonnage | livrée (analyseurs jobup et Indeed) ; Job-Room : pas d'analyseur dédié, présent en pause dans les sites (docs/11) |
| 0.3.0 | Documents, blocs de profil, prérequis et réglages, filtre | livrée |
| 0.3.1 | Lien de candidature et texte complet des offres jobup | livrée |
| 0.4.0 | Page Offres avec filtres, note et résumé IA, notifications | livrée |
| 0.4.1 | Propositions de blocs de profil par l'IA depuis un document | livrée |
| 0.5.0 | Suivi des candidatures (a), lettre (b) et CV adapté (c) | livrée |
| 0.6.0 | Export ORP (a) et rappels (b) | livrée |
| 0.6.1 | Offres expirées (a), prise en main (b), filtres au choix (c) | livrée |
| 0.7.0 | Expiration signalée (a), mots-clés (b), sites ajoutés : jobs.ch, LinkedIn (c) | livrée |
| 0.7.1 | Détail allégé et adresse de l'annonce (a), registre IDE (b) | livrée |
| 0.7.2 | Adresse cherchée sur Internet par l'IA | livrée |
| 0.7.3 | Postuler depuis la préparation, lien de candidature pour l'ORP | livrée |
| 0.7.4 | Page Offres (transition, tri), logos des entreprises | livrée |
| 0.8.0 | Cloche des alertes (a), Actualités (b) | livrée |
| 0.9.0 | Actualités ciblées (a), sources suggérées et veilles (b), formations (c) | livrée |
| 0.10.0 | Profils d'essai : Actualités (a), Formations (b) | livrée |
| 0.11.0 | Connexion (a), Candidatures et ORP réunies (b) | livrée |
| 0.12.0 | Navigation par catégories : menu et rubrique Candidatures (a), Aujourd'hui et Réglages (b) | livrée |
| 0.13.0 | Mes alertes (a), Voir l'offre chez l'employeur (b) | livrée |
| 0.14.0 | Simplifier : textes et « Comment ça marche » (a), Alertes (b), offre, ORP, Réglages, Profil (c) | livrée |
| 0.15.0 | Suivi et preuves ORP en un onglet, en calendrier | livrée |
| 0.16.0 | Retour d'entretien : formulaire (a), enseignements et préparation (b) | livrée |
| 0.17.0 | Assistant : discussion et lecture des données (a), contexte de la page et raccourcis (b) | livrée |
| 0.18.0 | Remplir le formulaire de l'employeur : PDF et fiche à copier (a), extension du navigateur (b) | livrée |
| 0.19.0 | Télétravail : repérage, règle et filtre (a), sites d'offres à distance (b) | livrée |
| 0.20.0 | Filtres des offres en cartes, courbe des notes | livrée |
| 0.21.0 | Accessibilité : contraste, couleur seule, zones de clic | livrée |
| 0.22.0 | Une action principale par page (a), aides visibles (b) | livrée |
| 0.23.0 | Repérer les offres douteuses : doublons, annonces permanentes, employeur caché, arnaques | livrée |
| 0.24.0 | Contacts dans l'entreprise : recherches LinkedIn déjà remplies, premier message rédigé par l'IA, suivi des prises de contact et relance | livrée |
| 0.25.0 | Alléger la plateforme : bulle temporaire, lignes dépliables, panneau latéral, pages compactes, aides derrière « ? », Actualités en page journal | livrée |
| 0.26.0 | La plateforme sur téléphone : menu burger, rien ne déborde, action principale en bas, écrans plein écran, écran d'accueil | livrée |
| 0.27.0 | Téléphone : pages longues raccourcies (Formations en liste, Réglages en lignes dépliables, Aujourd'hui l'essentiel d'abord) | livrée |
| 0.28.0 | Actualités en modules à la manière de RTS : en tête, second rang, lignes à vignette ; format téléphone | livrée |
| 0.29.0 | Téléphone : Candidatures et Profil (en-tête compact, offres en lignes, « Filtrer » en carte, Suivi sur une ligne, onglets courts) | livrée |
| 0.30.0 | Formations : une formation terminée entre dans ton profil (a), demande de financement à l'ORP (b) | livrée |
| 0.31.0 | Relancer une candidature : message rédigé (ou modèle), messagerie, date de relance, « Sans réponse » après 14 jours | livrée |
| 0.32.0 | Candidatures spontanées : sans annonce, préparées comme une offre (lettre adaptée, CV, adresse au registre), ligne ORP habituelle | livrée |
| 0.33.0 | Tes dates dans ton agenda : fichier par entretien, abonnement (entretiens, suites, remise ORP, relances) | livrée |
| 0.33.1 | Revue 0.24 à 0.33 : corrections (spontanée expirée, Échap, cloche, relances, agenda, IA indisponible…) | livrée |
| 0.34.0 | Bilan : ce qui donne des réponses (source, note, contact, relance), parcours, résumé pour le rendez-vous ORP | livrée |
| 0.35.0 | Revue page par page : Aujourd'hui par urgence, Actualités emploi / économie, un en-tête et une largeur, vrais pluriels, alignements | livrée |
| 0.36.0 | Formations : cartes calmes (3 lignes, « Suivre » ou état + « Gérer »), suivi dans le panneau latéral en trois sections | livrée |
| 0.37.0 | Fiche d'une offre : deux boutons et « ⋯ », sections Pour toi, À savoir (✓ ! ✗), Entreprise, Annonce repliée | livrée |
| 0.38.0 | Suivi : cartes calmes (statut, une seule prochaine étape), panneau d'une candidature en cinq sections, ouvert aussi depuis la liste | livrée |
| 0.39.0 | Préparer une candidature : onglets ① Lettre ② CV ③ Postuler, l'offre à côté de la lettre, PDF / Word sur une ligne | livrée |
| 0.40.0 | Réglages : une rubrique à la fois (six), sites et sources en lignes calmes avec panneau, seuils dits en clair | livrée |
| 0.41.0 | Mon parcours : un encart de dépôt, documents en lignes calmes, cartes de bloc calmes, le bloc dans le panneau latéral | livrée |
| 0.41.1 | Revue : menu « ⋯ » commun (Échap ne ferme que le menu), une classe de section, 61 règles CSS inutiles retirées | livrée |
| 0.41.2 | Téléphone, revue de 0.36 à 0.41 : contexte de la préparation, objet de la lettre, texte aligné, étapes de Postuler, filtres du parcours | livrée |
| 0.42.0 | L'assistant propose, tu confirmes : trier une offre, la signaler expirée, changer le statut d'une candidature ; « Annuler » ensuite | livrée |
| 0.43.0 | Plus de « ? » : l'assistant explique (« Comment ça marche ici ? »), 14 descriptions au survol de 3 s pour le moins évident | livrée |
| 0.44.0 | Aujourd'hui en tableau de bord : quatre tuiles à pictogramme, la semaine en barres, les offres en tableau, la jauge de l'objectif ORP | livrée |
| 0.45.0 | Le Bilan dans le style du tableau de bord : quatre tuiles, le parcours en barres, candidatures et réponses par mois, comparaisons en barres, résumé ORP visible | livrée |
| 0.45.1 | Revue : guide de l'assistant à jour (Aujourd'hui, Bilan), suggestions du Bilan, ménage de la feuille de style | livrée |
| 0.45.2 | Clic direct : l'élément entier ouvre son contenu avec un survol, plus de « › » ni de « Continuer › » | livrée |
| 0.46.0 | Illustrations animées : prise en main, chargements, rédaction par l'IA, fichiers en préparation | livrée |
| 0.47.0 | Micro-interactions : appui, survol, sélecteurs, coches, copier, fichiers sur le bouton, étapes de l'IA ; illustrations réduites aux pages vides | livrée |
| 0.47.1 | Illustrations en grand sur ordinateur (réussites, prise en main, formulaires, pages vides), retours d'actions, entrée des chiffres et des barres | livrée |
| 0.47.2 | Illustrations à côté des cartes et plus grandes ; Engagement en grand par-dessus la page | livrée |
| 0.48.0 | Carte de réussite qui vient devant, transition des pages qui chargent, images à côté des blocs trop larges | livrée |
| 0.48.1 | Illustrations à leur place : retirées des Réglages, de Profil, de Préparer et d'Aujourd'hui ; une seule famille aux couleurs de l'interface | livrée |
| 0.48.2 | Des blocs à leur taille : frise des étapes, ce que donnent tes critères, dépense de l'IA, Réglages à la largeur de lecture ; transition plus lente | livrée |
| 0.48.3 | Revue : l'assistant connaît tes critères et la dépense de l'IA, ménage de la feuille de style, téléphone vérifié (sélecteurs, barres des critères, guides, page introuvable) | livrée |
| 0.50.0 | Chaque donnée appartient à un compte, séparé par la base ; tâches compte par compte ; test des deux comptes sur toutes les routes | livrée |
| 0.51.0 | Comptes invités : invitation et nouveau mot de passe par lien, suspension, suppression ; rubrique Plateforme ; plafond de l'IA par compte et total ; notifications à soi | livrée |
| 0.52.0 | Une adresse de réception par compte, collecte rangée par destinataire, e-mails « confirmez votre alerte » dans Alertes, pause des sites par compte | livrée |
| 0.53.0 | Tes données : page publique (ce qui est gardé, ce qui part à l'IA, tes mentions), export complet du compte, suppression de son compte | livrée |
| 0.53.1 | Page de connexion en deux moitiés : illustration à gauche, connexion à droite ; Google, Apple, Microsoft présentés (pas encore branchés) | livrée |
| 0.54.0 | L'accueil après la première connexion, façon Duolingo : sept questions en cartes, chaque réponse règle la plateforme, puis la création des alertes | livrée |
| 0.55.0 | Les illustrations de jobA1 : des images générées, plus grandes, remplacent les dessins unDraw (gardés en réserve) ; sans connexion, la présentation de la plateforme à la place des Actualités | livrée |
| 0.55.1 | Les pages qui chargent gardent leurs dessins animés d'avant (Aujourd'hui, Offres, Suivi, Bilan, Alertes, Actualités, Formations) | livrée |
| 0.55.2 | La connexion illustrée par la ville et le bureau, l'image entière remplissant la moitié gauche | livrée |
| 0.55.3 | En sombre, la connexion joue la vidéo du soir qui tombe, puis l'image du soir | livrée |
| 0.55.4 | La connexion sans voile : la phrase en haut à gauche, la lune visible, les couleurs qui suivent le ciel | livrée |
| 0.55.5 | La connexion plus nette, la phrase qui blanchit plus tard | livrée |
| 0.56.0 | Le titre animé : une fois connecté, un personnage à la place du « 1 », qui change chaque heure | livrée |
| 0.56.1 | Revue des comptes : les Actualités fermées sans connexion, liens d'invitation verrouillés, identifiant unique, journal des tâches réservé, export complet | livrée |
| 0.56.2 | Revue, suite : l'assistant à jour (`assistant-v6`), le ménage des illustrations, le focus de l'accueil, le test instable stabilisé | livrée |
| 0.57.0 | L'extension remplit la saisie Job-Room d'une candidature (tu vérifies et sauvegardes) ; « déclarée dans Job-Room » suivi pour chaque candidature | livrée |
| 0.57.1 | Job-Room dans Firefox : le remplissage tourne dans la page, les valeurs tapées sont prises ; chaque valeur relue après la saisie | livrée |
| 0.58.0 | L'extension prête pour la boutique de Mozilla : relier en un clic (« Relier ce navigateur »), onglet d'accueil à l'installation, paquet, fiche et politique de confidentialité | livrée |
| 0.58.1 | Premier essai réel : le panneau tient dans sa largeur, les champs facultatifs de Job-Room ne sont plus signalés, essai par le paquet (zip) | livrée |
| 0.59.0 | La démo publique : une installation à part, sans connexion, en lecture seule, remplie de données fictives par `jobbot demo-seed` | livrée |
| 0.59.1 | `make demo` : la démo en local en une commande, pour la montrer depuis son ordinateur | livrée |
| 0.60.0 | Des offres plus légères : une ligne par jour, une offre sur une ligne, une seule alerte si nécessaire, les filtres secondaires repliés | livrée |
| 0.61.0 | Les actions rangées dans « ⋯ » : dans chaque partie, le contenu visible, au plus une action importante, le reste dans un menu | livrée |
| 0.62.0 | S'entraîner à l'entretien : l'IA joue le recruteur, cinq questions, une relance au plus, puis un retour question par question | livrée |
| 0.62.1 | Revue : garde-fou de la démo, un seul cadre par bloc, jeton de liaison qui expire, démo en lecture seule, entraînement verrouillé | livrée |
| 0.62.2 | Revue : assistant v8, cohérence des « ⋯ » et de la note, accessibilité, ménage, extension 0.58.2 | livrée |
| 0.63.0 | La démo en ligne : `deploy/demo/` (Docker, Caddy, remise à neuf chaque nuit) et son mode d'emploi | livrée |
| 0.63.1 | La démo en ligne sur https://demo.joba1.ch ; mode d'emploi corrigé d'après la mise en ligne | livrée |
| 0.63.2 | Actualités : plus de message « rien n'est enregistré » à l'ouverture de la démo, vignettes sans image centrées | livrée |
| 0.64.0 | Étanchéité des comptes : le serveur jamais administrateur de la base (rôles `jobbot_app`, `jobbot_worker`), une règle pour chaque table, règles de sécurité écrites | livrée |
| 0.64.1 | Aucun lien entre deux comptes dans la base, tâches qui gardent leur compte, erreur de notation par compte | livrée |
| 0.64.2 | Connexion : jetons coupés à la suspension, essais comptés par adresse, session de 90 jours au plus, mode sans connexion verrouillé ; en-têtes de sécurité, taille des envois, audit hebdomadaire des bibliothèques | livrée |
| 0.65.0 | La page de maintenance : par-dessus l'écran pendant une mise à jour, `jobbot maintenance on/off`, `make update` | livrée |
| 0.65.1 | Maintenance en lecture seule (`--lecture`), tâches de fond en pause, le dessin unDraw animé sur la page d'attente | livrée |
| 0.65.2 | Revue : Actualités sans message pendant une maintenance en lecture seule, curseur retrouvé après la page d'attente, base pas à jour avant la connexion, worker en pause ; documentation à jour | livrée |
| 0.66.0 | Les sauvegardes automatiques : chaque nuit, chiffrées, gardées 7 jours, 4 semaines et 6 mois, essayées chaque dimanche ; `jobbot backup`, `jobbot restore` | livrée |
| 0.66.1 | `jobbot restore` trouve une sauvegarde par son seul nom | livrée |
| 0.67.0 | Le rendez-vous ORP : une feuille pour le conseiller (mois en bref, ce qui bloque, ce qui te manque, questions, obligations), en PDF ; rappel la veille | livrée |
| 0.67.1 | Des textes plus courts dans l'interface ; la page Tes données en listes | livrée |
| 0.67.2 | Après le rendez-vous ORP : ce qui a été convenu, le carnet, l'agenda et le rappel de la veille, l'objectif et les formations mis à jour ; le message rédigé par l'IA, sur demande | livrée |
| 0.67.3 | « Déclaration Job-Room » dit ce qui reste à faire ; cases du calendrier à la même taille | livrée |
| 0.67.4 | La déclaration Job-Room en liste courte, sous « À relancer » ; PDF et CSV dans le ⋯ du mois | livrée |
| 0.67.5 | Nouvelles images et nouvelle vidéo de la page de connexion | livrée |
| 0.67.6 | Connexion : la phrase passe en blanc à 3 s de la vidéo du soir | livrée |
| 0.68.0 | Le bon rythme : l'objectif ORP réparti par semaine, la dose du jour, les jours sans recherche, un message d'offres par jour | livrée |
| 0.68.1 | La pause, le message de fin de semaine, tes semaines dans le Bilan, le rythme dans l'assistant | livrée |
| 0.69.0 | Les certificats de travail décodés : formules codées, note, conseil ; lecture détaillée par l'IA sur demande | livrée |
| 0.69.1 | Certificats : la lettre de correction, le certificat intermédiaire, les certificats à joindre dans Préparer | livrée |
| 0.70.0 | Une interface qui s'affiche : titres = menu, sans sous-titres, étiquettes sans « ton », « ta », « tes » | livrée |
| 0.70.1 | Les textes d'aide triés : ce qui explique passe en description au survol, les prix sortent des boutons | livrée |
| 0.70.2 | La capsule à droite : la cloche et le menu du compte (Réglages, Données personnelles, Diagnostic, collecte) ; cinq pages dans le menu | livrée |
| 0.70.3 | Trois entrées : Aujourd'hui, Candidatures, Progresser (Actualités et Formations) ; Profil dans le menu du compte | livrée |
| 0.70.4 | La capsule qui se déroule : cloche, compte et ☰ s'ouvrent dans son cadre, séparés par des filets ; les menus « ⋯ » au même style | livrée |
| 0.70.5 | Progresser dans la capsule (l'étincelle et son aperçu) ; deux pages dans le menu, en barre d'onglets sur téléphone | livrée |
| 0.70.6 | Les formations en cartes aérées (à la manière de Sphere), le cœur « Intéressé » ; les logos en carrés arrondis | livrée |
| 0.70.7 | Une seule hauteur pour les contrôles, alignés dans leur rangée ; l'audit des rangées | livrée |
| 0.71.0 | Aujourd'hui épuré : la phrase du jour et une action, les bandeaux datés, À faire et Mois ORP ; la jauge dans le Bilan | livrée |
| 0.71.1 | La page en cours entourée à main levée, dans le menu et la barre d'onglets | livrée |
| 0.71.2 | Le nouveau logo (deux boucles bleues autour de l'étoile) et la mascotte de l'assistant ; icônes régénérées | livrée |
| 0.71.3 | Le logo au diamant en contour ; « jobA1 » en entier, sans le personnage de l'heure | livrée |
| 0.71.4 | La boucle à main levée de la page en cours retirée (le logo va changer) | livrée |
| 0.71.5 | Les trois visages de l'assistant (à l'écoute, réfléchit, a trouvé) ; le bouton « Assistant » au bleu de la mascotte | livrée |
| 0.71.6 | Le logo choisi : un trait qui entoure le diamant pêche ; icônes régénérées, version noire | livrée |
| 0.72.0 | L'iconographie : une seule famille d'icônes au trait, à côté du texte ou à sa place ; le point pêche pour les actions IA | livrée |
| 0.73.0 | S'inscrire, sur demande : « Créer un compte » depuis la connexion, validé par l'exploitant dans Réglages › Plateforme | livrée |
| 0.74.0 | Le logo : un visage complice fait avec le 1 du nom, la bille pêche en œil ; les icônes de l'onglet, de l'app et de l'extension | livrée |
| 0.74.1 | Les icônes portent leur version (`?v=0.74.0`) : le navigateur prend le nouveau favicon sans vider son cache | livrée |
| 0.74.2 | La doc du logo passe en docs/103 (le numéro 102 est celui de l'inscription sur demande) | livrée |
| 0.75.0 | Premiers pas d'un nouveau compte : le crayon pour modifier l'accueil, deux boutons égaux par site, des exemples qui suivent le métier | livrée |
| 0.75.1 | « Fermer mon compte », aussi depuis le menu du compte, la confirmation déjà ouverte | livrée |
| 0.76.0 | Des Réglages épurés : une carte par rubrique, sans barre ni filet orphelin ; le seuil des notifications en pastilles ; les nombres sans flèches | livrée |
| 0.76.1 | Réglages sur téléphone : le contenu ne colle plus au bord, les parties resserrées, les pastilles sur une ligne ; des exemples de mots-clés pour tous les métiers | livrée |
| 0.76.2 | L'accent au bleu du logo, en clair et en sombre ; le texte sur l'accent lisible en sombre | livrée |
| 0.77.0 | Annuler plutôt que confirmer (plus de fenêtres du navigateur) ; l'aide au doigt sur téléphone ; le Diagnostic à l'exploitant | livrée |
| 0.77.1 | Renommer un profil d'essai et modifier une recherche d'alerte sur place ; plus aucune fenêtre du navigateur | livrée |
| 0.77.2 | Réglages › Compte : un titre par partie, « Se déconnecter partout » en lien | livrée |
| 0.77.3 | Réglages structurés : un filet fin entre les parties, sur ordinateur et téléphone | livrée |
| 0.77.4 | Fermer son compte sur téléphone : la confirmation tient dans l'écran, le champ du mot de passe stylé | livrée |
| 0.77.5 | Le menu comme Sphere : la capsule à largeur fixe sur ordinateur, le plein écran sur téléphone | livrée |
| 0.77.6 | Réglages aérés comme les CFF : 1,5 rem de marge, 1,5 à 1,75 rem autour des filets | livrée |
| 0.78.0 | Les Réglages comme les CFF : une longue page avec des marqueurs sur téléphone, les titres au-dessus des cartes, les descriptions visibles, consulter en gris, les actions en pilules | livrée |
| 0.78.1 | Les marqueurs des Réglages ne touchent plus le bord de l'écran ; un fondu montre que la rangée défile | livrée |
| 0.78.2 | Le Profil comme les CFF : les prérequis en carte grise avec un crayon rond, les descriptions visibles, les blocs en objets gris, la page en blanc | livrée |
| 0.78.3 | Retours d'affichage : « Enregistrer » avec sa marge, « Enregistré » sous le seuil, la bulle centrée, l'export sur une ligne, l'installation de l'extension en étapes | livrée |
| 0.78.4 | Cohérence sur ordinateur : titres en gras, l'effet des critères en carte grise, les Réglages en blanc, le plafond total au changement, le Diagnostic dans le sommaire | livrée |
| 0.79.0 | Une adresse d'alerte à jobA1 pour les invités (`nom-code@alertes.joba1.ch`) ; en attendant, l'adresse abrégée et « Copier l'adresse » | livrée |
| 0.79.1 | La plateforme présentée : le chemin bleu jusqu'à la fin, une marge sur les côtés, les notes en cercle | livrée |
| 0.79.2 | La plateforme sur téléphone : les personnages qui cachaient du texte passent sous la maquette | livrée |
| 0.80.0 | Des offres dès le premier jour : à la fin de l'accueil, jobA1 lit la recherche publique de jobup (20 offres au plus) pour ton métier et tes lieux ; relance depuis Alertes | livrée |
| 0.80.1 | Les premières offres aussi pour les comptes qui avaient fini leur accueil avant : la recherche jobup part à leur première visite | livrée |
| 0.81.0 | Ajouter une offre trouvée ailleurs (site d'entreprise, LinkedIn, journal, Google Jobs) par son lien ou son texte, aussi par « Partager vers jobA1 » sur Android ; les exemples suivent ton métier | livrée |
| 0.82.0 | Les codes et les messages des sites : le code de vérification affiché (et dans la notification), rempli par l'extension, la boîte relevée toutes les 15 s à la demande ; les liens de confirmation ouverts par jobA1 ; les messages des sites lisibles 30 jours ; extension 0.59.0 | livrée |
| 0.82.1 | La page d'attente refaite : l'en-tête de jobA1, une carte avec le dessin (qui ne dépend plus du réseau), le compte à rebours et « Réessayer maintenant » | livrée |
| 0.82.2 | L'assistant ne sort plus du cadre sur téléphone : une infobulle invisible au bord droit élargissait l'écran ; rien ne déborde plus sur le côté | livrée |
| 0.82.3 | L'adresse d'alerte sans « catch-all » : `JOBBOT_ALERT_DOMAIN=alertes@joba1.ch` donne `alertes+nom-code@joba1.ch`, qui passe par une seule redirection | livrée |
| 0.82.4 | La recherche publique de jobup coupée : ses conditions d'utilisation (déc. 2025, §7) interdisent les robots ; réglage `JOBBOT_PUBLIC_SEARCH_ENABLED`, faux par défaut | livrée |
| 0.83.0 | La boîte des invités à part : une vraie boîte Infomaniak (`alertes@joba1.ch`), lue puis vidée par jobA1, plus rien dans la boîte de l'exploitant ; la copie d'un code effacée à 30 minutes ; les invités prévenus | livrée |
| 0.83.1 | La page Alertes remise en ordre : le code en tête, « Les alertes », puis « Les e-mails des sites » en une carte (« J'attends un code », les messages) | livrée |
| 0.83.2 | La page Alertes en deux colonnes sur ordinateur : les alertes à gauche, les e-mails des sites à droite, titres et cartes alignés | livrée |
| 0.84.0 | « Cette note ne me correspond pas » : trop haute ou trop basse, pourquoi ; un bloc de profil proposé (l'offre renotée), ou un critère en un clic pour le lieu, le taux, le contrat | livrée |
| 0.84.1 | L'extension dans la boutique de Mozilla : le lien dans les Réglages ; la description et la fiche de la 0.59.0 disent les codes de vérification et leur accord | livrée |
| 0.84.2 | La page Alertes resserrée : le code dans la carte des e-mails des sites, moins de texte, les deux cartes de même hauteur ; une seule règle pour les pastilles ; « Comment ça marche » masqué s'annule et revient par le menu du compte | livrée |
| 0.84.3 | Le résumé des alertes structuré (une recherche par ligne, l'état en pastille) ; une image haute à l'étape 2 de l'assistant ; la page de maintenance sans carte | livrée |
| 0.84.4 | Les titres des cartes décollés du bord : 1,75 rem en haut (1,5 rem sur téléphone), comme les côtés | livrée |
| 0.85.0 | Seulement le métier : les recommandations jobup hors métier écartées (comptées dans le journal) ; les actualités par familles de métiers, « Rien de neuf sur ton métier » plutôt que l'économie | livrée |
| 0.86.0 | Lier ses alertes existantes : le pas-à-pas pour que sa messagerie (Gmail, Outlook) transfère les seules alertes jobup et Indeed à l'adresse jobA1 ; le code de Gmail affiché ; jamais un mot de passe | livrée |
| 0.86.1 | Les règles de l'interface appliquées : « Alertes existantes » en trois lignes et deux icônes de copie, les explications au survol ; l'audit des rangées remis à zéro (pilules à la hauteur commune, champs des Réglages alignés) | livrée |
| 0.86.2 | La démo : les actualités ne répondaient plus (une écriture dans une base en lecture seule) | livrée |
| 0.87.0 | Le poids des pages : chaque page se charge à l'ouverture (premier écran 82 Ko au lieu de 205) ; un budget vérifié par `make poids` | livrée |
| 0.88.0 | L'accessibilité vérifiée : audit axe-core et parcours au clavier sur la démo, tout corrigé (calendrier du Suivi, contrastes, liens, repères) ; la page « Accessibilité » ; « écris ou dicte » sur téléphone | livrée |
| 0.89.0 | Les règles de l'interface partout : descriptions en une ligne (le reste au survol), plus de barre verticale dans les repliables, titres sans « ton » ni question ; un troisième audit (`regles.py`), 49 défauts → 0 | livrée |
| 0.89.1 | Une structure cohérente : 18 règles validées reportées dans docs/interface.md ; repliables à 1,5 rem du bord, « Masquer » sur la ligne du titre, cartes d'une rangée de même hauteur, 2 rem entre grands blocs ; l'audit vérifie marges et hauteurs | livrée |
| 0.90.0 | Le code d'un site ne part plus dans la notification du téléphone (« Code jobup reçu ») ; les copies des alertes lues des invités effacées au bout de 90 jours | livrée |
| 0.90.1 | Les coordonnées ne partent jamais à l'IA : nom, adresse et date de naissance retirés du CV et des certificats avant l'envoi, même sans coordonnées saisies | livrée |
| 0.90.2 | Les pastilles du calendrier : un anneau orange pour « à compléter » au lieu d'un « ! » rouge qui débordait, « En attente » lisible en sombre, des pastilles espacées | livrée |
| 0.91.0 | Le profil depuis le CV, à l'accueil : le CV lu par l'IA (sans coordonnées), « Voici ce que j'ai compris » (blocs et postes à valider) ; les langues et le télétravail demandés, préremplis | livrée |
| 0.92.0 | Les alertes préparées : 63 métiers et leurs recherches (l'IA pour les autres, avec le seul nom du métier), les postes du CV ; l'adresse copiée en ouvrant un site ; la première alerte d'un site annoncée ; « rien reçu » après 24 heures | livrée |
| 0.93.0 | La note expliquée : en mots dans les listes (Très proche, Proche, À creuser, Loin) avec le visage du 1 et un filet ; dans la fiche, pourquoi en une phrase et le niveau visé ; « Je l'ai » ajoute un manque au profil et renote ; la jauge du profil | livrée |
| 0.93.1 | La démo, une note qui a du sens : la phrase « pourquoi » tirée de ce que chaque offre demande, le poste de données décrit comme tel, le niveau seulement sur « SRE junior » | livrée |
| 0.94.0 | Le visage du 1 : le mois ORP avec son humeur (une tuile, des segments, « Dans les temps », « On rattrape », « Objectif atteint ») dans Aujourd'hui et le Bilan ; le visage au chargement des pages et dans les listes vides, à la place des dessins | livrée |
| 0.95.0 | Les moments du visage : « Rien d'urgent aujourd'hui » un jour calme ; deux victoires (un entretien proposé, l'objectif du mois atteint) ; Aujourd'hui en compact sur téléphone (le mois ORP en une ligne) | livrée |
| 0.96.0 | Le personnage se transforme : pendant le chargement d'une page, le visage prend l'objet de la page (soleil, loupe, flèche, cloche, anneau, cravate, profil, roue dentée) ; le Rendez-vous, le Profil et les Réglages ont aussi leur transition | livrée |
| 0.97.0 | Les offres du jour une par une dans Aujourd'hui (Garder ou Écarter, Annuler, le balayage au doigt ; 5 quand le mois est à rattraper) ; l'étape ④ Suivre dans Préparer (la relance à la date choisie, la preuve ORP à compléter, le contact) | livrée |
| 0.98.0 | Les formules, sans paiement : Essentiel gratuite (150 offres notées, 10 lettres, 10 CV, 30 messages, 1 entraînement par mois) et Plus ; les compteurs au survol et dans Réglages › Compte, la ligne à la limite ; la formule réglée par l'exploitant ; la note avec un modèle moins cher, à comparer avant (`jobbot score-compare`) | livrée |
| 0.99.0 | Le paiement de Plus par Payrexx, fermé par défaut : « Passer à Plus » après les conditions acceptées, la confirmation vérifiée auprès de Payrexx, le webhook signé, la résiliation, les paiements reçus ; la page Conditions d'utilisation ; le paiement dans Données personnelles | livrée |
| 0.99.1 | Les corrections des audits d'ergonomie du 22 octobre : plus de page blanche après une mise à jour, le menu ne mène plus à une offre disparue, une seule étape courante dans Préparer, un titre d'onglet par page, « Aller au contenu », les contrastes des initiales et de la cloche, les cibles de 24 px, le retour en haut à gauche, l'adresse et le focus à l'ouverture d'une offre, sans jargon technique | livrée |
| 0.99.2 | Les tests du frontend sans erreur non gérée : chaque maquette répond à sa propre adresse (Bilan, fiche d'offre, aperçu Progresser), les pages démontées à la fin de chaque test (Actualités, Réglages) | livrée |
| 1.0.0 | La structure : trois entrées (Aujourd'hui, Candidatures, Bilan), le Bilan au menu avec Résultats, Formations et Actualités, Progresser retiré ; les Résultats allégés (la conclusion d'abord, le détail replié) ; les mêmes mots partout (Gardées, À préparer, Poste obtenu) ; l'assistant à jour | livrée |
| 1.0.1 | La crédibilité : un pied de page (Données personnelles, Conditions, Accessibilité, À propos) sur chaque page, la page « À propos », « Le code » hors du bandeau de la démo ; une lettre et un CV d'exemple dans la démo ; la fiche du test avec 5 personnes (docs/127) | livrée |
| 1.1.0 | Les premiers pas : en haut d'Aujourd'hui, une seule prochaine action en cinq étapes (« 2 sur 5 »), l'attente des premières offres dite, Aujourd'hui allégé tant qu'elles manquent, les deux anciens guides retirés ; des écrans vides qui disent quoi faire (Offres, Suivi, Rendez-vous, Bilan) ; le chiffre des premiers pas pour l'équipe (Réglages › Plateforme) | livrée |
| 1.1.1 | Les audits sur un vrai compte (hors démo) : titres en noms (premiers pas, alertes, langues), aides du Profil en une ligne, liste des profils d'essai sans cadre par ligne, contraste d'un site en pause, lien souligné, attribut d'accessibilité des filtres « Domaine », message des sauvegardes raccourci | livrée |
| 1.2.0 | « À faire » rangé : deux rangées de deux cartes (Offres du jour · Mois ORP, puis À préparer · À relancer), le compte et « Tout voir » dans le titre, une seule forme de ligne (logo, texte coupé par « … », action alignée), 3 lignes au plus, une carte vide absente | livrée |
| 1.3.0 | Les pages rangées (1) : le Suivi (l'en-tête sur deux lignes, « À relancer » et « À déclarer » dans la forme de ligne d'Aujourd'hui, 5 puis la suite) et le Rendez-vous (Préparer, Le mois en une carte, le carnet replié) | livrée |
| 1.3.1 | Les pages rangées (2) : les titres d'une seule taille et d'une seule graisse partout, Profil (« Critères », blocs sur 3 colonnes sans crayon, plus de barre orange), Réglages (filet en trop, descriptions en une ligne, vide du bas), Formations (une ligne d'outils, le marque-page en haut), Alertes en une colonne ; l'assistant à jour | livrée |
| 1.4.0 | Le nécessaire : chaque information aide à décider ; ce qui se répète part (l'action en double, la semaine dite deux fois, la ligne « Offre », la note en chiffre), ce qui n'aide pas passe au survol ou n'apparaît qu'au besoin (la collecte, les blocs, les parties vides, les obligations faites, le code de vérification), « Enseignements » dans le Bilan, le filtre de note en trois choix, le seuil de l'employeur dans Outils | livrée |
| 1.4.1 | La lecture : les phrases longues raccourcies (16 mots au plus), toutes les cases à cocher en interrupteurs, le texte collé détecté par l'audit et écarté (docs/132) | livrée |
| 1.5.0 | Les vues choisies : le Suivi en deux onglets (à relancer, à déclarer), la légende au-dessus du calendrier ; le Bilan avec les tuiles en carrés et les mois précédents à côté, « Le détail » en une vue choisie à la fois (plus de cartes dans une carte) ; le Rendez-vous sur toute la largeur ; les audits ouvrent les repliables et chaque vue, en clair et en sombre (docs/133) | livrée |
| 1.5.1 | Le Suivi : la colonne de droite reprend la hauteur du calendrier et défile dedans (retour du 7 octobre rétabli) ; l'état des preuves en bandeau daté, une phrase et une action (docs/134) | livrée |
| 1.6.0 | Les échelles de design, le socle : espacements, tailles de texte, rayons et graisses en variables, doublons de couleurs fusionnés, rendu identique au pixel près ; captures avant/après de toutes les pages (docs/135) | livrée |
| 1.6.1 | Le gris du texte : tout texte gris en `--muted`, `--faint` réservé aux chevrons, soulignés et dessins (3,3:1 au moins en clair) ; le compteur des Actualités ne revient plus après la visite ; captures à heure figée côté serveur (docs/135) | livrée |
| 1.6.2 | Les échelles, le commun : barre du haut, menu, boutons, champs, pastilles, repliables, onglets, toasts, titres, pied de page à l'échelle ; titres et boutons en 600 ; trois interlignes ; une seule orange ; doublons de la mascotte et de `--panel` fusionnés (docs/135) | livrée |
| 1.6.3 | Les échelles, Aujourd'hui : la page à l'échelle ; les initiales d'entreprise sans orange (accent, menthe, ciel) ; un test prouve que l'audit trouve toujours un texte collé au bord (docs/135) | livrée |
| 1.6.4 | Les trois composants : bouton secondaire bordé à 3:1, principal gris une fois désactivé et survol visible en sombre ; repliable entouré au focus et teinté au survol ; note d'une offre sans jauge, « À creuser » en gris chaud ; styles de texte en 600 dans Figma (docs/135) | livrée |
| 1.6.5 | Les échelles, Offres, fiche d'une offre et Préparer à l'échelle ; le visage du 1 remplit ses 20 px dans la note ; l'anneau du repliable suit les coins (docs/135) | livrée |
| 1.6.6 | Les échelles, le Suivi à l'échelle ; la jauge d'affinité revient sous la note ; le visage du 1 cadré au plus près partout (docs/135) | livrée |
| 1.6.7 | Les échelles, le Bilan à l'échelle : tuiles, mois précédents, vues du détail (docs/135) | livrée |
| 1.6.8 | Les échelles, le Rendez-vous à l'échelle (docs/135) | livrée |
| 1.6.9 | Les échelles, Alertes, Profil et Réglages à l'échelle (docs/135) | livrée |
| 1.6.10 | Les échelles, Formations, Actualités et l'assistant à l'échelle (docs/135) | livrée |
| 1.6.11 | Les échelles, les pages publiques et les composants partagés à l'échelle (docs/135) | livrée |
| 1.6.12 | Les échelles, le garde-fou : un test refuse toute valeur en dur hors des exceptions listées ; code mort `.preview-*` supprimé (docs/135) | livrée |
| 1.6.13 | Des tests fiables : un fichier qui ne démarre pas fait échouer la suite, deux processus par défaut ; le garde-fou contrôle aussi l'intérieur des calculs (`--dock-h`, centrage du bouton « ⋯ ») (docs/135) | livrée |
| 1.6.14 | Les tests en CI : serveur (pytest sur PostgreSQL 17) et interface (vitest, types, poids) à chaque envoi sur main et chaque PR (docs/exploitation.md) | livrée |
| 1.6.15 | Les repères : l'anneau d'aujourd'hui en accent, jours vides et cases ORP à faire en `--faint`, visage de la tuile ORP à 32 px, initiales sans couleur en dur (docs/135) | livrée |
| 1.6.16 | La tuile du visage sur les variables (`--mint-soft`, le beige retiré, l'orange pour « à agir »), l'étiquette en majuscules (`--letter-label`), les points des premiers pas en `--faint` (docs/135) | livrée |
| 1.6.17 | La date au-dessus du titre en style étiquette (exception de la §3 des règles), l'action des écrans vides en bouton principal, la devise anglaise retirée de l'interface (docs/135) | livrée |
| 1.6.18 | Candidatures : la conclusion en une phrase, des blocs de chargement, « Ajouter une offre » seul dans l'écran vide ; la pastille de la cloche en orange ; la sélection d'une offre lisible (4,5:1) ; « au plus une action principale » (docs/135) | livrée |
| 1.6.19 | Bilan : la conclusion en haut, le détail en lignes repliables à la place du sélecteur ; les tuiles sans libellé coupé (docs/135) | livrée |
| 1.6.20 | Suivi : la conclusion en haut, « À faire » d'abord (trois lignes), l'objectif en cases, le calendrier et la liste du mois repliés ; le titre des repliables en 600 ; « Refus » en gris (docs/135) | livrée |
| 1.6.21 | Détail d'une offre : « ← Offres » en haut à gauche sur téléphone, l'entreprise et l'annonce repliées (docs/135) | livrée |
| 1.6.22 | Alertes : la conclusion en haut, « Le détail » au-dessus des lignes repliables, des blocs de chargement ; « Rien reçu » en `--orange` (docs/135) | livrée |
| 1.6.23 | Rendez-vous : la conclusion en haut avec « Préparer », une obligation en retard dedans ; la feuille sur une colonne ; le mois replié, « En bref » ouvert ; l'interrupteur non coché en `--faint` (docs/135) | livrée |
| 1.6.24 | Nettoyage : l'historique des versions passe du README à CHANGELOG.md ; le résumé d'une ligne repliable n'est plus jamais coupé ; Rendez-vous sans titre « Préparer » au-dessus du seul formulaire, « Ce qui bloque » avec son résumé, le nom sur toute la largeur ; le bilan du cadrage (docs/135) | livrée |
| 1.6.25 | Actualités retirées de l'interface : l'onglet du Bilan et sa pastille, la rubrique des Réglages, les liens (les anciennes adresses mènent au Bilan) ; le code serveur reste, sa liste est dans docs/135 (docs/135) | livrée |
| 1.6.26 | Clarté : un jour de repos en une phrase qui dit quoi faire ; « Jour de repos », « En retard de N candidatures », « Proximité avec ton profil » ; le chiffre d'abord dans les tuiles du Bilan ; « Filtrer » en toutes lettres (docs/135) | livrée |
| 1.6.27 | Revue sur ordinateur : le vrai nombre de jours sans réponse, la place du bouton « Assistant », à relancer et à déclarer en deux listes, « en dessous » en gris, les Réglages sans jargon (et leur écran Figma), la pastille et la phrase d'Offres d'accord, les boutons secondaires pareils, « Semaine faite » muette quand le mois est en retard (docs/135) | livrée |
| 1.6.28 | Réglages : « Chercher l'annonce chez l'employeur à partir de » revient dans « Recherche d'emploi » (docs/135) | livrée |
| 1.6.29 | Largeur sur ordinateur : pages à 1 020 px (Offres à 1 280 px), 75 caractères par ligne au plus, boutons à la largeur de leur texte, champs à la taille du contenu, listes courtes dans la colonne des deux tiers ; règles (§3) et Figma d'abord (docs/135) | livrée |
| 1.6.30 | Suivi, Alertes et Rendez-vous dans une seule colonne des deux tiers, même largeur de haut en bas (le calendrier ouvert garde la largeur de la page) ; plus de « … » dans les lignes de liste sur ordinateur ; « à » et l'heure insécables ; le bandeau du Bilan dans Figma comme dans le code (docs/135) | livrée |
| 1.6.31 | Règles d'interface, §9 : les références classées par autorité (normes WCAG 2.2 AA et ISO 9241-110/210, recherche NN/g et Baymard, systèmes Material 3, Polaris et Apple HIG, Laws of UX en aide-mémoire) ; GOV.UK, USWDS, DSFR et le Design System de la Confédération retirés ; chaque choix d'interface dans une PR cite une référence | livrée |
| 1.6.32 | Largeurs revues à partir des références (§3) : plus de colonne des deux tiers, un seul conteneur de 1 020 px où chaque bloc prend toute la largeur (Aujourd'hui, Suivi, Alertes, Rendez-vous, Bilan) ; boutons à la largeur de leur texte à toutes les tailles, 44 px de haut sur téléphone ; « Toutes les candidatures » tient dans sa carte ; lignes de liste sans « … » ; GOV.UK et NHS retirés des citations | livrée |
| 1.6.33 | Une seule pastille de nombre (`CountBadge`, NN/g heuristique 4) : la cloche, la barre d'onglets du téléphone, les onglets et le nombre de filtres ; même taille partout, un contour de la couleur du fond (blanc en clair, fond sombre en sombre) ; orange pour la cloche, accent ailleurs ; Figma d'abord (composant Pastille utilisé par Cloche et Onglet) | livrée |
| 1.6.34 | Figma suit la mesure du code (31 em) : `measure` 496 px (texte courant), `measure-small` 434 px (petit texte), `measure-figure` 806 px sur ordinateur et 682 px sur téléphone (phrases de conclusion) ; les textes limités dans le code (phrases de conclusion, paragraphes, questions au conseiller, étapes, aides) reliés par un cadre « Mesure » sur tous les écrans, 1440 et 390, sans débordement ; pastille de l'onglet et de la cloche rebranchées sur leur propriété ; planches dans `docs/captures/1.6.34/` | livrée |
| 1.6.35 | Réglages selon le modèle de Polaris (titre et description à gauche, les contrôles dans une carte à droite, plus de filets) ; la mesure (31 em, 75 caractères) s'étend aux lignes de liste, au mois en bref et aux avis ; l'audit mesure le texte par rapport aux cartes des réglages ; Figma : Réglages, planche 1920 (docs/135) | livrée |
| 1.6.36 | L'historique des versions sans conflit : un fichier par version dans `changelog.d/`, `CHANGELOG.md` assemblé sur main après chaque fusion (`scripts/changelog.py`, action `changelog.yml`) ; la CI refuse une PR qui modifie `CHANGELOG.md` à la main ; les 7 versions restées « en cours » passent à « livrée » ; quatre branches fusionnées supprimées | livrée |
| 1.6.37 | En-tête sur ordinateur (planche Figma « Planche · En-tête ») : deux bulles au même style, le menu et le compte, de 48 px (`--control-h` + 2 × `--space-1`), `--space-2` entre les onglets, `--space-5` de chaque côté ; onglet actif en pastille accent léger, texte accent en 600 ; survol en couche neutre à 8 %, sans accent ; la ligne du bas seulement quand le contenu défile, en fondu de 250 ms (aucun si moins d'animations) ; l'en-tête garde 73 px et le logo 32 px | livrée |
| 1.6.38 | La coordination des trois sessions (Design, Pages, Dépôt) : `docs/coordination.md` (territoires, règles, tableau des tâches et des fichiers touchés) et `docs/versions.md` (réservation des numéros avant d'ouvrir une PR) | livrée |
| 1.6.39 | Règles §6 : la séparation sous l'en-tête n'apparaît que quand le contenu défile dessous, en fondu bref de 250 ms (Material Design 3, barre du haut) ; sans fondu si l'appareil demande moins d'animations (WCAG 2.2, 2.3.3 ; Apple HIG) | livrée |
| 1.6.40 | Les tableaux de coordination tenus à jour : la 1.6.38 fusionnée, la 1.6.39 réservée par la session Design (règles §6, le mouvement) et ses micro-animations dans Figma inscrites, ainsi que la 1.6.41 (boutons segmentés au style de l'en-tête) | livrée |
| 1.6.41 | Boutons segmentés selon Material 3 (§4) : un rail neutre (`--panel`) à `--control-h`, une pastille par option à la largeur de son texte (`--control-inner-h`, `--space-3`), qui passe à la ligne entière plutôt que de couper le texte ; l'option active au style de l'onglet actif de l'en-tête, le survol en couche neutre à 8 % ; appliqué à la période du Bilan et à la Note des Offres (et aux autres sélecteurs `.segmented`) ; règle §4 : pour filtrer ou changer l'affichage d'une carte, jamais pour naviguer ; Figma : Segment, Sélecteur segmenté, variable `control-inner-h` | livrée |
| 1.6.42 | Les tableaux de coordination à jour : la 1.6.40 fusionnée, la 1.6.41 de la session Design précisée (boutons segmentés selon Material 3, variable `--control-inner-h`) | livrée |
| 1.6.43 | « Jour de repos » partout : l'assistant (consigne assistant-v21), les notifications et le rythme côté serveur ; les tests prennent « aujourd'hui » à l'heure de Zurich comme l'application (plus d'échec la dernière heure d'un jour ou d'un mois sur la CI en UTC) ; la fin d'une session de connexion (90 jours) comptée en temps réel, une heure de trop après le passage à l'heure d'hiver ; la baisse des tests de 478 à 463 expliquée (la 1.6.25 retire les 16 tests d'Actualités et en ajoute 1 au Bilan) | livrée |
| 1.6.44 | Chaque session tient elle-même ses lignes dans `docs/coordination.md` et `docs/versions.md` (dans la PR de sa tâche) ; la session Pages inscrite (1.6.43, « jour de repos ») ; la 1.6.42 fusionnée | livrée |
| 1.6.46 | Revue de la plateforme, en-tête et règles : menu sans bulle (onglet actif souligné de 3 px, survol par le texte seul) ; cloche et avatar en boutons ronds sans capsule, la cloche en capsule orange clair avec le chiffre quand il y a des alertes, l'initiale seule, menus au clic avec Échap et légende au survol et au focus ; variable --accent-band ; règles réécrites pour la nouvelle structure d'Aujourd'hui et l'écran de tri (§4, interface.md 17, docs/129) ; Figma : planche Revue 1.6.46, composants Lien de navigation et En-tête | livrée |
| 1.6.47 | Revue de la plateforme (1.6.46), Offres : un seul bouton « + Ajouter » dont le menu propose « Ajouter une offre » et « Postuler spontanément » (Polaris : les actions de la page regroupées) ; la Note en ligne « Note · Toutes › » comme Statut et Tri ; une marge dans la colonne des filtres, l'anneau de focus de la recherche n'est plus rogné | livrée |
| 1.6.48 | Règle §3 : la bande d'action, une bande accent pleine largeur sous la conclusion avec une carte qui porte la seule action principale de la page, une seule par page, seulement s'il y a quelque chose à faire ; les cinq planches inscrites au tableau | livrée |
| 1.6.49 | Composant ActionBand (§3, la bande d'action) : une bande --accent-band pleine largeur sous la conclusion, une carte avec le titre, une phrase, un aperçu facultatif et la seule action principale (lien ou bouton) ; prêt pour Aujourd'hui, Offres, Suivi, Rendez-vous, Alertes et Bilan | livrée |
| 1.6.50 | Revue de la plateforme (1.6.46) : l'écran de tri des offres du jour (`/aujourdhui/tri`), une offre à la fois en pile, « Écarter » ou « Garder », sans barre d'onglets ; dans Offres, la bande d'action « Offres à examiner. » (les nouvelles depuis hier, les très proches) et son bouton « Commencer le tri » (Polaris : une action principale par page) ; quand tout est examiné, « Tout est examiné. » | livrée |
| 1.6.51 | Revue de la plateforme (1.6.46) : Aujourd'hui en une colonne (docs/interface.md n° 17) : la phrase de conclusion ; le tri du jour dans la bande d'action, la meilleure offre en aperçu et « Commencer le tri », seule action principale, puis « Tri terminé · À demain » ; « À faire aujourd'hui. », des lignes construites pareil (icône, verbe et nombre, détail, bouton), le daté d'abord ; « Mois ORP. », le mois et la semaine face à face ; « À retenir. », l'écart du Bilan en un mot et une phrase. L'état « Rien d'urgent » disparaît : « Tout est à jour. » suffit | livrée |
| 1.6.52 | Aujourd'hui, « Mois ORP. » : sans la tuile du visage, le mois prend la place (« Ce mois · 6 / 10 » plus grand, la barre sur toute la colonne) ; le Bilan garde sa tuile | livrée |
| 1.6.53 | Offres sans bande d'action : la liste est déjà la tâche, le nombre est dans l'onglet et dans la conclusion (décision de Kevin) ; « Tout est examiné. » reste ; la bande reste sur Aujourd'hui | livrée |
| 1.6.54 | Règle §3 : la bande d'action ne répète jamais le contenu de la page ; pas de bande sur Offres, où la liste est déjà la tâche ; les planches de la bande et de la Ligne d'offre mises à jour au tableau | livrée |
| 1.6.55 | Offres, barre d'outils : la recherche, « Filtrer » et « + Ajouter » sur une ligne ; « Filtrer » ouvre un panneau sous le bouton sur ordinateur, une feuille en bas de l'écran sur téléphone (avec la recherche) ; les filtres actifs en pastilles avec « Tout effacer » ; la liste sur toute la largeur, sans colonne de filtres (planche validée par Kevin) | livrée |
| 1.6.56 | Test du retour d'entretien indépendant de la date du jour : le jour du retour calculé comme celui de l'entretien (il cassait depuis le 27.10) | livrée |
| 1.6.57 | Offres, feuille « Filtres » sur téléphone selon la planche : voile à 40 %, coins du haut à 16 px | livrée |
| 1.6.58 | Sélection des onglets : l'onglet actif de l'en-tête dans une pastille teintée (survol neutre, focus de 2 px, plus de soulignement) ; sur téléphone, une pastille de 64 × 32 derrière l'icône de l'onglet actif (indicateur de Material 3) | livrée |
| 1.6.59 | Coordination : la série de modifications du 27.10 inscrite au tableau (en-tête, recherche globale, Bilan, Réglages, Alertes, règles), la barre d'outils d'Offres et la sélection des onglets transmises à Pages | livrée |
| 1.6.60 | Barre d'onglets du téléphone un peu plus haute (4 rem au lieu de 3,6) : de l'air au-dessus de la pastille de l'onglet actif | livrée |
| 1.6.61 | Repliable : une icône dans une pastille et une phrase en gris sous le titre, en option ; elles serviront aux cartes du Bilan | livrée |
| 1.6.62 | Bilan selon la planche « 3 et 4. Bilan » : la conclusion comparée à la période d'avant, la bande du site qui répond le plus, la période en pastilles (Un mois, 3 mois, Tout), quatre repliables chiffrés (Parcours, Ce qui marche, Par mois, Entretiens) et « Pour l'ORP » sur un mois ; les mois d'avant la première activité ne s'affichent plus | livrée |
| 1.6.63 | Repliable ouvert et survolé : la phrase sous le titre passe en couleur de texte, pour rester lisible sur le fond accentué (contraste 4,5:1) | livrée |
| 1.6.64 | Coordination : le numéro de version se réserve dans la PR de la tâche elle-même, plus dans une PR de réservation à part | livrée |
| 1.6.65 | Réglages : une carte par réglage (titre, phrase, contrôle à droite), « Enregistré » annoncé aux lecteurs d'écran, l'erreur sous le champ ; les composants qui serviront à toutes les rubriques | livrée |
| 1.6.66 | Réglages en cartes (planche « 5. Réglages »), première partie : Recherche d'emploi, Rythme, Notifications, IA ; un interrupteur ou un choix s'applique tout de suite, un champ chiffré quand on le quitte, une valeur impossible est refusée sous le champ (l'ancienne reste), ne plus suivre un site se fait avec « Annuler » pendant 6 s ; plus de bouton « Enregistrer » | livrée |
| 1.6.67 | Réglages en cartes, seconde partie : Compte (formule, profils d'essai, connexion, données personnelles), Agenda et extension, Administration et État du service suivent le modèle « 5. Réglages » ; plus de bouton « Enregistrer », un champ chiffré s'enregistre quand on le quitte, les états écrits en mots | livrée |
| 1.6.68 | Réglages : les formulaires, messages et confirmations posés dans une carte prennent le même filet et la même marge partout ; un contrôle large (jeton, adresse, zone de texte) peut passer sous le texte ; une longue adresse se coupe au lieu de déborder | livrée |
| 1.6.69 | Règles d'interface de la série du 27.10 : structure des sections (titres sans point, cartes construites pareil, contrôle à droite), enregistrement immédiat, confirmation qui dit ce qui est vraiment fait, sélection unique en pastille teintée, recherche globale | livrée |
| 1.6.70 | Alertes selon la planche « 6. Alertes » : la conclusion, une seule bande (code attendu, confirmation, ou site muet 3 jours après la création), une carte par recherche avec ses lieux et une ligne par site (reçue, en attente, rien reçu, « rien depuis 14 jours » en gris, « Créer » qui ouvre le pas à pas), les messages des sites et les alertes reçues en trois lignes avec « Tout voir », les lieux avec majuscule et accents | livrée |
| 1.6.71 | Réglages et Alertes : un état court (« Reçue le 22 oct. ») reste à droite de sa ligne sur téléphone au lieu de passer dessous | livrée |
| 1.6.72 | Recherche globale : un champ dans l'en-tête (la loupe sur écran étroit), les résultats dans tes offres, candidatures et entreprises, au clavier comme à la souris ; « Suivre cette recherche » crée la recherche d'alerte avec les lieux du profil et dit sur quels sites l'alerte reste à créer | livrée |
| 1.6.73 | Illustrations : une nouvelle série pour les écrans vides, les réussites et les erreurs, prête à être posée dans les pages ; la règle de leur usage | livrée |
| 1.6.74 | Une pastille d'état commune (neutre, à faire, réussi, erreur) et une seule façon d'écrire les dates, prêtes pour toutes les pages | livrée |
| 1.6.75 | Ligne d'offre : une seule ligne pour une offre ou une candidature, partout (Tri du jour, Offres, Suivi) ; toute la ligne est un vrai lien, le verdict en mot ou ScoreWord au bout, l'état d'une candidature sous le titre en orange s'il faut agir, l'action à droite ou sous le texte sur téléphone ; les lignes d'un même jour d'Offres dans une seule carte | livrée |
| 1.6.76 | Suivi : un filtre par mots (poste, entreprise) dans la liste des candidatures, dans tous les mois ; la recherche globale y mène par « Tout voir (N) » pour les candidatures et les entreprises ; la date ne se coupe plus sur téléphone | livrée |
| 1.6.77 | Le numéro de version donné à la fusion : une PR dépose `changelog.d/<sujet>.md` sans numéro, numéroté dans l'ordre de fusion sur main avec l'assemblage de `CHANGELOG.md` ; `docs/versions.md` retiré et le tableau de `docs/coordination.md` gelé dans `docs/coordination-historique.md` ; les tâches se suivent dans les PR ouvertes ; la CI refuse un numéro posé dans une PR | livrée |
| 1.6.78 | Illustrations aux écrans vides et aux réussites : tri terminé et objectif atteint, rien à préparer, Bilan trop tôt, assistant, formations, rendez-vous ORP, offre et page introuvables, IA pas encore branchée ; un écran commun « Pas de connexion » qui réessaie seul dès que le réseau revient ; les illustrations centrées ne s'affichaient plus (largeur nulle) | livrée |
| 1.6.79 | Repliables : au survol d'un repliable ouvert, la teinte couvre toute la ligne de titre, menu « ⋯ » compris | livrée |
| 1.6.80 | Le README de `changelog.d/` donne un exemple de fragment avec une ligne « État : … » et dit quand l'employer | livrée |
| 1.6.81 | Composants communs : tête de carte « Titre · nombre », « Afficher plus (N) », bouton Copier annoncé, menu « ⋯ » nommé « Plus d'actions » et sans rouge | livrée |
| 1.6.82 | Vide et chargement : rien avant 300 ms puis les blocs gris, voile du visage seulement au premier chargement, bouton occupé à largeur fixe et focus gardé, tête de carte à hauteur fixe | livrée |
| 1.6.83 | Tri : la phrase « pourquoi » tient sur une ligne de 80 caractères, coupée au mot sans « … » ; le visage du 1 remplace les illustrations de l'accueil des nouveaux comptes et du moment d'engagement ; plus d'illustration dans l'assistant de création d'alertes | livrée |
| 1.6.84 | La fiche d'une offre en cartes, comme les Réglages : l'offre et ses deux actions, Pourquoi (la note, la phrase, « Cette note ne me correspond pas »), Points forts et Manques (trois au plus, le mot clé en gras en tête), À savoir en lignes « libellé : valeur » avec l'adresse, puis Entreprise et Annonce repliées | livrée |
| 1.6.85 | Téléphone : la cloche et le compte s'ouvrent en pleine largeur sous l'en-tête, zones tactiles de 44 px pour les liens et boutons texte, la cloche date ses alertes selon la règle des dates | livrée |
| 1.6.86 | Téléphone (audit en 320, 360 et 390 px) : la fiche d'une offre s'ouvre sous l'en-tête et laisse la cloche à portée ; l'accueil des nouveaux comptes tient en 320 px ; onglet « Contact » du Profil ; toute la ligne d'un choix des Réglages se touche ; les boutons du tri restent visibles ; « Tri du jour » et « À faire aujourd'hui » sans point final ; liens de « Tes données » à la bonne hauteur | livrée |
| 1.6.87 | Un audit téléphone en CI : en 320, 360 et 390 px, sur chaque page de la démo et avec le panneau de la cloche ouvert, il échoue si un élément sort de l'écran ou si une cible tactile fait moins de 24 × 24 px (WCAG 2.5.8), zone d'un ::before ou ::after positionné comprise (`frontend/scripts/telephone.py`, `make audit-telephone`, workflow « Audit téléphone » sur la démo Docker) | livrée |
| 1.6.88 | Réglages : les choix « Un message par jour » et « Dès qu'elles arrivent » ont un rond de 24 px (cible tactile minimale) | livrée |
| 1.6.89 | Le contrôle « Historique » d'une PR compare au main du moment (premier parent du commit de fusion de test), plus à l'ancien main de l'événement : une PR remise à jour sur main ne se voit plus attribuer les fichiers numérotés qu'apporte main | livrée |
| 1.6.90 | Pastille d'état et dates dans les pages : StatusPill aux états en bout de ligne (sites des alertes, analyse du journal, statut d'une offre, sauvegardes, formations) et en étiquette sans point (Spontanée, ORP, type de formation) ; toutes les dates passent par dates.ts, plus jamais « il y a 3 h » | livrée |
| 1.6.91 | Réglages : l'ordre des attributs des lignes radio suit la règle du lint (aucun changement visible) | livrée |
| 1.6.92 | Formulaires : champ commun (libellé, « facultatif », aide, erreur sous le champ avec icône), largeur de 10 caractères pour une date, cases à cocher sur 44 px | livrée |
| 1.6.93 | Composants communs dans les pages : bouton Copier unique, « Afficher plus » en bas des cartes, têtes de carte « Titre · nombre », menu « Plus d'actions » avec icônes et sans rouge (confirmation sur place ou « Annuler » 6 s), boutons qui gardent le focus pendant l'action, blocs de chargement des Réglages et du Profil, écrans vides alignés (« Aucun … pour l'instant. », une ligne et « Effacer les filtres » quand les filtres ne trouvent rien) | livrée |
| 1.6.94 | Composants communs de la structure téléphone : liste groupée, feuille du bas, action fixée en bas, contrôle segmenté pleine largeur | livrée |
| 1.6.95 | Règles : structure téléphone inspirée de l'application CFF (listes groupées, feuilles du bas, action fixée en bas, contrôle segmenté, recherche) ; Réglages en liste sur téléphone, liste et détail sur ordinateur | livrée |
| 1.6.96 | Cloche : le texte d'une alerte passe à la ligne au lieu d'être coupé par « … » | livrée |
| 1.6.97 | Téléphone : les titres d'offres, les jours du calendrier du Suivi et les cartes de l'accueil passent à la ligne au lieu d'être coupés en 320 px | livrée |
| 1.6.98 | L'audit téléphone ne compte plus une étiquette (label[for] ou qui entoure son champ) comme cible quand son champ fait lui-même au moins 24 × 24 px (WCAG 2.5.8, exception « équivalent ») ; une étiquette dont le champ est caché ou trop petit reste mesurée | livrée |
| 1.6.99 | Formulaires : un champ date natif garde la place de son icône, l'année n'est plus coupée | livrée |
| 1.6.100 | Formulaires selon la planche « Formulaires » : un libellé au-dessus de chaque champ, « (facultatif) » en gris, la largeur qui dit la réponse attendue, l'erreur sous le champ avec ce qu'il faut faire, le curseur sur le premier champ à corriger, un seul bouton principal nommé par l'action ; blocs de chargement des Critères et des Coordonnées | livrée |
| 1.6.101 | L'audit téléphone vérifie aussi les libellés : un segment, un onglet ou un bouton dont le texte dépasse sa boîte, est coupé par « … » ou, pour un segment et un onglet, passe sur deux lignes, fait échouer la CI ; le message nomme le libellé et sa largeur | livrée |
| 1.6.102 | Préparer une candidature : la colonne Versions ne déborde plus (nom court de six mots, consigne entière au survol et au-dessus de la lettre) ; « Rédiger la nouvelle version » et une consigne avec son libellé ; lettre alignée à gauche, jamais justifiée (page, PDF et Word) ; plus jamais de tiret cadratin dans une lettre | livrée |
| 1.6.103 | Champs : fond distinct, bordure à 3:1 au moins, focus visible, 48 px et rayon des cartes partout ; cases et radios dessinées, interrupteur seulement pour un réglage isolé ; consentements jamais cochés d'avance | livrée |
| 1.6.104 | Info-bulle : au focus clavier, fermée par Échap, la souris peut passer dessus sans qu'elle disparaisse (WCAG 1.4.13) | livrée |
| 1.6.105 | Barres de défilement aux couleurs de la plateforme sur ordinateur, fondu au bord des onglets qui défilent ; rien ne change sur téléphone ni en contraste élevé | livrée |
| 1.6.106 | Champs : un champ posé dans une rangée de boutons prend la hauteur des contrôles, la rangée reste alignée ; contrôle segmenté pleine largeur selon la planche | livrée |
| 1.6.107 | Liste groupée : l'entrée affichée à côté (liste et détail) porte la pastille de sélection et aria-current | livrée |
| 1.6.108 | Budget de poids : le total du JavaScript passe de 270 à 285 Ko compressés pour la structure téléphone, premier écran toujours à 120 Ko | livrée |
| 1.6.109 | Liste groupée : sur l'entrée affichée, la phrase grise passe en couleur du texte (contraste 4,5:1) | livrée |
| 1.6.110 | Listes de filtre compactes à la hauteur des boutons ; le chevron d'une liste ne recouvre plus jamais son texte | livrée |
| 1.6.111 | Profil sur téléphone (sous 600 px) : un contrôle segmenté pleine largeur (Critères, Parcours, Coordonnées), les critères en liste groupée qui ouvre le formulaire sur le critère touché, et l'effet des critères en deux lignes | livrée |
| 1.6.112 | Réglages selon la planche « Structure téléphone » : une liste groupée (La recherche, Être averti, Compte et aide) ; sur téléphone, la liste seule puis une sous-page par rubrique avec « ← Réglages », et « Recevoir sur mon téléphone » à un toucher depuis la liste ; sur ordinateur, la liste à gauche et la rubrique à droite | livrée |
| 1.6.113 | CI : l'audit des contrôles en 1440, 320, 360 et 390 px, rangées de même hauteur à 1 px près et texte des listes jamais sous le chevron | livrée |
| 1.6.114 | Préparer : la consigne modifie enfin la formule d'appel, l'objet et la formule de politesse (« Dear Hiring Committee ») ; une demande hors de portée (coordonnées, date) ou sans effet le dit en une ligne et ne crée pas de version ; la version affichée est marquée dans la liste | livrée |
| 1.6.115 | Cloche : sur téléphone, une feuille plein écran avec les alertes nouvelles et déjà lues en listes groupées | livrée |
| 1.6.116 | Réglages : le groupe « Recherche d'emploi » et sa ligne « Objectif ORP et sites » ; dans « Compte et aide », « Aide » ouvre l'Assistant (quand l'IA est configurée) et « Écrire à l'exploitant » reprend son contact | livrée |
| 1.6.117 | Cloche : « Notifications » au lieu d'« Alertes » (titre et nom accessible), « Alertes » étant l'onglet des sources d'offres | livrée |
| 1.6.118 | Préparer : chaque lettre est relue avant de s'afficher, sur sept critères (accroche, pertinence, précision, longueur, conclusion, aucune invention, règles) ; au plus une correction automatique ; un fait absent du profil est toujours retiré ; « Relue : 6/7 » sous la lettre et le détail avec ses pastilles | livrée |
| 1.6.119 | Réglages : la liste et le titre de chaque rubrique ont les mêmes icônes (Compte et Administration remis à l'endroit) ; « Recevoir sur mon téléphone » a son icône | livrée |
| 1.6.120 | Offres sur téléphone (sous 600 px) : la recherche sur toute la largeur, les jours avec leur nombre en pastille, et une feuille « Filtres » (statut, note, télétravail, taux, sites, cantons) avec « Réinitialiser » et « Afficher N offres » | livrée |
| 1.6.121 | Champs : les radios sont de nouveau rondes (la règle commune des cases l'emportait) | livrée |
| 1.6.122 | Tri : la phrase « pourquoi » suit la note ; pour une note basse, la cause principale d'abord (« Zurich, hors de tes lieux. Kubernetes et CI/CD collent. »), pour une bonne note ce qui colle d'abord ; elle ne répète jamais le mot de la note et tient en 80 caractères | livrée |
| 1.6.123 | Liens vers un autre site : l'icône « ouvrir ailleurs » (ou « télécharger » pour un fichier) et « (nouvel onglet) » pour les lecteurs d'écran, partout ; un test le vérifie | livrée |
| 1.6.124 | Filtre par lieu corrigé : variantes de langue (Bern, Berne, Zürich, Zuerich, Genf, Bienne…), abréviations et noms de canton, taux, pays et codes postaux retirés du lieu de l'annonce ; un chef-lieu vaut son canton entier ; enregistrer ses critères réévalue tout de suite les offres écartées et dit combien reviennent | livrée |
| 1.6.125 | La vraie plateforme en ligne : images construites par GitHub, `make deploy` depuis le Mac, démo sur le même serveur (docs/136) | préparée, pas encore installée sur le serveur |
