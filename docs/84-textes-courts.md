# 84 — Des textes plus courts (version 0.67.1)

> Statut : **validé** le 2026-10-19.
> Origine : ta remarque du 2026-10-19, « tes exemples sont toujours très verbeux ». Une relecture de l'interface a trouvé une vingtaine de textes de plus de deux lignes.

## Ce qui change

| Où | Avant | Après |
|---|---|---|
| Enseignements d'entretien, vide | 207 signes | « Rien pour l'instant. Après un entretien, clique sur « Faire le point sur l'entretien » dans sa candidature. » |
| Assistant, introduction | 197 | « Pose une question sur tes offres, candidatures ou preuves ORP. Il propose, tu confirmes. » |
| Entretien blanc | 182 + 171 | « L'IA joue le recruteur : 5 questions, puis un retour. » ; « Environ 0,20 CHF. Tu peux répondre en dictant. » |
| Candidature en télétravail | 188 | « Employeur à l'étranger ? Vérifie le contrat et les assurances avec ton conseiller. » |
| Découvrir, tes données | 159 | « Ton compte est séparé des autres. Tes coordonnées ne partent jamais à l'IA. » |
| Alertes créées | 142 | « …, souvent dès le lendemain. Tu les verras ici, avec le lien de confirmation si un site en demande un. » |
| Maintenance | 118 | « On réessaie toutes les 10 s. Ce que tu écrivais n'est pas perdu. » |
| Rendez-vous ORP | 6 petits textes | L'introduction raccourcie, la phrase sur la feuille A4 retirée, « Sur tes droits, c'est ton conseiller qui répond. » |
| Réglages, Plateforme, Extension | | Les textes qui répétaient le titre ou le bouton, raccourcis |

**Gardés tels quels** : l'avertissement avant de supprimer un compte, et les messages d'erreur qui disent quoi faire.

**La page Tes données** garde tout son contenu, mais en listes : elle se lit en diagonale.

## Écarts

- **Alertes créées** : le lien de confirmation d'un site reste mentionné, en une demi-phrase. Sans lui, on ne saurait pas où le trouver.
- **Notifications non configurées** : « réglage d'installation » reste, pour que l'invité sache que ce n'est pas à lui de le régler.
- **Le « après » du rendez-vous ORP** (docs/83) devient la **0.67.2**.
- **Vérifié** : 299 tests de l'interface, lint et typecheck ; la page Tes données capturée sur ordinateur et téléphone.

## 0.67.3 : le Suivi plus clair

Validé le 2026-10-19, après ta question : « Formulaire ORP du mois » a-t-il encore du sens, si l'extension remplit Job-Room ?

- **Le titre devient « Déclaration Job-Room »**, et à droite, ce qui reste à faire : « 1 ligne à compléter », « 4 à déclarer », « tout est déclaré » ou « aucune candidature ». Avant, il listait des formats (« tableau, PDF, CSV, Job-Room »).
- **Le tableau reste** : c'est lui que l'extension recopie, et il sert à vérifier avant de déclarer. Le PDF et le CSV étaient déjà dans le menu ⋯.
- **Les cases du calendrier ont toutes la même taille** : chaque semaine prend la hauteur de la plus haute. Les semaines sans candidature ne sont plus plus basses (retour sur docs/63 §2).
- **L'assistant** connaît le nouveau nom (assistant-v8, la ligne de la carte).
- **Vérifié** : tests de l'interface, dont 1 nouveau ; captures sur une démo de brouillon, avec une seule hauteur de case (83 px sur ordinateur, 58 px sur téléphone).

