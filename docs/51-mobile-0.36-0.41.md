# 51 — Téléphone : la revue de 0.36 à 0.41 (version 0.41.2)

> Statut : **validé** le 2026-10-15, livré.
> Les versions 0.36 à 0.41 ont été conçues sur ordinateur et seulement vérifiées « sans débordement » à 390 px. Revue à 390 px des pages touchées, le 2026-10-15 (données de test). Comme toujours, les corrections ne s'appliquent que **sous 820 px** ; l'ordinateur ne change pas.

## 1. Ce qui va

- **Suivi** : cartes calmes lisibles, colonne « À relancer » sous le calendrier, « Compléter 3 lignes » fixé en bas.
- **Réglages** : six lignes repliables, `?rubrique=` ouvre la bonne ; sources et sites en lignes calmes avec interrupteur.
- **Formations** : liste en deux groupes, pastille d'état.
- **Fiche d'offre** : plein écran, deux boutons fixés en bas ; le lien direct (`?offre=`) l'ouvre bien.

## 2. Ce qui ne va pas

| # | Page | Constat | Correction proposée |
|---|---|---|---|
| 1 | **Préparer** | La ligne « entreprise · lieu · ← Offres » disparaît : sur téléphone, le sous-titre des pages est masqué (docs/34). On ne sait plus pour quelle entreprise on écrit, et le seul retour est le menu. | Cette ligne-là reste affichée sur téléphone (les autres sous-titres restent masqués). |
| 2 | **Préparer › Lettre** | L'**objet** est coupé (« Candidature au poste de Cloud Arc… ») : c'est un champ d'une ligne. | Sur téléphone, l'objet passe à la ligne comme les paragraphes. |
| 3 | **Préparer › Lettre** | Les paragraphes sont **justifiés** : sur 300 px, de grands blancs entre les mots. | Alignés à gauche sur téléphone ; le PDF et le Word restent justifiés. |
| 4 | **Préparer › Postuler** | La section « **1. Postuler** » n'a plus qu'une phrase : son bouton est fixé en bas de l'écran. | Sur téléphone, cette section disparaît (le bouton en bas suffit) et les étapes se renumérotent : 1. Fiche pour le formulaire, 2. J'ai postulé. |
| 5 | **Profil › Parcours** | Les filtres des blocs passent sur **trois lignes** dans un cadre. | Une seule ligne qui défile, comme les onglets des pages. |

## 3. Livraison

Une PR (**0.41.2**), CSS surtout. Captures 390 px avant / après ; l'ordinateur comparé au pixel, inchangé.

## Points à valider

1. Les **cinq corrections** du §2, sous 820 px seulement.
2. **Une PR** (§3).

## Écarts avec la livraison

- **Objet de la lettre** : sur téléphone, « Objet : » sur sa ligne, puis l'objet sur toute la largeur, qui passe à la ligne (Entrée n'y ajoute pas de saut). Sur ordinateur, le champ d'une ligne reste.
- **Étapes de Postuler** : les numéros viennent d'un compteur CSS ; la section masquée ne compte pas. Sur téléphone, la première étape visible n'a plus de trait au-dessus.
- **Ordinateur** : 12 pages comparées au pixel avec 0.41.1 ; 10 identiques, la fiche d'offre varie d'une capture à l'autre (animation), et sur « Postuler » le numéro « 2. » bouge d'un sous-pixel (numéro généré par le CSS), identique à l'œil.
