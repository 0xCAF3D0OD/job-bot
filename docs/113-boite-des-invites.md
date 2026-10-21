# 113 — La boîte des invités, à part de la tienne (version 0.83.0)

> Statut : **validé en partie** le 2026-10-21 : « focus sur la boîte mail Infomaniak, je ne veux pas avoir accès aux informations des utilisateurs sur ma boîte mail ». Faits : §1 (deux boîtes), §2 (la boîte des invités vidée), la copie d'un code effacée à 30 minutes (§3) et l'information des invités (§5). Laissés tels quels, faute de réponse : le code dans la notification et la durée des copies d'alertes (§3, §4).
> Origine : ta question du 2026-10-21 : « est-ce que ce n'est pas problématique que je reçoive les codes en clair ? Ça peut me porter préjudice si un audit est fait sur ma plateforme. »
> Se construit sur docs/03 (la collecte en lecture seule), docs/65 §3 (une adresse par compte), docs/104 (l'adresse `alertes+nom-code@joba1.ch`, 0.82.3) et docs/112 (les codes et les messages des sites).
> Je ne suis pas juriste : pour un avis ferme sur la loi sur la protection des données (nLPD), demander à un spécialiste. Ce cadrage réduit le risque ; il ne remplace pas cet avis.

## Le constat

Aujourd'hui, tout ce que les sites écrivent aux invités passe par **ta boîte Gmail personnelle** :

`alertes+amy-32e6krri@joba1.ch` → redirection Infomaniak → `kevin.dinocera@gmail.com` → libellé « Professionnel/job-bot » → lu par jobA1.

| Ce qui pose problème | Pourquoi un audit le relèverait |
|---|---|
| **Tu reçois les codes de connexion des invités** | avec le code de jobup, on entre dans le compte jobup de la personne : tu *peux* le faire, même si tu ne le fais jamais |
| **Tes e-mails et ceux des invités sont mélangés**, dans une boîte privée | les données des invités chez un tiers (Google, États-Unis) qu'ils ne connaissent pas ; pas de séparation entre l'exploitant et la plateforme |
| **Les invités ne sont pas prévenus** | rien ne leur dit que ces e-mails passent par une boîte que l'exploitant peut lire |
| **Le code part dans la notification** (ntfy.sh, docs/112) | un service tiers de plus voit le code |
| **jobA1 garde les e-mails** | une copie de chaque e-mail : 30 jours pour les codes et les messages des sites, **sans limite** pour les alertes |

Ce qui va déjà bien : dans jobA1, les comptes sont cloisonnés (règles d'accès par compte, docs/78) ; l'exploitant ne voit pas les données d'un invité dans l'interface. Le trou, c'est la boîte e-mail, pas l'application.

## La proposition

### 1. Une boîte pour les invités, en Suisse, que personne ne lit

- **`alertes@joba1.ch` devient une vraie boîte e-mail chez Infomaniak** (hébergée en Suisse), au lieu d'une redirection vers Gmail. La redirection vers ta boîte Gmail est **supprimée**.
- **jobA1 lit deux boîtes** :
  - **ta boîte Gmail**, comme aujourd'hui, **pour tes seules alertes**, toujours en lecture seule (docs/03) ;
  - **la boîte des invités**, `alertes@joba1.ch`, pour tous les comptes invités. Les adresses déjà données aux sites (`alertes+nom-code@joba1.ch`) ne changent pas.
- **Personne ne lit cette boîte à la main.** Son mot de passe ne vit que dans le `.env` du serveur (`JOBBOT_GUEST_IMAP_*`), comme les autres secrets (docs/securite.md). Si Infomaniak montre les connexions récentes à la boîte (à vérifier), un accès qui ne vient pas du serveur se verrait.

### 2. La boîte des invités se vide toute seule

- **Un e-mail rangé dans le compte de l'invité est supprimé de la boîte** aussitôt la copie faite dans jobA1. La boîte reste vide : rien à y lire.
- **Un e-mail sans compte** (adresse inconnue, compte supprimé) est supprimé au bout de 7 jours.
- **C'est un changement de règle** : jusqu'ici, jobA1 n'écrit jamais dans une boîte (docs/03, un test le vérifie). La règle reste vraie pour **ta** boîte ; elle ne l'est plus pour **la boîte des invités**, qui appartient à la plateforme. Le test est adapté : écriture permise sur la boîte des invités seulement, et seulement « supprimer après copie ».

### 3. Les codes effacés vite, partout

- **L'e-mail d'un code** : supprimé de la boîte des invités dès qu'il est lu, et **sa copie dans jobA1 effacée quand le code expire** (30 minutes), au lieu de 30 jours. Le journal garde seulement « Code jobup reçu à 14:32 ».
- **La notification ne contient plus le code** : « Code jobup reçu », il faut ouvrir jobA1 pour le voir. Ça revient sur ta réponse au docs/112 (point à valider 3).
- **La cloche** : déjà « Code expiré » après 30 minutes (docs/112).

### 4. Les e-mails gardés moins longtemps

- **Les copies des alertes des invités** : gardées **90 jours**, puis effacées (aujourd'hui, sans limite). Les offres, la note, le journal et les preuves ORP restent : seul l'e-mail brut s'en va. Passé ce délai, une alerte ne peut plus être relue par un nouvel analyseur ; c'est la seule perte.
- **Tes alertes à toi** : rien ne change (c'est ta boîte et tes données).

### 5. Le dire aux invités

- **À l'inscription** et **en tête de la page Alertes**, une phrase : « Les e-mails des sites arrivent dans la boîte de jobA1, hébergée en Suisse chez Infomaniak. jobA1 les range dans ton compte, puis les efface de la boîte. Les codes de vérification s'effacent après 30 minutes. »
- **Dans « Confidentialité »** (la page publique, `PrivacyView`) : un paragraphe sur ce circuit, les délais, et qui peut y accéder.

## Ce que ça ne règle pas

- **L'exploitant garde un accès technique** : il connaît le mot de passe de la boîte des invités (il est dans le `.env`) et il administre le serveur. On ne peut pas l'empêcher ; on peut le rendre inutile (la boîte est vide), dit (page Confidentialité), et traçable si Infomaniak montre les connexions à la boîte.
- **Les sites eux-mêmes** (jobup, Indeed…) gardent ce qu'ils envoient : hors de jobA1.

## Ce qu'il te faudra faire (une fois)

1. **Chez Infomaniak** : créer une vraie boîte e-mail `alertes@joba1.ch`. Une seule adresse suffit, pas de pack. Vérifier que le « + » y arrive (comme pour la redirection, 0.82.3).
2. **Supprimer la redirection** `alertes@joba1.ch` → Gmail, et le filtre Gmail `À : joba1.ch` s'il a été créé.
3. **Dans le `.env`** : `JOBBOT_GUEST_IMAP_HOST=mail.infomaniak.com`, `JOBBOT_GUEST_IMAP_USER=alertes@joba1.ch`, `JOBBOT_GUEST_IMAP_PASSWORD=…` ; `JOBBOT_ALERT_DOMAIN=alertes@joba1.ch` reste.
4. **Effacer de ta boîte Gmail** les e-mails des invités déjà reçus (le code d'amy, le test).

## Écart à corriger au passage

- `docs/exploitation.md` dit encore, pour les liens « Confirmez votre alerte », « la plateforme ne l'ouvre jamais » : faux depuis la 0.82.0 (docs/112 §4). À mettre à jour.

## Écarts

- **La notification garde le code** et **les copies d'alertes ne sont pas limitées à 90 jours** : ta réponse portait sur ta boîte e-mail ; ces deux points n'y touchent pas (la notification va sur le téléphone de l'invité). Ils restent à décider.
- **Un e-mail de la boîte des invités sans code d'invité** (`alertes@joba1.ch` seul, ou une autre adresse) n'est à personne, **jamais à l'exploitant** : il n'est pas rangé, puis supprimé au bout de 7 jours.
- **Le vidage** passe à la fin de chaque relevé (toutes les 2 heures, et pendant « J'attends un code ») : il supprime ce dont jobA1 a déjà une copie (son Message-ID est connu), dans n'importe quel compte. Un e-mail est donc toujours copié **avant** d'être supprimé ; une copie ratée le laisse dans la boîte pour le relevé suivant.
- **La lecture reste en lecture seule**, dans les deux boîtes ; seule la suppression est ajoutée, et seulement pour la boîte des invités (`writable`, que la boîte de l'exploitant n'a jamais : un test le vérifie).
- **L'adresse d'un invité** peut être donnée même sans la boîte de l'exploitant : la boîte des invités suffit.
- **La phrase aux invités** : en tête de la page Alertes, seulement quand la boîte des invités est en place ; dans « Données personnelles », une partie « Les e-mails des sites d'emploi » qui dit l'une ou l'autre situation. L'inscription renvoie déjà à cette page.

## Vérifié

- Tests : la boîte des invités vidée de ce qui est copié et des e-mails sans compte de plus de 7 jours, un e-mail récent non copié gardé ; la lecture toujours en lecture seule ; la boîte de l'exploitant impossible à vider ; les deux boîtes lues, chaque e-mail dans son compte, un e-mail sans code jamais donné à l'exploitant ; l'adresse d'un invité avec la seule boîte des invités ; la copie d'un code effacée à 30 minutes ; la phrase sur la page Alertes (invité seulement) et dans « Données personnelles ». 576 tests backend, ruff, mypy ; tests de l'interface, lint, vue-tsc.
- **Pas encore essayé sur la vraie boîte Infomaniak** : à faire dès qu'elle existe (un e-mail à `alertes+test@joba1.ch`, rangé puis supprimé).

## Décisions (2026-10-21)

Ta réponse : « focus sur la boîte mail Infomaniak, je ne veux pas avoir accès aux informations des utilisateurs sur ma boîte mail ».

### Les questions posées

1. **Deux boîtes** : ta boîte Gmail pour tes alertes, une boîte Infomaniak `alertes@joba1.ch` pour les invités, la redirection vers Gmail supprimée ?
2. **Vider la boîte des invités** après chaque copie (et changer la règle « jamais d'écriture » pour cette boîte seulement) ?
3. **La notification sans le code** (« Code jobup reçu »), contrairement à ta réponse du docs/112 ?
4. **Les copies d'alertes des invités gardées 90 jours** : d'accord, ou une autre durée ?
5. **La phrase aux invités** (inscription, Alertes, Confidentialité) : le texte proposé te va ?

## 0.83.1 — La page Alertes remise en ordre

Ton retour du 2026-10-21 (le code d'amy bien arrivé, la boîte vidée) : « la structure de la page est vraiment pas bonne sur ordinateur ». La phrase sur la boîte, le code, « J'attends un code », l'assistant et les messages se suivaient sans rubrique, à des largeurs différentes.

- **En tête** : le code d'un site, seul (quand il y en a un), le temps de le recopier.
- **« Les alertes »** : un titre (pas de possessif en tête, docs/88) au-dessus de l'assistant ou du résumé, comme les autres rubriques (« Gérer » garde le sien).
- **« Les e-mails des sites »** : un titre, la phrase sur la boîte de jobA1 (invités seulement), puis **une carte** : « Code de vérification » avec sa description et la pilule **« J'attends un code »** ; sous un filet, **« Messages des sites »** et leur liste. Sur téléphone, la pilule passe sous le texte, en pleine largeur.
- Puis « Alertes reçues », comme avant.
- **Vérifié** : tests de la rubrique (attente, limite, phrase, messages), captures Playwright à 1440 et 414 px de l'écran d'amy (code en tête, assistant, rubrique des e-mails) ; rien ne dépasse.
