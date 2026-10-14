# 30 — Repérer les offres douteuses (version 0.23.0)

> Statut : **validé** le 2026-10-14. livré.
> Suite de la comparaison avec Jobright (2026-10-07) : repérer les annonces qui ne valent pas une candidature (arnaques, annonces « vivier », doublons, employeur caché), pour ne pas y perdre de temps.

## 1. Le constat

- Aujourd'hui, la plateforme repère seulement les **annonces d'agence** sans employeur nommé (liste de 20 agences et « pour notre client », docs/20 §2.4), et les **offres expirées**.
- Sur ta base (331 offres) : **28** offres vues dans au moins 5 alertes, **5** encore en ligne après 30 jours, **4** paires d'offres au même titre et même entreprise, **1** sans entreprise. Les plus revues viennent de sociétés de conseil (Qim Info, ELCA, Orange Business) : souvent des annonces permanentes pour constituer un vivier de profils, plutôt qu'un poste précis.
- Rien ne repère les **arnaques** (paiement demandé, contact par messagerie, « travail à domicile facile »), rares sur jobup et jobs.ch mais présentes sur LinkedIn et Indeed.

## 2. Les signaux

Chaque signal a **un nom court et une phrase d'explication** ; une offre peut en avoir plusieurs.

| Signal | Comment il est repéré | Coût |
|---|---|---|
| **Annonce permanente** | vue dans les alertes depuis **plus de 30 jours**, ou republiée après avoir expiré (même titre et même entreprise) | aucun |
| **Doublon** | même titre et même entreprise qu'une autre offre (autre site, autre lien) : les deux sont **regroupées** sous la plus récente, avec tous les liens | aucun |
| **Employeur caché** | annonce d'agence sans employeur nommé (déjà repérée), ou **aucune entreprise** indiquée | aucun |
| **Arnaque possible** | relevé par l'IA **à la notation**, dans le même appel (sans coût en plus) : paiement ou « frais de dossier » demandés, contact par WhatsApp, Telegram ou adresse personnelle (Gmail…), salaire sans rapport avec le poste, « gagnez X par jour depuis chez vous », vente pyramidale, demande de documents d'identité ou de coordonnées bancaires avant tout entretien | quasi nul |

Les trois premiers sont des **règles** de la plateforme ; le quatrième vient de l'IA, avec la phrase de l'annonce qui l'a déclenché, pour que tu puisses juger.

## 3. Ce que tu vois

- **Sur la carte** : une petite étiquette grise **« À vérifier »** (orange foncé pour « Arnaque possible »), à côté du lieu et du taux.
- **Dans le détail** : une ligne par signal, par exemple « Annonce permanente : vue dans les alertes depuis 42 jours » ou « Arnaque possible : demande des frais de dossier (« 50 CHF pour l'ouverture du dossier ») ».
- **Filtres des offres**, carte « Le poste » : un interrupteur **« Masquer les offres à vérifier »**, éteint par défaut. Rien n'est caché ni écarté sans ton choix.
- Les **doublons** n'apparaissent plus deux fois : une seule carte, avec les sites de toutes les annonces.

## 4. Ce qui n'est pas fait

- **Aucune offre n'est écartée automatiquement** : un signal peut se tromper (une annonce permanente peut cacher un vrai poste). Seul l'interrupteur les masque.
- Pas de vérification du **registre du commerce** pour chaque employeur (déjà utilisé pour l'adresse, docs/12) ni de liste noire partagée.
- Pas de note de **réputation** des employeurs (avis kununu, Glassdoor) : sites fermés aux lectures automatiques.

## 5. Base (migration 0037)

```
offers       + duplicate_of? (offre gardée), reposted_at? (republiée après expiration)
evaluations  + scam_signals [] (texte, extrait de l'annonce)   -- relevé à la notation
```

Les signaux « permanente » et « employeur caché » se calculent à l'affichage, sans colonne.

## 6. Livraison

Une seule PR (**0.23.0**). Les offres déjà notées n'ont pas le signal « arnaque » ; il apparaît sur les nouvelles notations, sans renotation.

## Points à valider

1. **Quatre signaux** : annonce permanente, doublon, employeur caché, arnaque possible (§2).
2. **Arnaque relevée par l'IA à la notation**, avec l'extrait qui l'a déclenchée, sans coût en plus (§2).
3. **Étiquette « À vérifier »** sur la carte, détail des signaux, interrupteur « Masquer les offres à vérifier » éteint par défaut (§3).
4. **Doublons regroupés** en une seule carte avec tous les sites (§3).
5. **Rien n'est écarté automatiquement** (§4).
6. **Une PR** (§6).

## Écarts avec la livraison

- **Base** : `offers.duplicate_of` et **`offers.seen_since`** (première apparition de l'annonce, doublons compris) au lieu de `reposted_at` : une annonce republiée après avoir expiré est soit la même offre revue (la collecte la remet en ligne, sa première date reste), soit un doublon d'une ancienne ; dans les deux cas, `seen_since` remonte à la première apparition et le signal « annonce permanente » s'allume. `evaluations.scam_signals` comme prévu. **Migration 0037**.
- **Doublons** : regroupés à chaque passage du filtre (après la collecte). L'offre gardée est celle sur laquelle tu as agi (envoyée, en préparation, mise de côté…), sinon une offre en ligne, sinon la plus récente. Les doublons ne sont **ni affichés, ni notés** (pas de coût en double), ni comptés sur Aujourd'hui ; la carte gardée porte les liens de tous les sites.
- **Annonce permanente** : seulement pour une offre encore en ligne ; une offre expirée n'est plus signalée.
- **Arnaque possible** : consignes de notation `score-v4` (aucune renotation ; une note plus ancienne n'a simplement pas ce signal), trois signes au plus, avec l'extrait de l'annonce.
- **Carte** : étiquette grise « À vérifier », ou orange « Arnaque possible » ; le détail des signaux est lu par les lecteurs d'écran. **Détail** : encadré « À vérifier », un signal par ligne, l'extrait entre guillemets.
- **Filtre** : interrupteur « Masquer les offres à vérifier » dans la carte « Le poste », `?verifier=masquer` ; visible aussi chez qui avait personnalisé ses filtres.
