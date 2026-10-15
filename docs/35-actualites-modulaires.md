# 35 — Actualités en modules, à la manière de RTS (version 0.28.0)

> Statut : **validé** le 2026-10-15. livré.
> Retour d'usage du 2026-10-15 : s'inspirer de la page d'accueil de RTS (rts.ch). Sur **ordinateur**, des modules qui s'adaptent au nombre d'actualités ; sur **téléphone**, une grande image en tête puis des lignes avec une vignette à droite. On garde notre ligne graphique (violet, cartes arrondies, police actuelle).

## 1. Ce qu'on reprend de RTS

- **Une hiérarchie nette** : une actualité en tête, en grand ; deux ou trois en second rang ; le reste en lignes régulières.
- **L'image d'abord**, puis le titre, sans résumé. Au-dessus du titre, une petite **étiquette** (chez RTS, la rubrique ; chez nous, la **source** : « SECO », « Le Temps ») ; en dessous, **l'heure relative** (« il y a 2 h »).
- **Des séparateurs fins** entre les lignes, beaucoup d'espace, pas de cadres autour de chaque article.

## 2. Nos volumes

Relevé du 2026-10-15 : 150 articles (dont 85 % avec image : Le Temps et RTS toujours, le SECO jamais) et 35 vidéos, toutes avec vignette. Avec « Mon domaine », il en reste souvent **5 à 20**. La page doit donc rester belle avec **1, 3 ou 30** actualités.

## 3. Ordinateur : des modules selon le nombre

| Nombre d'actualités | Disposition |
|---|---|
| **1** | L'actualité en tête, sur toute la largeur : image à gauche (60 %), titre à droite |
| **2** | En tête (2/3 de la largeur) + une en second rang à droite (1/3), image au-dessus du titre |
| **3 ou plus** | **Comme RTS** : en tête à gauche (2/3), **deux** en second rang empilées à droite (1/3) |
| **au-delà de 3** | En dessous, « Cette semaine » puis « Plus ancien » : des **lignes** sur **deux colonnes**, chacune avec étiquette, titre, heure et une **petite vignette à droite** |

- L'actualité en tête : la plus récente (de ton domaine si « Mon domaine » est choisi), titre en grand (environ 2 rem).
- Second rang : titre moyen (1,25 rem), image en 16/9.
- Les mots de ton domaine restent **surlignés** dans les titres.

## 4. Téléphone : le format RTS

- **En tête** : l'image sur toute la largeur, puis l'étiquette, le titre en grand et l'heure.
- **Ensuite, des lignes** séparées par un trait fin : à gauche l'étiquette, le titre (gras, trois lignes au plus) et l'heure ; à droite une **vignette carrée** d'un tiers de la largeur.
- Groupées comme aujourd'hui (« Aujourd'hui », « Cette semaine », « Plus ancien »).
- Le second rang de l'ordinateur devient de simples lignes : sur téléphone, une seule actualité est en grand.

## 5. Sans image

Le SECO n'en fournit jamais. À la place de l'image, une **vignette texte** dans notre style : fond violet pâle, le nom court de la source en violet (« SECO »), mêmes proportions que l'image. Si l'actualité en tête n'a pas d'image, c'est la première actualité **avec** image qui passe en tête (l'ordre reste chronologique ailleurs).

## 6. Vidéos

Même organisation (en tête, second rang, lignes), la vignette de la vidéo à la place de l'image, avec un petit ▶ dans le coin.

## 7. Ce qui ne change pas

« Mon domaine / Tout », « Filtrer · N » (avec la carte sur téléphone), « Relevé il y a 20 h · Relever » en bas de page.

## 8. Livraison

Une PR (**0.28.0**), sans migration ni changement d'API (l'image et l'heure sont déjà fournies). Vérifiée avec 1, 2, 3, 8 et 30 actualités, à 393 et 1280 px.

## Points à valider

1. **Hiérarchie RTS** : en tête, second rang, lignes ; image, étiquette (source), titre, heure ; pas de résumé (§1).
2. **Modules selon le nombre** sur ordinateur, dont le cas RTS dès 3 (§3).
3. **Téléphone** : grande image en tête, puis lignes avec vignette à droite (§4).
4. **Vignette texte** pour les actualités sans image, et en tête une actualité avec image (§5).
5. **Vidéos** dans la même organisation (§6).
6. **Une PR** (§8).

## Écarts avec la livraison

- **Trois actualités ou plus** (ordinateur) : l'image en tête **s'étire à la hauteur de la colonne de droite**, pour que les deux colonnes finissent à la même ligne ; les titres du second rang tiennent sur deux lignes au plus.
- **Vignettes des lignes** : au format 4/3 comme chez RTS (plutôt que carrées) ; 7,5 rem sur ordinateur, un tiers de la largeur sur téléphone.
- **Vérifié** dans le navigateur avec 30, 3, 2 et 1 actualités à 1280 px, et 30 à 393 px (images de démonstration, supprimées ensuite). Le cas de 8 actualités et l'onglet Vidéos n'ont pas été regardés à l'écran ; les vidéos passent par le même composant (▶ sur la vignette) et leur test existant passe.
- La page « journal » de docs/32 §5 (titres seuls, résumé au survol) est remplacée par ces modules.
