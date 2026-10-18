# 70 — Remplir Job-Room depuis l'extension (version 0.57.0)

> Statut : **validé** le 2026-10-18. Relevé du formulaire fait le même jour (`extension/fixtures/job-room-formulaire.json`).
> Origine : comparaison avec les concurrents du 2026-10-18. ApplyCH et une petite extension, My Efforts, remplissent déjà le formulaire des recherches d'emploi de Job-Room. jobA1 a tout ce qu'il faut pour le faire : l'extension (docs/25) et les champs Job-Room dans l'ordre du formulaire (« Copier », docs/46).

## 1. Le constat

- Chaque mois, chaque candidature se recopie dans Job-Room : une quinzaine de champs, un « Copier » et un « Coller » à la fois. Pour 10 candidatures, c'est environ 150 copier-coller.
- jobA1 ne sait pas non plus **ce qui est déjà déclaré**. Le mois se ferme sans savoir s'il en manque une dans Job-Room.

## 2. Le principe

C'est le même que pour les formulaires des employeurs (docs/25) :

- **jobA1 remplit, tu vérifies, tu enregistres.** Le bouton d'enregistrement de Job-Room reste le tien. Tu restes responsable de ce que tu déclares : la vérification avant l'enregistrement n'est pas une formalité.
- **Une candidature à la fois**, jamais d'envoi en masse.
- **Tu te connectes toi-même** à Job-Room (AGOV ou autre). L'extension ne se connecte jamais, ne navigue pas et ne lit rien d'autre que le formulaire ouvert.

## 3. Le parcours

1. Dans Job-Room, tu ouvres le formulaire pour saisir une recherche d'emploi.
2. Tu cliques sur l'icône **jobA1**. Le panneau reconnaît Job-Room et affiche **« À déclarer ce mois »**, c'est-à-dire les candidatures du mois ORP pas encore déclarées, de la plus ancienne à la plus récente.
3. Tu choisis la candidature, puis **« Remplir dans Job-Room »**.
4. Les champs se remplissent, **encadrés en violet**. Ceux qui manquent restent **en orange**, avec leur valeur et « Copier » dans le panneau (par exemple une adresse incomplète).
5. Tu vérifies, puis tu enregistres dans Job-Room.
6. Dans le panneau, **« C'est déclaré »** marque la candidature, et la suivante est proposée.

Si le formulaire de Job-Room a plusieurs étapes, il faut un clic sur « Remplir » par étape, comme pour les employeurs.

## 4. Ce qui est rempli

Ce sont les champs que la plateforme prépare déjà (`job_room_fields`, d'après le formulaire relevé le 2026-10-07) :

| Partie du formulaire | Champs |
|---|---|
| Quand avez-vous postulé ? | Date |
| Comment avez-vous postulé ? | Mode (électronique, lettre, contact personnel, téléphone) |
| Auprès de quelle entreprise ? | Entreprise, rue, n°, case postale, pays, NPA / lieu, personne contactée, courriel, téléphone |
| Pour quel poste ? | Désignation, lien vers le formulaire en ligne |
| Assignation par l'ORP ? | Oui ou non |
| Taux d'occupation | Plein temps ou temps partiel |
| Résultat | En suspens, entretien, réponse négative ou engagement |

**Écart avec la règle de docs/25** : ailleurs, l'extension ne choisit jamais un bouton radio ni une case. Sur Job-Room, le mode, l'assignation, le taux et le résultat sont des **réponses** de ta déclaration, et non des consentements : l'extension les choisit. Une case de confirmation (« Je confirme l'exactitude… ») ou de consentement n'est **jamais** cochée.

## 5. Reconnaître le formulaire de Job-Room

- Le code de Job-Room n'est pas public, et le formulaire n'est visible qu'une fois connecté. **Je ne me connecte pas à ton compte.** Il me faut donc un **relevé du formulaire vide**, fait par toi :
  - un petit script, que je te donne, à coller dans la console du navigateur sur le formulaire vide ;
  - il liste **seulement la structure** : étiquettes, types de champs, noms techniques et options des listes. Aucune valeur, ni ton nom ni ton numéro AVS ;
  - tu relis le résultat, puis tu me le colles. C'est une structure de page publique : elle peut aller dans le dépôt comme jeu de test.
- À partir du relevé, Job-Room devient un **site connu**, avec ses propres réglages. Les étiquettes sont prévues en français, allemand, italien et anglais, selon la langue choisie dans Job-Room.
- Job-Room est une application Angular. Il faut donc remplir les champs **comme une saisie au clavier** (événements de saisie et de changement), et ouvrir les listes déroulantes personnalisées pour choisir l'option.
- **Si Job-Room change son formulaire**, rien ne se casse : les champs non reconnus restent en orange, avec leur valeur à copier dans le panneau. C'est le même filet que « Copier pour Job-Room » aujourd'hui.
- **Tests** : une copie locale du formulaire, construite à partir du relevé, sert aux tests automatiques. L'essai réel se fait chez toi, sur une vraie candidature.

## 6. Savoir ce qui est déclaré

- Un nouveau champ sur la candidature : **déclarée dans Job-Room le …** (migration 0051).
- **« C'est déclaré »** dans l'extension le remplit. Pour celles saisies à la main, **« Marquer comme déclarée »** dans la section « Pour l'ORP » de la candidature fait de même. On peut annuler.
- Dans **Candidatures › vue ORP du mois** : « **3 à déclarer** dans Job-Room », et « Déclarée le 12.10 » sur chaque ligne déjà faite.
- Le **rappel ORP de fin de mois** (notifications) mentionne celles qui restent à déclarer, s'il y en a.

## 7. Sécurité et confidentialité

- **Aucune nouvelle permission** : l'extension agit toujours seulement sur l'onglet où tu cliques (`activeTab`), et ne demande aucun accès permanent à job-room.ch.
- **De Job-Room vers jobA1, rien n'est lu ni envoyé.** Le seul retour vers la plateforme est le « C'est déclaré ».
- Les données vont de ta plateforme au formulaire de Job-Room, comme si tu les collais. Rien ne passe par l'IA dans cette version : elle ne coûte rien.
- **Conditions d'utilisation de Job-Room** : je ne les ai pas trouvées en ligne sans connexion. À relire de ton côté avant l'essai réel : on remplit pour toi ce que tu saisirais toi-même, sans rien automatiser au-delà.

## 8. Livraison

Une seule PR, **0.57.0**, avec la migration 0051. **Prérequis : ton relevé du formulaire (§5).**

| Étape | Qui |
|---|---|
| Le script de relevé, puis le relevé collé ici | moi, puis toi |
| L'extension sur Job-Room, le champ « déclarée », la vue ORP et le rappel | moi |
| L'essai réel sur une candidature, puis `make migrate` | toi |

Rien ne change dans les droits de l'extension : la recharger suffit (Firefox : nouvelle signature privée).

## Points à valider

1. **Remplir Job-Room, une candidature à la fois, sans jamais enregistrer à ta place**, et sans connexion de ma part (§2).
2. **Choix des boutons de la déclaration** (mode, assignation, taux, résultat), jamais de case de confirmation ni de consentement (§4).
3. **Le relevé du formulaire vide**, fait par toi avec mon script, structure seulement (§5).
4. **« Déclarée dans Job-Room »** sur la candidature, avec le compte « à déclarer » et le rappel de fin de mois (§6).
5. **Une PR, 0.57.0**, avec la migration 0051 (§8).

## Écarts avec le cadrage

- **Le relevé a corrigé trois points** :
  - le mode de candidature et « Entretien d'embauche » sont des **cases à cocher**, pas des boutons. L'extension coche seulement la case du mode de la candidature, sans décocher les autres ;
  - il n'y a **aucune case de confirmation ni de consentement** dans le formulaire ;
  - le formulaire tient **sur une seule page**, donc un seul clic sur « Remplir ».
- **Reconnaissance par identifiant** : les identifiants des champs portent les clés du formulaire (`apply-channel.electronic`, `company.name`, `radio-button-…-FULLTIME`). Ce sont les mêmes dans toutes les langues : il n'y a pas d'étiquettes à traduire.
- **La date** remplace celle que Job-Room propose. Les autres champs déjà remplis ne sont pas touchés.
- **« NPA / Lieu »** : l'extension tape le NPA, puis choisit la suggestion qui porte aussi le lieu (ou la seule suggestion du NPA). Sans suggestion sûre en 3 secondes, le champ reste en orange, avec sa valeur à copier.
- **« Entretien d'embauche »** est coché si un entretien a eu lieu : statut « Entretien », ou date d'entretien connue, même après un refus ou un engagement.
- **Candidatures proposées** : celles du mois précédent et du mois en cours, pas encore déclarées, les plus anciennes d'abord.
- **Le compte « à déclarer »** (vue ORP) et la mention dans le rappel de fin de mois n'apparaissent que si au moins une candidature du mois est déjà déclarée. Sinon, pour qui remet le PDF, le compte serait toujours plein.
- **« Marquer comme déclarée »** est dans le panneau d'une candidature (section « Pour l'ORP ») et sur chaque carte de « Recopier dans Job-Room ». « Annuler » l'enlève. Déclarer ne marque pas un mois remis comme modifié.
- **Assistant** : la consigne passe en `assistant-v7`. Elle décrit l'extension sur Job-Room et « Marquer comme déclarée », et remplace « Copier pour Job-Room » (ancien nom) par « Recopier dans Job-Room ».
- **Extension 0.57.0**, sans nouvelle permission. Le script de relevé est dans le dépôt (`extension/releve-formulaire.js`), pour refaire le relevé si Job-Room change.
- **Essayé** :
  - le remplissage, sur une copie du formulaire reconstruite d'après le relevé : tout rempli, rien d'écrasé sauf la date, ce qui reste listé, jamais d'envoi ;
  - les routes avec un vrai jeton ;
  - la migration 0051 sur une copie de ta base (13 candidatures), aller et retour.
- **Non essayé** : le vrai Job-Room (il faut ta connexion) et le panneau dans le navigateur (le navigateur de test ne charge pas d'extension). C'est l'essai réel de ton côté.

## Complément : premier essai réel (2026-10-18)

- **Constat** : la case « Par voie électronique » est cochée, mais la date et l'entreprise restent vides, avec « Champ obligatoire ».
- **Première hypothèse, écartée** : un cadre ou une étiquette au même identifiant, placé avant le champ. Le relevé des identifiants montre que le champ vient bien en premier ; seuls les messages d'erreur (`…-validation`) et l'aide (`…-help`) portent un identifiant voisin, après lui.
- **Gardé quand même** : la recherche se limite aux champs (`input`, `select`, `textarea`), et chaque valeur est relue après la saisie. Si la page ne l'a pas prise, le champ passe en orange avec sa valeur à copier, au lieu d'être compté comme rempli.
- **À vérifier** : l'essai suppose la plateforme de cette version (routes de l'extension, migration 0051) et l'extension de cette branche.
