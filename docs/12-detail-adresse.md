# 12 — Détail d'une offre allégé et adresse de l'entreprise (version 0.7.1)

> Statut : **à valider**. Aucun code avant accord.
> Retours d'usage du 2026-10-05. Complète [11-sites-etiquettes.md](11-sites-etiquettes.md) ; s'insère avant les PR b et c de la 0.7.

## 1. Actions du détail : deux boutons et un menu

**Constat** : une seule ligne mélange Reprendre la lettre, Marquer comme envoyée, Remettre à examiner et Signaler comme expirée.

**Proposition**, de haut en bas dans le détail :

| Zone | Contenu |
|---|---|
| **Action principale** | un seul gros bouton qui suit l'étape : « Préparer ma candidature », puis « Reprendre la lettre » une fois commencée |
| **Action secondaire** | « Marquer comme envoyée » ; une fois envoyée, à la place : pastille « Candidature envoyée » et lien « Voir le suivi » |
| **Liens** | Postuler chez l'employeur · Voir sur jobup (inchangés) |
| **Menu « ⋯ »** | Plus tard · Ignorer (ou Remettre à examiner) · Signaler comme expirée (ou Pas expirée) |

Le statut actuel (« En préparation », « Plus tard », « Expirée ») est rappelé en petite pastille sous le titre, au lieu de prendre la place d'un bouton.

## 2. Adresse de l'entreprise, trouvée automatiquement

Elle sert à l'en-tête de la lettre et au formulaire ORP (colonne obligatoire). Trois sources, dans l'ordre :

1. **L'annonce elle-même** (jobup, et jobs.ch ensuite). La page de l'offre contient l'adresse du lieu de travail (par exemple « Chemin Malombré 10, 1206 Genève »). La plateforme la lit déjà lentement pour le lien de candidature : l'adresse vient en plus, sans requête supplémentaire. Les offres déjà lues la reçoivent à leur prochaine revérification (tous les 3 jours).
2. **Le registre du commerce (Zefix)**, service officiel et gratuit de la Confédération, pour les annonces sans page lisible (Indeed, LinkedIn) :
   - recherche par nom d'entreprise ;
   - retenue seulement si une seule entreprise active correspond, de préférence dans le canton de l'offre ;
   - sinon, les 3 meilleures propositions te sont montrées, à choisir en un clic ;
   - c'est l'adresse du **siège** : elle peut différer du lieu de travail, la mention « registre du commerce » l'indique.
3. **Le texte de l'annonce, lu par l'IA** pendant la rédaction de la lettre (déjà en place depuis la 0.5).

Dans le détail, la ligne **« Adresse : … »** indique sa source (annonce, registre du commerce, lettre) et reste modifiable. Elle pré-remplit « Marquer comme envoyée », l'en-tête de la lettre et l'export ORP.

**De ton côté, pour Zefix** : l'API officielle demande un compte gratuit, à demander sur le site de Zefix. Tu renseignes ensuite `JOBBOT_ZEFIX_USER` et `JOBBOT_ZEFIX_PASSWORD` dans `.env`. Ne me les donne pas dans la conversation. Sans compte, seules les sources 1 et 3 fonctionnent.

**Rythme** : une recherche Zefix par entreprise, au plus 30 par passage, mise en cache : une entreprise déjà trouvée n'est pas recherchée deux fois.

## 3. Base (migration 0015)

```
offers     + company_address?, company_address_source? (page|registry|letter|manual)
companies  name_key PRIMARY, uid?, address?, candidates JSONB, looked_up_at   -- cache Zefix
```

Les migrations prévues au cadrage 11 pour les mots-clés et les sites deviennent 0016 et 0017.

## 4. Livraison en deux PR

| PR | Contenu | Prérequis de ton côté |
|---|---|---|
| **0.7.1-a** | Détail réorganisé ; adresse lue sur la page jobup ; adresse modifiable | aucun |
| **0.7.1-b** | Recherche dans le registre du commerce, choix parmi les propositions | compte Zefix (facultatif) |

## Points à valider

1. **Détail en deux boutons et un menu « ⋯ »**, avec le statut en pastille (§1).
2. **Adresse du lieu de travail** lue sur la page de l'annonce quand elle existe (§2.1).
3. **Registre du commerce (Zefix)** pour les autres : adresse du siège, retenue seulement si la correspondance est sûre, sinon tu choisis (§2.2).
4. **Compte Zefix gratuit** à créer de ton côté (facultatif) (§2).
5. **Deux PR** (§4).
