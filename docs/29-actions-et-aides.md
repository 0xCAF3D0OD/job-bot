# 29 — Une action principale par page, aides visibles (version 0.22.0)

> Statut : **à valider**.
> Suite de la comparaison avec le guide [Clay — UI elements](https://clay.global/blog/ux-guide/ui-elements) (2026-10-14) : le point 1 (un seul bouton principal par page) et les points respectés en partie (infobulles, boutons désactivés, vérification des saisies, libellés).

## 1. Un seul bouton principal par page

### 1.1 Le constat

Un bouton **plein violet** dit « c'est ça qu'on fait ici ». Aujourd'hui, il y en a souvent plusieurs à l'écran :

- **partout** : « Collecter » en haut (alors que la collecte est automatique toutes les 2 heures) et le bouton **Assistant** violet en bas à droite ;
- **Aujourd'hui** : « Collecter maintenant » en plus de « Collecter » en haut (le même geste deux fois) ;
- **Préparation** : « Postuler », « Rédiger la lettre / Nouvelle version » et « Préparer le CV » ;
- **Détail d'une offre** : « Préparer ma candidature » et un autre bouton plein plus bas ;
- **Profil › Mon parcours** : jusqu'à 4 ; **Réglages** : un « Enregistrer » plein par section ; **Formulaire ORP du mois** : 2.

### 1.2 La règle

- **Un seul bouton plein par page** : **la prochaine étape**. Les autres deviennent des boutons en contour (secondaires) ou des liens.
- Ce qui est partout (barre du haut, Assistant) n'est **jamais** plein : il ne doit pas concurrencer la page.

### 1.3 Page par page

| Page | Bouton plein | Devient secondaire ou lien |
|---|---|---|
| **Barre du haut** | aucun | « Collecter » en contour |
| **Assistant** (bas à droite) | aucun | fond blanc, bord et texte violets, point menthe gardé |
| **Aujourd'hui** | aucun d'office ; le premier encart « à faire » porte l'action | « Collecter maintenant » retiré (la barre du haut suffit) |
| **Offres** (détail) | « Préparer ma candidature » | le reste |
| **Préparation** | **la prochaine étape** : « Rédiger la lettre » tant qu'il n'y en a pas, puis « Préparer le CV » s'il manque, puis **« Postuler »** | les deux autres |
| **Suivi** | l'action ORP du moment (« Compléter N ligne(s) », puis « Marquer comme remis ») — déjà une seule | les boutons du « Formulaire ORP du mois » |
| **Alertes** (assistant) | le bouton de l'étape affichée | « Passer ce site », etc. |
| **Profil › Mon parcours** | le premier élément qui manque (déposer le CV, puis créer les blocs) | les autres |
| **Réglages** | aucun : chaque « Enregistrer » en contour, à côté de sa section | — |
| **Connexion** | « Se connecter » | — |

## 2. Les infobulles

Une **infobulle** (texte au survol, attribut `title`) ne s'affiche ni au toucher ni au clavier. Les 34 de la plateforme sont classées en trois groupes :

- **Inutiles**, elles répètent ce qui est déjà écrit (titre de page, « Ouvrir la recherche sur jobup » sur un lien « Ouvrir » de la colonne jobup) : **retirées**.
- **Utiles mais secondaires** (statut d'une pastille du calendrier, date exacte d'une tâche) : gardées pour la souris, **l'information existe aussi ailleurs** (carte du jour, Diagnostic).
- **Nécessaires**, elles portent une information qu'on ne trouve nulle part ailleurs : elles deviennent **visibles**, en texte d'aide sous l'élément ou derrière un petit bouton **« ? »** qui s'ouvre au clic, au toucher et au clavier (Échap pour fermer). Ce sont :
  - le **coût** des suggestions de l'IA (sources, formations : « environ 0,02 à 0,05 $ ») ;
  - « **Note faite avec un ancien profil** » et « **Pas de note : aucun bloc de profil actif** » sur la note d'une offre ;
  - les **mots de « Mon domaine »** utilisés pour une suggestion ;
  - le **« Quatre chiffres »** du NPA (devient une aide sous le champ, §4).

## 3. Les boutons désactivés

Un bouton grisé sans explication laisse deviner. **Règle** : un bouton n'est grisé que si la raison est **écrite juste à côté** ; sinon il reste actif et explique au clic.

- **Gardés grisés** (la raison se voit déjà) : « Effacer tout (0) », « Enregistrer » tant que rien n'a changé (« Aucune modification »), un bouton pendant son propre traitement (« Rédaction… »).
- **Rendus actifs, avec message au clic** : « Envoyer » de l'Assistant avec un champ vide (le curseur revient dans le champ, « Écris ta question »), « Préparer » sans offre choisie, les boutons de l'IA quand elle n'est pas configurée ou au plafond (« Plafond de l'IA atteint ce mois : Réglages › IA »).
- **Raison écrite à côté** pour les autres : par exemple « Télécharger » grisé → « Enregistre d'abord tes modifications » (déjà fait pour la lettre et le CV, étendu au reste).

## 4. Vérifier au fil de la saisie

Aujourd'hui, les erreurs n'arrivent qu'à l'enregistrement. **Règle** : chaque champ au format précis est vérifié **en le quittant**, avec le message **sous le champ**, en rouge lisible, et il s'efface dès qu'on corrige :

- **NPA** : quatre chiffres ;
- **e-mail** : une adresse complète ;
- **LinkedIn, site personnel, adresse d'un site suivi** : une adresse web (le `https://` reste ajouté automatiquement) ;
- **adresses d'expédition** d'un site suivi : adresse ou domaine ;
- **dates** (entretien, prochaine étape) : une vraie date, et pas une suite attendue dans le passé ;
- **note minimale et maximale** : entre 0 et 100, déjà corrigée en remettant les bornes dans l'ordre.

Le bouton « Enregistrer » reste actif ; s'il reste une erreur, l'enregistrement s'arrête et le premier champ en erreur reçoit le curseur.

## 5. Les libellés visibles

- Les formulaires ont déjà leur libellé au-dessus des champs.
- **Deux exceptions assumées**, conformes à l'usage courant : le champ de **recherche** des offres (avec une **loupe** devant, comme partout) et le champ de **l'Assistant** (zone de discussion). Leur libellé reste lu par les lecteurs d'écran.

## 6. Livraison en deux PR

| PR | Contenu |
|---|---|
| **0.22.0-a** | Une action principale par page (§1) |
| **0.22.0-b** | Infobulles (§2), boutons désactivés (§3), vérification au fil de la saisie (§4), loupe de la recherche (§5) |

Sans migration ni changement d'API.

## Points à valider

1. **Un seul bouton plein par page**, la prochaine étape ; « Collecter » et l'Assistant jamais pleins (§1).
2. **Préparation** : le bouton plein suit l'étape (lettre, CV, puis Postuler) (§1.3).
3. **Réglages** sans bouton plein, Aujourd'hui sans « Collecter maintenant » (§1.3).
4. **Infobulles** : retirées si inutiles, rendues visibles (aide ou « ? ») si nécessaires (§2).
5. **Boutons grisés** seulement avec la raison à côté, sinon actifs avec message (§3).
6. **Vérification en quittant chaque champ** (§4), deux exceptions de libellé (§5).
7. **Deux PR** (§6).
