# 126 — La structure : trois entrées, des pages allégées, des mots clairs, la crédibilité (version 1.0.0)

> Statut : **validé** le 2026-10-22 (« oui pour tout le cadrage 126 »). Lu ainsi : les trois entrées (1), les mots (2), **Actualités gardées dans le Bilan en attendant le test avec 5 personnes** (3, le choix le plus prudent des trois), **les règles validées restent** pour les cinq contradictions (4 a à e), **un premier jet de « À propos » à corriger** (5), 1.0.0 puis 1.0.1 (6). Dis-le si une de ces lectures est fausse.
> Origine : les quatre audits d'ergonomie du 22 octobre 2026 (notes de 6,5 à 7,6 sur 10) et ta demande « écris le cadrage 126 ». Les défauts confirmés dans le code sont corrigés en 0.99.1 ; ce cadrage reprend ce qui touche la conception.
> Références citées par les audits : Nielsen Norman Group (10 heuristiques), WCAG 2.2 AA, GOV.UK Design System, Design System de la Confédération, Laws of UX. On reprend les principes, pas l'apparence : la DA de jobA1 reste.

## La phrase qui guide

jobA1 tient ton objectif ORP sans y passer tes journées, te montre ce qui obtient des réponses et t'aide à progresser. Chaque page répond à une question :

| Page | La question |
|---|---|
| Aujourd'hui | Que fais-je aujourd'hui ? |
| Candidatures | Où en sont mes candidatures ? |
| Bilan | Qu'est-ce qui marche, et quoi améliorer ? |

## 1. La navigation : trois entrées

**Aujourd'hui · Candidatures · Bilan**, en haut sur ordinateur, dans la barre du bas sur téléphone (aujourd'hui : deux entrées, plus le livre de Progresser dans la capsule).

| Aujourd'hui | Candidatures | Bilan |
|---|---|---|
| Les offres du jour, le mois ORP, les relances | Offres · Suivi · Alertes · Rendez-vous | Ce qui te répond · Formations |

- **Le Bilan remonte au premier niveau** : c'est l'atout que les concurrents n'ont pas (« ce qui obtient des réponses »), il était au deuxième niveau, après Offres et Suivi (Nielsen, architecture de l'information).
- **Candidatures passe de 5 à 4 onglets** ; « RDV » devient « Rendez-vous » (il y a la place).
- **Progresser disparaît** : Formations rejoint le Bilan (« ce qui marche, quoi améliorer » : les manques mènent aux formations) ; le livre quitte la capsule, qui garde la cloche et le compte.
- **Actualités** : voir la question 3.
- L'assistant reste accessible de partout.

## 2. Des pages allégées : la conclusion d'abord, le détail sur demande

- **Bilan** : en haut, la phrase de conclusion (« Ce qui te répond le plus : les candidatures envoyées dans la semaine qui suit l'annonce. ») puis trois chiffres (envoyées, réponses, entretiens) et l'objectif ORP. Le parcours, le graphique, les quatre analyses et les semaines passent dans des repliables (« Le détail », docs/interface.md, Les repliables). Un audit a vu des chiffres à 0 alors que le parcours dit 26 candidatures : à vérifier en même temps (l'entrée animée des chiffres, docs/60 §3).
- **Suivi** : le calendrier (ou la liste) et « À relancer » ; Job-Room et les enseignements passent en repliables sous eux.
- **Une action principale par page** (loi de Hick) : déjà la règle ; vérifiée à nouveau sur ces deux pages.

## 3. Les mêmes mots pour les mêmes choses

Une liste de termes, tenue dans `docs/interface.md`, que chaque écran respecte :

| Aujourd'hui | Proposé | Pourquoi |
|---|---|---|
| Offre, annonce, poste (mêlés) | **Offre** : ce que jobA1 reçoit ; **candidature** : ce que tu as envoyé | les audits relèvent le mélange |
| « Retenues » (Bilan) | **Gardées** | le même mot que « Garder » des offres du jour |
| « Commencées » (Aujourd'hui) | **À préparer** | le nom du statut, et de l'onglet des Offres |
| « Engagement » (statut, Bilan) | **Poste obtenu** | « engagement » est juste en Suisse romande, mais lu « engagement envers… » par plusieurs |
| « Progresser » | disparaît (§1) | |
| « exploitant » | **l'équipe jobA1** pour une personne invitée | du jargon (audit) |

## 4. La crédibilité

Par ordre d'importance, d'après les audits :

1. **Un pied de page sur chaque page** : Données personnelles · Conditions d'utilisation · Accessibilité · À propos · contact. La nLPD demande que le responsable et la protection des données soient faciles à trouver ; aujourd'hui, elles ne sont pas liées depuis chaque page.
2. **Une page « À propos »** : qui est derrière jobA1, pourquoi, où sont les données. **Le texte est à toi** (ton parcours, la raison d'être) ; je prépare la page et sa structure.
3. **Retirer le lien « Le code » (GitHub) du bandeau de la démo** : rassurant pour un développeur, « projet perso » pour un conseiller ORP. Il reste dans le README et dans « À propos ».
4. **Des témoignages** de 2 ou 3 personnes test, avec leur accord écrit, sur la page « La plateforme » : quand tu les auras.

## 5. La démo montre la valeur

- **Une lettre d'exemple** : aujourd'hui, la démo bloque la rédaction et n'en montre aucune ; le visiteur ne voit pas la fonction phare. La démo reçoit une lettre et un CV déjà rédigés pour les deux meilleures offres, avec leurs paragraphes reliés aux blocs du profil.
- **Les écrans vides** de la démo sont vérifiés un par un (le visage, une ligne, quoi faire).

## 6. Vérifier avec de vraies personnes

Les quatre audits le disent : leurs notes sont provisoires tant que personne ne s'en sert.

- **5 personnes** (méthode Nielsen), sur la démo, chacune 20 minutes, en visio ou à côté.
- **Le test des 5 secondes** : montrer Aujourd'hui 5 secondes, puis « À quoi sert cette application ? ».
- **Trois tâches** : « Prépare ta feuille pour le rendez-vous ORP », « Trouve l'offre la mieux notée et garde-la », « Marque une candidature envoyée ». Réussite, temps, blocages, comparés à leur façon actuelle (Job-Room et un tableur).
- Je prépare la fiche du test (consignes, tâches, grille) ; tu fais passer les tests.

## Garde-fous

- **Rien ne se perd** : les adresses actuelles (`/progresser/formations`, `/candidatures/bilan`…) redirigent vers les nouvelles.
- **Le cycle ORP reste visible en 5 secondes** sur Aujourd'hui (le mois ORP).
- Les écrans suivent `docs/interface.md` ; les trois audits à zéro avant chaque PR.

## Livraison proposée

- **1.0.0** : la navigation à trois entrées (§1), le Bilan et le Suivi allégés (§2), la liste des mots (§3).
- **1.0.1** : le pied de page, « À propos », le lien « Le code » retiré (§4), la lettre d'exemple de la démo (§5), la fiche du test (§6).

## Les questions

1. **Les trois entrées** (Aujourd'hui, Candidatures, Bilan), avec Formations dans le Bilan et Progresser qui disparaît : d'accord ?
2. **Les mots** (§3) : « Gardées », « À préparer », « Poste obtenu », « l'équipe jobA1 » : d'accord, ou d'autres ?
3. **Actualités** : les retirer (elles n'aident ni l'objectif ORP, ni les réponses, ni la progression, et demandent de l'entretien), les garder dans le Bilan, ou attendre le test avec 5 personnes ?
4. **Les points où un audit contredit une règle validée** : pour chacun, la règle actuelle reste-t-elle ?
   - a. La note **en mot + visage + jauge, sans pastille, sans orange** (docs/121) ; l'audit « ergonomie et design » proposait une pastille colorée, « À creuser » en orange.
   - b. **Pas de sous-titre sous le titre d'une page** (docs/interface.md, Titres 1) ; un audit propose une ligne sous chaque titre qui dit à quoi sert la page.
   - c. **Le voile de chargement reste au moins 1,2 s** (docs/63) ; un audit veut une animation lisible en 0,6 s, jamais de chargement rallongé.
   - d. **Le balayage des offres du jour sur téléphone** (validé en docs/124) ; un audit conseille de le retirer (effet « appli de rencontre »).
   - e. **Les initiales d'entreprise** : en couleur (texte foncé depuis la 0.99.1), ou **en ton neutre** pour réserver la couleur à la note (audit) ?
5. **« À propos »** : tu écris le texte, ou je te propose un premier jet à corriger ?
6. **La livraison** : 1.0.0 puis 1.0.1, dans cet ordre ?

## Écarts (1.0.0)

- **Règles relues avant de construire** ; vérifiées sur captures à 1440 et 390 px : le Bilan (Résultats replié et ouvert), le Suivi, Aujourd'hui, la barre d'onglets du téléphone.
- **Le menu** : Aujourd'hui · Candidatures · Bilan, en haut et dans la barre du bas du téléphone. Le livre de Progresser a quitté la capsule (cloche et initiale seulement) ; son aperçu (dernières actualités, formations en cours) disparaît avec lui, la pastille du nouveau à lire passe sur l'onglet Actualités du Bilan.
- **Le Bilan** : trois onglets, **Résultats** (`/bilan`), **Formations** (`/bilan/formations`), **Actualités** (`/bilan/actualites`), avec les onglets de Candidatures sur téléphone (l'icône au-dessus du nom). « Ce qui te répond » aurait mis un pronom dans un onglet (docs/interface.md, Titres 2) : l'onglet s'appelle « Résultats ».
- **Les anciennes adresses** mènent aux nouvelles, avec leurs paramètres : `/candidatures/bilan?mois=…`, `/progresser`, `/progresser/actualites`, `/progresser/formations`, `/actualites`, `/formations`.
- **Candidatures** : quatre onglets (Offres, Suivi, Alertes, Rendez-vous) ; « RDV » devient « Rendez-vous », il tient.
- **Résultats allégés** : la phrase qui conclut, les quatre tuiles, l'objectif ORP ; le parcours, le graphique, les quatre analyses, les semaines et le résumé pour l'ORP sous « Le détail » (fermé). **Les chiffres à 0** vus par un audit : l'entrée animée attendait des images qui ne viennent pas dans un onglet en arrière-plan ; la vraie valeur s'affiche maintenant au plus tard après 0,7 s.
- **Le Suivi** était déjà conforme : le calendrier (ou la liste) et « À relancer » en tête, la légende et les enseignements repliés ; rien à changer.
- **Les mots** (`docs/interface.md`, Les mots) : « Gardées » (« offres gardées »), « À préparer » (l'onglet d'Aujourd'hui), « Poste obtenu » (le statut ; « Engagement » reste dans Job-Room, son mot officiel), « l'équipe jobA1 » dans l'application et la demande de compte ; « l'exploitant » reste dans les pages légales (un rôle juridique).
- **L'assistant** : nouvelle consigne `assistant-v15` (la navigation à trois entrées, les nouvelles adresses, les offres du jour, la formule, les nouveaux mots) ; la proposition de statut dit « en « Poste obtenu » ».
- **Les audits** visitent les nouvelles adresses.

## Vérifié (1.0.0)

- Tests de l'interface : le menu à trois entrées, le titre de chaque page, les anciennes adresses redirigées (dont `/candidatures/bilan?mois=2026-10` vers `/bilan?mois=2026-10`), les mots. 444 tests, lint, vue-tsc.
- Tests backend : les consignes de l'assistant (trois entrées, plus de Progresser, les nouvelles adresses), le libellé du statut. 629 tests, ruff, mypy.
- Les trois audits sur la démo à zéro.
