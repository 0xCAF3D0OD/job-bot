# 45 — La fiche d'une offre, en sections claires (version 0.37.0)

> Statut : **validé** le 2026-10-15, livré.
> Même constat que pour les formations (docs/44), sur la fiche qui s'ouvre à droite d'une offre : boutons, liens, note, doutes, adresse et texte de l'annonce se suivent sans ordre net. Capture du 2026-10-15 (« Cloud Architect », en préparation).

## 1. Ce qui ne va pas

| # | Constat |
|---|---|
| 1 | **Deux fois le même lien** : le bouton « Postuler sur jobup › » et le lien « Voir sur jobup ». |
| 2 | **Une rangée de quatre liens de nature différente**, sur deux lignes : une action (« J'ai postulé : marquer comme envoyée »), deux liens (« Voir sur jobup », « Entreprise ») et un panneau (« Contacts »). |
| 3 | **Ce qu'on sait de l'offre est éparpillé** : lieu, taux et « vue 1 fois depuis le 7 sept. » en bas avec des coches ; « À vérifier : annonce permanente, vue depuis 38 jours » dans un cadre à part ; les raisons d'écart encore ailleurs. |
| 4 | **La note** porte dans son en-tête « Ton profil a changé depuis : note à refaire », serré à côté du chiffre. |
| 5 | **Le texte de l'annonce** arrive en entier tout en bas : la fiche fait plusieurs écrans. |

## 2. La fiche proposée

Comme le panneau des formations : un en-tête, puis des **sections titrées**, séparées par un trait, chacune seulement si elle a du contenu.

```
┌ Cloud Architect                        ⋯  ✕ ┐
│ Jura Data SA · Fribourg     [En préparation] │
│ [ Reprendre la lettre ]  [ Postuler sur jobup ›] │
├ Pour toi ─────────────────────────────────────┤
│ 88/100   Poste · Demande · Offre              │
│ Points forts · Manques                         │
│ (Ton profil a changé : note à refaire)         │
├ À savoir ─────────────────────────────────────┤
│ ✓ Fribourg · 80–100 % · télétravail 2 j/sem.   │
│ ✓ Vue 1 fois, depuis le 7 sept.                │
│ ! Annonce permanente : vue depuis 38 jours     │
├ Entreprise ───────────────────────────────────┤
│ Adresse · Site de l'employeur · Contacts (2)   │
├ Annonce ──────────────────────────────────────┤
│ Missions : exploiter et faire évoluer…         │
│ Lire toute l'annonce ⌄                          │
└───────────────────────────────────────────────┘
```

- **En-tête** : titre, entreprise · lieu, pastille d'état. **Deux boutons seulement** : l'action principale (Préparer ma candidature / Reprendre la lettre) et « Postuler sur … » (le site de l'employeur s'il est connu, sinon le site d'emploi). Tout le reste dans **« ⋯ »** : J'ai postulé (marquer comme envoyée), Plus tard, Écarter, Signaler comme expirée, Chercher chez l'employeur, Demander à l'assistant. « Voir sur jobup » disparaît (doublon).
- **Pour toi** : la note et le résumé de l'IA, points forts et manques ; « note à refaire » en ligne discrète sous la note.
- **À savoir** : une seule liste, une ligne par fait, une marque devant : **✓** ce qui est sûr (lieu, taux, télétravail, vue N fois depuis…), **!** ce qui est à vérifier (annonce permanente, doutes, docs/30), **✗** la raison d'un écart (prérequis).
- **Entreprise** : l'adresse (et « Chercher au registre »), le site de l'employeur, **Contacts** avec leur nombre.
- **Annonce** : les 6 premières lignes, puis **« Lire toute l'annonce »** qui déplie le reste en douceur.

## 3. Téléphone

Même ordre ; les deux boutons de l'en-tête restent fixés en bas de l'écran comme aujourd'hui.

## 4. Rien ne change ailleurs

Pas de changement de base ni d'API : la présentation seulement. Les actions gardent leur comportement.

## 5. Livraison

Une PR (**0.37.0**). Ordinateur et téléphone, captures avant / après.

## Points à valider

1. **Deux boutons** dans l'en-tête, le reste dans « ⋯ » ; « Voir sur jobup » retiré (§2).
2. **Quatre sections** : Pour toi, À savoir (✓ / ! / ✗), Entreprise, Annonce repliée à 6 lignes (§2).
3. **Une PR** (§5).

## Écarts avec la livraison

- **« ⋯ » visible partout** : sur grand écran, le bouton « ⋯ » était masqué (il portait le style du bouton de fermeture) ; il a maintenant le sien. Il contient J'ai postulé, Plus tard / Ignorer (ou Remettre à examiner), Signaler comme expirée, Chercher chez l'employeur, Demander à l'assistant. « Ignorer » garde son nom, en accord avec la pastille « Ignorée ».
- **Les deux boutons côte à côte** sur ordinateur aussi (ils s'empilaient en pleine largeur) ; sur téléphone, ils restent fixés en bas.
- **« Voir sur jobup »** n'est retiré que lorsqu'il mène au même lien que « Postuler » ; quand on postule chez l'employeur, l'annonce d'origine reste en lien sous le texte de l'annonce.
- **Le lieu** est dans l'en-tête (entreprise · lieu) et n'est pas répété dans « À savoir », qui commence par taux · télétravail · type, puis « Vue N fois ». Un télétravail fermé depuis la Suisse devient une ligne **!**.
- **Entreprise** : l'adresse, le registre et l'annonce chez l'employeur sont dans la section, plus dans un panneau latéral ; les Contacts gardent leur panneau.
- **Annonce** : repliée à 6 lignes avec un fondu quand elle dépasse ~420 caractères ; « Lire toute l'annonce » la déplie en douceur (sans animation si le système le demande).
