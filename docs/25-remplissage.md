# 25 — Remplir le formulaire de l'employeur (version 0.18.0)

> Statut : **validé** le 2026-10-07, avec la consigne de garder l'interface simple. livré : PR a (PDF, champs pour les formulaires, fiche à copier).
> Retours d'usage du 2026-10-07 : après la comparaison avec Jobright, reprendre l'idée du remplissage des formulaires de candidature, sans envoi automatique.

## 1. Le constat

- Une fois la lettre et le CV prêts, « Postuler » ouvre le formulaire de l'employeur (son site ou son outil de recrutement). Là, tout se ressaisit à la main : nom, adresse, téléphone, e-mail, lien LinkedIn, CV et lettre à joindre, parfois des questions (« Pourquoi nous ? », prétentions salariales, date de disponibilité).
- C'est le moment le plus répétitif de la candidature. C'est aussi là qu'on abandonne.

## 2. Le principe

- **job-bot remplit, tu vérifies, tu envoies.** La plateforme n'envoie **jamais** une candidature à ta place : le bouton « Envoyer » du site reste le tien.
- **Pas d'envoi en masse** : une candidature à la fois, celle que tu as préparée.
- Rien ne se fait sans ton clic, ni sur un site que tu n'as pas ouvert toi-même.

## 3. Comment : une extension de navigateur

Un site d'employeur ne laisse pas une autre page remplir ses champs. Il faut donc une **petite extension** (Chrome, Edge, Brave ; Firefox ensuite), installée une fois et reliée à ta plateforme.

### 3.1 Sur le formulaire

1. Tu ouvres le formulaire depuis « Postuler » (ou directement sur le site).
2. Tu cliques sur l'icône **job-bot** dans la barre du navigateur.
3. Un petit panneau s'ouvre :
   - **la candidature reconnue** (« SRE chez Exemple SA », d'après l'adresse de la page ; sinon, tu choisis parmi tes offres en préparation) ;
   - un bouton **« Remplir le formulaire »**.
4. Les champs reconnus se remplissent et sont **encadrés en violet** ; ceux qu'il n'a pas su remplir restent en **orange**, à faire toi-même.
5. Le panneau liste ce qui a été rempli et ce qui reste, avec **« Copier »** à côté de chaque valeur pour les champs non reconnus.
6. Après l'envoi sur le site : **« J'ai envoyé »** dans le panneau crée la candidature dans le Suivi (comme « Marquer comme envoyée »), avec l'adresse du formulaire comme lien de candidature pour l'ORP.

### 3.2 Ce qui est rempli

| Champ du formulaire | Valeur |
|---|---|
| Prénom, nom, civilité | tes coordonnées (Profil) |
| Adresse, NPA, localité, pays | tes coordonnées |
| Téléphone, e-mail | tes coordonnées |
| LinkedIn, site personnel | nouveau champ dans tes coordonnées |
| CV, lettre (pièces jointes) | ceux préparés pour cette offre, en **PDF** (§3.4) |
| « Lettre de motivation » en texte | le texte de ta lettre |
| Disponibilité, prétentions salariales, permis, taux | nouveaux champs dans « Ce que je cherche » (facultatifs) |
| Questions libres (« Pourquoi nous ? ») | proposition de l'IA, **à relire**, sur demande (§3.3) |

Les cases à cocher de consentement (« J'accepte la politique de confidentialité ») ne sont **jamais** cochées à ta place.

### 3.3 Les questions libres

- Bouton **« Proposer une réponse »** à côté d'une question reconnue comme libre.
- L'IA reçoit la question, l'offre, ta lettre et tes blocs de profil, **jamais tes coordonnées** ; elle répond dans la langue de la question, sans expérience inventée.
- Claude Haiku, environ **0,005 $ par réponse**, dans le plafond mensuel (`purpose = form`). La réponse est insérée dans le champ ; tu la relis avant d'envoyer.

### 3.4 Le PDF

Les recruteurs et leurs outils préfèrent le PDF. La plateforme produit aujourd'hui des fichiers Word : elle produira aussi le **PDF de la lettre et du CV**, téléchargeable dans la préparation (utile même sans extension).

### 3.5 Reconnaître les champs

- D'après l'étiquette, le nom, l'attribut d'autocomplétion et le texte d'aide du champ, en **français, allemand et anglais** (« Vorname », « NPA / PLZ », « Lebenslauf »…).
- Réglages connus pour les outils de recrutement fréquents en Suisse, vérifiés un par un avant d'être annoncés : Greenhouse, Lever, SmartRecruiters, Personio, Workday, SAP SuccessFactors, Abacus Umantis, Recruitee, Join.
- Les formulaires en plusieurs étapes se remplissent étape par étape (un clic par page).
- Formulaires qui exigent un compte (Workday, SuccessFactors) : tu crées le compte et tu te connectes toi-même ; l'extension remplit ensuite.

## 4. Sécurité et confidentialité

- **Lien avec ta plateforme** : dans Réglages › « Extension du navigateur », un **jeton de connexion** à coller une fois dans l'extension ; révocable, limité à ce dont l'extension a besoin (lire la candidature et ses documents, enregistrer « J'ai envoyé », demander une réponse).
- **Permissions minimales** : l'extension n'agit que sur l'onglet où tu cliques sur son icône (aucune lecture des autres sites ni de ton historique).
- Tes coordonnées vont de ta plateforme **au formulaire seulement** ; aucune n'est envoyée à l'IA ni à un tiers.
- **Code dans le dépôt** (`extension/`), installable en mode développeur ; publication sur le Chrome Web Store seulement si tu le souhaites plus tard.

## 5. Sans extension

Pour un formulaire rebelle ou un ordinateur sans l'extension : dans la préparation, une **fiche « Pour le formulaire »** avec chaque valeur et son bouton « Copier » (comme « Copier pour Job-Room »), et le CV et la lettre en PDF.

## 6. Base (migration 0035)

```
coordonnées         + linkedin_url?, website?
ce que je cherche   + available_from?, salary_expectation?, work_permit?
extension_tokens    id, name, token_hash, created_at, last_used_at?, revoked_at?
```

## 7. Livraison en deux PR

| PR | Contenu | De ton côté |
|---|---|---|
| **0.18.0-a** | PDF de la lettre et du CV, nouveaux champs (LinkedIn, disponibilité, prétentions, permis), fiche « Pour le formulaire », jetons de l'extension | compléter les nouveaux champs |
| **0.18.0-b** | Extension : candidature reconnue, remplissage, pièces jointes, « J'ai envoyé », réponses de l'IA aux questions libres | installer l'extension, coller le jeton |

## Points à valider

1. **Remplir sans jamais envoyer**, une candidature à la fois (§2).
2. **Extension de navigateur** (Chrome et dérivés d'abord), reliée par un jeton révocable, active seulement sur l'onglet où tu cliques (§3, §4).
3. **Champs remplis** (§3.2), cases de consentement jamais cochées, nouveaux champs : LinkedIn, disponibilité, prétentions, permis.
4. **Réponses de l'IA aux questions libres**, à la demande, environ 0,005 $ chacune (§3.3).
5. **PDF** de la lettre et du CV (§3.4) et **fiche à copier** sans extension (§5).
6. **Deux PR** (§7).

## Écarts avec la PR a

- **Interface légère** (consigne du 2026-10-07) : rien de nouveau n'est déplié par défaut.
- **Nouveaux champs** regroupés dans **Profil › Mes coordonnées**, section repliée « Pour les formulaires en ligne · facultatif » : LinkedIn, site personnel, disponibilité, prétentions salariales, permis de travail (suggestions : nationalité suisse, permis C, B, G). Ils ne vont pas dans « Ce que je cherche », qui reste réservé au filtre des offres. Une adresse saisie sans `https://` est complétée.
- **LinkedIn sur le CV** : ajouté aux coordonnées du CV (Word et PDF), sous forme courte (`linkedin.com/in/…`).
- **PDF** : produit par la plateforme (Helvetica, même mise en page que le Word). « Télécharger en PDF » télécharge désormais le fichier directement, sans passer par la fenêtre d'impression ; dans la barre de la préparation, « Lettre (PDF) » et « CV (PDF) » remplacent les liens Word (le Word reste dans « Cette version »).
- **Fiche pour le formulaire** : un lien dans la barre de la préparation l'ouvre sous la barre ; valeurs remplies seulement (prénom et nom séparés, pays « Suisse »), corps de la lettre en texte, liens vers les PDF, et « compléter dans Profil » s'il manque nom, e-mail ou téléphone.
- **Jetons de l'extension** : reportés à la PR b, avec l'extension qui s'en sert (un réglage sans usage alourdirait les Réglages). Pas de migration dans cette PR.
- Nouvelle dépendance : `reportlab` (licence BSD).
