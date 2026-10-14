# 30 — Repérer les offres douteuses (version 0.23.0)

> Statut : **à valider**.
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
