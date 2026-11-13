# 145 — Des offres sans alerte : les pages carrières des employeurs

> Statut : **étape 1 (inventaire) validée par Kevin le 2026-11-11**, seuils et 4e métier le 2026-11-13. Étapes 2 et 3 : pas encore.
> Origine : la question de Kevin du 2026-11-11 : « il devrait pouvoir y en avoir sans alerte ? Sur Google n'y en a-t-il pas ? » Recommandation détaillée dans le doc « Sources d'offres sans alerte e-mail » (agrégateurs, comparaison, courriers).
> Se construit sur docs/104 (recherche jobup, coupée en 0.82.4), docs/111 (`JobPosting`) et docs/144 (Google Emplois, accès partenaires).

## 1. Pourquoi

Sans alerte e-mail, jobA1 ne reçoit aucune offre. Google Emplois trouve les siennes sur les pages carrières des employeurs, par le balisage `JobPosting` ou par le flux du logiciel de recrutement. jobA1 sait déjà lire `JobPosting` (`sources/jobposting.py`). Les agrégateurs (Adzuna, Jooble, Careerjet, JobCloud) demandent tous une licence ou un partenariat (doc de recommandation, piste 1).

## 2. Étape 1 : l'inventaire

> Seuils et périmètre fixés par Kevin le **2026-11-13, avant le résultat**. Un premier passage du 13.11, lancé avant ces seuils, était faux (le script ne suivait pas les liens vers le logiciel de recrutement : 27 employeurs sur 35 « inconnus ») : il est écarté.

**Périmètre** : Vaud ; quatre métiers (santé, bâtiment, bureau, informatique) ; 40 employeurs dans `docs/inventaire-employeurs/employeurs-vaud.csv` (santé 13, bâtiment 8, bureau 13, informatique 8 ; l'État de Vaud et l'EPFL comptent en bureau et en informatique, une seule fois dans le total). Informatique, ajoutés par Kevin : ELCA, Kudelski / Nagravision, Logitech, Nexthink, SICPA, EPFL, État de Vaud (DGNSI : même page d'offres que l'État de Vaud), Swisscom (sites vaudois). Un employeur sans page lisible ou sans offre en Vaud est noté tel quel, jamais remplacé sans accord.

**Seuils**

| Étape | On continue seulement si |
|---|---|
| 1. Inventaire | au moins 50 % des employeurs testés sont **lisibles** (20 sur 40), **et** au moins 3 employeurs lisibles dans chaque métier |
| 3. Essai de 14 jours | chaque métier reçoit en moyenne au moins 5 nouvelles offres par jour, après dédoublonnage |

En dessous d'un seuil, on arrête et Kevin reçoit les chiffres ; on n'ajoute pas de sources pour rattraper.

**Seuil par métier** (ajouté par Kevin le **2026-11-13 à 16 h 30 (heure suisse), avant le résultat**) : un métier qui a moins de 3 employeurs lisibles est retiré de l'essai ; les autres métiers continuent, si le seuil de 50 % au total est atteint. Un employeur classé dans deux métiers compte dans chacun.

**Trois verdicts** (définition stricte gardée, complétée le 13.11.2026) :

- **lisible**, les trois à la fois : balisage `JobPosting` complet (titre, lieu, date) sur les offres lues, ou flux public d'un logiciel du cas 1 (Personio, Greenhouse, Lever, Recruitee, Workable, SmartRecruiters, Ashby) ; robots.txt qui autorise (absent = autorisé) ; conditions d'utilisation trouvées, sans phrase qui interdit la lecture automatique ;
- **non lisible** : balisage absent ou incomplet (« partiel »), offres affichées seulement par JavaScript (pas de navigateur piloté), robots.txt qui interdit la page carrières, ou conditions qui interdisent ;
- **à vérifier à la main** : conditions introuvables, illisibles ou interdites d'accès par robots.txt ; robots.txt injoignable, ou qui permet la liste mais pas les pages d'offres (« ambigu ») ; page de départ en erreur.

En haut du tableau, deux pourcentages : **strict** (les « à vérifier » comptent comme non lisibles) et **provisoire** (ils sont exclus du calcul). Le haut du tableau donne aussi, pour chaque métier, le nombre d'employeurs lisibles, strict et provisoire, face au minimum de 3. Kevin vérifie ces lignes à la main ; le chiffre final, après vérification, se compare aux seuils.

**Page en erreur** (ajouté le 2026-11-13) : un employeur dont le robots.txt, la page de départ ou la page des conditions répond en erreur (code HTTP, ou pas de réponse) est relu une seconde fois en fin de passage, avec les mêmes règles de rythme. S'il est encore en erreur, il est classé « à vérifier à la main » et la raison donne le code d'erreur.

**Rythme** : 2 s au moins entre deux requêtes sur un même site, plus si son `Crawl-delay` le demande (CHUV : 5 s, EHC : 10 s) ; par employeur, au plus 41 pages (page de départ, 3 liens suivis, 6 fichiers du plan du site, 30 offres ou un flux, la page des conditions), plus un robots.txt par site visité. Une page interdite par robots.txt n'est jamais demandée ; si c'est la page de départ, une page d'offre ou le flux, la lecture de l'employeur s'arrête aussitôt.

**Le script** (`scripts/inventaire_employeurs.py`, sans effet sur l'app ni la base) : pour chaque employeur, robots.txt, puis au plus 3 liens suivis depuis l'adresse de départ jusqu'à la liste des offres (liens vers un logiciel connu d'abord, puis « offres d'emploi », « postes vacants »…), le plan du site quand la liste est dessinée en JavaScript, au plus 30 pages d'offres lues ou le flux public, la page des conditions. Tableau `inventaire.md` (et `.csv`) : employeur, métier, page carrière et logiciel, balisage (oui / partiel / non / flux), robots.txt (autorisé / interdit / absent), conditions (avec la phrase trouvée), offres en Vaud ce jour, verdict et raison, puis le résumé contre le seuil de 50 %.

**Règles suivies** : robots.txt avant chaque page (403 = tout refusé) ; 2 s au moins entre deux pages d'un site, plus si `Crawl-delay` le demande ; robot nommé `jobA1-inventaire/1.1 (+https://joba1.ch)`, avec une adresse de contact si on passe `--contact` ; seulement des noms d'employeurs, titres, lieux et dates.

**Abandonné** : la liste « à l'envers » (toutes les entreprises vaudoises à flux public) passait par l'index de Common Crawl, dont le robots.txt interdit la lecture (`Disallow: /`). Le script l'a respecté ; la liste est retirée.

**Où le lancer** : sur le Mac de Kevin (la machine de Claude ne peut pas ouvrir ces sites) :

```
cd ~/Documents/job-bot && git pull && python3 scripts/inventaire_employeurs.py --contact contact@joba1.ch
```

`--reprendre` relit `inventaire.csv` d'un passage fini, fait la seconde tentative des seuls employeurs en erreur et réécrit le tableau, sans relire les autres sites (utilisé pour le passage du 13.11, lancé avant ces deux ajouts).

## 3. Étape 2 (à valider après l'inventaire) : règle déjà décidée

Décision de Kevin du 2026-11-11 : **les coordonnées des recruteurs (nom, e-mail, téléphone) lues dans une offre ne sont pas gardées au-delà de la durée de l'offre**, et la politique de confidentialité le dit. La PR de l'étape 2 :

- efface ces champs quand l'offre disparaît de la page de l'employeur ou atteint sa date `validThrough`, au plus tard au passage quotidien suivant ;
- ajoute la phrase à la page Confidentialité dans la même PR (pas avant : la source n'existe pas encore) ;
- cite les règles de docs/regles-securite-donnees.md concernées (R-1), en particulier la conservation.

## 4. Règles de données (R-1)

Étape 1 : aucune donnée d'un utilisateur n'est lue, écrite, envoyée ni journalisée. Le script ne touche pas la base ; il ne garde que des noms d'entreprises, des titres d'offres et des lieux publics.
