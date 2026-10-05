# 13 — Postuler depuis la préparation, lien de candidature pour l'ORP (version 0.7.3)

> Statut : **à valider**. Aucun code avant accord.
> Retours d'usage du 2026-10-05. Complète [08-candidatures.md](08-candidatures.md) et [09-export-orp.md](09-export-orp.md).

## 1. Postuler sans quitter la préparation

**Constat** : une fois la lettre et le CV prêts, il faut revenir à la liste des offres pour postuler puis « Marquer comme envoyée ». Le lien « Postuler chez l'employeur » n'existe que dans l'onglet Lettre, et seulement pour les offres jobup.

**Proposition** : une **barre fixe en haut de la page de préparation**, visible dans les deux onglets (Lettre et CV) :

| Élément | Comportement |
|---|---|
| **Postuler** | ouvre le formulaire de l'employeur (lien lu sur jobup) ; à défaut, l'annonce sur le site d'origine (Indeed, jobup…) ; dans un nouvel onglet |
| **Télécharger** | la lettre et le CV en PDF ou Word, sans changer d'onglet |
| **Marquer comme envoyée** | ouvre ici le formulaire de suivi pré-rempli (le même que dans la liste) ; une fois enregistré, la barre affiche « Candidature envoyée le … » et « Voir le suivi » |

## 2. Lien de candidature dans le suivi et l'export ORP

**Constat** : l'ORP demande de pouvoir retrouver l'annonce ou le formulaire utilisé ; ce lien n'est pas enregistré avec la candidature.

**Proposition** :

- La candidature reçoit un champ **« Lien de la candidature »**, pré-rempli avec le formulaire de l'employeur, sinon le lien de l'annonce. Il reste modifiable : par exemple, si tu as finalement postulé par e-mail, tu le remplaces par l'adresse e-mail utilisée.
- Il apparaît :
  - dans la page Candidatures ;
  - dans la page ORP, avec un bouton « copier » en mode Job-Room ;
  - dans le CSV ;
  - dans le PDF, en une ligne courte sous le poste.
- Les candidatures déjà enregistrées reçoivent le lien de leur offre (migration), si elle en a un.

## 3. Base (migration 0019)

```
applications  + application_url?
```

La migration des sites (cadrage 11, PR c) passe en 0020.

## Points à valider

1. **Barre « Postuler · Télécharger · Marquer comme envoyée »** en haut de la préparation, dans les deux onglets (§1).
2. **Lien de la candidature** enregistré, pré-rempli et modifiable, présent dans la page Candidatures, la page ORP, le CSV et le PDF (§2).
3. **Une seule PR** pour les deux.
