# 66 — L'accueil après la première connexion, façon Duolingo (version 0.54.0)

> Statut : **validé** le 2026-10-16, livré.
> Demande du 2026-10-16 : « un onboarding style Duolingo, où on passe sur plusieurs points avec un choix, après la connexion ». Aujourd'hui, un nouveau compte arrive sur Aujourd'hui vide, avec la liste « Pour bien démarrer » : à lui de trouver où régler quoi.

## 1. Le principe

- **Un écran, une question.** Plein écran, sans menu. Une barre de progression en haut, « ← » pour revenir, « Passer » pour sauter la question.
- **Des choix en grandes cartes** qu'on touche (une icône, un mot, une ligne d'explication). La carte choisie se marque ; « Continuer » s'allume. Quand une question n'a qu'un choix possible, toucher la carte suffit pour avancer.
- **Chaque réponse remplit un vrai réglage** (critères, objectif ORP, Mon domaine, CV, notifications). Rien n'est demandé deux fois : la liste « Pour bien démarrer » d'Aujourd'hui se coche d'elle-même.
- **Court** : 7 écrans, environ 2 minutes. On peut tout passer, et reprendre plus tard là où on s'était arrêté.

## 2. Les écrans

| # | Question | Les choix | Ce que ça règle |
|---|---|---|---|
| 1 | **Bienvenue ! Qu'est-ce qui t'amène ?** | Je cherche un emploi · Je suis inscrit·e à l'ORP et je dois prouver mes recherches · Je veux surtout suivre l'actualité de mon métier | l'ordre et le ton des écrans suivants (l'écran 5 n'apparaît que pour l'ORP) |
| 2 | **Quel métier cherches-tu ?** | un champ libre, avec des propositions en cartes (DevOps, Infirmier·ère, Comptable, Vente, Logistique…) | les mots de l'alerte proposée à l'écran 7 et « Mon domaine » des Actualités |
| 3 | **Où veux-tu travailler ?** | des cartes de cantons romands et « Toute la Suisse », plusieurs choix possibles ; un champ pour une ville | Ce que je cherche › lieux |
| 4 | **Quel taux d'activité ?** | 100 % · 80 à 100 % · 50 à 80 % · Peu importe | Ce que je cherche › taux minimum |
| 5 | **Combien de recherches l'ORP te demande-t-il par mois ?** (ORP seulement) | 4 · 6 · 8 · 10 · 12 · Je ne sais pas encore ; puis le jour de remise (5 par défaut) | objectif ORP et date limite |
| 6 | **Ton CV, pour que la plateforme te connaisse** | Déposer mon CV (PDF ou Word) · Plus tard | le document ; la plateforme propose ensuite les blocs de profil, comme dans Profil |
| 7 | **Dernière chose : comment veux-tu être prévenu·e ?** | Sur mon téléphone (ntfy) · Seulement dans la plateforme | les notifications du compte |

Puis un écran **« C'est prêt »** : un petit récapitulatif (« DevOps · Vaud, Genève · 80 % et plus · 10 recherches par mois ») et un seul bouton, **« Créer mes alertes »**, qui ouvre l'assistant des alertes avec la recherche déjà remplie (métier et lieu des écrans 2 et 3).

## 3. Le style

- **Façon Duolingo, aux couleurs de jobA1** : cartes arrondies, bordure qui passe au violet quand on choisit, un léger rebond à la sélection (150 ms), la barre de progression qui avance en glissant (250 ms), l'écran suivant qui arrive de la droite (250 ms) ; « réduire les animations » : rien ne bouge.
- **Une illustration par écran**, petite (160 px), au-dessus de la question, prise dans les dix illustrations existantes (mailbox, stepping-up, done, morning-plans…) : c'est une « première fois », la règle de `docs/interface.md` le permet.
- **Aucun son, aucune mascotte, aucun point à gagner.** Le côté Duolingo, c'est le rythme : une question, un geste, on avance.
- **Téléphone d'abord** : les cartes en une colonne, le bouton « Continuer » collé en bas de l'écran.

## 4. Qui le voit, et quand

- **Chaque nouveau compte**, juste après sa première connexion (ou après l'invitation), avant Aujourd'hui.
- **Pas toi, ni les comptes déjà utilisés** : ils sont marqués « accueil fait ».
- **Reprendre** : s'il quitte en route, il reprend à l'écran où il s'était arrêté à sa prochaine connexion ; « Plus tard » (en haut à droite) l'emmène à Aujourd'hui, et une ligne « Terminer mon accueil » y reste tant que ce n'est pas fini.
- **Revoir** : Réglages › Compte, « Refaire l'accueil » (les réponses actuelles sont proposées).

## 5. Côté technique

- Une page `/bienvenue`, sans menu ; le routeur y envoie un compte dont l'accueil n'est pas fait.
- L'avancement (écran atteint, réponses de l'écran 1) est un réglage du compte ; les réponses vont dans les routes existantes (critères, réglages, Mon domaine, dépôt de document, notifications). Une seule petite route nouvelle : lire et marquer l'avancement de l'accueil.
- Aucun appel à l'IA pendant l'accueil (les propositions de blocs depuis le CV restent dans Profil, à la demande).

## 6. Livraison

Une PR (**0.54.0**). Captures de chaque écran sur ordinateur et téléphone, clair et sombre ; un compte de test qui le parcourt en entier sur l'instance de test.

## Points à valider

1. **Le principe** : un écran, une question, des cartes, « Passer » partout, environ 2 minutes (§1).
2. **Les 7 écrans** et l'écran « C'est prêt » qui mène à la création des alertes (§2).
3. **Le style** : rythme Duolingo, couleurs jobA1, une petite illustration par écran, ni son ni points (§3).
4. **Qui le voit** : seulement les nouveaux comptes ; reprendre là où on s'est arrêté ; « Refaire l'accueil » dans les Réglages (§4).
5. **Une PR** (§6).

## Écarts avec la livraison

- **Rythme** : l'écran suivant arrive aussitôt (il glisse de la droite en avançant, de la gauche en revenant) ; les réponses s'enregistrent en arrière-plan, fusionnées d'abord dans la page puis dans la base, pour qu'aucune n'en écrase une autre.
- **Écrans** : à l'écran 1, toucher une carte suffit pour avancer, comme au taux d'activité. Écran 3 : Vaud, Genève, Fribourg, Neuchâtel, Valais, Jura, Berne, Zurich et « Toute la Suisse », plus un champ ville. Écran 6 : le dépôt du CV, « Continuer » s'allume une fois déposé. Écran 7 : « Sur mon téléphone » montre le sujet ntfy à suivre.
- **« C'est prêt »** : le récapitulatif (métier, cantons en toutes lettres, taux, recherches ORP) ; « Créer mes alertes » ouvre l'assistant des alertes, où la recherche du métier est déjà proposée (la page Alertes propose « Mon domaine » × les villes ; les cantons restent dans les critères, qui filtrent les offres).
- **Qui le voit** : la migration 0049 marque « accueil fait » pour tous les comptes déjà là. Après la connexion, un compte dont l'accueil n'est pas fini y retourne ; tant qu'il est « à faire », chaque page y mène (sauf les pages publiques). « Plus tard » le remet à plus tard : Aujourd'hui montre « Terminer mon accueil ». « Refaire l'accueil » est dans Réglages › Compte, pour les comptes invités.
- **Vérifié** sur l'instance de test avec un compte neuf : connexion, les sept écrans jusqu'à « C'est prêt », puis l'assistant des alertes pré-rempli ; sur téléphone, sans débordement.
- **Complément (retour du 2026-10-16, « pouvoir revenir en arrière si une erreur a été faite, et passer »)** : « ← Retour » et « Passer → » sont deux vrais boutons en bas de chaque écran, sous « Continuer » (la flèche discrète en haut est retirée). Sur « C'est prêt », chaque ligne du récapitulatif (objectif, métier, lieux, taux, recherches ORP) porte « Modifier » : elle ramène à la question, le bouton devient « Enregistrer » et revient aussitôt au récapitulatif (« ← Revenir au récapitulatif » sans rien changer). Choisir l'ORP en corrigeant l'objectif pose d'abord la question ORP.
- **Complément (même jour, « des points qui marquent les étapes, et y accéder ainsi »)** : la barre de progression devient une rangée de points, un par écran (7, ou 8 avec l'ORP). Le point de l'écran en cours s'allonge, ceux des questions déjà répondues sont pleins ; on touche un point pour aller directement à cet écran (zone de 1,75 rem au doigt, nom de l'étape au survol et pour les lecteurs d'écran).
- **Complément (même jour, « pour la date, un calendrier, et sa propre étape »)** : la date de remise ORP quitte l'écran 5 pour un écran à elle, juste après (ORP seulement). Un calendrier du mois prochain, semaines du lundi au dimanche ; on touche le jour et on avance. Le 1er et les jours après le 28 sont grisés (l'ORP accepte du 2 au 28). Le récapitulatif ajoute « Preuves à remettre avant le … du mois », modifiable comme les autres lignes.
- **Complément (même jour, illustrations)** : trois dessins unDraw de plus, choisis sur planche et préparés par `scripts/illustrations.mjs` : taux d'activité → *tight-deadline*, CV → *my-resume*, notifications → *lock-screen-notifications*. « Où travailler » garde la boîte aux lettres (aucune carte dans les dessins disponibles). Environ 25 Ko en tout, chargés seulement à l'écran concerné. *lock-screen-notifications* dessine un téléphone, objet plutôt que maquette d'écran : exception à la règle 3 de `docs/interface.md`, limitée à l'accueil. La date de remise reste sans illustration : le calendrier occupe déjà l'écran.
- **Complément (même jour)** : sur « C'est prêt », les coches vertes du récapitulatif passent de 16 à 20 px, et le lien « Aller à Aujourd'hui » est retiré : un seul bouton, « Créer mes alertes » (« ← Retour » reste).
