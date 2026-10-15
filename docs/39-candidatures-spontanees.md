# 39 — Candidatures spontanées (version 0.32.0)

> Statut : **validé** le 2026-10-15. livré.
> Aujourd'hui, tout part d'une **offre reçue** : la lettre, le CV adapté et la ligne ORP. Or on postule aussi **sans annonce**, auprès d'une entreprise qu'on vise. La plateforme permet seulement d'**enregistrer** une telle candidature à la main (Suivi › ＋), sans aide pour la lettre ni le CV.

## 1. Commencer une candidature spontanée

- Depuis **Candidatures › Offres** : un bouton **« Candidature spontanée »** à côté de « Filtrer ».
- Un court formulaire :
  - **Entreprise** : le nom, avec la recherche au **registre du commerce (IDE)** déjà utilisée pour les adresses (docs/12) : l'adresse se remplit seule si tu choisis la bonne ;
  - **Poste visé** : « Ingénieur DevOps », « Platform Engineer »… ;
  - **Site de l'entreprise** (facultatif) ;
  - **Pourquoi elle** : deux ou trois lignes, avec tes mots (ce que fait l'entreprise, ce qui t'attire, une personne rencontrée…). C'est ce qui rend la lettre spécifique ;
  - **Contact** (facultatif) : nom et e-mail, si tu le connais.
- **« Préparer »** ouvre la **page de préparation habituelle**, comme pour une offre.

## 2. La préparer comme une offre

- **Lettre** : même bouton, même coût (≈ 0,10 $). Les consignes changent pour une candidature spontanée :
  - pas de « suite à votre annonce » ; une **ouverture** qui dit pourquoi cette entreprise (tiré de « Pourquoi elle ») ;
  - ce que tu peux apporter au **poste visé**, tiré de tes blocs de profil ;
  - une **demande d'entretien** ou d'échange, même sans poste ouvert.
  - Comme toujours, l'IA ne reçoit ni ton nom ni tes coordonnées.
- **CV adapté** : choisi pour le poste visé et « Pourquoi elle » (≈ 0,05 $), comme pour une offre.
- **Contacts** (docs/31) : les recherches LinkedIn marchent aussi (entreprise + poste visé) ; c'est souvent le meilleur chemin pour une candidature spontanée.
- **« Marquer comme envoyée »** : la candidature rejoint le **Suivi**, avec la lettre et le CV, et la **relance après 10 jours** (docs/38).

## 3. Pour l'ORP

- Elle entre dans le **formulaire ORP du mois** comme les autres : date, entreprise, adresse, poste visé, mode. Le formulaire de Job-Room **n'a pas de case « spontanée »** : la saisie est la même.
- La carte du Suivi porte une petite mention **« Spontanée »**.

## 4. Ce qu'elle n'a pas (et c'est voulu)

- **Pas de note de l'IA** : il n'y a pas d'annonce à comparer à ton profil ; rien n'est dépensé pour elle.
- Elle **n'apparaît pas** dans « À examiner », dans la recherche de doublons, ni dans les vérifications d'expiration ou d'annonce chez l'employeur (docs/20, 30).
- Dans **Offres › En cours**, elle figure avec la mention « Spontanée », pour la retrouver tant qu'elle n'est pas envoyée.

## 5. Base (migration 0042)

```
offers   + spontaneous (booléen, faux par défaut)
         + spontaneous_reason?   (« Pourquoi elle »)
```

Une candidature spontanée est une **offre que tu crées toi-même**, sans lien de site d'emploi : elle réutilise toute la préparation (lettre, CV, contacts, fiche du formulaire) sans rien dupliquer.

## 6. Livraison

Une PR (**0.32.0**). Ordinateur et téléphone.

## Points à valider

1. **« Candidature spontanée »** dans Offres, formulaire court avec le registre IDE et « Pourquoi elle » (§1).
2. **Lettre aux consignes adaptées** et **CV** comme pour une offre ; contacts et relance aussi (§2).
3. **Ligne ORP** comme les autres, mention « Spontanée » sur la carte (§3).
4. **Pas de note de l'IA**, hors doublons et vérifications (§4).
5. **Une PR** (§6).

## Écarts avec la livraison

- **Deux temps dans le panneau** : d'abord entreprise, poste visé, site et « Pourquoi elle » (**« Continuer »** crée la candidature) ; puis l'adresse, **au choix** : « Chercher l'adresse au registre » propose les entreprises du registre IDE (gratuit ; s'il ne trouve rien, l'IA cherche sur Internet, environ 0,02 $, comme dans le détail d'une offre), et « Préparer la candidature » ouvre la préparation. Exemple réel : « Swisscom » → Swisscom AG, Alte Tiefenaustrasse 6, 3050 Bern.
- **Contact** : pas dans ce formulaire (une offre n'a pas de champ contact) ; il se saisit à l'envoi, comme pour une offre, ou dans « Contacts » (docs/31).
- **Texte lu par la lettre et le CV** : « Candidature spontanée : aucune annonce publiée. / Poste visé : … / Pourquoi cette entreprise : … / Site : … ». Les consignes de la lettre ont une section « Candidature spontanée » (pas de « suite à votre annonce », ouverture sur pourquoi l'entreprise, demande d'échange). Pas vérifié avec une vraie lettre (IA non configurée sur l'instance de test).
- **Préparation** : pas de bouton « Postuler » (il n'y a pas de lien d'annonce) ; « Marquer comme envoyée » préremplit l'entreprise, le poste et l'adresse choisie.
- **Vérifié** dans le navigateur : création, registre, préparation, envoi, carte « Spontanée » et ligne ORP complète ; données de test supprimées ensuite.
