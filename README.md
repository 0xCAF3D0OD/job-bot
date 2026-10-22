# jobA1

> **Less searching. More living.** (anciennement job-bot : le dépôt, le paquet `jobbot`, la commande `jobbot` et les variables `JOBBOT_*` gardent leur nom technique.)

Assistant de recherche d'emploi : il collecte les offres reçues par alerte e-mail (jobup et Indeed, les autres sites lus par l'IA), écarte celles qui ne respectent pas tes prérequis, note les autres par rapport à ton profil, prépare lettre et CV, et tient le journal des candidatures exportable pour l'ORP. Tu valides chaque envoi.

- Cadrage : [docs/01-cadrage.md](docs/01-cadrage.md)
- Version en cours : [docs/134-suivi-colonne.md](docs/134-suivi-colonne.md) (1.5.1)
- Règles de sécurité : [docs/securite.md](docs/securite.md) ; signaler une faille : [SECURITY.md](SECURITY.md)
- Règles de l'interface (illustrations, mouvement, clic) : [docs/interface.md](docs/interface.md)
- Contrat d'exploitation, pour l'infrastructure : [docs/exploitation.md](docs/exploitation.md)

## Versions

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
| 0.82.4 | La recherche publique de jobup coupée : ses conditions d'utilisation (déc. 2025, §7) interdisent les robots ; réglage `JOBBOT_PUBLIC_SEARCH_ENABLED`, faux par défaut | en cours |
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
| 1.5.1 | Le Suivi : la colonne de droite reprend la hauteur du calendrier et défile dedans (retour du 7 octobre rétabli) ; l'état des preuves en bandeau daté, une phrase et une action (docs/134) | en cours |

## Lancer en local

Prérequis (macOS) :

```bash
brew install uv postgresql@17
```

```bash
brew services start postgresql@17
```

Puis, à la racine du dépôt :

```bash
make setup
```

```bash
make migrate
```

```bash
make dev
```

L'interface est sur http://localhost:5173 (page Aujourd'hui), l'API sur http://127.0.0.1:8000 (documentation sur `/api/docs`). `Ctrl-C` arrête tout.

| Commande | Effet |
|---|---|
| `make setup` | dépendances backend et frontend, bases `jobbot` et `jobbot_test`, copie de `.env.example` en `.env` |
| `make migrate` | applique les migrations |
| `make update` | met la plateforme à jour : maintenance annoncée, `git pull`, dépendances, migrations, maintenance levée ; il reste à redémarrer `make dev` (docs/79) |
| `make check` | vérifie configuration et base |
| `make dev` | API + worker + frontend |
| `make demo` | la démo, avec des données fictives du jour, sur sa propre base (`jobbot_demo`) et ses propres ports (http://localhost:5200), à côté de `make dev` ; ouvre le navigateur ; Ctrl-C l'arrête |
| `make test` | tests backend (sur `jobbot_test`) et frontend |
| `make lint` | ruff, mypy, eslint |
| `make openapi` | régénère le contrat OpenAPI et les types TypeScript du frontend |
| `make check-openapi` | échoue si les types du frontend ne correspondent plus au backend |

## Réglages d'installation

L'interface renvoie ici pour ce qui se règle sur l'ordinateur qui fait tourner la plateforme, dans le fichier `.env` à la racine (créé par `make setup` à partir de `.env.example`), puis `make dev` relancé. Ne mets jamais ces valeurs dans le dépôt.

| Pour | Réglage |
|---|---|
| Créer le compte de connexion, ou changer son mot de passe | `cd backend && uv run jobbot set-password` (saisie masquée ; ferme les sessions ouvertes) |
| Lire les e-mails d'alerte | `JOBBOT_IMAP_USER`, `JOBBOT_IMAP_PASSWORD` (mot de passe d'application Gmail), `JOBBOT_IMAP_FOLDER` |
| Noter les offres et rédiger avec l'IA | `JOBBOT_ANTHROPIC_API_KEY` |
| Notifications sur le téléphone (application ntfy) | `JOBBOT_NTFY_TOPIC` : un sujet difficile à deviner, auquel tu t'abonnes dans l'application |
| Essai local sans connexion | `JOBBOT_AUTH_ENABLED=false` |

La liste complète est dans [docs/exploitation.md](docs/exploitation.md) (section Configuration).

## Organisation

```
backend/    Python 3.13 (uv) : FastAPI, SQLAlchemy, Alembic, procrastinate
frontend/   Vue 3 + Vite + TypeScript, types générés depuis l'OpenAPI du backend
docs/       cadrage, documents de version, règles de l'interface, contrat d'exploitation
data/       fichiers personnels, ignoré par git
```

L'infrastructure (conteneurs, CI, Kubernetes, Terraform, Ansible, supervision) n'est pas dans ce dépôt pour l'instant : elle se construit à partir de [docs/exploitation.md](docs/exploitation.md).

## Données personnelles

Le dépôt est public. CV, profil, offres, lettres et exports ORP restent dans `data/` et dans la base, jamais dans git ; un test le vérifie (`backend/tests/test_no_personal_data.py`).

## Licence

GPL-3.0, voir [LICENSE](LICENSE).

Les illustrations de `frontend/src/assets/illustrations/` viennent d'[unDraw](https://undraw.co) (Katerina Limpitsouni), sous la licence unDraw ; elles sont animées et préparées par `frontend/scripts/illustrations.mjs` (docs/58), sans changer leurs formes.
