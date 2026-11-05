# Les règles de sécurité du code pour les données des utilisateurs

> Auteur : Kevin, 2026-11-04. Origine : l'audit de sécurité du 2026-11-04.
> Ce texte dit **comment le code doit traiter les données des utilisateurs**. Il complète `docs/securite.md`, qui dit qui voit quoi et que faire en cas d'incident.
> Toute modification du code qui lit, écrit, envoie, journalise ou efface une donnée d'un utilisateur suit ces règles. Une règle qu'on ne peut pas suivre se signale dans la PR, avec la raison, et va au §14 (« Écarts connus »).

## Les références

Chaque règle cite d'où elle vient. Les références sont reconnues au niveau international, ou sont la loi qui s'applique à jobA1.

| Abréviation | Référence | Ce qu'on en prend |
|---|---|---|
| **ASVS** | OWASP Application Security Verification Standard 5.0, niveau 2 | les exigences vérifiables, chapitre par chapitre |
| **Top 10** | OWASP Top 10:2025 | les familles de failles les plus courantes (A01 à A10) |
| **API** | OWASP API Security Top 10:2023 | les failles propres aux API (API1 à API10) : exposition excessive, consommation sans limite |
| **LLM** | OWASP Top 10 for LLM Applications 2025 | ce qui touche à l'IA (injection d'instructions, fuite de données) |
| **CS** | OWASP Cheat Sheet Series | les réglages précis (stockage des mots de passe, CSP, journaux) |
| **CWE** | MITRE CWE Top 25 | les noms des failles, pour les tests et les revues |
| **NIST 63B** | NIST SP 800-63B-4, *Digital Identity Guidelines* | mots de passe et sessions |
| **SSDF** | NIST SP 800-218, *Secure Software Development Framework* | comment on développe : revue, dépendances, secrets |
| **ISO 27001** | ISO/IEC 27001:2022, annexe A (8.24 cryptographie, 8.25 à 8.28 développement sûr, 8.10 à 8.12 effacement, masquage, fuite) | le cadre de gestion |
| **ISO 29100** | ISO/IEC 29100, principes de protection de la vie privée | minimisation, finalité, transparence |
| **nLPD** | Loi fédérale suisse sur la protection des données (2023) | la loi applicable : art. 6 (principes), 7 (protection dès la conception et par défaut), 8 (sécurité), 16 et 17 (communication à l'étranger), 19 (devoir d'informer), 24 (annonce des violations), 25 (droit d'accès), 28 (portabilité) |
| **RGPD** | Règlement (UE) 2016/679 | pour les utilisateurs dans l'UE : art. 5, 25, 32, 33 (mêmes principes que la nLPD) |

## 1. Les données qu'on traite, et leur niveau

Chaque donnée a un niveau. Le niveau décide des règles qui s'appliquent.

| Niveau | Exemples dans jobA1 | Règles en plus |
|---|---|---|
| **Secret** | mots de passe, jetons de session, d'invitation, d'extension et d'agenda, clés d'API, phrase des sauvegardes, codes d'adresse d'alerte | jamais en clair dans la base, les journaux, git, les tests ou les captures (§3, §6) |
| **Sensible** | CV, lettres, situation de chômage et données ORP, entretiens, notes, e-mails reçus, santé ou permis s'ils apparaissent dans un CV | cloisonnés par compte (§2), jamais dans un journal, minimisés avant l'envoi à l'IA (§7) |
| **Sensible** (voix) | enregistrements vocaux (entraînement aux entretiens, dictée), leurs transcriptions | §10 en plus ; une voix qui sert à reconnaître la personne est une donnée biométrique (nLPD art. 5 let. c ch. 4) : interdit dans jobA1 |
| **Coordonnées** | adresse postale, numéro de téléphone, adresse e-mail, de l'utilisateur et de ses contacts | §9 en plus : jamais en masse, jamais vers un tiers ou dans une notification |
| **Personnelle** | identifiant, nom, offres et candidatures | cloisonnées par compte (§2), exportables et effaçables (§8) |
| **Publique** | entreprises (registre IDE), offres publiées, actualités | tables communes, en lecture pour tous les comptes |

Les données ORP et de recherche d'emploi touchent à l'aide sociale : on les traite comme **sensibles** au sens de la nLPD (art. 5 let. c ch. 5).

**Règle D-1.** Une nouvelle table ou un nouveau champ annonce son niveau dans le commentaire du modèle (`db/models.py`) et dans la PR. *Réf. : ISO 27001 A.5.12 (classification), nLPD art. 7.*

## 2. Le cloisonnement des comptes

**C-1.** Chaque table qui contient des données d'un compte a une règle de sécurité au niveau des lignes (RLS) dans `db/policies.py`. Aucune exception. Le test `tests/test_policies.py` échoue si une table n'a pas de famille. *Réf. : ASVS « Authorization », Top 10 A01, CWE-639.*

**C-2.** Le code ne filtre jamais « à la main » par `user_id` **à la place** de la RLS. Il peut le faire **en plus**, jamais seul. *Réf. : ASVS « Authorization » (contrôle côté serveur, à la couche des données).*

**C-3.** L'API et le worker se connectent avec des rôles sans privilège (`jobbot_app`, `jobbot_worker`) : ni superutilisateur, ni `BYPASSRLS`. L'accès propriétaire est réservé à `migrate`, aux sauvegardes et aux commandes ponctuelles. Un service qui lit du contenu venu d'Internet (e-mails, pages web) n'a jamais l'accès propriétaire. *Réf. : ASVS « Secure Coding and Architecture » (moindre privilège), ISO 27001 A.8.2.*

**C-4.** Une nouvelle route de l'API a son test « second compte » : un autre compte reçoit 404 (et pas 403, pour ne pas révéler que la ressource existe). *Réf. : ASVS « Authorization », CWE-284.*

**C-5.** Un identifiant reçu du client (id d'offre, de document, de candidature) n'est jamais une preuve d'accès. Il est toujours relu en base sous la RLS du compte en cours. *Réf. : Top 10 A01 (IDOR), CWE-639.*

**C-6.** Une tâche de fond agit au nom d'un seul compte à la fois et fixe ce compte avant toute requête. *Réf. : ASVS « Authorization ».*

## 3. Les secrets

**S-1.** Un secret ne vit que dans les variables d'environnement ou les fichiers `_FILE` du serveur. Jamais dans git, une image Docker, un test, une doc ou une capture. *Réf. : SSDF PS.1, ISO 27001 A.8.4, CWE-798.*

**S-2.** Les tests et les docs n'utilisent que des valeurs **factices et reconnaissables comme telles** : `fictif01`, `exemple@example.ch`, `sk-test-…`. Jamais une valeur copiée depuis une vraie installation, même « pour l'exemple ». *Réf. : SSDF PW.1, CWE-540 (voir la PR 491).*

**S-3.** Chaque service ne reçoit que les secrets dont il a besoin. L'API, exposée à Internet, ne détient ni la phrase des sauvegardes ni les mots de passe des boîtes e-mail. *Réf. : ASVS « Configuration », ISO 27001 A.8.2 (moindre privilège).*

**S-4.** La base ne garde des jetons que leur empreinte (SHA-256), et des mots de passe que leur hachage lent (§4). Un jeton se compare en temps constant (`hmac.compare_digest`). *Réf. : ASVS « Cryptography », CWE-208.*

**S-5.** Un code ou un jeton qui donne un droit (adresse d'alerte, invitation, extension, agenda) se tire avec `secrets`, fait au moins 40 bits d'entropie pour un code de routage et 128 bits pour un jeton d'accès, et peut être **révoqué** par l'utilisateur ou l'exploitant. *Réf. : ASVS « Cryptography » et « Self-contained Tokens », CWE-330.*

## 4. Authentification et sessions

**A-1.** Mots de passe hachés avec scrypt, aux paramètres minimaux de l'OWASP : N = 2^17, r = 8, p = 1 (ou Argon2id, m = 19 Mio, t = 2, p = 1). Les anciens hachages sont recalculés à la connexion suivante. *Réf. : CS « Password Storage », ASVS « Authentication », ISO 27001 A.8.5.*

**A-2.** Longueur minimale : 15 caractères quand le mot de passe est le seul facteur. Pas de règle de composition imposée, pas de changement périodique forcé, mais un refus des mots de passe connus comme compromis. *Réf. : NIST 63B-4 §3.1.1.*

**A-3.** Limiter les essais par compte et par adresse IP, avec une attente croissante, sans permettre à un inconnu de bloquer un compte. *Réf. : NIST 63B-4, ASVS « Authentication », CWE-307.*

**A-4.** Cookie de session : `HttpOnly`, `Secure`, `SameSite=Lax` au moins, durée bornée (30 jours prolongés, 90 jours au plus). Nouveau jeton à chaque connexion. Toutes les sessions fermées au changement de mot de passe, à la suspension et sur « Se déconnecter partout ». *Réf. : ASVS « Session Management », CS « Session Management », CWE-384.*

**A-5.** Toute requête qui modifie vérifie l'origine (protection CSRF). *Réf. : ASVS « Web Frontend Security », CWE-352.*

**A-6.** Un message d'erreur de connexion ne dit pas si l'identifiant existe. *Réf. : ASVS « Authentication », CWE-204.*

## 5. Les entrées, les sorties et l'interface

**E-1.** Toute entrée est validée côté serveur par un schéma (Pydantic) : type, longueur maximale, format. La validation du frontend n'est qu'un confort. *Réf. : ASVS « Validation and Business Logic », Top 10 A05.*

**E-2.** SQL uniquement par SQLAlchemy avec paramètres liés. Pas de requête construite par concaténation, y compris pour `ORDER BY` ou un nom de colonne (liste blanche). *Réf. : Top 10 A05, CWE-89.*

**E-3.** Dans Vue, pas de `v-html` sur un contenu venu d'un utilisateur, d'une offre, d'un e-mail ou de l'IA. Si du HTML est indispensable, il passe par un nettoyeur à liste blanche (DOMPurify). *Réf. : ASVS « Encoding and Sanitization », CWE-79.*

**E-4.** Le site envoie une Content-Security-Policy stricte (`default-src 'self'`, pas de script en ligne, `object-src 'none'`, `frame-ancestors 'none'`), plus `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin` et HSTS. Un nouveau domaine tiers s'ajoute à la CSP dans la même PR que le code qui l'utilise. *Réf. : ASVS « Web Frontend Security », CS « Content Security Policy », Top 10 A02.*

**E-5.** Un fichier téléversé : taille maximale, type vérifié par son contenu (pas seulement l'extension), nom réécrit par le serveur, rangé sous `accounts/<compte>/`, jamais servi depuis un chemin construit avec une entrée. Un PDF ou un DOCX est lu par une bibliothèque, jamais exécuté. *Réf. : ASVS « File Handling », CWE-22, CWE-434.*

**E-6.** Le serveur ne va chercher une adresse donnée par un utilisateur ou un e-mail qu'après avoir refusé les adresses internes (localhost, réseaux privés, métadonnées), y compris après redirection. *Réf. : Top 10 A01 (SSRF), CWE-918.*

**E-7.** Pas de désérialisation de données non fiables autrement qu'en JSON (ni `pickle`, ni `yaml.load`). *Réf. : Top 10 A08, CWE-502.*

## 6. Journaux et erreurs

**J-1.** Un journal ne contient jamais : mot de passe, jeton, cookie, clé, contenu d'un CV, d'une lettre ou d'un e-mail, texte envoyé à l'IA ou reçu d'elle. Il peut contenir l'id du compte, l'id de l'objet, l'action et le résultat. *Réf. : ASVS « Security Logging and Error Handling », CS « Logging », CWE-532, ISO 27001 A.8.11 (masquage).*

**J-2.** Sont journalisés : connexions réussies et ratées, changement de mot de passe, suspension, export, suppression de compte, accès de l'exploitant aux pages d'administration. *Réf. : ASVS « Security Logging », Top 10 A09, ISO 27001 A.8.15.*

**J-3.** Une erreur renvoyée au client ne contient ni trace, ni requête SQL, ni chemin de fichier. Le détail va au journal du serveur. *Réf. : Top 10 A10, CWE-209.*

**J-4.** Un incident qui touche des données personnelles suit `docs/securite.md` §5 ; s'il met probablement ces données en danger, il est annoncé au PFPDT dès que possible. *Réf. : nLPD art. 24, RGPD art. 33.*

## 7. L'IA et les services tiers

**I-1.** N'envoyer à l'IA que ce qui sert à la tâche : texte de l'offre, blocs du CV utiles, réponse d'entraînement. Jamais les noms des contacts, les coordonnées de la personne, le numéro AVS, les données ORP brutes. Les champs à retirer sont listés dans le code qui construit l'appel, et testés. *Réf. : nLPD art. 6 al. 2 (proportionnalité), ISO 29100 (minimisation), LLM02.*

**I-2.** Un contenu non fiable (offre, page web, e-mail) envoyé à l'IA est délimité comme données, et la réponse de l'IA est traitée comme une entrée non fiable : validée par un schéma, jamais exécutée, jamais utilisée pour choisir un compte, une adresse ou une action sans contrôle. *Réf. : LLM01 (injection d'instructions), LLM05 (sortie mal traitée).*

**I-3.** L'IA n'a jamais d'outil qui écrit dans les données d'un autre compte ou qui envoie un message à l'extérieur sans confirmation de l'utilisateur. *Réf. : LLM06 (autonomie excessive).*

**I-4.** Chaque service tiers qui reçoit des données personnelles (Anthropic, hébergeur, e-mail, paiement) est listé sur la page Confidentialité avec : ce qui part, le pays, la garantie (clauses contractuelles types, contrat de traitement), la durée de conservation. Un nouveau service s'ajoute à cette page **dans la même PR**. *Réf. : nLPD art. 16, 17 et 19, RGPD art. 13 et 28.*

**I-5.** Un appel à l'IA est compté et plafonné par compte. *Réf. : LLM10 (consommation sans limite).*

## 8. Les droits des personnes et le cycle de vie

**V-1.** Protection par défaut : une nouvelle fonction qui partage, publie ou envoie des données est **désactivée** tant que l'utilisateur ne l'a pas choisie. *Réf. : nLPD art. 7 al. 3, RGPD art. 25.*

**V-2.** Toute nouvelle donnée d'un compte entre dans l'export (Réglages › Mes données, archive ZIP) dans un format lisible (JSON, fichiers d'origine). Un test vérifie que chaque table du compte est exportée. *Réf. : nLPD art. 25 et 28, RGPD art. 15 et 20.*

**V-3.** Toute nouvelle donnée d'un compte est effacée à la suppression du compte : lignes et fichiers. Un test vérifie qu'il ne reste rien. *Réf. : nLPD art. 6 al. 4, RGPD art. 17, ISO 27001 A.8.10.*

**V-4.** Chaque donnée a une durée de conservation écrite (dans `docs/securite.md` §2). Une donnée temporaire (discussion, notification, journal, e-mail brut) a sa tâche d'effacement. *Réf. : nLPD art. 6 al. 4, ISO 29100 (limitation de conservation).*

**V-5.** Une donnée n'est utilisée que pour la finalité annoncée. Une nouvelle finalité (statistiques, entraînement d'un modèle, partage) passe d'abord par la page Confidentialité et le consentement. *Réf. : nLPD art. 6 al. 3, ISO 29100 (finalité).*

## 9. Les coordonnées et la sortie des données

Le but : une personne malveillante, même avec une session volée ou une faille d'injection de script, ne doit pas pouvoir emporter les coordonnées ni les données d'un compte, et encore moins de plusieurs. L'export reste un droit de la personne (nLPD art. 25 et 28) : on le protège, on ne le supprime pas.

**X-1.** L'export complet ne se fait que par le compte lui-même, **après avoir retapé son mot de passe** (réauthentification), comme la suppression du compte : `POST /api/account/export`, essais ratés limités comme à la connexion. *Réf. : NIST 63B-4 (réauthentification avant une opération sensible), ASVS « Authentication » et « Data Protection », OWASP API Security Top 10:2023 API2.*

**X-2.** L'export est limité : 3 par 24 heures et par compte au plus. Au-delà, 429 avec `Retry-After`. *Réf. : OWASP API Security Top 10:2023 API4 (consommation sans limite), ISO 27001 A.8.12 (prévention des fuites).*

**X-3.** Chaque export est annoncé à la personne, dans la cloche et sur le téléphone, avec l'heure et quoi faire si ce n'était pas elle. L'annonce ne contient rien des données. L'export est journalisé (compte, heure), jamais son contenu. *Réf. : ASVS « Security Logging », Top 10 A09, ISO 27001 A.8.15 et A.8.16.*

**X-4.** Aucune route ne rend des coordonnées **en masse**. Une liste (contacts, candidatures) est paginée, avec une taille de page bornée côté serveur ; le téléphone et l'adresse d'un contact ne sont rendus que dans sa fiche, pas dans les listes, sauf si l'écran les affiche. Une route rend les champs dont l'écran a besoin, pas l'objet entier de la base. *Réf. : OWASP API Security Top 10:2023 API3 (exposition excessive de propriétés) et API4, ASVS « API and Web Service ».*

**X-5.** Une coordonnée ne part jamais : ni à l'IA (I-1), ni dans une notification ou un message ntfy (service tiers), ni dans un journal (J-1), ni dans une adresse de page (les paramètres d'URL finissent dans les journaux et l'historique). *Réf. : ASVS « Data Protection », CWE-598, CWE-532, nLPD art. 6 al. 2.*

**X-6.** Une réponse qui contient des données personnelles est servie avec `Cache-Control: no-store`. L'archive d'export ne passe jamais par un lien public ou durable : elle est produite à la demande et envoyée directement. *Réf. : ASVS « Data Protection » (données sensibles dans les réponses HTTP), CWE-524.*

**X-7.** L'exploitant ne peut exporter ni lire, depuis l'interface, les données d'un autre compte. Aucune route « administrateur » ne rend des coordonnées d'invités. *Réf. : Top 10 A01, nLPD art. 8, `docs/securite.md` §1.*

**X-8.** Un nombre anormal de lectures (beaucoup de fiches de contacts ou de documents en peu de temps) se limite et se journalise, comme les essais de connexion. *Réf. : OWASP API Security Top 10:2023 API4 et API6 (accès sans limite à un flux métier), ISO 27001 A.8.16.*

**X-9.** La première ligne de défense contre l'emport par un script injecté reste la CSP stricte (E-4) et l'absence de `v-html` sur un contenu non fiable (E-3) : un script qui ne s'exécute pas n'emporte rien. *Réf. : ASVS « Web Frontend Security ».*

## 10. Les enregistrements vocaux

**O-1.** Le micro ne s'ouvre que sur un geste de la personne (un bouton), jamais au chargement d'une page, et un témoin visible montre qu'il enregistre. La première fois, un texte court dit ce qui est gardé, combien de temps, et où ça part. *Réf. : nLPD art. 6 al. 3 et 19, ISO 29100 (consentement, transparence).*

**O-2.** Par défaut, l'audio **n'est pas gardé** : il est transcrit, puis effacé tout de suite. Seule la transcription reste, comme une réponse écrite. Garder l'audio est un choix de la personne, désactivé par défaut. *Réf. : nLPD art. 7 al. 3 (protection par défaut), ISO 29100 (minimisation).*

**O-3.** Un audio gardé est rangé sous `accounts/<compte>/`, chiffré au repos, servi seulement à son compte avec `Cache-Control: no-store`, et effacé après 30 jours au plus. Il entre dans l'export (V-2) et dans l'effacement (V-3). *Réf. : ISO 27001 A.8.10 et A.8.24, ASVS « File Handling » et « Data Protection ».*

**O-4.** L'audio ne part chez un service de transcription tiers que s'il est listé sur la page Confidentialité (I-4) avec son pays et sa garantie, et que la personne l'a accepté. On préfère une transcription sur l'appareil ou chez un hébergeur en Suisse. *Réf. : nLPD art. 16, 17 et 19.*

**O-5.** La voix ne sert jamais à reconnaître ou à authentifier la personne, ni à déduire son état de santé, ses émotions ou son origine. *Réf. : nLPD art. 5 let. c ch. 4 (données biométriques), RGPD art. 9.*

**O-6.** Un audio et sa transcription ne vont jamais dans un journal, une notification ou une adresse de page (X-5), et ne sont pas envoyés à l'IA tels quels : seule la transcription utile à la tâche l'est (I-1). *Réf. : CWE-532, LLM02.*

## 11. Le chiffrement et le stockage

**K-1.** TLS 1.2 au moins pour tout ce qui sort ou entre, certificats vérifiés. Jamais `verify=False`. *Réf. : ASVS « Secure Communication », CWE-295.*

**K-2.** Les sauvegardes sont chiffrées avant de quitter le service, gardées en au moins deux lieux dont un hors du serveur, et la clé qui les déchiffre n'est pas sur le même serveur. Une restauration est essayée au moins une fois par trimestre. *Réf. : ISO 27001 A.8.13, nLPD art. 8.*

**K-3.** Uniquement les algorithmes de la bibliothèque standard ou d'une bibliothèque reconnue (`hashlib`, `secrets`, `cryptography`). Pas de chiffrement « maison », pas de MD5 ni de SHA-1 pour la sécurité. *Réf. : ASVS « Cryptography », ISO 27001 A.8.24, CWE-327.*

## 12. Les dépendances et la chaîne de production

**P-1.** Les dépendances sont épinglées (verrous `uv.lock`, `package-lock.json`) et auditées chaque semaine (`pip-audit`, `npm audit`). Une faille élevée ou critique se corrige avant la prochaine mise en production. *Réf. : Top 10 A03, SSDF PW.4, ISO 27001 A.8.8.*

**P-2.** Une nouvelle dépendance se justifie dans la PR (maintenue, licence, ce qu'elle remplace). *Réf. : SSDF PW.4.*

**P-3.** Les images Docker partent d'une image officielle épinglée, tournent sans root et sans port inutile publié. *Réf. : Top 10 A02, ISO 27001 A.8.9.*

## 13. Comment on vérifie

**R-1.** Une PR qui touche aux données des utilisateurs dit, dans sa description, quelles règles de ce texte elle concerne et comment elle les respecte. *Réf. : SSDF PW.7, ISO 27001 A.8.25.*

**R-2.** Les tests couvrent au moins : la RLS de chaque table (C-1), le second compte sur chaque route (C-4), l'export et l'effacement complets (V-2, V-3), l'absence de secret dans les journaux (J-1), la limite et l'annonce de l'export (X-2, X-3). *Réf. : ASVS niveau 2, SSDF PW.8, ISO 27001 A.8.29.*

**R-3.** Une revue de sécurité tous les six mois, ou avant d'ouvrir la plateforme à de nouveaux utilisateurs (`docs/securite.md` §6). *Réf. : ISO 27001 A.5.35, SSDF RV.1.*

## 14. Écarts connus (au 2026-11-04)

Ce que le code ne respecte pas encore, d'après l'audit du 2026-11-04 et la relecture de ce texte. Chaque écart se corrige par sa propre PR et se retire de cette liste à la fusion.

| Règle | Écart | Où |
|---|---|---|
| E-4 | pas de Content-Security-Policy | `deploy/prod/Caddyfile` |
| C-3, S-3 | le worker reçoit l'accès propriétaire de la base (pour les sauvegardes) ; tous les services lisent le même `jobbot.env` | `deploy/prod/docker-compose.yml` |
| K-2 | sauvegardes sur le même serveur que leur phrase, copie ailleurs manuelle | `backend/src/jobbot/backup.py`, `deploy/prod` |
| A-1 | scrypt avec N = 2^14, sous le minimum de l'OWASP (2^17) | `backend/src/jobbot/auth/passwords.py` |
| A-2 | 12 caractères au minimum au lieu de 15, pas de refus des mots de passe compromis | `backend/src/jobbot/auth/passwords.py` |
| I-4 | la page Confidentialité ne dit pas la garantie du transfert vers Anthropic aux États-Unis | `frontend/src/views/PrivacyView.vue` |
| X-4 | listes non vérifiées route par route (pagination bornée, champs rendus) | `backend/src/jobbot/api/routes/` |
| X-8 | pas de limite sur les lectures en rafale | `backend/src/jobbot/api/` |
| O-1 à O-6 | aucun enregistrement vocal n'existe encore (la dictée du clavier du téléphone ne passe pas par jobA1) ; les règles s'appliquent dès le premier | entraînement aux entretiens |
| X-1, V-2, V-3 | un compte créé par Apple, Google ou Microsoft n'a pas de mot de passe : il ne peut ni exporter ses données ni fermer son compte tant que la réauthentification ne passe pas aussi par le fournisseur | `backend/src/jobbot/api/routes/oauth.py`, `account.py` |
| P-3 et serveur | le script d'installation ne règle ni le pare-feu, ni SSH par clé seule, ni les mises à jour automatiques | `deploy/prod/serveur.sh` |
