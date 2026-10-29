# 117 — Accessibilité vérifiée, dictée vocale, poids des pages (version 0.87.0)

> Statut : **validé** le 2026-10-21 (« oui pour tout, vas-y ») : §3 en 0.87.0, puis §1 et le rappel de §2 en 0.88.0.
> Origine : les trois points restants de la comparaison avec l'article « The top UX design trends in 2026 » (UX Design Institute), après « Cette note ne me correspond pas » (docs/114, 0.84.0) : la conformité (point 4), les interfaces multimodales (point 1), l'UX sobre (point 6). Ta demande du 2026-10-21 : « n'oublie pas qu'on a encore le point du blog à finir ».

## Le constat

| Point | Aujourd'hui | Ce qui manque |
|---|---|---|
| **Accessibilité** | contrastes testés (`contrast.test.ts`), focus gardé dans les fenêtres, noms pour lecteur d'écran, « réduire les animations » respecté | aucun contrôle automatique des pages ; pas de parcours vérifié au clavier de bout en bout |
| **Voix** | tout s'écrit | rien pour dicter ; or les claviers des téléphones (iPhone, Android) ont **déjà un micro** qui dicte dans n'importe quel champ |
| **Poids** | images en WebP, la vidéo de la page de connexion (3,2 Mo) chargée seulement à la lecture, coupée si « réduire les animations » | **un seul fichier JavaScript** pour toute l'application : 663 Ko (205 Ko compressés) téléchargés dès la première page, même la connexion ; CSS 205 Ko (39 Ko compressés) ; aucune mesure ni limite |

Correction de ma comparaison précédente : j'avais écrit « pas de vidéo » ; il y en a une, sur la page de connexion, mais elle ne se charge qu'à la lecture.

## La proposition

### 1. L'accessibilité vérifiée à chaque PR

- **Un contrôle automatique** (axe-core, la référence des contrôles WCAG) sur chaque page principale, dans les tests de l'interface : Aujourd'hui, Offres, la fiche d'une offre, Suivi, Alertes, Bilan, Rendez-vous, Profil, Réglages, Préparer, connexion. Une erreur « grave » ou « critique » fait échouer les tests.
- **Un parcours au clavier** vérifié par Playwright, dans les captures : se connecter, ouvrir une offre, la noter « ne me correspond pas », préparer une candidature, la marquer envoyée, sans souris.
- **Ce que je corrigerai** : ce que les contrôles trouveront (je ne le sais pas encore ; je donnerai la liste avant de corriger si elle est longue).
- **Une page « Accessibilité »** courte, liée depuis le pied de page : ce qui est vérifié, ce qui ne l'est pas, et comment signaler un problème. Utile devant l'ORP.

### 2. La dictée : utiliser celle du téléphone, l'ajouter sur ordinateur seulement si besoin

- **Sur téléphone, rien à construire** : le micro du clavier dicte déjà dans tous les champs de jobA1. Je vérifie que rien ne la gêne (champs qui perdent le texte, limites trop courtes) et l'assistant le rappelle (« Tu peux aussi dicter avec le micro de ton clavier »), à côté du champ de l'assistant et des réponses d'entretien.
- **Sur ordinateur**, un bouton micro **ne serait pas privé** : la dictée de Chrome envoie la voix aux serveurs de Google, Firefox ne l'a pas, Safari la fait sur l'appareil. Je propose de **ne pas l'ajouter** pour l'instant ; à revoir si des personnes le demandent.

### 3. Un budget de poids

- **Découper l'application par page** : chaque page se charge quand on l'ouvre. La page de connexion et Aujourd'hui ne téléchargent plus Préparer, le Bilan ou les Réglages. Objectif : moins de 120 Ko compressés pour la première page (205 Ko aujourd'hui).
- **Une limite vérifiée à chaque PR** : un test mesure, après la construction, la taille compressée du code de la première page et du total ; au-delà de la limite (premier écran 120 Ko, total 260 Ko, CSS 45 Ko), il échoue et dit quel fichier a grossi.
- **Le temps de chargement** mesuré une fois dans les captures (téléphone, connexion 4G simulée), noté dans ce document ; pas de mesure en continu.

## Garde-fous

- Le découpage ne change rien à ce que l'on voit ; la page suivante peut mettre un instant à s'ouvrir la première fois : l'animation de chargement existante (docs/80) s'affiche.
- Pas de nouvelle dépendance envoyée au navigateur : axe-core ne sert qu'aux tests.

## Écarts (0.87.0 : §3)

- **Le découpage** : toutes les pages se chargent à l'ouverture (`router.ts`), sauf la page provisoire des entrées à venir. Le premier écran (l'application et Aujourd'hui) passe de **205 Ko à 82 Ko** compressés (−60 %).
- **Les limites** (`frontend/scripts/poids.mjs`, `make poids`, et dans `make test`) : premier écran 120 Ko, CSS 45 Ko, et **total 270 Ko au lieu de 260** : découpé en 50 fichiers, le code pèse un peu plus au total (257 Ko au lieu de 226), chaque fichier se compressant à part. Vite écrit son manifeste (`build.manifest`) pour que le script sache ce que charge chaque page.
- **Total porté à 285 Ko** (29.10, décision de Kevin) : main pèse 268,4 Ko, et la structure téléphone charge pour la première fois GroupedList, GroupedRow et SegmentedControl (+1,7 Ko pour le Profil, 270,4 Ko) ; ses 7 étapes suivantes ajoutent chacune un peu. Le premier écran reste limité à 120 Ko et le CSS à 45 Ko.
- **Le temps de chargement** (version construite, téléphone simulé, processeur ralenti 4 fois, médiane de 5) : **inchangé**. Aujourd'hui s'affiche en 1,0 s en 4G rapide (avant 1,0 s) et en 2,0 s en 4G lente (avant 2,0 s). Ce temps vient des appels à l'API et de la transition de page (docs/63), pas du code. Le gain est ailleurs : 120 Ko de moins à télécharger et à lire à chaque première visite, ce qui compte sur un forfait limité ou un vieux téléphone.

## Vérifié (0.87.0)

- `make poids` : premier écran 81,9 Ko / 120, total 257,0 / 270, CSS 38,6 / 45.
- Toutes les pages parcourues dans la démo construite (Aujourd'hui, les cinq onglets de Candidatures, Progresser, Profil, Réglages, Diagnostic, La plateforme, Données personnelles, page introuvable) : chacune s'ouvre. Ce parcours a trouvé l'erreur des actualités de la démo, corrigée à part (0.86.2).
- 408 tests de l'interface, lint, vue-tsc.

## Écarts (0.88.0 : §1 et §2)

- **Le contrôle automatique** est un audit sur la démo, comme celui des rangées : `frontend/scripts/accessibilite.py` passe axe-core (règles WCAG 2.1 AA) sur 15 pages, à 1440 et 390 px, puis le parcours au clavier. Dans les tests de l'interface (jsdom), axe ne peut pas juger les contrastes ni la mise en page : la démo, oui. axe-core n'est qu'une dépendance de développement.
- **Ce que l'audit a trouvé, et la correction** :
  - Suivi, le calendrier : déclaré en grille sans lignes (rôles `grid`, `gridcell`, `columnheader` mal imbriqués, 31 jours en défaut « critique ») → un groupe de boutons ; le nom de chaque jour dit le jour de la semaine (« mardi 21 ») ; les en-têtes « L M M… » sont visuels.
  - Les deux barres de progression (objectif ORP du mois, dépense de l'IA) sans nom → nommées.
  - Bilan : le gris des mois réussis, sur fond menthe, à 4,4:1 → un gris plus sombre (4,5:1 exigé). La plateforme : le gris des maquettes à 4,2:1 → idem.
  - Réglages : un lien dans une phrase, reconnaissable seulement à sa couleur → souligné.
  - Le bandeau de la démo hors des repères de la page → un repère nommé « Démo » ; six `aside` dans le contenu de la page → des sections.
  - Le parcours au clavier (Aujourd'hui, Candidatures, une offre, « Cette note ne me correspond pas », « Trop haute ») : rien ne bloquait.
- **Résultat** : 0 défaut grave, 0 défaut mineur, parcours au clavier sans blocage.
- **La page « Accessibilité »** (`/accessibilite`, publique) : il n'y a pas de pied de page ; elle est liée depuis Données personnelles.
- **§2, la dictée** : « Écris ou dicte ta question… » dans l'assistant, « Ta réponse, écrite ou dictée… » dans l'entraînement à l'entretien, sur téléphone seulement. Pas de phrase d'aide en plus (docs/interface.md, titres et textes 5).

## Vérifié (0.88.0)

- `accessibilite.py` sur la démo : `{"défauts graves": 0, "défauts mineurs": 0, "parcours au clavier": []}`.
- 409 tests de l'interface (la page Accessibilité), lint, vue-tsc ; `make poids` : 82,0 / 258,0 / 38,7 Ko.
- L'audit des rangées remonte les 8 rangées des Réglages corrigées par la 0.86.1 (#267), pas encore sur cette branche.

## Les questions

1. **§1** : le contrôle automatique sur les pages principales, le parcours au clavier, la page « Accessibilité » : d'accord ? Je corrige directement ce qui est trouvé, ou je te montre la liste d'abord ?
2. **§2** : rien à construire sur téléphone (le micro du clavier), un rappel dans l'assistant ; pas de bouton micro sur ordinateur : d'accord ?
3. **§3** : le découpage par page et les limites (120 Ko pour le premier écran, 260 Ko au total, 45 Ko de CSS) : d'accord ?
4. **L'ordre** : je propose §3 (0.87.0, le plus mécanique), puis §1 (0.88.0), puis le rappel de §2 avec §1.
