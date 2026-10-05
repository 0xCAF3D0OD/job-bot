# 08 — Candidatures : lettre, CV adapté et suivi (version 0.5.0)

> Statut : **validé** le 2026-10-05. PR a (tri, suivi, coordonnées, relance) livrée ; PR b et c à venir.
> S'appuie sur [01-cadrage.md](01-cadrage.md) §2, §3 et §5 (`drafts`, `applications`), sur le profil en blocs (0.3) et la note IA (0.4). L'export ORP reste en 0.6, mais la 0.5 enregistre déjà tout ce dont il aura besoin.

## 1. Objectif

Passer d'une offre bien notée à une candidature envoyée **en quelques minutes**, sans rien envoyer à ta place :

1. Sur une offre, tu cliques **« Préparer ma candidature »**.
2. L'IA rédige une **lettre de motivation** à partir de tes blocs, et propose un **CV adapté** à l'offre.
3. Tu relis, tu corriges, tu demandes une autre version si besoin, puis tu télécharges les documents (PDF ou Word).
4. Tu postules toi-même (bouton « Postuler chez l'employeur »), puis tu cliques **« Marquer comme envoyée »**.
5. La candidature apparaît dans la nouvelle page **Candidatures**, avec son suivi (relance, entretien, refus…) et tout ce que demande le formulaire ORP.

## 2. Actions sur une offre (tri manuel)

Le détail d'une offre reçoit quatre boutons, qui correspondent aux statuts déjà prévus en base :

| Bouton | Statut | Effet |
|---|---|---|
| Préparer ma candidature | `preparing` | ouvre la préparation (§3) |
| Plus tard | `later` | l'offre quitte « À examiner » ; un onglet « Plus tard » la garde |
| Ignorer | `ignored` | l'offre quitte « À examiner » ; récupérable dans « Toutes » |
| Marquer comme envoyée | `applied` | ouvre le formulaire de suivi (§5) |

Ces statuts posés à la main ne sont jamais modifiés par le filtre (règle de la 0.3). La barre de filtres gagne les onglets **Plus tard** et **En cours** (préparées et envoyées).

## 3. Lettre de motivation

**Ce que reçoit l'IA :** tes blocs actifs (y compris le bloc « Ton » s'il existe), l'offre (texte complet si jobup, sinon l'extrait), et la note avec ses points forts et ses manques.

**Ce qu'elle ne reçoit jamais :** tes coordonnées. La lettre est **assemblée par la plateforme** : en-tête avec ton nom, ton adresse, ton téléphone et ton e-mail (saisis une fois dans Réglages → « Mes coordonnées », stockés en local), lieu et date, destinataire, objet. L'IA n'écrit que **l'objet et le corps**.

**Règles imposées à l'IA :**
- seulement des faits présents dans tes blocs ; chaque paragraphe indique les blocs qui le justifient (affichés sous la lettre, pour vérifier) ;
- 250 à 350 mots, quatre paragraphes au plus, sans formules creuses (« dynamique et motivé ») ni flatterie générique ;
- adaptée à l'offre : elle reprend les 2 ou 3 exigences principales et montre comment ton parcours y répond ; un manque important n'est pas caché mais présenté honnêtement (par exemple : « je n'ai pas encore d'expérience VMware, mais… »), seulement s'il est utile ;
- **langue** : celle de l'annonce par défaut (français, anglais ou allemand), modifiable ;
- registre suisse romand pour le français (vouvoiement, « Madame, Monsieur », formule de politesse standard).

**Relecture :** la lettre s'ouvre dans un éditeur. Tu peux modifier le texte, ou demander une nouvelle version avec une consigne (« plus court », « insiste sur Kubernetes », « en anglais »). Chaque version est gardée. La dernière que tu as modifiée est celle qui compte.

## 4. CV adapté

Tu as déjà un CV (Word). L'objectif n'est pas de le remplacer, mais d'en produire une **version ciblée d'une page** pour chaque offre, à partir de tes blocs :

- l'IA choisit et **ordonne** les blocs les plus pertinents pour l'offre (expériences, compétences, formation), et rédige un **résumé de profil** de 2 ou 3 lignes adapté au poste ;
- elle ne réécrit **pas** le contenu de tes expériences : elle se contente de sélectionner, d'ordonner, et de mettre en avant les mots-clés de l'offre que tes blocs contiennent déjà ;
- la mise en page est fixe, sobre, d'une page A4 : coordonnées, résumé, expériences, compétences, formation, langues ;
- tu peux cocher ou décocher des blocs et changer l'ordre avant de télécharger.

## 5. Suivi des candidatures (page « Candidatures »)

**« Marquer comme envoyée »** ouvre un formulaire pré-rempli. Ces champs servent directement à l'export ORP de la 0.6 :

| Champ | Pré-rempli avec |
|---|---|
| Date d'envoi | aujourd'hui |
| Entreprise, poste, lieu | l'offre |
| Adresse de l'entreprise, personne de contact, téléphone | extraits du texte de l'annonce par l'IA pendant la préparation, si présents |
| Taux | l'offre (plein temps ou temps partiel) |
| Mode | électronique (ou écrit, téléphone, en personne) |
| Assignée par l'ORP | non |

Le mode « électronique » est l'option par défaut, puisqu'on postule en ligne.

**La page Candidatures** liste les candidatures, les plus récentes d'abord, avec :
- le statut : en attente, relancée, entretien, refus (avec un motif facultatif), engagement, sans réponse ;
- un bouton pour changer le statut et noter une date d'entretien ;
- les documents envoyés (lettre et CV), retéléchargeables ;
- un **compteur du mois** par rapport à ton objectif ORP (Réglages : 20 par mois), par exemple « 7 / 20 en octobre ».

**Relance :** une notification ntfy après **10 jours** sans réponse (« Tu as postulé chez Acme le 3 octobre : relancer ? »), une seule fois par candidature.

## 6. Modèle et coût

- **Même modèle** que la note (Claude Opus 5), avec un effort `medium` pour la rédaction, qui demande plus de soin que la notation.
- **Estimation** : lettre ≈ 0,06 $, CV adapté ≈ 0,03 $, soit moins de 0,10 $ par candidature préparée. Avec 20 candidatures par mois, compte environ 2 $ par mois en plus.
- Toujours dans le plafond mensuel des Réglages, et enregistré dans `llm_calls` (`purpose = letter` ou `cv`).

## 7. Base (migration 0010)

```
drafts        id, offer_id, kind (letter|cv), version, language, content JSONB,
              source_chunk_ids[], instruction?, model?, created_at, edited_at?
              -- lettre : {subject, paragraphs[{text, chunk_ids}]} ; CV : {summary, sections[{kind, chunk_ids}]}
applications  id, offer_id UNIQUE, sent_at, method (electronique|ecrit|telephone|personnel),
              assigned_by_orp, company, company_address?, contact_name?, contact_phone?,
              job_title, rate_text?, status (en_attente|relancee|entretien|refus|engagement|sans_reponse),
              status_reason?, status_at?, interview_at?, letter_draft_id?, cv_draft_id?,
              reminded_at?, orp_month (AAAA-MM)
settings      + coordonnées : identity_name, identity_street, identity_postcode, identity_city, identity_phone, identity_email
```

## 8. Documents produits

- **PDF :** la lettre et le CV sont rendus en page A4 dans l'interface, et le bouton « Télécharger en PDF » passe par l'impression du navigateur (« Enregistrer en PDF »). Aucune dépendance lourde côté serveur.
- **Word (.docx) :** généré par le backend (python-docx, déjà utilisé), pour retoucher dans Word si besoin.
- Les documents ne sont pas stockés en fichiers : ils sont régénérés à la demande à partir du brouillon enregistré.

## 9. Livraison en trois PR

| PR | Contenu | Prérequis de ton côté |
|---|---|---|
| **0.5.0-a** | Actions sur les offres, page Candidatures et suivi, coordonnées, relance à 10 jours | aucun |
| **0.5.0-b** | Lettre de motivation (rédaction, versions, PDF, Word) | coordonnées saisies |
| **0.5.0-c** | CV adapté (sélection, ordre, résumé, PDF, Word) | idem |

La PR a sert tout de suite : tu peux suivre les candidatures que tu envoies déjà à la main.

## Points à valider

1. **L'IA n'écrit que l'objet et le corps de la lettre** ; tes coordonnées sont ajoutées par la plateforme et ne partent jamais vers l'IA (§3).
2. **Langue de la lettre** = celle de l'annonce par défaut (§3).
3. **CV adapté par sélection et ordre de tes blocs**, sans réécriture de tes expériences (§4).
4. **Mode « électronique » par défaut** pour l'ORP (§5).
5. **Relance proposée après 10 jours** sans réponse (§5).
6. **Opus 5 en effort `medium`** pour la rédaction, environ 0,10 $ par candidature (§6).
7. **PDF par l'impression du navigateur, plus un export Word** (§8).
8. **Trois PR**, le suivi d'abord (§9).

## Écarts avec la PR a

- **Migration 0010** : seule la table `applications` est créée ; `drafts` et les colonnes `letter_draft_id`, `cv_draft_id` arriveront avec la PR b (migration 0011). La table `applications` garde en plus `location`, utile à l'export ORP.
- **Pré-remplissage** : adresse, contact et téléphone de l'entreprise restent vides tant que la préparation par l'IA (PR b) n'existe pas ; tu peux les saisir à la main.
- **Ajout manuel** : la page Candidatures permet aussi d'enregistrer une candidature envoyée hors plateforme (sans offre liée).
- **Suppression** : supprimer une candidature remet l'offre « en préparation ».
- **Relance** : la tâche `reminders` passe une fois par jour vers 9 h ; sans ntfy configuré, aucune candidature n'est marquée comme relancée.
