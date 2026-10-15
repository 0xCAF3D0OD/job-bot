# 38 — Relancer une candidature (version 0.31.0)

> Statut : **validé** le 2026-10-15. livré.
> Constat du 2026-10-15 : 12 candidatures envoyées entre le 12 septembre et le 7 octobre, **toutes en attente**, aucune réponse. La plateforme dit déjà « à relancer » après 10 jours (Aujourd'hui, cloche, Suivi), mais n'aide pas à **écrire** la relance ni à la **retenir**.

## 1. Où

- Sur la **carte d'une candidature** (Suivi) en attente depuis 10 jours ou plus : un bouton **« Relancer »**.
- Dans **Aujourd'hui**, la ligne « N à relancer » mène au Suivi, filtré sur ces candidatures (la liste du jour), dans l'ordre d'ancienneté.

## 2. Le message

- **« Rédiger la relance · 0,002 $ »** : un court message (**80 mots au plus**) rédigé par l'IA (Claude Haiku, `purpose = relance`) :
  - il rappelle **le poste** et **la date d'envoi** ;
  - il redit en une phrase **pourquoi tu conviens**, tiré d'un point fort de la note de l'offre (docs/06) ou de tes blocs de profil ;
  - il pose **une question simple** : où en est le processus, et s'il manque quelque chose à ton dossier ;
  - ton poli et direct, sans insistance ni excuse ;
  - **dans la langue de l'offre** (français, allemand ou anglais).
- L'IA reçoit le poste, l'entreprise, la date d'envoi, le résumé de l'offre et tes blocs de profil ; **jamais tes coordonnées ni ton nom**. La plateforme ajoute elle-même ta **signature** (Mes coordonnées) et un **objet** : « Relance – candidature [poste] ».
- Le texte reste **modifiable**, avec **« Copier »**.
- **Sans IA** (non configurée ou plafond atteint) : un modèle simple, prérempli avec le poste et la date, est proposé à la place, gratuitement.

## 3. Envoyer, puis retenir

- Si la candidature a une **adresse e-mail de contact** (champ existant) : **« Ouvrir dans ma messagerie »** ouvre ton application de messagerie avec le destinataire, l'objet et le texte déjà remplis. **Rien n'est envoyé par la plateforme** : tu relis et tu envoies toi-même.
- Sinon : « Copier », pour le formulaire de l'employeur, LinkedIn ou un e-mail que tu retrouves.
- **« Marquer comme relancée »** : la candidature passe au statut **Relancée** (déjà existant, orange dans le calendrier), avec la date. Elle sort de « à relancer ».

## 4. Et après

- **Seconde relance** : non. Une candidature relancée qui reste **sans réponse 14 jours** après la relance est proposée en **« Sans réponse »** (une ligne sur la carte : « Pas de réponse depuis la relance : passer en Sans réponse ? »). Un clic, rien d'automatique.
- La relance **n'est pas une nouvelle candidature** : elle ne compte pas dans les preuves ORP. Elle reste visible dans la candidature (date de relance), utile si ton conseiller te la demande.

## 5. Base (migration 0041)

```
applications   + followed_up_at?   (date de la relance)
```

Le statut `relancee` existe déjà ; seule la date manque pour la règle des 14 jours.

## 6. Livraison

Une PR (**0.31.0**). Ordinateur et téléphone (la carte du Suivi ouvre déjà ses détails ; sur téléphone, la relance s'ouvre dans le panneau en plein écran).

## Points à valider

1. **« Relancer »** sur la carte après 10 jours, et Aujourd'hui qui mène à la liste (§1).
2. **Message par l'IA**, 80 mots, langue de l'offre, sans tes coordonnées ; signature et objet ajoutés par la plateforme ; modèle gratuit sans IA (§2).
3. **« Ouvrir dans ma messagerie »** quand l'e-mail du contact est connu, rien n'est envoyé par la plateforme (§3).
4. **« Marquer comme relancée »** avec la date ; « Sans réponse » proposé 14 jours après (§3, §4).
5. **Pas une preuve ORP**, **une PR** (§4, §6).

## Écarts avec la livraison

- **Où** : sur la carte, la ligne « Sans réponse depuis 10 jours. Relancer » ouvre la relance dans le panneau latéral. La liste « À relancer » du Suivi (celle où mène Aujourd'hui) existait déjà ; elle est maintenant triée de la plus ancienne à la plus récente et reprend aussi les candidatures **relancées sans réponse depuis 14 jours** (« Pas de réponse depuis la relance. Passer en Sans réponse »).
- **Langue** : celle de la lettre envoyée si elle existe, sinon celle de l'annonce (détectée sur son texte), sinon le français. Objet : « Relance – candidature [poste] », « Nachfrage – Bewerbung … » ou « Follow-up – application for … ».
- **Sans IA** : un modèle en français, allemand ou anglais, avec la date d'envoi et le poste ; la raison est écrite au-dessus (« IA non configurée », « plafond mensuel de l'IA atteint »…).
- **Statut « Relancée » choisi à la main** : la date de relance est aussi retenue. La migration 0041 reprend la date du statut pour les candidatures déjà relancées.
- **Vérifié** dans le navigateur (instance de test sans IA) : modèle, lien vers la messagerie, « Marquer comme relancée », « Passer en Sans réponse ». Le message rédigé par l'IA n'est vérifié que par les tests (IA simulée).
