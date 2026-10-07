# 23 — Retour d'entretien (version 0.16.0)

> Statut : **validé** le 2026-10-07. livré : PR a (formulaire, résumé, rappel, suite dans le calendrier).
> Retours d'usage du 2026-10-07 : après un entretien, répondre à quelques questions pour comprendre ce qui a bien ou mal fonctionné, et garder un constat.

## 1. Quand et où

- **Sur la carte** d'une candidature au statut « entretien » (calendrier et liste) : bouton **« Faire le point sur l'entretien »**.
- **Le lendemain de l'entretien** (date saisie) : une alerte dans la cloche et sur Aujourd'hui, « Comment s'est passé ton entretien chez Exemple SA ? », avec le lien.
- **Plusieurs entretiens** pour une même candidature (premier, technique, final) : un retour par entretien.
- Le formulaire se remplit en **2 minutes** ; tout est facultatif sauf le ressenti global. On peut l'enregistrer à moitié et y revenir.

## 2. Les questions

Questions fermées d'abord (un clic), puis quelques champs libres courts.

### 2.1 Le déroulé

1. **Quel entretien ?** premier contact (RH) · entretien avec le manager · technique · test ou étude de cas · final · autre.
2. **Format** : sur place · visio · téléphone.
3. **Durée** : moins de 30 min · 30-60 min · plus d'une heure.
4. **Avec qui ?** RH · futur manager · membres de l'équipe · direction (plusieurs choix), et combien de personnes.

### 2.2 Ton ressenti

5. **Comment ça s'est passé, globalement ?** de 1 (mal) à 5 (très bien).
6. **Ton niveau de stress** : de 1 (calme) à 5 (très stressé).
7. **Ton intérêt pour le poste après l'entretien** : plus qu'avant · pareil · moins.
8. **Ton estimation de la suite** : probablement positive · incertaine · probablement négative.

### 2.3 Les questions qu'on t'a posées

9. **Les questions posées**, une par ligne, en coche celles qui **t'ont mis en difficulté**. Exemples proposés en un clic : « Présentez-vous », « Pourquoi ce poste ? », « Vos points faibles ? », « Prétentions salariales ? », « Une situation difficile que vous avez gérée ? », « Questions techniques ».
10. **Y a-t-il eu une question sur le salaire ?** non · oui ; si oui, **ce que tu as répondu** (champ court).

### 2.4 Ce qui a marché, ce qui n'a pas marché

11. **Ce qui a bien fonctionné** (une ou deux phrases) : un exemple qui a porté, une réponse bien préparée, le contact…
12. **Ce qui a moins bien fonctionné** : une réponse hésitante, un manque de préparation, un point du CV mal expliqué…
13. **Ce que tu aurais dû préparer** (liste courte) : alimente la prochaine préparation.
14. **Tes questions à toi** : celles que tu as posées, et celles que tu regrettes de ne pas avoir posées.

### 2.5 Ce que tu as appris sur le poste

15. **Ce que tu as appris** (missions réelles, équipe, outils, télétravail, horaires) ; **points d'attention** éventuels (charge, ambiance, flou sur le poste).

### 2.6 La suite

16. **Prochaine étape annoncée** : rien de dit · un autre entretien · une réponse attendue · un test à rendre ; **avant quelle date**.
17. **Remerciement envoyé ?** oui · non · à faire (rappel le lendemain).
18. Plus tard, quand la candidature passe en « refus » ou « engagement » : **le retour de l'employeur**, s'il en a donné un (motif, conseils).

## 3. Ce que la plateforme en fait

- **Sur la carte** : un résumé d'une ligne (« Entretien technique · ressenti 4/5 · suite : réponse avant le 20 octobre ») et le retour complet en un clic.
- **Prochaine étape** : si une date est donnée, elle apparaît dans le calendrier (repère « réponse attendue ») et une relance est proposée si rien n'arrive à cette date.
- **« Mes enseignements »** (nouvelle section dans Candidatures › Suivi, repliée) : sur tous tes entretiens,
  - les **questions qui reviennent** et celles qui t'ont mis en difficulté le plus souvent,
  - ce qui **a marché** et ce qui **n'a pas marché**, regroupés,
  - ce que tu as noté **à préparer**, en liste à cocher.
- **Avant un prochain entretien** (bouton sur la carte quand un entretien est prévu) : la fiche de préparation reprend ces enseignements et les questions difficiles déjà rencontrées.
- **En option, l'IA** (à la demande, environ 0,02 à 0,05 $) : à partir de tes retours seulement (sans ton nom ni tes coordonnées), des **pistes concrètes** pour la prochaine fois et des propositions de réponse aux questions qui t'ont mis en difficulté, en s'appuyant sur tes blocs de profil.
- **Confidentialité** : les retours restent sur ta plateforme ; ils ne sont jamais envoyés à l'IA sans clic de ta part, ni repris dans les preuves ORP.

## 4. Base (migration 0033)

```
interviews  id, application_id, kind, held_at?, format?, duration?, interviewers[] , people_count?,
            rating?, stress?, interest? (more|same|less), outlook? (positive|unsure|negative),
            questions JSONB [{text, difficult}], salary_asked?, salary_answer?,
            went_well?, went_badly?, to_prepare[] , my_questions?, missed_questions?,
            learned?, warnings?, next_step?, next_step_at?, thanks (sent|no|todo)?,
            employer_feedback?, created_at, updated_at
```

## 5. Livraison en deux PR

| PR | Contenu |
|---|---|
| **0.16.0-a** | Formulaire de retour, résumé sur la carte, alerte du lendemain, prochaine étape dans le calendrier |
| **0.16.0-b** | « Mes enseignements », fiche de préparation avant un entretien, pistes de l'IA à la demande |

## Points à valider

1. **Où et quand** : bouton sur la carte « entretien », alerte le lendemain, un retour par entretien (§1).
2. **Les 18 questions** (§2) : à garder, retirer ou compléter.
3. **Résumé sur la carte** et **prochaine étape** dans le calendrier (§3).
4. **« Mes enseignements »** et fiche de préparation (§3).
5. **IA en option**, à la demande, sur tes retours seulement (§3).
6. **Deux PR** (§5).

## Écarts avec la PR a

- **Bouton sur la carte** : « Faire le point sur l'entretien » quand la candidature est au statut entretien et qu'aucun retour n'existe pour la date d'entretien (ou aucun retour du tout) ; ensuite « Voir le retour » et « Ajouter un autre entretien ».
- **Rappel** : envoyé par la tâche quotidienne `reminders` (vers 9 h), le lendemain ou dans les 14 jours suivant l'entretien, une fois par date d'entretien ; il ouvre le Suivi sur le jour de l'entretien (`?jour=`). Sur Aujourd'hui, un encart par entretien sans retour.
- **Questions proposées** en un clic : neuf questions fréquentes (présentation, motivation, entreprise, points forts et faibles, salaire, situation difficile, dans 5 ans, questions techniques), plus les tiennes.
- **Retour de l'employeur** : le champ n'apparaît que pour une candidature en refus ou engagement.
- **Calendrier** : repère vert « suite attendue » à la date de la prochaine étape ; la carte apparaît aussi ce jour-là.
- **Migration 0033** (`interviews`, `applications.interview_reminded_at`).
- « Mes enseignements », la fiche de préparation et les pistes de l'IA viennent avec la PR b.
