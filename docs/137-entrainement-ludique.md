# 137 — S'entraîner en jouant : préparer un entretien par petites leçons

> Statut : **proposé** le 2026-10-30, rien de codé.
> Origine : ta demande du 30 octobre : une application pour le téléphone, adaptée à l'ordinateur, où une personne de jobA1 s'entraîne à l'entretien de façon ludique, sur le modèle de Duolingo : des jeux pour connaître l'entreprise, puis un entretien blanc avec des questions liées à l'offre. Brief joint : `prompt-app-entretien.md`.
> Se construit sur docs/75 (l'entretien blanc par écrit), docs/23 (le retour d'entretien et « Mes enseignements »), docs/45 (la fiche de l'offre et l'entreprise), docs/12 (le registre du commerce), docs/99 (la mascotte), docs/125 (le freemium), docs/33 (le téléphone).

## 1. En clair

- Pour **chaque entretien décroché**, jobA1 prépare un **parcours de petites leçons** de 3 à 5 minutes : d'abord l'entreprise, puis le poste, puis toi, et à la fin l'**entretien blanc** qui existe déjà (docs/75).
- **Le jour de l'entretien est la ligne d'arrivée.** Duolingo veut qu'on revienne tous les jours, pour toujours. Ici, le but est d'arriver prêt le jour J : « Entretien chez Jura Data dans 4 jours · 4 séances ».
- **Même compte, mêmes données, même IA que jobA1.** Pas une seconde plateforme à côté.

## 2. Ce que jobA1 sait déjà, et qu'une application à part n'aurait pas

| Ce que jobA1 a | Ce que ça donne au jeu |
|---|---|
| L'offre, ses exigences, la note de l'IA et **les manques** | les questions sur le poste, et celles où un recruteur va creuser |
| Ton profil (blocs) | des exercices construits avec **tes** expériences, pas des exemples génériques |
| La date et le type d'entretien (agenda, docs/40) | le compte à rebours et le choix RH, manager ou technique |
| **Les questions difficiles** de tes vrais entretiens (« Mes enseignements ») | elles reviennent en révision |
| L'entreprise : l'annonce chez l'employeur, son site, le registre du commerce (docs/12 : forme, siège, but social) | les jeux sur l'entreprise, avec des faits sourcés |
| L'entretien blanc avec l'IA (docs/75), son retour par repères | le « boss » de fin de parcours, déjà construit |

## 3. Le parcours d'une candidature

Quatre étapes et l'entretien blanc, numérotés avec la pastille des étapes de Préparer (en cours, faite, à venir) :

| Étape | La question | Les jeux |
|---|---|---|
| **1. L'entreprise** | « Est-ce que je sais chez qui je vais ? » | Vrai ou faux sur l'entreprise ; associer l'entreprise à son secteur, ses produits, ses clients ; trouver l'intrus |
| **2. Le poste** | « Est-ce que je comprends ce qu'ils cherchent ? » | relier chaque exigence de l'annonce à une de tes expériences ; ce que veut dire un mot de l'annonce (« autonome », « polyvalent ») ; QCM « la meilleure réponse » |
| **3. Toi** | « Est-ce que je sais me présenter ? » | remettre une réponse STAR dans l'ordre (Situation, Tâche, Action, Résultat), avec une de tes expériences ; compléter ta présentation avec des mots proposés ; repérer la phrase faible dans la réponse d'un candidat |
| **4. Les questions qui piquent** | « Est-ce que je suis prêt pour les moments délicats ? » | tes manques pour cette offre, les prétentions salariales, la disponibilité, une question illégale et comment y répondre ; vrai ou faux sur les bonnes pratiques |
| **Final** | « Je le passe » | l'entretien blanc de docs/75 : cinq questions, une relance au plus, le retour par repères |

- **Le rythme suit la date** : entretien dans 5 jours, une séance par jour ; entretien demain, une version express (étapes 1, 2, puis l'entretien blanc).
- **Sans entretien prévu**, un parcours **« Les classiques »** par type d'entretien et par métier (docs/122) : une banque de questions écrite à l'avance, sans IA, donc gratuite et utilisable hors connexion. Les questions ratées reviennent en révision (répétition espacée).

### Une leçon

Comme dans le brief : plein écran, barre de progression en haut, une consigne courte, la mascotte, le bouton « Vérifier » en bas sur toute la largeur, puis la feuille de retour qui monte du bas (« Bien joué ! » ou la bonne réponse, avec une explication d'une ligne). Couleur, icône **et** texte, jamais la couleur seule. Les erreurs reviennent en fin de leçon. Fin de leçon : ce qui est acquis, le temps passé, la séance suivante.

## 4. Ce que je garde de Duolingo, et ce que j'adoucis

| Mécanique | Proposition | Pourquoi |
|---|---|---|
| Leçons courtes, retour immédiat, progression visible, combo | **garder** | c'est ce qui rend l'exercice agréable |
| XP et objectif du jour | **garder, discret** | |
| Série de jours (flamme) qu'on perd | **remplacer** par le compte à rebours de l'entretien, et une série douce qui ne se perd pas (« 3 jours d'entraînement cette semaine ») | beaucoup de personnes sont au chômage et déjà sous pression ; docs/125 : « pas de compte à rebours ni de culpabilité » |
| Vies (cœurs) qui bloquent après 5 erreurs | **retirer** : une erreur revient en fin de leçon, rien ne bloque | chez Duolingo, les vies servent à vendre l'abonnement ; bloquer quelqu'un qui s'entraîne la veille d'un entretien irait contre le but |
| Ligues, classement de 30 personnes | **ne pas faire** | comparer des personnes en recherche d'emploi entre elles ; et il faut des centaines de comptes actifs pour remplir une ligue |
| Monnaie, coffres, gel de série | **ne pas faire au début** | ils n'ont de sens qu'avec les vies et la série |
| Mascotte qui réagit | **reprendre celle de l'assistant** (docs/99) : « à l'écoute » pendant la question, « réfléchit » pendant la vérification, « a trouvé » sur une bonne réponse ; un quatrième visage « encourage » pour une erreur, à dessiner | elle existe déjà et elle est déjà liée à l'IA ; le brief demandait d'en créer une |

## 5. L'entreprise : ne jamais inventer

C'est le point le plus délicat : une IA qui invente un fait sur l'entreprise, répété en entretien, met la personne en difficulté.

- **Les faits viennent seulement de sources lues** : l'annonce, la page de l'annonce chez l'employeur, la page « À propos » de son site (lue une fois), le registre du commerce.
- **Chaque question garde sa source**, montrée dans le retour : « D'après leur site, page À propos ».
- **Si les sources sont maigres, l'étape est courte** (trois questions), plutôt que remplie d'inventions. L'IA a pour consigne d'écrire « je ne sais pas » plutôt que de deviner.

## 6. Le coût et le freemium

- Le parcours d'une candidature est **généré une fois** par l'IA, puis gardé : un appel du même ordre qu'une lettre (~0,10 $, à mesurer), plus l'entretien blanc (~0,30 $, docs/125).
- Proposition : **un parcours de candidature compte comme un entraînement** dans les formules (Essentiel : 1 par mois, Plus : 8). **« Les classiques » restent illimités**, puisqu'ils n'appellent pas l'IA.

## 7. Le téléphone d'abord, l'ordinateur aussi : application native, ou dans jobA1 ?

Il y a une contradiction à trancher : le brief dit **« 100 % mobile, sans version web »** ; ton message dit **« exclusive au téléphone, mais adaptée pour ordinateur »**.

| | **A. Dans jobA1** (l'interface actuelle, installable sur l'écran d'accueil) | **B. Application Expo à part, avec son serveur AWS** (le brief) | **C. Application Expo branchée sur jobA1** |
|---|---|---|---|
| Compte | le même | un nouveau (Apple, Google, lien par e-mail) | le même |
| Données | le serveur Infomaniak, en Suisse | une deuxième base, chez AWS, à synchroniser avec jobA1 | en Suisse |
| Sur ordinateur | oui | non | en partie (Expo pour le web) |
| App Store et Google Play | non : l'ajout à l'écran d'accueil existe déjà (docs/33) | oui : 99 $ par an chez Apple, 25 $ chez Google, et la revue de chaque version | oui, idem |
| Paiement | Payrexx, déjà en place | RevenueCat, avec la commission d'Apple et Google (15 à 30 %) | idem B |
| Hors connexion | limité | oui | oui |
| Vibrations | Android oui, iPhone non | oui | oui |
| Rappels | ntfy, déjà en place, et les notifications web (iPhone : une fois installée) | oui | oui |
| Travail | le plus court | un second produit entier | moyen |

**Ma recommandation : A d'abord.** On mesure sur les vrais comptes si les gens jouent vraiment. Si oui, et si la présence dans les stores compte, on passe à **C** : l'application native se branche sur l'API de jobA1, sans tout refaire. **B est à éviter** : il dédouble les comptes, les données, le paiement et l'IA pour les mêmes personnes, et sort les données de l'infrastructure suisse que jobA1 met en avant.

**A respecte aussi les règles de l'interface** (docs/regles-ui-ergonomie.md) : l'entraînement sert le niveau « 2. Progresser » (§1), et il s'ouvre en plein écran comme un 2e niveau, depuis la candidature et depuis Aujourd'hui (« Entretien chez Jura Data dans 3 jours · Séance du jour »), sans ajouter de quatrième onglet (§2).

## 8. Le style

- **Le brief** propose une palette terreuse (crème, brun), la police Urbanist et le kit « freud » comme inspiration. **jobA1** a son violet, son accent bleu, sa mascotte bleue et son diamant.
- **Ma recommandation** : le style de jobA1, sans les couleurs d'étape du brief. La pastille numérotée de Préparer suffit à distinguer les étapes. Une palette à part ferait de l'entraînement un autre produit.
- **Décision du 30 octobre : l'entraînement suit la référence du brief**, pas le style de jobA1. La direction est proposée dans la page Figma « Planche · Entraînement · Direction visuelle (proposition) » : palette crème et bruns, sauge, orange et moutarde, avec leur version sombre ; Urbanist en deux graisses ; boutons en pilule brune ; parcours en chemin de nœuds ; mascotte provisoire, à faire dessiner. Les couleurs vives de la référence (1,6 à 2,6:1) ne servent qu'aux formes ; le texte coloré utilise une version foncée (5:1 et plus). Le style ne couvre que les écrans de l'entraînement, en plein écran ; la ligne d'entrée sur Aujourd'hui reste en style jobA1. C'est une exception aux règles de l'interface (docs/regles-ui-ergonomie.md), à écrire au §4 une fois la direction validée.
- **Le parcours est une ligne jusqu'au jour J** (décision du 30 octobre, à la place du chemin de nœuds, jugé trop proche de Duolingo). C'est un trajet : un arrêt par étape avec son jour, l'entretien comme terminus avec son heure. La mascotte attend à l'arrêt en cours.
- **Une seule animation**, au retour d'une séance terminée : l'arrêt se remplit (250 ms, `--t-state`, `--ease-out`), puis le trait avance et la mascotte glisse jusqu'à l'arrêt suivant (500 ms, `--t-enter`, `--ease-out`). Rien ne bouge en boucle, ni à la simple ouverture de l'écran. Si l'appareil demande moins d'animations, l'état final s'affiche par un fondu de 250 ms au plus. Le jour J, la mascotte rejoint le terminus de la même façon, une seule fois. Planche Figma « Mouvement · fin de séance ».
- **Les écrans sont convertis** (30 octobre) dans la page Figma « Planche · Entraînement · Écrans (style freud) » : 16 écrans liés aux variables, avec les modes « Entraînement clair » et « Entraînement sombre » (Couleurs) et « Entraînement » (Rayons, Typographie), créés par la session Design. Téléphone : la ligne, une question, le retour juste, le retour à revoir, la fin de séance. Ordinateur : la ligne, une question, le retour juste. Les écrans de l'entraînement s'ouvrent en plein écran, sans l'en-tête ni la barre d'onglets de jobA1. Ajoutés ensuite, sur téléphone, en clair et en sombre :
  - **remettre dans l'ordre** une réponse STAR construite avec le profil : poignée de glisser, et les boutons « Monter » et « Descendre » comme alternative, avec le déplacement annoncé aux lecteurs d'écran ;
  - **repérer l'erreur** : chaque phrase de la réponse d'un candidat est un bouton ;
  - **compléter** sa présentation avec des mots en pastilles ;
  - **vrai ou faux**, avec deux boutons de même largeur et sans chrono ;
  - **l'entretien blanc** en conversation : une question et sa relance, une zone de réponse avec la dictée du clavier, « Envoyer », « Passer la question » et « Terminer » ; pas de minuteur.

  Ces cinq écrans existent aussi sur ordinateur, dans la même colonne centrée que les autres, avec une aide clavier en bas de chacun : Alt + flèches pour déplacer une carte, Tab et Espace pour choisir une phrase ou un mot, ← pour faux et → pour vrai (« Faux » à gauche, « Vrai » à droite, comme « Écarter » et « Garder » dans le tri, avec les mêmes garde-fous : rien dans un champ ni quand une fenêtre est ouverte ; pas de raccourci d'une seule lettre, WCAG 2.1.4), Entrée pour envoyer (Maj + Entrée pour aller à la ligne).

- **La mascotte est un billet de train** (décision du 30 octobre), poinçonné à chaque arrêt terminé, avec 4 expressions : contente, réfléchit, on s'accroche, ravie. Il remplace le robot provisoire dans tous les écrans. À la fin d'une séance, le poinçon fait partie de l'animation. Brief pour l'illustration : docs/138. Le dessin final reste à commander. Le kit « freud » est payant : on s'en inspire, on ne reprend rien.
- **Figma d'abord** : aucun écran de ce parcours n'existe dans Figma. Selon les règles du projet, il faut les dessiner et les valider avant de coder. Je peux préparer ces maquettes dans le fichier Figma de jobA1.

## 9. Ce qui change par rapport au brief, si tu valides

- **Tous les métiers**, pas seulement les profils tech (docs/122).
- **Pas d'AWS, de Terraform ni de DynamoDB** : le serveur de jobA1 (FastAPI, PostgreSQL).
- **Pas de nouvelle connexion** (Apple, Google) ni de **RevenueCat** : le compte et Payrexx de jobA1.
- **Pas de vies, de ligues ni de monnaie** (§4).
- **La mascotte existante** (§4).
- **Pas d'enregistrement de la voix** pour l'instant : docs/75 §11 l'a écarté, parce qu'une transcription par un service externe enverrait la voix ailleurs. La dictée du téléphone suffit, comme dans l'entretien blanc.

## 10. Livraison proposée

1. **Les maquettes Figma** : le parcours d'une candidature, une leçon (question, retour juste, retour faux), la fin de leçon, l'entrée depuis Aujourd'hui ; téléphone et ordinateur. Préparées le 30 octobre, page « Planche · Entraînement (proposition) » du fichier jobA1, et validées le même jour. L'entrée depuis Aujourd'hui est une ligne de plus dans « À faire aujourd'hui » (« Faire 1 séance d'entraînement », bouton « S'entraîner »), qui n'apparaît que s'il reste une séance pour le jour même.
2. **1.7.0** : la leçon et les cinq types de jeux, avec « Les classiques » (une banque de 60 questions en français, écrite à l'avance, sans IA).
3. **1.8.0** : le parcours d'une candidature préparé par l'IA (entreprise, poste, toi, questions qui piquent), avec l'entretien blanc en final.
4. **1.9.0** : le rythme jusqu'à la date de l'entretien, les rappels par ntfy, la révision des questions ratées.

## Points à valider

1. **Dans jobA1 d'abord (A)**, une application native branchée sur jobA1 plus tard si besoin (C), pas de second serveur (B) (§7).
2. **Le parcours en quatre étapes** et l'entretien blanc en final, rythmé par la date de l'entretien (§3).
3. **Ce qu'on garde et ce qu'on adoucit** de Duolingo : pas de vies, pas de ligues, pas de série qu'on perd (§4).
4. **Des faits sourcés** sur l'entreprise, jamais inventés (§5).
5. **Un parcours compte comme un entraînement** ; « Les classiques » illimités (§6).
6. **Le style de jobA1**, sans couleurs d'étape, et la mascotte existante (§4, §8).
7. **Les maquettes Figma avant tout code**, puis trois versions (§10).
