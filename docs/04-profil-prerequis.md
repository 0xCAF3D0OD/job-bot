# 04 — Profil, prérequis et filtre (version 0.3.0)

> Statut : **validé le 2026-10-05**. Parties a (prérequis, filtre, réglages) et b (documents, blocs) livrées.
> S'appuie sur [01-cadrage.md](01-cadrage.md) §3, §4 et §5. Interface dans le style de la maquette Hirace (PR #9).

## 1. Objectif

À la fin de la 0.3, la page Offres ne montre plus que les offres qui respectent tes prérequis. Les autres restent consultables, avec la raison de leur exclusion. Tu as aussi déposé tes documents et rédigé tes blocs de profil, qui serviront à l'IA en 0.4.

Pas d'IA dans cette version : tout est fait par règles, ce qui est gratuit, prévisible et expliqué.

## 2. Ce que les alertes contiennent vraiment

Le filtre ne peut juger que ce que les e-mails fournissent. Sur tes 204 offres :

| Information | Disponible ? | Conséquence |
|---|---|---|
| Titre, entreprise, lieu | presque toujours | filtre fiable |
| Taux d'activité | quand il est écrit dans le titre (environ 1 offre sur 5) | appliqué seulement s'il est connu |
| Extrait de l'annonce | Indeed oui, jobup non | les mots-clés ne sont cherchés que là où il y a du texte |
| Type de contrat, langues, salaire | jamais en champ, parfois dans le titre ou l'extrait | détection par mots-clés, prudente |

**Règle d'or : une information inconnue n'exclut jamais une offre.** Seule une information présente et contraire à un prérequis l'écarte.

## 3. Prérequis (page « Prérequis »)

Un formulaire, enregistré dans `criteria`. Chaque règle est facultative :

| Règle | Saisie | Une offre est écartée si… |
|---|---|---|
| **Lieux acceptés** | liste de communes et/ou de cantons (`Lausanne`, `VD`, `GE`…), plus une case « télétravail complet accepté » | son lieu est connu et ne correspond à aucune commune ni aucun canton de la liste |
| **Taux minimum** | un nombre, par exemple 80 | son taux maximum est connu et inférieur (une offre « 60-80 % » passe avec un minimum de 80) |
| **Types exclus** | cases : stage, apprentissage, temporaire, mission courte | le titre ou l'extrait contient un mot-clé du type (`stage`, `intern`, `Praktikum`, `apprenti`, `temporaire`…) |
| **Mots interdits** | liste libre (`vente`, `commercial`…) | le titre en contient un, sans tenir compte des accents ni de la casse |
| **Langues que tu ne parles pas** | cases : allemand, italien, anglais | le titre ou l'extrait exige cette langue (`allemand courant`, `fliessend Deutsch`, `German C1`, `Deutsch zwingend`…) |

Les listes de mots-clés (types, langues) sont dans le code, testées, et affichées sous chaque case pour que tu voies ce qui est cherché.

**Reportés, avec la raison :**
- **Rayon en km** : il faut les coordonnées de chaque commune (répertoire officiel des localités de swisstopo). C'est faisable, mais ce serait un chantier à part. La liste de communes et de cantons couvre le besoin en attendant.
- **Salaire minimum** : aucune alerte ne fournit de salaire aujourd'hui. L'IA le lira dans le texte complet en 0.4.

## 4. Le filtre

- **Quand :** juste après chaque collecte (tâche `filter` enchaînée), et avec le bouton « Refiltrer » de la page Prérequis.
- **Sur quoi :** les offres au statut `new`, `to_review` ou `filtered_out`. Celles que tu as déjà triées toi-même (plus tard, ignorée, en préparation, envoyée) ne sont jamais modifiées.
- **Résultat :** statut `to_review` (à examiner) ou `filtered_out` (écartée), et une ligne dans `evaluations` avec la liste des raisons, par exemple « Lieu : Zürich n'est pas dans tes lieux acceptés » ou « Langue : allemand exigé (« fliessend Deutsch ») ».
- **Idempotent :** refiltrer donne le même résultat tant que les prérequis ne changent pas.

## 5. Documents et blocs de profil (page « Profil »)

**Documents**
- Dépôt de fichiers PDF, DOCX, TXT ou MD, 10 Mo au plus chacun. Ils sont stockés dans `data/documents/`, jamais dans git.
- Le texte est extrait (pypdf, python-docx) et affiché à côté du document, pour t'aider à écrire tes blocs. Pas de reconnaissance de texte pour les PDF scannés en 0.3 : ils sont signalés « texte non lisible ».
- Suppression possible : le fichier, le texte extrait et le lien vers les blocs sont effacés, mais les blocs restent.

**Blocs de profil**
- Formulaire : type (expérience, compétence, formation, préférence, rédhibitoire, ton), titre, contenu, étiquettes, actif ou non, document d'origine (facultatif).
- Bouton « Créer un bloc à partir de ce passage » : tu sélectionnes un passage du texte extrait et il pré-remplit le contenu.
- Les blocs servent à l'IA à partir de la 0.4. En 0.3, ils sont seulement saisis et rangés.

## 6. Réglages (page « Réglages »)

Formulaire sur la table `settings` existante : objectif mensuel ORP, seuil de notification (score sur 100) et plafond mensuel du coût IA (CHF). La fréquence de collecte reste fixe (toutes les 2 h de 7 h à 21 h) : la rendre réglable demanderait de reconstruire le planificateur à chaud, sans grand bénéfice.

## 7. Page Offres

Les onglets deviennent **À examiner | Écartées | Toutes**. Sur une offre écartée, une pastille orange donne la première raison, et le panneau de détail les donne toutes. Le compteur de chaque onglet est affiché.

## 8. Base de données (migration 0004)

```
criteria         id, kind (locations|min_rate|excluded_types|banned_words|unspoken_languages),
                 value JSONB, updated_at                      -- une ligne par règle
documents        id, filename, content_type, size, sha256 UNIQUE, storage_key,
                 text_status (ok|empty|unreadable), extracted_text, uploaded_at
profile_chunks   id, document_id? → documents (SET NULL), kind, title, content,
                 tags TEXT[], active, created_at, updated_at
evaluations      id, offer_id → offers UNIQUE, filter_passed, filter_reasons JSONB,
                 criteria_hash, evaluated_at                  -- la note IA s'y ajoutera en 0.4
```

**Écart avec le cadrage §5** : `criteria` stocke une règle par ligne avec une valeur JSON, au lieu du triplet `field, operator, value`. Les règles réelles sont des listes (communes, mots), qu'un triplet représentait mal.

## 9. API

| Route | Rôle |
|---|---|
| `GET /api/criteria`, `PUT /api/criteria` | lire et enregistrer tous les prérequis d'un coup |
| `POST /api/filter` | refiltrer (mise en file de la tâche `filter`) |
| `GET /api/settings`, `PUT /api/settings` | réglages |
| `GET /api/documents`, `POST /api/documents` (envoi de fichier), `DELETE /api/documents/{id}` | documents |
| `GET /api/documents/{id}/text` | texte extrait |
| `GET /api/profile-chunks`, `POST`, `PUT /{id}`, `DELETE /{id}` | blocs de profil |
| `GET /api/offers?status=to_review\|filtered_out\|all` | filtre par statut, avec les raisons |

## 10. Tests

- **Règles** (`core/filter.py`, pur) : chaque règle seule, l'information inconnue qui laisse passer, les accents et la casse, les combinaisons. Il y aura aussi un jeu de vrais titres tirés de tes offres (« fliessend Deutsch », « Internship », « 60-80 % »…).
- **Filtre** : enchaîné après la collecte, idempotent, sans toucher aux statuts que tu as posés.
- **Documents** : envoi, extraction (PDF, DOCX, PDF sans texte), refus d'un type ou d'une taille non acceptés, suppression.
- **Interface** : formulaires Prérequis, Réglages et Profil, et onglets des Offres.

## 11. Livraison en deux PR

| PR | Contenu |
|---|---|
| **0.3.0-a** | Prérequis, filtre, Réglages, onglets des Offres |
| **0.3.0-b** | Documents, extraction du texte, blocs de profil |

La PR a te sert tout de suite (tri des 204 offres). La PR b prépare la 0.4.

## Points à valider

1. **Une information inconnue n'exclut jamais** (§2).
2. **Lieux par communes et cantons**, avec le rayon en km reporté (§3).
3. **Salaire reporté à la 0.4** (§3).
4. **Détection par mots-clés** pour les types de contrat et les langues, avec des listes visibles dans le formulaire (§3).
5. **Les offres que tu as triées toi-même ne sont jamais refiltrées** (§4).
6. **Documents** : PDF, DOCX, TXT et MD, 10 Mo au plus, sans reconnaissance de texte pour les scans (§5).
7. **Fréquence de collecte non réglable** (§6).
8. **Deux PR**, les prérequis d'abord (§11).

## Écarts à la livraison (partie a)

- **Télétravail complet** : la règle ne s'applique que si des lieux sont saisis. Sans lieux, aucune règle de lieu, sinon trois offres en télétravail étaient écartées alors qu'aucun prérequis n'était saisi.
- **Canton d'une ville sans canton** (jobup) : appris des autres offres qui l'indiquent (« Prilly, VD »). Si le canton reste inconnu et que tu acceptes des cantons, l'offre n'est pas écartée.
- **Enregistrer les prérequis relance le filtre** automatiquement : un seul bouton « Enregistrer et refiltrer ».
- **Onglet « À examiner »** : il contient aussi les offres pas encore passées par le filtre (statut `new`), pour qu'aucune offre ne soit cachée.

## Écarts à la livraison (partie b)

- **Type de document** vérifié sur le contenu (signature PDF, archive Word), pas seulement sur l'extension.
- **Doublons** : un même fichier (même contenu) ne peut être déposé qu'une fois.
- **Bouton « Ouvrir »** : affiche le fichier d'origine, en plus du texte extrait.
- **Journalisation** : seuls l'identifiant et la taille d'un document sont journalisés, jamais son nom ni son contenu.
