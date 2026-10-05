# 05 — Lien de candidature externe jobup

> Statut : **à valider**. Aucun code avant accord.
> Demande de Kevin (2026-10-05) : récupérer le lien vers la candidature chez l'employeur.

## 1. Ce qui est possible

| Site | Lien de candidature | Pourquoi |
|---|---|---|
| **jobup** | oui | La page publique de l'offre contient `applicationOptions` : la méthode (`APPLICATION_METHOD.EXTERNAL` ou formulaire jobup) et `externalUrl`. Vérifié sur une offre (lien vers le site de recrutement de Michael Page). |
| **Indeed** | non | Les pages d'offres sont protégées contre les robots (réponse 401 avec un défi Cloudflare). On ne contourne pas cette protection : le bouton reste « Voir sur Indeed ». |

**Risque accepté par Kevin :** les conditions d'utilisation de jobup interdisent probablement la lecture automatisée. Le `robots.txt` de jobup n'interdit pas les pages d'offres (`/fr/emplois/detail/`), seulement `/external/`, `/api/` et les pages de candidature. Le bot ne les visite pas.

## 2. Fonctionnement

- **Nouvelle tâche `enrich`**, enchaînée après le filtre.
- **Offres visées :** celles de jobup, à examiner (pas les offres écartées), et jamais lues.
- **Rythme :** une requête toutes les 10 secondes, au plus 30 par exécution, et une seule lecture par offre. Tes 67 offres jobup actuelles seront traitées en 3 collectes.
- **Navigateur annoncé :** le bot se présente honnêtement comme `job-bot/0.3 (usage personnel)`.
- **Ce qui est extrait** de la page, sans rien suivre d'autre :
  - **lien de candidature** : `externalUrl` si la méthode est externe ; sinon la page jobup elle-même, puisque la candidature se fait par le formulaire jobup ;
  - **type de candidature** : `external` (chez l'employeur) ou `jobup` (formulaire jobup) ;
  - **texte complet de l'annonce**, s'il est présent dans le même bloc JSON. C'est la même requête, et il servira à l'IA en 0.4.
- **En cas d'échec :** au plus 3 essais par offre, espacés d'un jour au moins. Une offre expirée sur jobup est marquée `expired`.

## 3. Base (migration 0005)

```
offers  + apply_url TEXT?, apply_kind (external|jobup)?, description TEXT?,
          enrich_status (pending|ok|expired|failed|skipped) DEFAULT 'pending',
          enrich_attempts INT DEFAULT 0, enriched_at?
```

Les offres Indeed sont marquées `skipped` dès la migration.

## 4. Interface

Dans le panneau de détail d'une offre :
- **« Postuler chez l'employeur »**, bouton violet, quand le lien est externe ;
- **« Postuler sur jobup »** quand la candidature passe par le formulaire jobup ;
- **« Voir sur Indeed »** pour Indeed, sans changement ;
- le **texte complet** de l'annonce remplace l'extrait quand il est connu.

## 5. Tests

- **Analyseur de page** : sur 2 pages jobup enregistrées et réduites au bloc JSON utile, une candidature externe et une par le formulaire jobup. Ce sont des pages publiques : aucune donnée personnelle.
- **Tâche** : rythme respecté (horloge simulée), plafond de 30, essais limités, offres Indeed et écartées ignorées, aucune requête hors de `www.jobup.ch/*/emplois/detail/`.

## Points à valider

1. **Lecture des pages jobup**, risque des conditions d'utilisation accepté (§1).
2. **Rythme** : 1 requête toutes les 10 s, 30 au plus par exécution (§2).
3. **Seulement les offres à examiner**, pas les écartées (§2).
4. **Texte complet de l'annonce** récupéré dans la même requête, pour l'IA en 0.4 (§2).
