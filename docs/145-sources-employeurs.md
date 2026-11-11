# 145 — Des offres sans alerte : les pages carrières des employeurs

> Statut : **étape 1 (inventaire) validée par Kevin le 2026-11-11**, Vaud seulement. Étapes 2 et 3 : pas encore.
> Origine : la question de Kevin du 2026-11-11 : « il devrait pouvoir y en avoir sans alerte ? Sur Google n'y en a-t-il pas ? » Recommandation détaillée dans le doc « Sources d'offres sans alerte e-mail » (agrégateurs, comparaison, courriers).
> Se construit sur docs/104 (recherche jobup, coupée en 0.82.4), docs/111 (`JobPosting`) et docs/144 (Google Emplois, accès partenaires).

## 1. Pourquoi

Sans alerte e-mail, jobA1 ne reçoit aucune offre. Google Emplois trouve les siennes sur les pages carrières des employeurs, par le balisage `JobPosting` ou par le flux du logiciel de recrutement. jobA1 sait déjà lire `JobPosting` (`sources/jobposting.py`). Les agrégateurs (Adzuna, Jooble, Careerjet, JobCloud) demandent tous une licence ou un partenariat (doc de recommandation, piste 1).

## 2. Étape 1 : l'inventaire (cette PR)

`scripts/inventaire_employeurs.py`, sans effet sur l'app ni sur la base. Il lit des pages publiques et écrit deux tableaux dans `docs/inventaire-employeurs/`.

- **Liste 1** (`liste1.md`) : ~35 employeurs vaudois choisis par métier (santé, bâtiment, bureau), dans `employeurs-vaud.csv`. Pour chacun : la page carrières, le logiciel reconnu, le cas, le nombre de `JobPosting`, robots.txt et `Crawl-delay`, et la colonne **conditions d'utilisation : permise / interdite / rien**.
  - Cas 1 : flux public d'un logiciel fait pour être lu (Personio, Greenhouse, Lever, Recruitee, Workable, SmartRecruiters, Ashby).
  - Cas 2 : `JobPosting` sur la page carrières ou sur une page d'offre.
  - Cas 3 : SuccessFactors, Refline, Abacus/umantis ou Prospective, sans `JobPosting`.
  - Le résumé donne aussi la **part des employeurs sur un logiciel du cas 3, même quand leurs pages ont un `JobPosting`** (demande de Kevin : il pense que la plupart des grands employeurs vaudois y tombent).
- **Liste 2** (`liste2.md`), construite à l'envers : toutes les entreprises qui ont un flux public sur l'une des sept plateformes du cas 1 et au moins une offre dans une localité vaudoise, quel que soit le métier. Les comptes viennent de l'index public de Common Crawl ; chaque flux est lu une fois. Long (plusieurs heures pour Personio) : le script reprend là où il s'est arrêté (`liste2-cache.json`), et `--max-par-plateforme` limite un essai.

**Règles suivies par le script** : robots.txt lu avant chaque page, une page refusée n'est pas lue (403 sur robots.txt = tout refusé) ; 2 s au moins entre deux pages d'un site, plus si `Crawl-delay` le demande ; 2 s entre deux comptes d'une même plateforme ; un robot qui se nomme (`jobA1-inventaire/1.0`) ; seulement des noms d'employeurs, des titres d'offres et des lieux.

**Conditions d'utilisation** : le script cherche, dans la page des conditions liée depuis l'accueil, une phrase qui parle de robots ou d'extraction automatique, et propose « interdite », « permise » ou « rien » avec la phrase. Ce n'est qu'une proposition : chaque « interdite » et chaque « permise » se relit à la main, et un site sans page trouvée se vérifie avant l'étape 2.

**Où le lancer** : sur le Mac de Kevin ou sur le serveur (`python3 scripts/inventaire_employeurs.py liste1`). La machine de Claude ne peut pas ouvrir ces sites.

## 3. Étape 2 (à valider après l'inventaire) : règle déjà décidée

Décision de Kevin du 2026-11-11 : **les coordonnées des recruteurs (nom, e-mail, téléphone) lues dans une offre ne sont pas gardées au-delà de la durée de l'offre**, et la politique de confidentialité le dit. La PR de l'étape 2 :

- efface ces champs quand l'offre disparaît de la page de l'employeur ou atteint sa date `validThrough`, au plus tard au passage quotidien suivant ;
- ajoute la phrase à la page Confidentialité dans la même PR (pas avant : la source n'existe pas encore) ;
- cite les règles de docs/regles-securite-donnees.md concernées (R-1), en particulier la conservation.

## 4. Règles de données (R-1)

Étape 1 : aucune donnée d'un utilisateur n'est lue, écrite, envoyée ni journalisée. Le script ne touche pas la base ; il ne garde que des noms d'entreprises, des titres d'offres et des lieux publics.
