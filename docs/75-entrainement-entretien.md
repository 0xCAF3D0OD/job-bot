# 75 — S'entraîner à l'entretien (version 0.62.0)

> Statut : **validé** le 2026-10-18.
> Origine : suite proposée le 2026-10-18. Le parcours s'arrête aujourd'hui à « Préparer l'entretien », une fiche à lire. L'idée : l'IA joue le recruteur à partir de l'offre et de ton profil, pose les questions une à une, puis fait un retour.

## 1. Ce qui existe déjà

- **Le retour après un vrai entretien** (docs/23) : les questions posées (et celles qui étaient difficiles), ce qui a marché ou pas, ce qu'il reste à préparer.
- **« Mes enseignements »** : la plateforme rassemble ces retours elle-même, sans IA. On y trouve les questions qui reviennent, les difficiles d'abord, et la liste « À préparer ».
- **« Préparer l'entretien »** : une fiche qui reprend l'offre, les entretiens déjà passés chez cet employeur, les questions difficiles et des questions à poser. Le bouton facultatif « Pistes de l'IA » ajoute des pistes et des brouillons de réponses tirés de ton profil.

Il manque **la pratique** : répondre à voix haute, ou par écrit, à des questions qu'on n'a pas choisies, puis savoir ce qui était solide et ce qui ne l'était pas.

## 2. Le principe

**Un entretien blanc, par écrit, d'environ quinze minutes.**
- L'IA tient le rôle du recruteur. Elle pose **une question à la fois**.
- Si ta réponse est vague, elle **relance une fois**, comme un vrai recruteur (« Pouvez-vous donner un exemple concret ? »).
- À la fin, tu reçois un **retour** : question par question, puis en bref.
- Tout reste dans jobA1. Un entraînement n'est **jamais compté comme un vrai entretien** : il n'apparaît ni dans « Mes enseignements », ni dans les Preuves ORP.

## 3. Où le trouver

- **Dans le panneau d'une candidature**, partie Entretiens : « M'entraîner » dans le « ⋯ ». « Préparer l'entretien » reste l'action visible (docs/74).
- **Dans la fiche « Préparer l'entretien »** : un bouton **« M'entraîner pour cet entretien »**, en haut. C'est l'endroit naturel, quelques jours avant.
- **Sans candidature**, depuis « Mes enseignements » : **« M'entraîner sur un entretien type »**. Il porte sur ton métier, d'après ton profil, sans offre précise.

## 4. Avant de commencer : trois choix

| Choix | Options | Par défaut |
|---|---|---|
| **Le type d'entretien** | RH, manager, technique (les mêmes types que le retour d'entretien) | celui de l'entretien prévu, sinon RH |
| **Le ton du recruteur** | bienveillant, exigeant | bienveillant |
| **La langue** | français, anglais, allemand | la langue de l'annonce |

La durée est fixe : **cinq questions**, chacune avec au plus une relance.

## 5. Les questions

Le recruteur choisit ses questions dans cet ordre :
1. **Ce qui manque à ton profil pour cette offre**, d'après la note de l'IA (« Il te manque : Bicep »). C'est là qu'un vrai recruteur creuse, et là que l'entraînement est le plus utile.
2. **Les questions difficiles déjà rencontrées** dans tes vrais entretiens, tirées de « Mes enseignements ».
3. **Les exigences de l'annonce** (« Demande »).
4. **Les classiques du type d'entretien**. En RH : se présenter, la motivation, les prétentions salariales, la disponibilité. En manager : un conflit, une priorité, un échec. En technique : un problème concret du domaine de l'offre.

Il ne pose jamais de question illégale ou intrusive : religion, santé, projet d'enfant, origine.

## 6. Pendant l'entraînement

- Une page en plein écran, comme une discussion :
  - les questions du recruteur à gauche, tes réponses à droite ;
  - en haut, « Question 2 sur 5 ».
- **Tes boutons** :
  - « Envoyer » (Entrée ; Maj+Entrée pour aller à la ligne) ;
  - « Passer la question » ;
  - « Terminer et voir le retour », à tout moment.
- **À l'oral si tu veux** : la dictée de ton système (macOS, iPhone, Android) écrit dans le champ de réponse. jobA1 n'enregistre pas de son (voir §11).
- Tu peux quitter et reprendre plus tard : l'entraînement reste « en cours ».

## 7. Le retour

À la fin, un retour en deux parties.

**Question par question** :
- ta réponse, repliée ;
- **un repère** : « solide », « à préciser » ou « à retravailler » (plutôt qu'une note, pour éviter un chiffre qui juge) ;
- **ce qui marche**, en une phrase ;
- **ce qui manque**, en une phrase : un exemple concret, un chiffre, le lien avec l'offre…
- **une meilleure réponse possible**, écrite **uniquement à partir de ton profil**. L'IA n'invente jamais une expérience que tu n'as pas. Si ton profil ne couvre pas le sujet, elle le dit et propose une manière honnête d'y répondre (« Je ne l'ai pas encore pratiqué, mais… »).

**En bref** :
- trois points forts, trois points à travailler ;
- un bouton **« Ajouter à À préparer »** pour chaque point à travailler, qui le range dans la liste de « Mes enseignements ».

Le retour reste consultable dans la fiche « Préparer l'entretien », partie **« Mes entraînements »** : la date, le type et les repères. Tu peux supprimer un entraînement.

## 8. Ce que reçoit l'IA

Comme pour les « Pistes de l'IA » (docs/23) :
- **oui** : l'offre (titre, entreprise, résumé, exigences), tes blocs de profil actifs, tes questions difficiles et tes points « à préparer », tes réponses de l'entraînement ;
- **jamais** : ton nom, tes coordonnées, les noms des recruteurs que tu as notés dans tes retours, tes contacts.

Le recruteur n'a pas de nom : il parle au nom de « l'entreprise ».

## 9. Le coût

- **Sonnet 5**, comme l'assistant et les pistes.
- Environ **0,15 à 0,25 CHF par entraînement** complet : une douzaine d'échanges et le retour. Les consignes du recruteur sont mises en cache pour réduire le coût.
- Le coût est compté dans ton **plafond mensuel de l'IA**. « M'entraîner » est refusé s'il reste moins que le coût d'un entraînement complet, pour ne pas s'arrêter avant le retour.
- Sans clé d'IA, et dans la démo, « M'entraîner » n'apparaît pas.

## 10. Ce qui change dans le code

| Où | Quoi |
|---|---|
| Base | une table `interview_practices` : candidature (facultative), type, ton, langue, état (en cours, terminé), échanges, retour, coût ; migration **0052** |
| Serveur | démarrer, répondre (en flux, comme l'assistant), passer, terminer, lire, supprimer ; deux consignes versionnées, `recruiter-v1.md` et `practice-feedback-v1.md` ; contrôle du plafond avant chaque échange |
| Interface | la page d'entraînement ; « M'entraîner » dans les Entretiens, la fiche « Préparer l'entretien » et « Mes enseignements » ; la partie « Mes entraînements » |
| Tests | avec une IA simulée : ordre des questions, une seule relance, rien de personnel envoyé, plafond, un entraînement absent de « Mes enseignements » et des preuves |

## 11. Plus tard, pas dans cette version

- **La voix dans jobA1** : le recruteur qui parle et la réponse dictée sans passer par le système. La reconnaissance vocale du navigateur n'existe pas sur Firefox, et une transcription par un service externe enverrait ta voix ailleurs. On en reparlera après les premiers essais à l'écrit.
- **Un entraînement dans l'assistant** : il reste centré sur la plateforme.
- **Une démo d'entraînement** : un exemple fictif, déjà écrit, à lire dans la démo publique.

## 12. Livraison

Une PR, **0.62.0**, avec la migration 0052.

Vérification : un entraînement complet sur ta plateforme, avec ta clé, sur une vraie candidature. Captures de la page, du retour et de « Mes entraînements », sur ordinateur et téléphone. Coût réel relevé et comparé à l'estimation.

## Points à valider

1. **Un entretien blanc par écrit**, cinq questions, une relance au plus, un retour à la fin (§2, §6, §7).
2. **Les trois entrées** : le « ⋯ » des Entretiens, la fiche « Préparer l'entretien », « Mes enseignements » pour un entretien type (§3).
3. **Les trois choix** : type, ton, langue (§4).
4. **L'ordre des questions** : d'abord ce qui manque à ton profil, puis tes questions difficiles, l'annonce et les classiques (§5).
5. **Le retour par repères** (solide, à préciser, à retravailler) plutôt qu'une note, avec des réponses tirées **uniquement** de ton profil (§7).
6. **Ce que reçoit l'IA**, et ce qu'elle ne reçoit jamais (§8).
7. **Le coût**, environ 0,15 à 0,25 CHF, compté dans le plafond mensuel, et refusé s'il ne reste pas assez (§9).
8. **Pas de voix dans jobA1 pour l'instant**, la dictée du système suffit (§11).
9. **Une PR 0.62.0**, migration 0052 (§12).

## Écarts avec le cadrage

- **Pas de flux mot à mot** : une question du recruteur fait une ou deux phrases. Elle arrive d'un bloc, après « Le recruteur réfléchit… », plutôt qu'en flux comme l'assistant. C'est plus simple, et l'attente reste de quelques secondes.
- **La plateforme tient le compte**, pas l'IA : le numéro de la question, une relance au plus (une seconde relance devient la question suivante), pas de relance après une question passée, la fin après la cinquième. L'IA ne choisit que la question et sa formulation.
- **Le retour arrive tout seul** après la dernière réponse ; « Terminer et voir le retour » le demande avant. Si l'IA échoue en route, la réponse est gardée et un bouton « Réessayer » relance le recruteur.
- **La langue par défaut** est devinée d'après les mots courants de l'annonce (français, anglais, allemand). **Le type par défaut** est celui du dernier entretien noté pour cette candidature, sinon RH.
- **Les manques** viennent de la note de l'IA : les exigences de l'annonce non couvertes par le profil, et les points faibles relevés.
- **« Ajouter à À préparer »** range le point dans la liste « À préparer » de « Mes enseignements », avec les points tirés des vrais retours. Il se coche de la même façon.
- **Coût** : départ refusé s'il reste moins de 0,30 $ (environ 0,24 CHF) sur le plafond du mois. Chaque appel est compté dans le journal de l'IA (`practice`), et le coût de l'entraînement est gardé avec lui.
- **Sur téléphone** : l'entraînement prend tout l'écran ; le titre devient le nom de l'entreprise, et « Terminer et voir le retour » devient « Terminer ».
- **Vérifié** sans ta clé : avec une IA simulée dans les tests (déroulé complet, relance unique, question passée, reprise après erreur, plafond, rien de personnel envoyé, absent de « Mes enseignements »). Les écrans ont été vérifiés sur la démo, réponses de l'IA simulées dans le navigateur. **L'essai réel avec ta clé, sur une vraie candidature, reste à faire de ton côté** : il dira le vrai coût et la qualité des questions.

