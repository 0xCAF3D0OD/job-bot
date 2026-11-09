# 144 — Des offres dès l'inscription : Google Emplois, l'ajout par lien, le transfert

> Statut : **validé par Kevin le 2026-11-09** (choix « Google Emplois + vérifier les API »).
> Origine : la question de Kevin du 2026-11-06 : « la personne attend un jour avant de recevoir quoi que ce soit ? Il faudrait que l'utilisateur puisse postuler dès son inscription. » Puis, le 2026-11-09 : « on peut les trouver sur internet en libre accès sur Google. »
> Se construit sur docs/116 (offres dès le départ), docs/111 (ajouter une offre), docs/112 (le relevé rapide), docs/128 (premiers pas) et la maquette du 8 novembre (docs/143, Aujourd'hui sur ordinateur).

## 1. Pourquoi un nouveau compte attend

- Les offres n'arrivent que par les e-mails d'alerte des sites (jobup, Indeed), envoyés à l'adresse jobA1 de la personne.
- Les sites envoient leur premier e-mail à leur rythme, souvent le lendemain matin.
- Le serveur relève la boîte toutes les 2 heures, de 7 h à 21 h (`worker/tasks/collect.py`).
- Les voies plus rapides restent fermées (docs/116 §2 b) : un robot sur jobup, ou montrer à un compte les annonces reçues par un autre, est interdit par les conditions de JobCloud. Google n'a pas d'accès officiel à sa liste d'offres et interdit les recherches automatiques. Job-Room attend une demande au SECO (docs/116 §2 c, pas encore envoyée le 2026-11-09).

## 2. Ce qui change

1. **« Des offres dès maintenant »**, sur Aujourd'hui (ordinateur), sous les premiers pas, tant qu'aucune offre n'est arrivée. Trois lignes de tâche, comme celles de la maquette :
   - **Chercher sur Google Emplois** : la recherche du métier, déjà remplie (première alerte active, sinon première recherche du métier avec le premier lieu), dans l'onglet Emplois de Google (`udm=8`), dans un nouvel onglet. La personne choisit une offre et l'ajoute par son lien. jobA1 ne lit pas Google.
   - **Ajouter une offre vue ailleurs** : le formulaire d'ajout par lien (docs/111). Absente une fois les alertes créées : la carte des premiers pas « Alertes prêtes » la propose déjà.
   - **Transférer mes alertes existantes** : la page Alertes, où vit le transfert (docs/116 §1).
2. **Le relevé rapide après « J'ai créé l'alerte »** (assistant des alertes et extension) : toutes les 15 secondes pendant 5 minutes, comme « J'attends un code » (docs/112), au plus 6 fois par heure. La confirmation du site et un éventuel premier envoi sont lus sans attendre le relevé des 2 heures.
3. **Le mois ORP sans « en retard » pendant les premiers pas** : « Encore 10 d'ici le 30 novembre », comme la maquette mobile.

## 3. Écarts

- **Écran sans maquette** : la maquette du 8 novembre ne dessine pas le premier jour sur ordinateur. Kevin a accepté que la disposition soit dessinée par Claude (2026-11-06, puis le choix du 2026-11-09). Elle n'ajoute aucun composant : un titre de section et des lignes de tâche existants.
- **Téléphone inchangé** : la maquette mobile (AccueilSmile, OnboardingC) n'a pas cette section. À dessiner si Kevin la veut aussi sur téléphone.
- **Poids** : +0,5 Ko (total 345,5 Ko sur 346 Ko). Rien retiré ailleurs : la hausse tient sous le plafond.
- **Google Emplois** : `udm=8` ouvre l'onglet Emplois de Google ; si Google le change, le lien reste une recherche « métier emploi lieu », dont la première boîte est la liste d'offres.

## 4. Les accès partenaires (vérifié le 2026-11-09, à confirmer avec chaque site)

| Site | Accès | Suisse | Ce qui bloque |
|---|---|---|---|
| Jooble | clé par pays, sur le portail API | ch.jooble.org existe ; non confirmé dans la doc | l'offre gratuite donne **500 requêtes pour toute la vie de la clé** : il faut un partenariat |
| Careerjet | clé de « publisher », compte éditeur | locale suisse non confirmée | chaque appel exige **l'adresse IP et le navigateur de la personne** : une donnée personnelle envoyée à un tiers (règle I-4, page Confidentialité) |
| Adzuna | clé développeur | Suisse dans la liste des pays (depuis 2022) | conditions d'affichage et volume gratuit à lire avant de s'inscrire |

Proposition : Adzuna d'abord (Suisse confirmée, aucune donnée personnelle à envoyer), puis Jooble par une demande de partenariat. Rien n'est codé avant l'accord écrit du site.

## 5. Règles de données (R-1)

- **E-2, C-2** : la recherche se lit par SQLAlchemy sous la RLS du compte (alertes, métier, lieux).
- **I-4** : Google ne reçoit le métier et le lieu que si la personne ouvre le lien, comme les recherches jobup déjà proposées ; `rel="noopener noreferrer"` et `Referrer-Policy: same-origin` : Google ne sait pas d'où vient la personne. Aucun service tiers nouveau côté serveur.
- **J-1** : rien de nouveau dans les journaux.
