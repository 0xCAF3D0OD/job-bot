# 86 — Le bon rythme (versions 0.68.0 et 0.68.1)

> Statut : **validé** le 2026-10-19.
> Origine : ta demande du 2026-10-19, se démarquer d'ApplyCH et de SwissJobs.app. Ces deux plateformes poussent au volume : plus d'annonces, plus de candidatures, jusqu'à la candidature automatique. jobA1 fait l'inverse, fidèle à « Less searching. More living. » : une dose juste chaque semaine, puis du temps pour vivre.

## 1. Le constat

Aujourd'hui, jobA1 :
- connaît ton **objectif mensuel** ORP, mais ne le répartit pas dans le mois : on voit « 6 / 10 » sans savoir si c'est en avance ou en retard ;
- **notifie les offres bien notées à chaque passage**, toutes les 10 minutes. Les sites sont collectés toutes les 2 heures, de 7 h à 21 h, ce qui fait jusqu'à 7 messages par jour, le week-end compris ;
- ne connaît ni tes **jours sans recherche** ni tes **pauses** (vacances, maladie) ;
- ne dit rien quand tu en fais **trop**, par exemple beaucoup d'envois sur des offres peu notées.

## 2. En clair

### Ta semaine
- **L'objectif de la semaine** vient de l'objectif mensuel, réparti sur les semaines du mois. Par exemple, 10 par mois donne 2 ou 3 par semaine. Une semaine en retard reporte le manque sur les suivantes, sans tout rattraper d'un coup.
- **Tes jours de recherche** se choisissent dans les Réglages. Par défaut, du lundi au vendredi. Tu peux aussi n'en garder que trois.
- **Aujourd'hui** gagne une carte « Ta semaine » :
  - « 2 / 3 candidatures cette semaine », avec un point par jour de recherche ;
  - **la dose du jour** : les 3 meilleures offres à regarder, pas toute la pile. Le reste attend dans Offres ;
  - quand la semaine est faite : « Semaine faite. Le reste du temps est à toi. »

### Les jours sans recherche
- **Rien n'arrive sur ton téléphone.** La cloche garde tout, pour quand tu reviens.
- La page Aujourd'hui le dit simplement : « Jour sans recherche ». Aucune liste à traiter.
- Les rappels ORP qui ont une date limite (la remise des preuves, le rendez-vous de demain) passent quand même.

### Les notifications groupées
- **Les offres bien notées arrivent en un seul message par jour**, à l'heure que tu choisis (9 h par défaut), seulement un jour de recherche. Par exemple : « 4 nouvelles offres bien notées, dont Acme SA (82) ».
- Tu peux garder l'ancien envoi, « dès qu'elles arrivent », dans les Réglages.

### Les pauses (0.68.1)
- **« Je fais une pause »** du … au …, pour des vacances ou une maladie :
  - pas de dose, pas de notifications d'offres, pas de signal de retard ;
  - la page Aujourd'hui affiche « En pause jusqu'au 3 novembre » ;
  - jobA1 rappelle d'**annoncer la pause à ton conseiller**, qui décide de ce qu'elle change pour l'objectif.
- **Après la pause**, la semaine repart à zéro, sans dette à rattraper.

### Le signal juste (0.68.1)
Un seul message, le dernier jour de recherche de la semaine :
- **à jour** : « Semaine faite : 3 candidatures. Octobre est en bonne voie (8 / 10). » ;
- **en retard** : « 1 sur 3 cette semaine. Lundi, 3 offres bien notées t'attendent. » Le message dit ce qu'il faut faire, sans reproche ;
- **trop** : tu as dépassé une fois et demie ton rythme, avec des envois sur des offres notées sous 50 : « 7 cette semaine, dont 4 peu notées. Mieux vaut moins, mais mieux ciblé. »

## 3. Pourquoi ça démarque jobA1

- **Personne ne le fait** : les autres mesurent combien tu envoies, jamais si c'est trop.
- **L'ORP demande un nombre, pas un épuisement** : répartir l'objectif enlève la panique de la fin du mois.
- **Moins de bruit** : un message par jour au lieu de sept, et rien les jours sans recherche.

## 4. Sans IA

Tout est calculé avec des règles simples, écrites dans le code : la répartition de l'objectif, la dose du jour (les meilleures notes déjà calculées), les signaux de la semaine. Rien n'est envoyé à l'IA, et cela ne coûte rien.

## 5. Ce qu'on ne fait pas

- **L'objectif ORP ne change jamais tout seul**, pas même pendant une pause : c'est ton conseiller qui le fixe.
- **Pas de séries ni de trophées** qui punissent un jour manqué. Pas de comparaison avec d'autres personnes.
- **Pas d'avis sur tes droits** (jours sans contrôle, vacances) : jobA1 te rappelle d'en parler à ton conseiller.
- **La dose est une proposition** : toutes les offres restent dans Offres.

## 6. Où ça vit

- **Aujourd'hui** : la carte « Ta semaine », en haut. Sur téléphone, elle passe juste après l'action du moment.
- **Réglages › Rythme**, une nouvelle rubrique :
  - tes jours de recherche ;
  - l'heure du message des offres, ou « dès qu'elles arrivent » ;
  - la pause (en 0.68.1).
- **Bilan** : les semaines du mois, faites ou non, pauses comprises (en 0.68.1).
- **L'assistant** connaît le rythme et peut le régler, avec ta confirmation comme pour le reste.

## 7. Données

Pas de nouvelle table. De nouveaux réglages par compte (`settings`) : les jours de recherche, l'heure des notifications et leur mode, la pause (début et fin). Les offres déjà annoncées gardent leur marque actuelle : le message du jour ne reprend que les nouvelles.

## 8. Livraison en deux PR

| Version | Contenu |
|---|---|
| **0.68.0** | La semaine (objectif réparti, dose du jour, carte Aujourd'hui), les jours sans recherche, les notifications groupées, Réglages › Rythme |
| **0.68.1** | La pause, le signal de fin de semaine (à jour, en retard, trop), les semaines dans le Bilan, l'assistant |

Vérifié à chaque fois :
- tests serveur et interface ;
- la répartition sur des mois de 4 et 5 semaines, et un objectif qui change en cours de mois ;
- captures sur ordinateur et téléphone, en clair et en sombre ;
- la démo, avec une semaine en cours.

## Points à valider

1. **L'objectif de la semaine**, réparti depuis l'objectif mensuel, avec la dose du jour (3 offres) sur Aujourd'hui (§2).
2. **Les jours sans recherche** : rien sur le téléphone, sauf les rappels ORP datés (§2).
3. **Un message d'offres par jour**, à 9 h par défaut, avec l'ancien envoi en option (§2).
4. **La pause et le signal de fin de semaine** en 0.68.1, y compris le signal « trop » (§2).
5. **L'objectif ORP jamais modifié par jobA1** (§5).

## Écarts avec le cadrage (0.68.0)

- **La dose du jour reprend le tableau existant** d'Aujourd'hui (« À examiner en priorité ») : il s'appelle maintenant « La dose du jour » et montre 3 offres au lieu de 5. Un jour sans recherche, il affiche « Jour sans recherche », sans liste.
- **« Ta semaine »** passe au-dessus de la dose du jour, à gauche ; la jauge ORP reste à droite. Le graphique du haut, qui s'appelait aussi « Ta semaine », devient « Tes 7 derniers jours ». Sur téléphone, l'ordre est : Ta semaine, la jauge ORP, la dose du jour.
- **Le message des offres** part une fois par jour, dès l'heure choisie (6 h à 21 h), au premier passage de la notation qui trouve de nouvelles offres. S'il n'y en a pas à 9 h, il part plus tard dans la journée, mais toujours une seule fois. Les offres d'un jour sans recherche attendent le jour de recherche suivant.
- **Ce qui se tait un jour sans recherche** : les offres, les relances, le retour d'entretien, les contacts, le financement des formations et l'objectif du mois en retard. **Ce qui passe toujours** : la remise des preuves, le rendez-vous ORP de demain, et les alertes techniques (plafond de l'IA, collecte en échec).
- **Une semaine à cheval sur deux mois** compte pour le mois en cours, avec ses jours de ce mois seulement.
- **Les tests** fixent l'heure à un mardi à 10 h (`rhythm.now`), pour ne pas dépendre du jour où ils tournent.
- **Vérifié** :
  - les tests serveur, dont 5 nouveaux (`test_rhythm.py`) : la répartition sur octobre 2026, le message une fois par jour, le téléphone silencieux le samedi, les réglages ;
  - les tests de l'interface, dont 4 nouveaux ;
  - sur une démo de brouillon : un jour de recherche et un jour sans recherche, sur ordinateur (clair) et téléphone (sombre), sans débordement ; la rubrique Rythme des Réglages.

