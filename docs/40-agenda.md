# 40 — Tes dates dans ton agenda (version 0.33.0)

> Statut : **validé** le 2026-10-15. livré.
> Les dates qui comptent (entretiens, remise des preuves ORP, suites attendues, relances) n'existent que dans la plateforme : il faut l'ouvrir pour s'en souvenir. Ton téléphone a déjà un agenda ; elles devraient y être.

## 1. Un entretien dans ton agenda, en un clic

- Sur la carte d'une candidature avec un **entretien prévu** (Suivi) : **« Ajouter à mon agenda »**.
- Le navigateur télécharge un petit fichier **.ics** ; l'ouvrir l'ajoute à l'agenda du téléphone ou de l'ordinateur (iPhone, Android, Outlook, Google Agenda).
- L'événement : **« Entretien – Exemple SA »**, à l'heure prévue, **1 heure** par défaut, avec un **rappel la veille** et **2 heures avant** ; en description, le poste et le lien vers la candidature dans la plateforme.
- Marche partout, sans réglage, même si la plateforme n'est pas joignable depuis Internet.

## 2. Ou un abonnement : tout, tenu à jour

Pour ne plus y penser, **Réglages › Agenda** donne une **adresse d'abonnement** à coller une fois dans ton agenda. Il la relit tout seul (en général toutes les quelques heures) :

| Ce qui apparaît | Comment |
|---|---|
| **Entretiens** | à l'heure prévue, rappels la veille et 2 h avant |
| **Suites attendues** (« réponse avant le … », docs/23) | journée entière |
| **Remise des preuves ORP** | journée entière, le jour limite, rappel 3 jours avant |
| **Relances à faire** (docs/38) | journée entière, le jour où la candidature atteint 10 jours sans réponse |

- **Comment l'ajouter** : instructions courtes pour iPhone (Réglages › Calendrier › Comptes › Ajouter un compte › Autre › Calendrier avec abonnement), Google Agenda (« À partir de l'URL ») et Outlook (« S'abonner à partir du web »), avec un bouton **« Copier l'adresse »**.
- **Ce que contient l'adresse** : un **jeton secret** (comme pour l'extension, docs/25), révocable à tout moment (**« Révoquer »**). Seule son empreinte est gardée.
- **Le minimum dans l'agenda** : entreprise, poste et date ; **ni adresse, ni contact, ni note**. Quiconque aurait l'adresse ne verrait que cela.
- **Joignable depuis Internet** : Google Agenda et Outlook relisent l'adresse depuis leurs propres serveurs ; ils ne la verront que si ta plateforme est accessible publiquement (ton tunnel, plus tard ton déploiement). L'iPhone la relit lui-même : il suffit qu'il puisse joindre la plateforme. La page le dit.

## 3. Ce que ça ne fait pas

- La plateforme **n'écrit pas** dans ton agenda : c'est ton agenda qui lit (abonnement) ou toi qui importes (fichier). Rien ne passe par un compte Google ou Microsoft.
- Pas de modification depuis l'agenda : un entretien déplacé se change dans la plateforme, l'abonnement suit.

## 4. Base (migration 0043)

```
calendar_tokens   id, name, token_hash, created_at, last_used_at?, revoked_at?
```

Même forme que les jetons de l'extension, dans une table à part : révoquer l'un ne touche pas l'autre.

## 5. Livraison

Une PR (**0.33.0**) : le fichier par entretien (§1) et l'abonnement (§2). Ordinateur et téléphone.

## Points à valider

1. **« Ajouter à mon agenda »** sur un entretien prévu : fichier .ics, rappels la veille et 2 h avant (§1).
2. **Abonnement** dans Réglages › Agenda : entretiens, suites attendues, remise ORP, relances ; jeton secret révocable (§2).
3. **Le minimum** dans l'agenda : entreprise, poste, date (§2).
4. **Une PR** (§5).

## Écarts avec la livraison

- **Adresse de la plateforme** : c'est le **navigateur** qui la donne (son adresse exacte, avec le tunnel et le https) à la création de l'abonnement et au téléchargement d'un entretien ; elle sert à l'adresse d'abonnement et aux liens des événements. Derrière le relais de développement, l'API, elle, ne voit ni le https ni toujours le bon nom. L'adresse est gardée avec le jeton (migration 0043 : `calendar_tokens.origin`).
- **Ce que contient l'abonnement** : entretiens des 30 derniers jours et à venir ; relances au jour où la candidature atteint 10 jours (aujourd'hui si c'est déjà passé) ; suites attendues depuis 7 jours et à venir ; remise ORP du mois précédent et du mois en cours, tant qu'ils ne sont pas remis et s'ils ont des candidatures. Relu toutes les 4 heures par les agendas qui le respectent.
- **Titres** : « Entretien – Exemple SA », « Suite attendue – Exemple SA », « Relancer Autre SA ? », « Preuves ORP d'octobre 2026 à remettre ».
- **Réglages › Agenda** : « Créer une adresse d'abonnement » la montre **une seule fois** avec « Copier l'adresse » ; « Comment l'ajouter » (iPhone, Google Agenda, Outlook) ; « Révoquer ».
- **Vérifié** dans le navigateur : abonnement lu sans session (entretien avec ses deux rappels, relance, remise ORP), fichier d'un entretien depuis le Suivi. Pas essayé dans un vrai agenda (iPhone, Google).
