# 140 — « Se connecter avec jobA1 » depuis Get'emAll

> Statut : **validé** par Kevin le 2026-11-05 (plan de l'API de Get'emAll, points 1 à 9). Ce document décrit la
> part de jobA1. Le plan entier est dans le dépôt Get'emAll, `docs/api-plan.md`.
> Lot 2 : la base, l'échange et les routes de lecture sont livrés ; la page « Autoriser Get'emAll », la ligne
> « Connexions » des Réglages et la page Confidentialité attendent les maquettes de Kevin.

## 1. Pourquoi

Get'emAll (getthemall.ch) est l'app d'entraînement aux entretiens. Elle a sa propre base et ne parle à jobA1 que par
l'API. Elle a besoin de deux choses : savoir que la personne a un compte jobA1, et lire son suivi (profil, ORP du
mois, candidatures) pour proposer de s'entraîner à l'entretien qui vient.

Le schéma retenu est le « code d'autorisation » d'OAuth 2 avec PKCE, sans OpenID Connect. Un mot de passe jobA1 ne
passe jamais par Get'emAll.

## 2. Le parcours

1. L'app Get'emAll ouvre la page « Autoriser Get'emAll » de jobA1 avec une adresse de retour, un `state` et un
   `code_challenge` (PKCE, S256 seulement).
2. La personne, connectée, autorise (avec ou sans la case ORP, §3). La page appelle
   `POST /api/partenaires/getemall/autorisation` et envoie le navigateur à l'adresse rendue, avec `code` et `state`.
3. Le serveur de Get'emAll appelle `POST /api/partenaires/getemall/echange` avec son secret client, le code, le
   `code_verifier` et l'adresse de retour.
4. jobA1 brûle le code, vérifie qu'il n'a pas expiré, que l'adresse est la même et que le PKCE est juste, puis rend :
   - `subject` : un identifiant propre à Get'emAll, tiré au hasard (192 bits), le même d'une autorisation à l'autre,
     jamais l'id du compte ;
   - `token` : un jeton `jbg_…` (256 bits) qui ne sert qu'à lire le suivi ;
   - `orp` : la case cochée ou non.

| Règle | Valeur |
| --- | --- |
| Code | `jbc_…`, 128 bits, **60 s**, une seule lecture, empreinte seule en base |
| Lecture du code | `take_partner_code` le brûle dans le même geste : un PKCE faux ou un code expiré le brûle aussi |
| Adresses de retour | `JOBBOT_GETEMALL_REDIRECT_URIS`, fixées par environnement, comparées telles quelles |
| Secret client | `JOBBOT_GETEMALL_CLIENT_SECRET` (ou `_FILE`), comparé en temps constant |
| Essais | un mauvais secret compte, par adresse IP, avec l'attente croissante de la connexion (A-3). Un code faux ne compte pas : il vient d'une personne par le serveur de Get'emAll, et bloquerait tout le monde |
| Testeurs | seuls les comptes marqués `jobbot getemall-tester <identifiant>` autorisent ; retirer la marque coupe aussi la lecture |
| Sans configuration | sans secret ni adresse de retour, l'autorisation et l'échange répondent 404, la lecture 401 |

Adresses de retour, par environnement :

| jobA1 | `JOBBOT_GETEMALL_REDIRECT_URIS` |
| --- | --- |
| production | `["https://getthemall.ch/connexion","getthemall://connexion"]` |
| staging | `["https://staging.getthemall.ch/connexion"]` |
| poste de développement | `["http://localhost:8081/connexion"]` |

Une nouvelle autorisation garde le `subject` et remplace le jeton : l'ancien ne sert plus.

## 3. Ce que Get'emAll lit

Deux routes en lecture, avec le jeton (`Authorization: Bearer jbg_…`), sous la RLS du compte, servies avec
`Cache-Control: no-store` :

| Route | Rend |
| --- | --- |
| `GET /api/partenaires/getemall/suivi` | `profile` (étapes faites sur les 5 premiers pas de docs/128, pourcentage, prochaine étape) ; `orp` (mois, recherches faites, objectif, date de remise) **seulement si la case ORP est cochée** ; `applications` (id, poste, entreprise, statut, date d'entretien), les 50 dernières |
| `GET /api/partenaires/getemall/candidatures/{id}/offre` | titre, entreprise, texte de l'annonce passé par `llm/redact.py`, puis sans les noms des contacts notés pour cette candidature ou cette offre |

**« Profil complété ».** jobA1 n'a pas de pourcentage de profil. Get'emAll reçoit les premiers pas (docs/128) :
étapes faites sur 5, et la prochaine (`profile`, `alerts`, `keep`, `prepare`, `sent`) comme « ce qui manque ». La
lecture ne garde rien : elle ne change pas ce que la personne verra dans jobA1.

**ORP.** Les compteurs disent qu'une personne est suivie par l'ORP (nLPD art. 5 let. c ch. 5). La page de
consentement a une case à part. Sans elle, le champ `orp` n'est pas rendu du tout. Le mois est celui de la page ORP
(le précédent tant qu'il n'est pas remis).

**Jamais** : nom, coordonnées, numéro AVS, id du compte jobA1, noms et coordonnées des contacts, CV, lettres, lignes
ORP. Un statut de candidature passe tel quel ; Get'emAll le ramène à ses trois pastilles.

## 4. La fin de la liaison

| Qui | Comment | Effet |
| --- | --- | --- |
| La personne, dans jobA1 | Réglages, Connexions, « Retirer » (`DELETE /api/partenaires/getemall`) | jeton révoqué ; Get'emAll reçoit 401 et propose de se reconnecter |
| La personne, dans Get'emAll | « Supprimer mes données » : Get'emAll appelle `DELETE /api/partenaires/getemall/lien` | idem |
| L'exploitant | suspension du compte, ou `jobbot getemall-tester <identifiant> --retirer` | idem |
| La personne | suppression du compte jobA1 | lignes effacées (clé étrangère en cascade) |

Le `subject` reste après une révocation : une reconnexion retrouve le même compte Get'emAll.

## 5. La base (migration 0074)

- `users.getemall_tester` : faux par défaut.
- `partner_codes` : compte, app, empreinte du code, `code_challenge`, adresse de retour, case ORP, création,
  expiration, lecture. Un code lu ou expiré est effacé à l'échange ou à l'autorisation suivante du compte.
- `partner_links` : compte, app, `subject`, empreinte du jeton, case ORP, création, autorisation, dernière lecture,
  révocation. Une ligne par compte et par app.
- Deux tables personnelles (`account_isolation`), exportées sans les empreintes, effacées avec le compte.
- `take_partner_code(hash)` et `account_of_partner_token(hash)` : fonctions `security definer` qui ne rendent que ce
  qu'il faut, comme pour l'extension (0053, 0056). Elles ignorent un compte suspendu ou qui n'est plus testeur.
- Pas d'unicité globale sur `subject` (migration 0055) : 192 bits au hasard suffisent.

## 6. Les tests (`tests/test_getemall.py`)

Code brûlé après une lecture ; expiré après 60 s ; PKCE faux refusé et code brûlé ; PKCE `plain` refusé ; adresse de
retour hors liste refusée, à l'autorisation comme à l'échange ; secret faux refusé puis ralenti ; testeurs seuls ;
champ ORP absent sans la case ; texte de l'offre sans e-mail, téléphone, lien ni nom de contact ; second compte en
404 (C-4) ; « Retirer » puis reconnexion avec le même `subject` ; révocation par Get'emAll ; sans jeton, 401 ; sans
configuration, 404 ; export sans empreinte et effacement avec le compte.

## 7. Ce qui reste (lot 2, interface)

- La page « Autoriser Get'emAll » (case ORP à part, texte clair sur la sensibilité des données ORP) et la ligne
  « Connexions » des Réglages : d'après les maquettes de Kevin (CLAUDE.md : pas d'écran sans maquette).
- Get'emAll sur la page Confidentialité (I-4, V-5) : avec la page « Autoriser », avant toute configuration en
  production. Tant que le secret n'est pas posé, rien ne part.
- Une limite des lectures en rafale par jeton (X-8), comme pour le reste de l'API (écart connu).
