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
