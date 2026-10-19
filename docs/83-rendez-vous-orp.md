# 83 — Le rendez-vous ORP (version 0.67.0)

> Statut : **validé** le 2026-10-19.
> Origine : ta demande du 2026-10-19 de te démarquer d'ApplyCH et de SwissJobs.app. Les deux poussent vers le volume (plus d'annonces, plus de CV, jusqu'à la candidature automatique), et leur lien avec l'ORP s'arrête au formulaire des preuves. jobA1 va plus loin : il aide à **préparer l'entretien avec ton conseiller**, puis à **garder ce qui a été convenu**.
> Ce qui existe déjà : le « Résumé pour l'ORP » d'un mois, sous le Bilan (docs/42 §3). C'est quelques lignes à copier, sans plus. Il reste la base de cette version.

## 1. En clair

Une nouvelle page, **« Rendez-vous ORP »**, dans Candidatures, à côté du Bilan. Elle sert **avant** et **après** chaque entretien avec ton conseiller.

**Avant**, la page prépare tout en une feuille, que tu peux imprimer ou envoyer :
1. **Ton mois en bref** : le résumé d'aujourd'hui (candidatures et objectif, réponses, entretiens, sources, formations).
2. **Ce qui bloque**, tiré de tes données : par exemple « 31 candidatures en 3 mois, 2 réponses : les candidatures par formulaire ne répondent presque jamais » ou « aucune réponse sur les postes seniors ».
3. **Ce qui revient dans les offres et te manque** : les compétences demandées le plus souvent par les offres bien notées, et absentes de ton profil (par exemple « Terraform : demandé dans 14 offres sur 22 »). À côté, une formation de la page Formations qui le couvre, s'il y en a une.
4. **Tes questions au conseiller**, proposées d'après ta situation, à cocher ou à écrire :
   - le financement d'une formation (avec la demande déjà prête, docs/37) ;
   - un stage ou une mesure, si les réponses manquent depuis des mois ;
   - un gain intermédiaire, si tu en as un ;
   - la suite d'une assignation.
5. **Tes obligations et leurs dates** :
   - les preuves du mois, à remettre avant le 5 ;
   - les assignations de l'ORP en cours, et ta réponse ;
   - le prochain rendez-vous.

**Après**, tu notes en une minute ce qui a été convenu :
- le nouvel objectif mensuel, s'il change ;
- les mesures accordées (formation, stage, cours) ;
- les assignations reçues ;
- la date du prochain rendez-vous ;
- une note libre.

jobA1 en tient compte tout seul :
- l'objectif du mois est mis à jour ;
- le rendez-vous suivant entre dans l'agenda, avec un rappel la veille ;
- une formation accordée passe en « financement accepté ».

Le **carnet ORP** garde tous les rendez-vous, l'un après l'autre. C'est utile si un conseiller change, ou en cas de désaccord sur ce qui avait été dit.

## 2. Pourquoi ça démarque jobA1

- **Personne ne le fait** : ApplyCH et SwissJobs.app remplissent le formulaire, puis s'arrêtent là.
- **C'est l'entretien qui compte** : le conseiller décide des mesures, des formations, et apprécie tes efforts. Arriver avec une feuille claire change la discussion.
- **« Ce qui te manque »** transforme tes offres en arguments : une demande de formation appuyée par 14 offres sur 22 se défend mieux qu'une envie.
- **Fidèle à « Less searching. More living. »** : moins de stress avant le rendez-vous, rien à reconstituer de tête.

## 3. Ce qui est fait avec ou sans IA

- **Sans IA** (gratuit) : le résumé, les dates, les obligations, ce qui bloque, ce qui manque, les questions proposées. Ce sont des faits tirés de tes données, avec des règles simples et écrites. Par exemple « ce qui bloque » compare les réponses par canal, comme le Bilan.
- **Avec l'IA, si tu le demandes** (« Rédiger la feuille », moins de 0,05 $) : un texte suivi, poli, à envoyer au conseiller avant l'entretien. Il est construit seulement à partir des faits de la page, sans ton nom ni tes coordonnées, comme les lettres.

## 4. Où ça vit

- **Candidatures › Rendez-vous ORP** : une colonne « avant », puis le carnet. Sur téléphone, une colonne, et la feuille se lit d'un trait.
- **Aujourd'hui** : la veille d'un rendez-vous, une carte « Rendez-vous ORP demain : ta feuille est prête ».
- **L'agenda** (abonnement d'agenda, docs/40) : les rendez-vous ORP y apparaissent comme les entretiens.
- **La feuille** : « Imprimer » ou « Télécharger en PDF », sur une page A4. Elle porte ton nom seulement si tu le veux, puisque c'est toi qui la remets.

## 5. Ce qu'on ne fait pas

- **Rien n'est envoyé à l'ORP par jobA1** : tu imprimes, tu envoies ou tu lis toi-même.
- **Pas de conseil juridique** sur l'assurance chômage (droits, sanctions, gain intermédiaire) : jobA1 propose de **poser la question**, et renvoie vers ton conseiller et les pages officielles.
- **Pas de prédiction** (« tes chances ») ni de comparaison avec d'autres personnes.

## 6. Base de données

Une table **`orp_meetings`**, par compte : date, lieu ou visio, conseiller (facultatif), objectif convenu, mesures, assignations, note, et le lien vers la feuille préparée. Elle est rangée dans la famille **personnelle** (`db/policies.py`), avec sa règle `account_isolation` : le test des familles le vérifie (docs/78).

## 7. Livraison en deux PR

| Version | Contenu |
|---|---|
| **0.67.0** | La page « avant » : le résumé, ce qui bloque, ce qui manque, les questions, les obligations ; la feuille imprimable et en PDF ; la carte de la veille dans Aujourd'hui |
| **0.67.2** | Le « après » : ce qui a été convenu, le carnet, l'agenda et le rappel, l'objectif et les formations mis à jour ; la feuille rédigée par l'IA, sur demande |

Vérifié à chaque fois :
- tests serveur et interface ;
- une démo avec deux mois fictifs de rendez-vous ;
- captures sur ordinateur et téléphone, en clair et en sombre.

La démo en ligne en profite : un rendez-vous fictif rempli, pour montrer la page.

## Points à valider

1. **Une page « Rendez-vous ORP »** dans Candidatures, avant et après l'entretien (§1, §4).
2. **« Ce qui bloque » et « ce qui te manque »**, tirés de tes données, sans IA (§1, §3).
3. **Les questions proposées**, sans conseil juridique (§1, §5).
4. **La feuille** imprimable et en PDF ; l'IA seulement sur demande, pour un texte suivi (§3, §4).
5. **Le carnet**, l'agenda et l'objectif mis à jour après le rendez-vous (§1).
6. **Deux PR, 0.67.0 et 0.67.1** (le « après » est devenu la 0.67.2, voir docs/84), avec une table `orp_meetings` dans la famille personnelle (§6, §7).

## Écarts avec le cadrage (0.67.0)

- **La table `orp_meetings` arrive dès la 0.67.0** : la date du prochain rendez-vous et les questions cochées lui sont rattachées. La 0.67.1 y ajoutera ce qui a été convenu.
- **Pas de bouton « Imprimer »** : la feuille se télécharge en PDF, une page A4 qui s'imprime telle quelle. Une impression de la page web elle-même aurait emporté les menus et les boutons.
- **La carte d'Aujourd'hui** apparaît la veille, et aussi le jour même.
- **La formation proposée face à une compétence qui manque** est d'abord celle que tu suis ou envisages, puis une du catalogue.
- **Les questions cochées d'office** : le financement d'une formation payante suivie ou envisagée, une mesure si aucune réponse n'est venue en 3 mois, la suite d'une assignation des 60 derniers jours. La question du gain intermédiaire est proposée, non cochée.
- **Sur téléphone**, l'onglet s'appelle « RDV », pour que les cinq tiennent sur une ligne. Le titre de la page reste « Rendez-vous ORP ».
- **Dans la démo**, le rendez-vous fictif tombe toujours un mardi, cinq à onze jours plus tard.
- **Le PDF** a une partie « Ce qui marche » à part, et seulement les questions cochées.
- **Vérifié** :
  - 513 tests serveur, dont 4 nouveaux (`test_orp_meeting.py`) ; la table entre dans la famille personnelle, vérifiée par `test_policies.py`. 299 tests de l'interface, dont 2 nouveaux ;
  - sur une démo de brouillon : la page sur ordinateur (clair) et téléphone (sombre), aucune erreur d'API, et la feuille PDF téléchargée et relue.

## Écarts avec le cadrage (0.67.2)

- **Le rendez-vous suivant** se note avec ce qui a été convenu. S'il existe déjà, il est déplacé, pas doublé. Il garde le lieu et le conseiller du précédent.
- **« Ce qui a été convenu »** se note dès le début du rendez-vous, depuis la carte du prochain rendez-vous, puis depuis le carnet. Un rendez-vous à venir le refuse.
- **Les mesures** : les formations suivies, à cocher, passent en « financement accepté ». Les autres mesures (stage, cours…) s'écrivent une par ligne.
- **Le carnet** garde aussi les questions cochées pour chaque rendez-vous.
- **L'agenda** reçoit seulement la date, sans le lieu ni le conseiller, comme les entretiens (docs/40).
- **Le message rédigé par l'IA** (« Le message pour ton conseiller ») : environ 0,02 CHF. L'IA ne reçoit ni le lieu ni le conseiller, et la ligne du rendez-vous est retirée des obligations envoyées. Le message se copie ; il n'entre pas dans le PDF.
- **La démo** montre un rendez-vous passé, avec ce qui a été convenu, dans le carnet.
- **Vérifié** :
  - 516 tests serveur, dont 3 nouveaux (convenu, rappel et agenda, message de l'IA avec un faux client) ; le test des comptes essaie aussi un rendez-vous d'un autre compte ;
  - 301 tests de l'interface, dont 2 nouveaux ;
  - sur une démo de brouillon : la page sur ordinateur (clair) et téléphone (sombre), le formulaire ouvert, aucune erreur d'API.

