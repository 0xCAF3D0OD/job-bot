# 85 — La déclaration Job-Room, en liste (version 0.67.4)

> Statut : **validé** le 2026-10-19.
> Origine : ta remarque du 2026-10-19. L'extension remplit Job-Room toute seule, alors à quoi sert encore la grande carte « Déclaration Job-Room » ? Elle est trop large, et elle répète ce que l'on voit déjà ailleurs.

## Le constat

La carte, sous le calendrier, montre deux choses :
- **le tableau du mois** ;
- **la vue « Recopier dans Job-Room »** : chaque candidature, champ par champ, avec un bouton « Copier ».

Les deux font doublon :
- l'**extension** remplit Job-Room à partir de jobA1, sans cette vue ;
- le **panneau d'une candidature** (on l'ouvre d'un clic) montre déjà les mêmes champs avec « Copier », pour qui n'a pas l'extension. On y trouve aussi « Marquer comme déclarée », l'offre et « Modifier ».

## Ce qui change

1. **Une liste courte, « À déclarer », dans la colonne de droite**, sous « À relancer », à la hauteur du calendrier :
   - une ligne par candidature du mois pas encore déclarée : **date · entreprise · poste**, sur une seule ligne ;
   - une ligne incomplète porte « à compléter » ;
   - toute la ligne est cliquable : elle ouvre le panneau de la candidature, avec l'offre, « Modifier » et les champs de Job-Room ;
   - quand tout est déclaré : « Tout est déclaré », sur une ligne.
2. **La grande carte disparaît**, avec son tableau et la vue champ par champ.
3. **Le PDF et le CSV** passent dans un menu ⋯ de la barre du mois, à côté de « Marquer comme remis ». Le PDF garde tout le tableau, comme aujourd'hui.
4. **« Colonnes affichées » est retiré** : il ne réglait que le tableau à l'écran.
5. **Sur téléphone** : « À relancer », puis « À déclarer », sous le calendrier.

## Ce qui ne change pas

- La vue « Liste » du Suivi (le tableau de toutes les candidatures).
- L'extension, et ce qu'elle lit de jobA1.
- Le panneau d'une candidature, avec ses champs Job-Room et « Marquer comme déclarée ».

## Points à valider

1. La liste « À déclarer » sous « À relancer », avec la date, l'entreprise et le poste, cliquable (§1).
2. Retirer la grande carte et la vue champ par champ (§2).
3. PDF et CSV dans le ⋯ de la barre du mois ; « Colonnes affichées » retiré (§3, §4).

## Écarts avec le cadrage

- **Le compte** : « À déclarer dans Job-Room » porte le nombre de lignes restantes.
- **Un jour choisi** dans le calendrier affiche ses candidatures seules, sans la liste « À déclarer ».
- **Deux avis restent au-dessus du calendrier**, s'il y a lieu : une remise changée après coup, et le nom manquant pour l'en-tête du PDF.
- **La route `/api/orp-columns` est retirée**, avec son test : plus rien ne l'appelait.
- **L'assistant** décrit la nouvelle liste (assistant-v8).
- **Vérifié** :
  - 299 tests de l'interface, dont 1 nouveau sur la liste. Un test du routeur dépasse son délai de 5 s dans la suite complète, sur main aussi ; il passe lancé seul ;
  - 515 tests serveur (le test de la route retirée en moins), ruff, mypy, lint, typecheck ;
  - captures sur une démo de brouillon, sur ordinateur et téléphone, sans débordement horizontal (390 px sur téléphone).

