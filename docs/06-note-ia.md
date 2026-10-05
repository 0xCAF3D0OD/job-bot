# 06 — Note IA, résumé des offres et filtres toujours visibles (version 0.4.0)

> Statut : **à valider**. Aucun code avant accord.
> S'appuie sur [01-cadrage.md](01-cadrage.md) §2, §3 et §10, sur le profil (0.3) et le texte complet jobup (0.3.1).
> Demandes de Kevin (2026-10-05) : les principaux filtres toujours à disposition, et pour chaque offre un résumé de 2-3 lignes (ce qu'elle demande, ce qu'elle offre, le poste).

## 1. Objectif

Pour chaque offre à examiner, l'IA produit :

- un **résumé en trois lignes courtes**, affiché sur la carte de l'offre :
  - **Poste** : ce qu'on y fait ;
  - **Demande** : expérience, diplômes, compétences et langues exigés ;
  - **Offre** : taux, salaire, contrat, télétravail et avantages, quand l'annonce les donne ;
- une **note de 0 à 100**, qui mesure la correspondance avec ton profil, avec 2 à 4 **points forts** et 2 à 4 **manques**, chacun relié aux blocs de profil qui le justifient.

La page Offres est réorganisée : une **barre de filtres toujours visible** à gauche, et des cartes qui montrent la note et le résumé.

Hors périmètre : la lettre et le CV (0.5), l'export ORP (0.6).

## 2. Ce que l'IA reçoit, et ce qu'elle n'a pas le droit de faire

| Entrée | Source |
|---|---|
| Consignes et format de réponse | fixes, versionnés dans le code (`prompts/score-v1.md`) |
| Ton profil | **blocs actifs uniquement** (cadrage §3), avec leur identifiant |
| L'offre | titre, entreprise, lieu, taux, type d'emploi, texte complet (jobup) ou extrait (Indeed) |

Règles :

- **Rien n'est affirmé sur toi qui ne soit dans un bloc actif.** Chaque point fort cite l'identifiant du bloc qui le justifie, et un point fort sans bloc valide est rejeté à la réception.
- **Le texte de l'offre est une donnée, jamais une consigne.** Il est encadré et présenté comme tel. L'IA n'a aucun outil et ne peut que répondre au format imposé. Une annonce qui contiendrait « ignore tes instructions » n'a donc aucun effet possible au-delà d'une note faussée.
- **Résumé honnête :** si l'annonce ne dit rien du salaire ou du télétravail, la ligne « Offre » le dit (« non précisé ») au lieu d'inventer.
- **Offre Indeed sans texte complet :** le résumé se fait sur l'extrait et la carte affiche « résumé partiel ».

**Données envoyées à Anthropic :** tes blocs actifs et le texte des offres partent vers l'API d'Anthropic à chaque note. Rien d'autre : ni tes documents, ni ton adresse e-mail, ni le journal.

## 3. Modèle et coût

Mesures sur ta base : 213 offres à examiner, texte moyen d'environ 420 caractères (le plus long en fait 4 700). Hypothèses par offre :
- environ 3 000 jetons communs à toutes les offres (consignes et profil), mis en cache et donc facturés à 10 % après la première ;
- environ 400 jetons propres à l'offre ;
- environ 400 jetons de réponse, raisonnement compris.

| Modèle | Prix (entrée / sortie, par million de jetons) | Par offre | Rattrapage des 213 offres | Ensuite, 20 offres par jour |
|---|---|---|---|---|
| **Claude Opus 5** (`claude-opus-5`) | 5 $ / 25 $ | ≈ 0,014 $ | ≈ 3 $ (≈ 1,5 $ en lot) | ≈ 8,5 $ par mois |
| Claude Sonnet 5 (`claude-sonnet-5`) | 2 $ / 10 $ | ≈ 0,006 $ | ≈ 1,2 $ (≈ 0,6 $ en lot) | ≈ 3,5 $ par mois |
| Claude Haiku 4.5 (`claude-haiku-4-5`) | 1 $ / 5 $ | ≈ 0,003 $ | ≈ 0,6 $ (≈ 0,3 $ en lot) | ≈ 1,7 $ par mois |

Ce sont des **estimations**. Le coût réel de chaque appel est enregistré (§6), et la première semaine dira s'il faut ajuster.

**Proposition : Claude Opus 5, avec un effort `low`.** C'est le modèle le plus capable de juger finement l'adéquation entre un profil et une annonce. Le résumé et la note restent une tâche simple, donc un effort bas suffit et limite le coût. Avec ton plafond de 10 CHF par mois, la marge est faible les mois chargés. Si tu préfères la marge, Sonnet 5 coûte environ 2,5 fois moins. **C'est à toi de choisir**, et le modèle restera un réglage (`JOBBOT_LLM_MODEL`) pour changer plus tard sans code.

Autres choix :
- **Lot (Batch API, −50 %)** pour le rattrapage des offres existantes et pour toute renotation après un changement de profil. Le résultat arrive en moins de 24 h, en général bien plus vite.
- **Appel direct** pour les nouvelles offres après chaque collecte : quelques secondes, ce qui permet la notification.
- **Réponse au format imposé** (sortie structurée validée par un schéma) : pas d'analyse de texte libre.
- **Cache des consignes et du profil**, qui changent rarement. Toute modification d'un bloc invalide le cache une fois.
- **Repli en cas de refus** (option standard de l'API, activée par défaut) : si une réponse est refusée par les filtres de sécurité, la même demande est rejouée sur un autre modèle. Ça ne devrait pas arriver avec des offres d'emploi, mais ça évite une offre sans note. Le repli n'existe pas pour les lots : une offre refusée en lot est renotée en appel direct.

## 4. Quand l'IA est appelée

| Événement | Ce qui est noté | Mode |
|---|---|---|
| Nouvelles offres retenues par le filtre (après collecte, filtre et lecture jobup) | ces offres | direct |
| Premier lancement de la 0.4 | les 213 offres à examiner | lot |
| Bloc de profil ajouté, modifié ou (dés)activé | toutes les offres à examiner, **sur ton clic** « Renoter » (pas automatique, à cause du coût) | lot |
| Texte complet jobup arrivé après une note faite sur l'extrait | cette offre | direct |

Les offres **écartées ne sont jamais notées**, ce qui évite un coût inutile. Une note est liée à la version des consignes et à une empreinte des blocs actifs. La page Offres signale donc une note « périmée » quand ton profil a changé depuis.

## 5. Budget et notifications

- Chaque appel est enregistré dans `llm_calls` : jetons, coût en dollars et converti en CHF au taux fixé dans les Réglages.
- **Plafond mensuel** (Réglages, 10 CHF par défaut) : une fois atteint, plus aucun appel jusqu'au mois suivant. La page État l'affiche, et une notification te prévient à 80 %.
- **Notification ntfy** pour chaque nouvelle offre dont la note atteint ton seuil (Réglages, 70 par défaut) : titre, entreprise, note et lien vers l'offre dans job-bot. Au plus une notification groupée par collecte.

## 6. Base (migration 0007)

```
evaluations   + score SMALLINT?, summary_role TEXT?, summary_asks TEXT?, summary_offers TEXT?,
                summary_partial BOOL, strengths JSONB, gaps JSONB  -- [{text, chunk_ids[]}]
                + model TEXT?, prompt_version TEXT?, profile_hash TEXT?, scored_at?
llm_calls     id, purpose (score|…), offer_id?, model, batch_id?, input_tokens,
              cache_read_tokens, cache_write_tokens, output_tokens, cost_usd NUMERIC,
              cost_chf NUMERIC, created_at
llm_batches   id, provider_batch_id, status, offer_ids BIGINT[], created_at, ended_at?
settings      + usd_chf_rate (0.80 par défaut)
```

## 7. Page Offres : filtres toujours visibles

**Ordinateur :** trois colonnes.

```
┌──────────────┬──────────────────────────┬────────────────────────────┐
│ FILTRES      │ cartes d'offres          │ détail de l'offre choisie  │
│ (collant)    │                          │                            │
│ Recherche    │ ● Titre          82 /100 │ Postuler chez l'employeur  │
│ Statut       │   Entreprise · Lieu      │ Note, points forts,        │
│ Tri          │   Poste : …              │ manques (avec les blocs),  │
│ Note min.    │   Demande : …            │ texte complet              │
│ Sites        │   Offre : …              │                            │
│ Cantons      │   📍 Lieu • % • site     │                            │
│ Taux min.    │                          │                            │
│ Candidature  │                          │                            │
│ chez l'empl. │                          │                            │
│ [Effacer]    │                          │                            │
└──────────────┴──────────────────────────┴────────────────────────────┘
```

**Mobile :** un bouton « Filtres (3) » ouvre un panneau, et le nombre de filtres actifs reste visible.

Filtres, appliqués par l'API et gardés dans l'adresse de la page (donc partageables et conservés au rechargement) :

| Filtre | Valeurs |
|---|---|
| Recherche | texte libre dans le titre, l'entreprise et le texte |
| Statut | À examiner, Écartées, Toutes (avec les compteurs) |
| Tri | Meilleure note, Récentes, Populaires |
| Note minimale | curseur de 0 à 100 |
| Sites | jobup, Indeed |
| Cantons | ceux présents dans les offres, avec le nombre d'offres |
| Taux minimum | curseur (les offres sans taux restent visibles) |
| Candidature chez l'employeur | oui ou non |

Ces filtres **n'écartent rien** : ils changent seulement ce que tu vois. Les prérequis de la 0.3 restent seuls à décider de ce qui est écarté.

**Carte d'offre :** pastille de l'entreprise, titre, entreprise, date, **note** (pastille violette, ou « à noter » en gris), puis le **résumé en trois lignes** (Poste, Demande, Offre, chacune coupée à une ligne), et la ligne lieu, taux et site.

## 8. Configuration ajoutée

| Variable | Type | Défaut | Rôle |
|---|---|---|---|
| `JOBBOT_ANTHROPIC_API_KEY` | secret | vide | clé API Anthropic (facturation à l'usage, distincte de l'abonnement claude.ai) ; vide : pas de note |
| `JOBBOT_LLM_MODEL` | config | `claude-opus-5` | modèle de notation |
| `JOBBOT_LLM_EFFORT` | config | `low` | effort de raisonnement |
| `JOBBOT_NTFY_URL` | config | `https://ntfy.sh` | serveur ntfy |
| `JOBBOT_NTFY_TOPIC` | secret | vide | sujet ntfy (secret, car quiconque le connaît lit tes notifications) ; vide : pas de notification |

## 9. Tests

- **Sans réseau ni coût :** les appels à l'IA sont simulés en test.
- **Format :** une réponse valide est enregistrée. Une réponse incomplète est rejetée et réessayée une fois, puis l'offre est marquée « note impossible ».
- **Fidélité au profil :** un point fort qui cite un bloc inexistant ou inactif est retiré.
- **Budget :** plafond atteint, plus d'appel ; alerte à 80 %.
- **Lot :** envoi, relève des résultats dans n'importe quel ordre, reprise après redémarrage du worker.
- **Filtres :** chaque filtre seul et combinés, compteurs, adresse de page.
- **Évaluation manuelle avant la mise en service :** tu notes toi-même 15 offres (bonne, moyenne, mauvaise), et je compare avec la note de l'IA. Coût : environ 0,2 $.

## 10. Livraison en trois PR

| PR | Contenu | Prérequis de ton côté |
|---|---|---|
| **0.4.0-a** | Nouvelle page Offres : barre de filtres, cartes, recherche, tri. Sans IA : la note est encore « à noter » et le résumé utilise l'extrait. | aucun |
| **0.4.0-b** | Note et résumé IA, cache, lots, budget, page État | clé API Anthropic dans `.env`, tes blocs de profil saisis |
| **0.4.0-c** | Notifications ntfy | sujet ntfy dans `.env` |

## Points à valider

1. **Modèle** : Claude Opus 5 en effort `low` (≈ 8,5 $ par mois), ou Sonnet 5 (≈ 3,5 $ par mois) (§3).
2. **Résumé en trois lignes** : Poste, Demande, Offre (§1).
3. **Les offres écartées ne sont pas notées** (§4).
4. **Renotation après un changement de profil sur ton clic**, en lot, pas automatiquement (§4).
5. **Filtres de la barre** : la liste du §7 te convient-elle ? Faut-il en ajouter ou en retirer ?
6. **Ordre des PR** : la page Offres d'abord, sans IA (§10).
7. **Évaluation manuelle sur 15 offres** avant la mise en service (§9).
