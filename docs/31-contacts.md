# 31 — Contacts dans l'entreprise (version 0.24.0)

> Statut : **à valider**.
> Dernière idée tirée de Jobright (2026-10-07) : trouver quelqu'un dans l'entreprise (recruteur, futur responsable, ancien de ton école), lui écrire un message court, et suivre ces prises de contact. Une recommandation interne multiplie les chances d'entretien.

## 1. Le principe

- La plateforme **ne lit pas LinkedIn** et ne contacte personne à ta place : elle ouvre des **recherches déjà remplies**, t'aide à **écrire le message**, et **garde la trace** de tes prises de contact.
- Les noms des personnes restent sur ta plateforme ; ils ne sont **jamais** envoyés à l'IA.

## 2. Trouver quelqu'un

Dans le détail d'une offre et dans la préparation, une section repliée **« Contacts chez Exemple SA »** propose trois recherches LinkedIn, ouvertes dans un nouvel onglet :

| Recherche | Ce qu'elle cherche |
|---|---|
| **Recrutement** | personnes de l'entreprise avec « recruiter », « talent », « RH », « HR » |
| **L'équipe du poste** | personnes de l'entreprise avec les mots du poste (« DevOps », « Platform ») |
| **Anciens de ton école** | personnes de l'entreprise passées par ton école (tirée de tes blocs « formation », par exemple « 42 Lausanne ») |

- Ce sont des recherches LinkedIn par mots-clés (entreprise + rôle ou école), les seules qu'une adresse peut pré-remplir sans compte ; LinkedIn affiche les résultats selon ton propre réseau.
- Plus un lien vers la **page « Équipe » ou « À propos »** du site de l'employeur quand elle a été trouvée (docs/20).

## 3. Écrire le message

- Bouton **« Rédiger un message »** pour une personne : tu choisis son rôle (recruteur, futur responsable, membre de l'équipe, ancien de ton école) et le canal (**invitation LinkedIn**, 300 caractères au plus, ou **message plus long**).
- L'IA reçoit le poste, l'entreprise, ce rôle et tes blocs de profil ; **jamais** le nom de la personne ni le tien : le texte contient « [Prénom] » et « [ton prénom] » à remplacer.
- Ton direct et court ; une question précise (le poste, l'équipe, le processus), jamais « pouvez-vous me recommander ? » au premier message.
- Claude Haiku, environ **0,002 $** par message, dans le plafond (`purpose = contact`). « Copier » sous le texte.

## 4. Suivre ses contacts

- **« J'ai contacté quelqu'un »** : nom (facultatif), rôle, canal, date, et plus tard **« a répondu »** avec une note.
- Les contacts apparaissent sur la **carte de la candidature** (Suivi) ou dans le détail de l'offre si tu n'as pas encore postulé.
- **Relance** : un rappel dans la cloche **7 jours** après une prise de contact restée sans réponse, une seule fois.
- **Aujourd'hui** : rien de plus qu'une ligne dans « Candidatures » quand une relance de contact est due.

## 5. Pour l'ORP

Une prise de contact n'est **pas** une candidature : elle ne compte pas dans les preuves ORP. Si elle débouche sur une candidature (spontanée ou à une offre), tu l'enregistres comme d'habitude.

## 6. Base (migration 0038)

```
contacts  id, offer_id?, application_id?, name?, role (recruiter|manager|team|alumni|other),
          channel (linkedin_invite|linkedin_message|email|phone|other), contacted_on,
          answered_on?, note?, reminded_at?, created_at
```

## 7. Livraison en deux PR

| PR | Contenu |
|---|---|
| **0.24.0-a** | Recherches déjà remplies, page « Équipe » de l'employeur, suivi des contacts (fiche, carte, relance) |
| **0.24.0-b** | Message rédigé par l'IA (invitation ou message) |

## Points à valider

1. **Rien n'est lu sur LinkedIn ni envoyé à ta place** : recherches pré-remplies seulement (§1, §2).
2. **Trois recherches** : recrutement, équipe du poste, anciens de ton école (§2).
3. **Message par l'IA**, sans aucun nom, environ 0,002 $ (§3).
4. **Suivi des contacts** avec relance après 7 jours (§4).
5. **Pas compté pour l'ORP** (§5).
6. **Deux PR** (§7).
