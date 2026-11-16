# 146 — Les réponses des entreprises, transférées par la personne

> Statut : **validé par Kevin le 2026-11-16** (option A, transfert à la main ; les cinq lignes du fonctionnement acceptées à 12 h 36). Livré côté serveur, sans écran nouveau.
> Origine : la question de Kevin du 2026-11-16 : « Ivy Partners m'a répondu et j'ai eu un entretien : est-ce qu'il serait possible de tracker ce genre de réponse ? »

## 1. Pourquoi pas automatique

jobA1 n'envoie pas les candidatures : la réponse d'une entreprise arrive dans la boîte personnelle de la personne, que jobA1 ne lit pas. Les options étudiées :

| Option | Pour | Contre |
|---|---|---|
| **A. Transfert à la main** (retenue) | presque gratuit, rien n'arrive sans geste de la personne | il faut penser à transférer |
| B. Filtre Gmail généré par l'extension | automatique | filtre à remettre à jour à chaque candidature ; « noreply » des logiciels de recrutement difficiles à rattacher |
| C. Connexion de la boîte (Gmail, Outlook) | entièrement automatique | lecture de Gmail = autorisation « restreinte » de Google : audit de sécurité annuel payant, vérification de plusieurs semaines ; jobA1 lirait tout le courrier, contraire à « jamais tout le courrier » (docs/142 §5) |

B pourra s'ajouter si le transfert à la main devient pénible.

## 2. Fonctionnement

1. La personne transfère la réponse vers son adresse jobA1 habituelle, celle des alertes. Pas de nouvelle adresse.
2. Un transfert fait à la main n'a pas les en-têtes d'un filtre Gmail (`X-Forwarded-To`, `X-Forwarded-For`) et porte dans son corps l'en-tête du message d'origine (« De : … » suivi de « Date : », « Envoyé : », « Objet : »…, tel que l'écrivent Gmail, Outlook, Apple Mail, en français, allemand, anglais ou italien). Sans cet en-tête, l'e-mail reste ignoré comme avant ; transféré par un filtre, il garde l'avertissement « Vérifie ton filtre Gmail ».
3. **Rattachement** (`mail/replies.py`) parmi les candidatures des 12 derniers mois :
   - le domaine de l'expéditeur d'origine, comparé au lien et à l'e-mail de chaque candidature, ou au nom de l'entreprise collé (`ivypartners.ch` ↔ « Ivy Partners SA ») ;
   - sinon, quand le domaine ne dit rien (boîte personnelle, logiciel de recrutement comme Workday ou SmartRecruiters, site d'annonces), le nom de l'entreprise, sans sa forme juridique, dans le message ;
   - plusieurs entreprises possibles : aucune (la personne choisit) ; plusieurs candidatures dans la même entreprise : la plus récente.
4. **Classement** par mots-clés, sans IA : un refus d'abord (« malheureusement », « leider », « unfortunately »…, car un refus parle souvent de l'entretien passé), puis un accusé de réception (« bien reçu votre candidature » : « autre »), puis un entretien (« entretien », « Vorstellungsgespräch », « interview »…), sinon « autre ».
5. **Rien ne change tout seul** : le statut de la candidature reste le même. Une notification (cloche ; téléphone un jour de recherche) dit « Ivy Partners SA t'a répondu : entretien ? » (ou « refus ? », ou seulement « t'a répondu ») et ouvre la candidature (`/candidatures/suivi?candidature=ID`), où la personne choisit le statut comme aujourd'hui. Candidature non retrouvée : « Réponse d'entreprise reçue », qui ouvre Candidatures.

## 3. Données (docs/regles-securite-donnees.md)

- Gardé : `applications.reply_kind` (« entretien », « refus », « autre ») et `applications.reply_at` (migration 0088). Colonnes d'une table cloisonnée : exportées et effacées avec la candidature (C-1, V-1 à V-3).
- Jamais gardé : le texte, l'expéditeur, la copie de l'e-mail. Il est lu en mémoire pendant la collecte puis rangé « ignoré » : seul son Message-ID reste, pour ne pas le relire (V-4).
- Journaux : le type de réponse et si une candidature a été trouvée, rien d'autre (J-1).
- Notification : le nom de l'entreprise, déjà dans la candidature ; jamais une coordonnée (X-5).
- Aucun service tiers, aucun appel à l'IA (I-1 à I-5 sans objet).

## 4. Limites connues

- Une adresse d'alertes est donnée aux sites : quelqu'un qui la connaît et devine une entreprise où la personne a postulé peut faire apparaître une notification. Elle ne change rien d'elle-même ; la personne confirme.
- Les mots-clés se trompent parfois (un refus sans mot attendu devient « autre ») : la notification pose une question, elle n'affirme pas.
- Aucun écran ne montre encore la réponse reçue (pastille, historique) : il faut d'abord une planche.
