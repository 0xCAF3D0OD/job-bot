# 17 — Profils d'essai pour les Actualités et les Formations (version 0.10.0)

> Statut : **validé** le 2026-10-06 (option A). livré : PR a (profils, Actualités par profil), PR b (Formations par profil, mots-clés proposés).
> Retours d'usage du 2026-10-06, après la 0.9.0 : tester plusieurs « sessions » pour juger si les Actualités et les Formations conviennent à d'autres chercheurs d'emploi.

## 1. Ce que je propose, et ce que je ne propose pas (encore)

Deux façons de comprendre « sessions » :

| | **A. Profils d'essai** (proposé) | **B. Vrais comptes** (plus tard) |
|---|---|---|
| But | voir la plateforme avec les yeux d'un autre chercheur d'emploi | plusieurs personnes utilisent la même plateforme |
| Connexion | aucune : on choisit le profil dans un menu | identifiant et mot de passe par personne |
| Séparé par profil | Actualités, Formations, « Mon domaine » | tout : offres, candidatures, ORP, documents, IA |
| Travail | moyen (deux PR) | très lourd : toutes les tables et toutes les pages, sécurité des comptes |

Je propose **A** : c'est exactement ce qu'il faut pour juger la pertinence, sans toucher à tes offres, candidatures et preuves ORP. **B** pourra venir ensuite si tu veux ouvrir la plateforme à d'autres ; A en serait une première brique.

## 2. Profils d'essai

- Ton profil actuel devient le **profil principal** (« Kevin ») ; rien ne change pour toi tant que tu ne changes pas de profil.
- **Réglages → Profils d'essai** : créer un profil avec
  - un **nom** (« Infirmière à Lausanne ») et un **métier** en clair (« infirmière en soins généraux ») ;
  - **« Mon domaine »** : les mots-clés, saisis à la main, ou **proposés par l'IA** à partir du métier (Claude Haiku, environ 0,001 $ ; elle ne reçoit que le métier) ;
  - les **langues** et **pays** des filtres.
- Les profils sont **fictifs** : aucune donnée personnelle n'est demandée. Ils restent dans ta base, jamais dans le dépôt.
- On peut **dupliquer** un profil (pour comparer deux variantes de mots-clés) et le **supprimer** (le profil principal ne se supprime pas).

## 3. Changer de profil

- Un **sélecteur** dans la barre du haut, à côté de la cloche : « Profil : Kevin ▾ ». Il n'apparaît que s'il existe au moins un profil d'essai.
- Le profil choisi est retenu par le navigateur. Une **bande colorée** rappelle qu'on est sur un profil d'essai (« Profil d'essai : Infirmière à Lausanne — revenir à Kevin »).
- **Sur un profil d'essai**, seules les pages **Actualités** et **Formations** (et la section Actualités des Réglages) suivent le profil. Les pages Offres, Candidatures, ORP, Profil et Aujourd'hui restent les tiennes, avec un rappel « ces pages ne changent pas selon le profil d'essai ».

## 4. Ce qui suit le profil

| | Par profil | Commun à tous |
|---|---|---|
| Actualités | « Mon domaine », filtres pays et langue, **sources suivies** et **veilles**, compteur de nouveautés | les contenus relevés (une source suivie par deux profils n'est relevée qu'une fois) |
| Formations | suivi (intéressé, en cours, terminée), **suggestions de l'IA** (et celles écartées) | le catalogue vérifié |

**À la création**, un profil d'essai suit les sources « marché de l'emploi » (SECO, RTS, Le Temps) ; à toi d'ajouter, depuis les suggestions ou par une veille, ce qui correspond à son métier.

**Ce que ça va montrer, et c'est voulu** : le catalogue de sources et de formations est aujourd'hui centré sur l'informatique. Pour un profil « infirmière », les Actualités ne garderont presque rien avec « Mon domaine » tant qu'aucune veille n'est créée, et les Formations dépendront des suggestions de l'IA. C'est précisément ce que ces essais doivent mettre en évidence ; on pourra ensuite enrichir les catalogues par domaine.

## 5. Côté technique

- Le navigateur envoie le profil choisi dans un en-tête (`X-Jobbot-Profile`) ; sans en-tête, le profil principal. Pas de connexion : la plateforme reste mono-utilisateur, derrière ton accès privé (tunnel).
- Base (migration 0027) :

```
profiles          id, name, occupation?, is_main (un seul), preferences JSONB, news_seen_at?, created_at
profile_sources   profile_id, source_id, active          -- sources suivies par profil
news_sources      (inchangé ; une source sans profil qui la suit n'est plus relevée)
trainings         + profile_id?   -- suggestion de l'IA propre à un profil ; vide = catalogue
training_marks    clé (profile_id, training_id) au lieu de training_id
```

- Les réglages actuels (`news_preferences`, `news_seen_at`) et tes sources suivies passent au profil principal.

## 6. Livraison en deux PR

| PR | Contenu |
|---|---|
| **0.10.0-a** | Profils (création, duplication, suppression), sélecteur et bande, Actualités et Réglages par profil |
| **0.10.0-b** | Formations par profil (suivi, suggestions de l'IA) ; mots-clés proposés par l'IA à partir du métier |

## Points à valider

1. **Profils d'essai (A)** plutôt que de vrais comptes (B) pour l'instant (§1).
2. **Seules les Actualités et les Formations** suivent le profil ; offres, candidatures et ORP restent les tiennes (§3).
3. **Sources et veilles par profil**, contenus relevés en commun (§4).
4. **Mots-clés proposés par l'IA** à partir du métier, environ 0,001 $ (§2).
5. **Sélecteur dans la barre du haut** et bande de rappel sur un profil d'essai (§3).
6. **Deux PR** (§6).

## Écarts avec la PR a

- **Nom du profil principal** : « Profil principal » (le dépôt est public, aucun prénom dans les migrations) ; « Renommer » dans Réglages → Profils d'essai.
- **Formations** : elles suivent déjà « Mon domaine » du profil choisi (filtre et recherche par l'IA) ; le suivi et les suggestions propres à chaque profil viennent avec la PR b.
- **Sources** : la pause vaut pour le profil ; le pays, la langue et la case « marché de l'emploi » décrivent la source elle-même et valent pour tous les profils qui la suivent. Retirée par le dernier profil qui la suit, une source est effacée avec ses contenus.
- **Sources de départ d'un profil d'essai** : les articles « marché de l'emploi » du catalogue (SECO, RTS Économie, Le Temps Économie). Un profil dupliqué reprend les sources et les réglages de l'original.
- **Changer de profil** recharge la page (toutes les données affichées suivent le profil) ; le choix est gardé dans le navigateur (`localStorage`), le profil principal n'y laisse rien.
- **Menu** : avec le sélecteur, il passe sur une deuxième ligne en dessous de 1180 px de large.
- **Migration 0027** : `profiles`, `profile_sources` ; les réglages `news_preferences` et `news_seen_at` passent au profil principal ; `news_sources.active` est remplacé par la pause par profil.
- **Essai réel** : profil « Infirmière à Lausanne » (soins, infirmière, hôpital, santé, EMS) avec une veille « infirmière emploi » : 4 articles de son domaine en plus du marché de l'emploi, surtout français ; aucune formation du catalogue ne correspond. Comme prévu au §4, les catalogues devront s'ouvrir à d'autres domaines.

## Écarts avec la PR b

- **Suggestions de l'IA par profil** : une formation suggérée appartient au profil qui l'a demandée (gardée, écartée ou à vérifier) ; la même adresse peut être proposée à plusieurs profils. Une suggestion déjà dans le catalogue n'est pas recopiée.
- **Suggestions et suivi existants** : passés au profil principal.
- **Mots-clés proposés** : bouton « Proposer des mots-clés à partir du métier » à la création d'un profil, affiché seulement avec une clé API ; Claude Haiku 4.5, sans recherche web, enregistré dans `llm_calls` (`purpose = keywords`). Les mots-clés proposés restent modifiables avant la création.
- **Migration 0028** (la connexion du cadrage 18 passe donc en 0029).
- **Non essayé en réel** : la proposition de mots-clés par l'IA (pas de clé API sur l'instance de test) ; couverte par des tests avec une réponse simulée.
