# 07 — Propositions de blocs par l'IA (version 0.4.1)

> Statut : **validé le 2026-10-05 dans la conversation, livré.**
> Demande de Kevin : pouvoir créer ses blocs de profil depuis la plateforme, à partir d'un document, y compris plus tard pour un nouveau poste.

## Fonctionnement

1. Page Profil, sur un document lisible : bouton **« Proposer des blocs »**.
2. L'IA (même modèle et même effort que la note) lit le texte du document et propose de 1 à 15 blocs : expériences, compétences regroupées par domaine, formations, et préférences si le document en exprime.
3. Une fenêtre montre les propositions. Chaque titre et contenu est modifiable. Les propositions qui ressemblent à un bloc existant sont signalées (« ressemble à : … ») et décochées.
4. **Rien n'est enregistré sans le clic « Ajouter N bloc(s) ».** Les blocs ajoutés sont reliés au document.

## Données envoyées et garde-fous

- Sont envoyés à l'API : le texte du document **sans coordonnées** (e-mails, numéros de téléphone et liens personnels retirés avant l'envoi), et les blocs actifs, pour repérer les doublons.
- Les coordonnées éventuellement présentes dans la réponse sont retirées aussi.
- Le texte du document est une donnée, jamais une consigne. Le format de la réponse est imposé, puis revalidé.
- Le plafond mensuel s'applique : la proposition est refusée s'il serait dépassé. Le coût est enregistré dans `llm_calls` (`purpose = propose`).

## Coût mesuré

Sur le CV de Kevin (5 000 caractères) : 22 secondes, **0,08 $** (5 300 jetons en entrée, 2 300 en sortie). Sur 12 propositions, 10 doublons ont été correctement reconnus, et 2 étaient de vraies nouveautés.

## API

`POST /api/documents/{id}/propose-chunks` → liste de propositions (`kind`, `title`, `content`, `tags`, `duplicate_of`). Codes : 409 (IA non configurée, plafond atteint, compte API indisponible), 422 (document sans texte), 502 (refus ou réponse inutilisable), 503 (API momentanément indisponible).
