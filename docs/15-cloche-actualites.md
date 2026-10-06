# 15 — Cloche des alertes et onglet Actualités (version 0.8.0)

> Statut : **validé** le 2026-10-06, sources proposées retenues. livré : PR a (cloche), PR b (Actualités).
> Retours d'usage du 2026-10-06.

## 1. La cloche : les alertes du téléphone, aussi dans la plateforme

**Constat** : les alertes partent seulement sur le téléphone (ntfy). Dans la plateforme, rien ne les montre, et sans ntfy configuré elles n'existent pas du tout.

**Proposition** : une **cloche** dans la barre du haut, à côté de « Collecter ».

- **Pastille** avec le nombre d'alertes non lues (« 3 »), rien s'il n'y en a pas.
- Un clic ouvre la **liste des 20 dernières** : titre, une ligne de texte, l'heure (« il y a 2 h »). Les non lues sont en gras.
- Un clic sur une alerte **ouvre la bonne page** (l'offre, les candidatures, le mois ORP) et la marque comme lue. Un lien « Tout marquer comme lu ».
- **Les mêmes alertes que sur le téléphone** :
  - nouvelles offres au-dessus du seuil de note ;
  - candidatures à relancer (10 jours) ;
  - rappels ORP (objectif, remise, veille de la date limite) ;
  - plafond de l'IA à 80 % ;
  - en plus, **collecte en échec** (connexion Gmail refusée, par exemple), qui n'existe pas encore sur le téléphone.
- **Sans ntfy**, les alertes existent quand même dans la cloche ; ntfy reste en plus, pour le téléphone.
- La cloche se met à jour toute seule chaque minute ; les alertes de plus de 90 jours sont effacées.

## 2. Onglet « Actualités »

**Proposition** : une nouvelle page **Actualités** (menu, entre ORP et Profil), en deux colonnes ou deux onglets :

| Rubrique | Contenu |
|---|---|
| **Marché de l'emploi** | articles récents sur l'emploi en Suisse et en Suisse romande : chiffres du chômage, tendances par secteur, conseils de candidature |
| **Vidéos** | vidéos YouTube récentes de chaînes choisies : recherche d'emploi, entretiens, et ton domaine (DevOps, Kubernetes, CKA) |

**D'où viennent les contenus** : des **flux publics** (RSS) des sites d'information et des chaînes YouTube. Aucun compte ni clé n'est nécessaire, et aucune IA n'est utilisée, donc aucun coût.

**Sources proposées au départ**, à valider ou compléter (je vérifierai que chaque flux répond avant de l'ajouter) :
- *Marché de l'emploi* : communiqués du SECO sur le marché du travail (chiffres mensuels du chômage), rubriques Économie de la RTS et du Temps, magazine de conseils de jobup / jobs.ch.
- *Vidéos* : par exemple TechWorld with Nana (DevOps), KodeKloud (Kubernetes, CKA), et une ou deux chaînes francophones sur la recherche d'emploi et les entretiens, que tu choisis.

**Fonctionnement** :
- Les sources se gèrent dans **Réglages → Actualités** : ajouter un flux (adresse d'un site, d'un flux RSS ou d'une chaîne YouTube), le mettre en pause, le retirer.
- La plateforme relève les nouveautés **toutes les 6 heures** et garde 60 jours d'articles.
- Chaque carte affiche titre, source, date, une ou deux lignes de résumé, et la miniature pour les vidéos. Un clic ouvre l'article ou la vidéo sur le site d'origine, dans un nouvel onglet.
- **Confidentialité** : les miniatures sont téléchargées et servies par la plateforme, comme les logos. Ton navigateur ne contacte YouTube ou les journaux que quand tu ouvres un contenu.
- Un compteur discret « 5 nouveautés » sur l'onglet, depuis ta dernière visite. Pas d'alerte dans la cloche, pour ne pas la noyer.

## 3. Base (migration 0022)

```
notifications  id, kind, title, message, link, created_at, read_at?
news_sources   id, kind (articles|videos), name, url, feed_url, active, created_at
news_items     id, source_id, title, url UNIQUE, summary?, image_key?, published_at, seen_at?
```

## 4. Livraison en deux PR

| PR | Contenu |
|---|---|
| **0.8.0-a** | Cloche des alertes (et alertes de collecte en échec) |
| **0.8.0-b** | Onglet Actualités, sources dans les Réglages |

## Points à valider

1. **Cloche** avec pastille, liste des 20 dernières, clic qui ouvre la bonne page (§1).
2. **Mêmes alertes que le téléphone**, plus « collecte en échec » ; alertes présentes même **sans ntfy** (§1).
3. **Onglet Actualités** : articles sur le marché de l'emploi et vidéos YouTube, depuis des **flux publics**, sans coût (§2).
4. **Sources de départ** : dis-moi lesquelles garder, et quelles chaînes YouTube ajouter (§2).
5. **Deux PR**, la cloche d'abord (§4).

## Écarts avec la PR a

- **Migrations** : la 0022 ne crée que `notifications` ; les tables des actualités viendront avec la PR b (0023).
- **Sans ntfy** : les relances, rappels ORP et alertes de notes sont désormais **marqués comme faits** une fois dans la cloche (avant, ils restaient en attente faute de téléphone).
- **Collecte en échec** : au plus une alerte toutes les 6 heures ; le message dit la cause (connexion refusée, Gmail injoignable) sans jamais reprendre de secret.
- **Échec de ntfy** : l'alerte reste dans la cloche, l'erreur est notée dans les journaux.
- **Nettoyage** : les alertes de plus de 90 jours sont effacées par la tâche quotidienne `reminders`.

## Écarts avec la PR b

- **Sources de départ** : SECO (flux officiel des communiqués de la Confédération, filtré sur l'auteur « Staatssekretariat für Wirtschaft » : il mêle allemand et français), RTS Info — Économie, Le Temps — Économie, TechWorld with Nana, KodeKloud. Le **magazine de conseils de jobup / jobs.ch** est écarté : ses pages refusent les lectures automatiques (erreur 403), et je ne contourne pas cette protection.
- **Filtre par source** : facultatif, « ne garder que ce qui contient » (titre, résumé ou auteur).
- **Chaînes YouTube** : à ajouter par leur **ID** (« UC… ») ou leur adresse `/channel/UC…`. Une adresse `youtube.com/@nom` mène, depuis la Suisse, à une page de consentement aux cookies que la plateforme n'accepte pas à ta place ; le message d'erreur explique où copier l'ID.
- **Base** : migration **0023** (`news_sources`, `news_items`) ; le compteur « nouveautés » repose sur la date de ta dernière visite (réglage `news_seen_at`), pas sur un champ par contenu.
- **Compteur** : sur l'entrée « Actualités » du menu (mis à jour toutes les 5 minutes) et sur chaque onglet de la page ; la visite le remet à zéro.
- **Rythme** : tâche `news`, toutes les 6 heures ; 30 éléments au plus par source et par relevé ; miniatures de 300 Ko au plus, avec les mêmes garde-fous que les logos ; les articles RTS et Le Temps ont aussi leur image.
- **Essai réel** : 98 contenus relevés sur les 5 sources, sans échec.
