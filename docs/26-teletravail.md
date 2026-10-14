# 26 — Les offres en télétravail (version 0.19.0)

> Statut : **validé** le 2026-10-14. livré : PR a (repérage, règle, filtre).
> Retours d'usage du 2026-10-14 : trouver les postes en télétravail (comme ceux qu'affiche Jobright), accessibles depuis la Suisse.

## 1. Le constat

- Jobright ne liste que des postes américains ; leur « remote » demande presque toujours de résider aux États-Unis. On ne l'importe pas (compte, protections contre les robots, et rien d'utile pour toi).
- Aujourd'hui, job-bot ne repère le télétravail que si le **lieu** de l'offre le dit (« Remote », « Home office ») ; la case « Accepter le télétravail complet, même hors de ces lieux » (Profil › Ce que je cherche) décide alors de la garder.
- Ce qui manque : le **télétravail partiel** (« 2 jours par semaine »), écrit dans le texte et non dans le lieu ; les **pays acceptés** (« Remote – US only », « Europe », « CET ± 2 h ») ; un moyen simple de **voir** ces offres ; et des **sources** d'offres à distance.

## 2. Repérer le télétravail dans chaque offre

À la notation, l'IA relève en plus, dans le texte de l'annonce (dans le même appel : quelques mots de réponse en plus, coût négligeable) :

| Information | Valeurs |
|---|---|
| **Télétravail** | sur site · partiel (avec le nombre de jours s'il est donné) · complet · non précisé |
| **Où on peut travailler** (télétravail complet) | Suisse · Europe · fuseaux horaires (« CET ± 2 h ») · monde entier · pays précis (« US only ») · non précisé |

- Sur la **carte** et le **détail** de l'offre : une petite étiquette « Télétravail 2 j » ou « 100 % télétravail · Europe ».
- Les offres **déjà notées** gardent « non précisé » ; un bouton dans Réglages › IA permet de les relire (Claude Haiku, environ 0,001 $ par offre, seulement les offres à examiner).

## 3. Écarter ce qui t'exclut

Dans **Profil › Ce que je cherche**, la case actuelle devient un choix à trois positions, la phrase reste courte :

- **Télétravail complet** : refusé · accepté si ouvert depuis la Suisse (par défaut si la case était cochée) · accepté partout.

« Ouvert depuis la Suisse » garde : Suisse, Europe, fuseaux horaires qui comprennent CET, monde entier, et « non précisé » (dans le doute, on garde). Il **écarte** les offres réservées à d'autres pays (« US only », « UK residents ») avec la raison affichée dans Écartées : « Télétravail réservé aux États-Unis ».

Le télétravail **partiel** suit tes lieux, comme un poste sur site (l'employeur est près de chez toi).

## 4. Voir les offres en télétravail

Dans Candidatures › Offres, panneau des filtres : une ligne **« Télétravail »** avec trois pastilles, comme les autres filtres — **tous** · **au moins partiel** · **complet**. Retenu dans l'adresse comme les autres (`?teletravail=`), masquable dans « Personnaliser les filtres ».

## 5. Des sources d'offres à distance

Sans code : ces sites envoient des alertes par e-mail, que la plateforme lit comme celles de LinkedIn (lecture par l'IA, docs/11).

- Dans **Réglages › Sites suivis**, quatre sites proposés en un clic, avec leur adresse d'expédition et leur page d'alertes : **We Work Remotely**, **Remotive**, **Himalayas**, **EU Remote Jobs**. Chaque adresse et chaque page seront vérifiées avant d'être proposées ; un site dont les alertes ne se lisent pas bien n'est pas gardé.
- Dans **Candidatures › Alertes**, l'assistant propose aussi ces sites, avec ta recherche déjà remplie quand le site le permet, et **le filtre « Télétravail »** de LinkedIn, jobup et jobs.ch (lieu « Suisse »).

## 6. Pour l'ORP

- Une candidature en télétravail chez un employeur **en Suisse** se déclare comme les autres.
- Chez un employeur **à l'étranger** : la ligne ORP s'enregistre normalement (adresse de l'employeur à l'étranger) ; une phrase dans la fiche de la candidature rappelle de **vérifier avec ton conseiller ORP** le contrat, les assurances sociales et l'imposition d'un emploi à distance pour une entreprise étrangère. Ce n'est pas un avis officiel.

## 7. Base (migration 0036)

```
evaluations  + remote? (onsite|hybrid|full|unknown), remote_days?, remote_scope? (ch|europe|timezone|worldwide|country|unknown), remote_detail?
criteria     remote_ok (bool) → remote_policy (refuse|from_switzerland|anywhere)
```

## 8. Livraison en deux PR

| PR | Contenu | De ton côté |
|---|---|---|
| **0.19.0-a** | Repérage à la notation, étiquettes, choix « Télétravail complet » et règle de filtre, filtre « Télétravail » dans Offres, relecture des offres déjà notées | aucun |
| **0.19.0-b** | Sites d'offres à distance proposés (vérifiés), filtre « Télétravail » dans l'assistant des alertes, rappel ORP | créer les alertes sur ces sites |

## Points à valider

1. **Pas d'import de Jobright** ; des sites d'offres à distance qui envoient des alertes par e-mail à la place (§1, §5).
2. **Repérage par l'IA à la notation**, dans le même appel : sur site, partiel, complet, et pays acceptés (§2).
3. **« Télétravail complet » à trois positions**, « ouvert depuis la Suisse » gardant le doute (§3).
4. **Filtre « Télétravail »** dans les Offres (§4).
5. **Rappel ORP** pour un employeur à l'étranger (§6).
6. **Deux PR** (§8).

## Écarts avec la PR a

- **Relevé à la notation** (consignes `score-v3`) : `remote` (sur site, partiel, complet, non précisé), jours par semaine, **région en quelques mots** (« Europe », « US only ») et **ouvert depuis la Suisse** (oui, non, non précisé). Plutôt qu'une liste fermée de régions (§7), l'IA tranche directement « ouvert depuis la Suisse » et garde la région en texte pour l'affichage.
- **Pas de renotation** : une note `score-v2` reste valable (`score-v3` n'ajoute que le télétravail) ; rien n'est renoté automatiquement.
- **Relecture des offres déjà notées** : lien « Relire (environ … $) » dans la carte IA des Réglages, avec le nombre d'offres concernées ; seulement les offres à examiner (300 au plus), Claude Haiku, `purpose = remote`. La tâche relance ensuite le filtre.
- **Règle « ouvert depuis la Suisse »** : une offre entièrement à distance dont l'annonce exclut la Suisse est écartée, **même sans lieux saisis** (raison dans Écartées : « Télétravail réservé : US only, pas ouvert depuis la Suisse ») ; sans précision, elle reste. Après chaque notation, le filtre est relancé pour en tenir compte.
- **Ta case cochée** « télétravail complet accepté » devient « Si ouvert depuis la Suisse » (migration 0036) ; décochée, « Refusé ». Le choix est en trois boutons sous les lieux, avec une phrase d'aide.
- **Étiquette** sur la carte (dans la ligne lieu · taux) et dans le détail : « Télétravail 2 j », « 100 % télétravail · Europe » ; barrée si le poste n'est pas ouvert depuis la Suisse. Un lieu « Remote » compte comme télétravail complet avant même la notation.
- **Filtre « Télétravail »** (Tous · Au moins partiel · Complet), `?teletravail=partiel|complet`. Il apparaît aussi chez qui avait déjà personnalisé ses filtres : un filtre ajouté depuis n'est pas considéré comme masqué.
- **Migration 0036** : colonnes de télétravail dans `evaluations`, critère `remote_policy` (contrainte des critères mise à jour).
- **Non essayé en réel** : l'appel à l'IA (pas de clé sur l'instance de test) ; couvert par des tests avec réponses simulées.
