# Numéros postaux suisses avec coordonnées (filtre « Distance »)

Données : GeoNames (geonames.org), CC BY 4.0

`zipcodes.ch.csv` sert au filtre « Distance depuis… » de la page Offres (issue #468, décision de Kevin du
18.11.2026) : il donne un point (latitude, longitude) à chaque numéro postal et à chaque localité de Suisse.
L'application le lit dans le dépôt. Elle ne fait aucun appel externe, ni au démarrage ni plus tard.

| | |
|---|---|
| Source | https://github.com/zauberware/postal-codes-json-xml-csv, fichier `data/CH.zip` (`zipcodes.ch.csv`) |
| Commit exact | `b10e9ee35a8ed552cb19733b71b047a2185a5a12` (2026-11-10) |
| Copié le | 2026-11-18 |
| Données d'origine | GeoNames, numéros postaux (https://download.geonames.org/export/zip/) |
| Licence | Creative Commons Attribution 4.0 (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/ |
| Attribution | « Données : GeoNames (geonames.org), CC BY 4.0 », dans ce fichier et sur la page « À propos » |
| Contenu | 4 520 lignes ; colonnes `country_code,zipcode,place,state,state_code,province,province_code,community,community_code,latitude,longitude` |
| Empreinte SHA-256 | `553325615aba33ab746b5f73bcbc156d397cc252d041b9f4056f3f727f2be482` |

Le fichier n'est pas modifié : il est copié tel quel.

## Pourquoi ici et pas dans `data/` à la racine

Le dossier `data/` à la racine du dépôt est ignoré par git : il reçoit les données des personnes (base locale,
sauvegardes). Une copie figée qui doit partir avec le code est donc rangée dans le paquet Python, à côté du code qui
la lit (`jobbot/core/geo.py`), et elle est livrée avec lui.

## Mise à jour (à la main, une fois par an)

```sh
make geonames-maj COMMIT=<commit du dépôt zauberware>
```

La commande clone le dépôt source au commit choisi, vérifie les colonnes, remplace `zipcodes.ch.csv` et affiche le
nombre de lignes, l'empreinte et la date du commit. Ensuite :

1. mettre à jour le tableau ci-dessus (commit, dates, lignes, empreinte) ;
2. lancer `cd backend && uv run pytest tests/test_geo.py` et vérifier quelques distances connues ;
3. ouvrir une PR. Les offres déjà en base gardent leur point ; une offre reçoit le sien à sa prochaine écriture.
