## Filtre Distance : numéros postaux GeoNames au lieu de swisstopo (Kevin, 18.11.2026)

Remplace la source de la partie « Distance » de 2026-11-18-0847-filtre-contrat-distance.md (swisstopo) :
- Source : les numéros postaux suisses avec coordonnées du dépôt GitHub zauberware/postal-codes-json-xml-csv (données
  GeoNames, licence CC BY 4.0). Une seule copie, commitée dans le dépôt, avec un README : source (URL du dépôt et
  commit exact), date, licence et l'attribution « Données : GeoNames (geonames.org), CC BY 4.0 ».
- L'attribution figure aussi dans « À propos ».
- Aucun appel externe depuis l'application, ni au démarrage ni plus tard. Mise à jour : une commande manuelle
  documentée (`make geonames-maj COMMIT=…`).
- La demande d'accès à swisstopo est annulée (aucun réglage d'environnement n'avait été changé).

Les autres règles de Distance restent : vol d'oiseau, libellé « Distance depuis Renens », choix 15, 30 et 50 km,
« Lieu non précisé » avec son nombre, jamais d'offre exclue en silence, nombre sous chaque choix.

Mise en œuvre (à valider par Kevin dans la PR) :
- La copie vit dans `backend/src/jobbot/data/geonames/` : le dossier `data/` de la racine est ignoré par git (données
  des personnes).
- « Renens » vient des coordonnées de la personne (numéro postal, sinon commune) : le libellé suit la commune saisie.
  Sans commune reconnue, le groupe ne s'affiche pas.
- Un lieu d'annonce n'a un point que s'il est sans ambiguïté : numéro postal connu, ou nom de localité dans un seul
  endroit (le canton cité tranche). « Buchs » sans canton, « Neuchâtel / Berne » ou « Suisse romande » vont dans
  « Lieu non précisé ».
- Choix par défaut « Toutes » (la planche part de 50 km) : un défaut à 50 km retirerait des offres de la liste de main.
