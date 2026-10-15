# 37 — Formations : vers ton profil et vers l'ORP (version 0.30.0)

> Statut : **validé** le 2026-10-15. livré : PR a (formation terminée vers le profil), PR b (demande de financement à l'ORP).
> Idée notée dans docs/16 (« pour plus tard ») : une formation terminée peut nourrir tes lettres et tes CV, et une formation payante se finance surtout **avec l'accord de l'ORP**. Aujourd'hui, la page Formations s'arrête au suivi (intéressé, en cours, terminée).

## 1. Une formation terminée entre dans ton profil

- Quand tu marques une formation **« Terminée »**, la fiche propose **« Ajouter à mon profil »**.
- Un petit formulaire s'ouvre, **déjà rempli**, que tu relis avant d'enregistrer :
  - **Titre** : « AWS Certified DevOps Engineer – Professional (Amazon Web Services) » ;
  - **Texte** : « Certification obtenue en octobre 2026. Automatisation, CI/CD et exploitation sur AWS. » (date, certificat obtenu ou non, description de la formation) ;
  - **Mots-clés** : ceux de la formation (Kubernetes, CKA…).
- Il devient un **bloc « formation »** de Mon parcours, comme ceux que tu crées toi-même : utilisé par les lettres, les CV et la note des offres.
- La fiche montre ensuite **« Dans ton profil »** avec un lien vers le bloc.
- **Rien n'est renoté d'office** : comme pour toute modification du profil, les notes existantes sont marquées « faites avec un ancien profil », et « Renoter » (Réglages › IA) les met à jour quand tu le décides.
- Pas d'IA, pas de coût.

## 2. Demander le financement à l'ORP

Pour une formation **payante** que tu suis ou qui t'intéresse, la fiche propose **« Préparer la demande à l'ORP »**.

### 2.1 Le texte

Un message prêt à envoyer à ton conseiller (par e-mail ou dans Job-Room), **sans IA** et donc gratuit, que tu peux modifier puis **copier** :

> Bonjour [nom du conseiller],
>
> Je souhaite suivre la formation « AWS Certified DevOps Engineer – Professional » (Amazon Web Services, examen en ligne, en anglais) : [lien].
>
> Elle répond à ce que demandent les offres de mon domaine : sur les 90 derniers jours, **12 offres** que j'ai reçues demandaient AWS ou une certification DevOps, par exemple « Ingénieur DevOps » chez Consort Group et « Cloud Engineer » chez Swisscom.
>
> Coût : [montant]. Durée : [durée].
>
> Pourriez-vous me dire si elle peut être prise en charge au titre des mesures relatives au marché du travail ?
>
> [ton prénom et nom]

- **L'argument chiffré** vient de tes offres : celles des 90 derniers jours dont les exigences (« Demande ») contiennent un mot-clé de la formation. Jusqu'à trois exemples (poste et entreprise). S'il n'y en a aucune, la phrase est retirée.
- Ce qui manque (montant, nom du conseiller) reste **entre crochets**, à compléter.
- Ton nom et prénom viennent de Mes coordonnées.

### 2.2 Le suivi de la demande

- **« Marquer comme demandée »** retient la date. La fiche affiche ensuite **« Demandée le 15 oct. »**, puis tu indiques la réponse : **« Acceptée »** ou **« Refusée »**.
- Dans **Mes formations**, une pastille montre l'état : « financement demandé », « accepté », « refusé ».
- **Relance** : un rappel dans la cloche **14 jours** après la demande restée sans réponse, une seule fois (comme pour les contacts, docs/31).

## 3. Ce que ça ne fait pas

- La plateforme **n'envoie rien** à l'ORP ni à personne : tu copies le texte.
- Elle **ne dit pas** si la formation sera acceptée : c'est la décision de l'ORP (docs/16).
- Une demande de financement **n'est pas une preuve de recherche d'emploi** : elle n'entre pas dans le formulaire ORP du mois.

## 4. Base (migration 0039)

```
training_marks   + chunk_id?            (bloc créé depuis la formation)
                 + funding_status?      (requested | accepted | refused)
                 + funding_requested_at?, funding_reminded_at?
```

## 5. Livraison en deux PR

| PR | Contenu |
|---|---|
| **0.30.0-a** | Une formation terminée entre dans ton profil (§1) |
| **0.30.0-b** | Demande de financement à l'ORP : texte, argument chiffré, suivi et relance (§2) |

Sur ordinateur comme sur téléphone (dans la fiche en plein écran, docs/34).

## Points à valider

1. **« Ajouter à mon profil »** pour une formation terminée, formulaire prérempli, sans renotation d'office (§1).
2. **Demande de financement** : texte sans IA, avec l'argument tiré de tes offres, à copier (§2.1).
3. **Suivi de la demande** (demandée, acceptée, refusée) et **relance après 14 jours** (§2.2).
4. **Rien n'est envoyé**, pas une preuve ORP (§3).
5. **Deux PR** (§5).

## Écarts avec la PR a

- **Migration** : la 0039 n'ajoute que `chunk_id` ; les colonnes du financement arriveront avec la PR b (migration 0040).
- **Texte prérempli** : « Formation terminée en octobre 2026, certificat obtenu. » suivi de la description de la formation ; titre « Formation (organisme) » ; mots-clés de la formation, séparés par des virgules et modifiables.
- **Profil d'essai** : l'ajout est refusé (« les blocs de profil appartiennent au profil principal ») : les blocs servent aux lettres et aux CV de ton profil.
- **« Dans ton profil »** mène à Profil › Parcours. Si le bloc est supprimé plus tard, le lien disparaît et « Ajouter à mon profil » revient.
- **Vérifié** dans le navigateur (formation marquée terminée, bloc relu et enregistré, bloc visible dans Mon parcours) ; données de démonstration supprimées ensuite.

## Écarts avec la PR b

- **Migration 0040** : `funding_status`, `funding_requested_at`, `funding_reminded_at` sur `training_marks`.
- **Quand** : la section « Préparer la demande à l'ORP » apparaît pour une formation **payante déjà suivie** (intéressé, en cours ou terminée) ; sans suivi, l'avertissement « Financement possible seulement avec l'accord préalable de ton conseiller ORP » reste seul.
- **Argument** : jusqu'à trois mots-clés de la formation, les plus demandés dans les exigences des offres des 90 derniers jours (doublons exclus), et jusqu'à trois exemples, du plus récent au plus ancien. Exemple réel sur l'instance de test : « 2 offre(s) que j'ai reçue(s) demandaient AWS ou CI/CD ou DevOps, par exemple « Ingénieur DevOps » chez Consort Group et « Cloud Engineer » chez Swisscom ».
- **Durée** reprise de la formation quand elle est connue, sinon « [durée] » ; le montant reste toujours « [montant] ».
- **Suivi** : « Marquer comme demandée » (date du jour), puis « Acceptée » ou « Refusée » ; « Retirer la demande » ou « Modifier » remet à zéro. Pastille dans l'en-tête de la fiche. Rappel dans la cloche après 14 jours, une seule fois, lien vers « Mes formations ».
