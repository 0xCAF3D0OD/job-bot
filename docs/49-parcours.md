# 49 — Mon parcours : documents et blocs, plus calmes (version 0.41.0)

> Statut : **validé** le 2026-10-15, livré.
> Revue de Profil › Mon parcours après docs/44 à 48. Capture du 2026-10-15, ordinateur, données de test : aucun document, 5 blocs.

## 1. Ce qui ne va pas

| # | Constat |
|---|---|
| 1 | **Le même message trois fois** quand il n'y a pas de document : « Il manque ton CV : dépose-le ci-dessous » en haut, « Aucun document pour l'instant : commence par ton CV » sous la zone de dépôt, et un grand cadre vide « Choisis « Texte » sur un document… » à droite. |
| 2 | **Ce cadre vide** occupe les deux tiers de la largeur tant qu'aucun document n'est ouvert. |
| 3 | **Chaque carte de bloc porte « Modifier » et « Supprimer »** (en rouge) : cinq cartes, dix liens, dont cinq rouges. |
| 4 | **Le type est dit deux fois** : en pastille sur chaque carte et dans les onglets de filtre au-dessus. |
| 5 | **Des onglets vides** : « Rédhibitoire 0 », « Ton 0 » prennent la même place que les autres. |
| 6 | **Les cartes n'ont pas la même hauteur** (titre sur une ou deux lignes, texte plus ou moins long), la rangée est en escalier. |
| 7 | **Chaque document porte quatre actions** sur sa ligne : Texte, Proposer des blocs, Ouvrir, Supprimer. |
| 8 | Modifier un bloc ouvre une **fenêtre au milieu de l'écran** ; le reste de l'application (contacts, relance, formations, offres) utilise le panneau latéral. |

## 2. Documents

- **Sans document** : un seul encart, sur toute la largeur : « Dépose ton CV (PDF, DOCX, TXT ou MD · 10 Mo au plus) : l'IA en tire tes premiers blocs. » Plus de bandeau en haut, plus de cadre vide.
- **Avec des documents** : une ligne par document (nom ; taille · date · N blocs) et **une seule action** à droite, « Proposer des blocs » ; « Déposer un document » en dessous. Un clic sur la ligne ouvre le **panneau latéral** : le texte lu, « Ouvrir le fichier », et « Supprimer ce document » en bas. Les propositions de l'IA s'affichent comme aujourd'hui sous la liste.

## 3. Blocs de profil

- **Filtres** : seulement les types qui ont des blocs (« Tous 5 · Expérience 1 · Compétence 2 · Formation 1 · Préférence 1 ») ; les types vides restent proposés dans « Nouveau bloc ».
- **Carte calme** :

```
┌──────────────────────────────────┐
│ Kubernetes                        │
│ CKA en cours ; clusters kubeadm,  │
│ Helm, Argo CD.                    │
│                                   │
│ Compétence · 2 mots-clés        › │
└──────────────────────────────────┘
```

  - le titre, le texte sur **3 lignes au plus** ; en bas, une seule ligne fixe : le type (qui remplace la pastille) et, s'il est mis de côté, « inactif » ;
  - **toutes les cartes d'une rangée ont la même hauteur** ;
  - toute la carte ouvre le bloc.
- **Le bloc s'ouvre dans le panneau latéral** (au lieu de la fenêtre centrale) : type, titre, texte, mots-clés, « utilisé par l'IA » ; « Enregistrer » ; « Supprimer ce bloc » en bas. « Nouveau bloc » ouvre le même panneau, vide.

## 4. Rien ne change ailleurs

Pas de changement de base ni d'API : la présentation seulement. Les blocs, les documents et la lecture par l'IA gardent leur comportement.

## 5. Livraison

Une PR (**0.41.0**). Ordinateur et téléphone, captures avant / après.

## Points à valider

1. **Documents** : un seul encart quand il n'y en a pas ; sinon des lignes avec « Proposer des blocs » seul, le texte, le fichier et « Supprimer » dans le panneau (§2).
2. **Blocs** : filtres sans les types vides ; carte calme (3 lignes, type en bas, même hauteur) ; le bloc dans le panneau latéral, « Supprimer » en bas du panneau (§3).
3. **Une PR** (§5).

## Écarts avec la livraison

- **Sans document** : l'encart « Dépose ton CV » prend toute la largeur ; le bandeau « Il manque tes blocs » reste quand un document est là mais aucun bloc actif (c'est alors la seule indication).
- **Panneau d'un document** : « Ouvrir le fichier › » et « Créer un bloc avec la sélection » en haut, le texte lu, « Supprimer ce document » en bas. Le panneau d'un bloc peut s'ouvrir par-dessus (créer un bloc depuis la sélection).
- **Carte de bloc** : en bas, le type et le nombre de mots-clés (« Compétence · 1 mot-clé »), « inactif » s'il est mis de côté, et « › ». Même hauteur dans une rangée sur ordinateur ; sur téléphone, une colonne, chaque carte à sa hauteur.
- **Panneau d'un bloc** : « Actif : l'IA peut s'en servir » devient l'interrupteur « Utilisé par l'IA » ; « Étiquettes » devient « Mots-clés ». « Annuler » disparaît : fermer le panneau suffit.
