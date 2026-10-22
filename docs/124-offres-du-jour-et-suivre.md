# 124 — Les offres du jour une par une, et l'étape « Suivre » (version 0.97.0)

> Statut : **validé** le 2026-10-22 (« oui pour tout, vas-y ») : la dose de 3, 5 quand le mois est à rattraper ; « Garder » passe l'offre en « À préparer » ; le balayage en plus des boutons ; la date de relance par candidature ; D et G en 0.97.0.
> Origine : l'audit des concurrents du 2026-10-21 (points 3 et 5 ; plan D et G). Ta demande du 2026-10-22 : « écris le cadrage 124 ».
> Se construit sur docs/86 (le bon rythme, la dose du jour), docs/95 (Aujourd'hui), docs/47 et docs/51 (Préparer), docs/108 (Annuler plutôt que confirmer), docs/123 (le visage du 1).

## Le constat

### D. Les offres du jour

- Aujourd'hui montre **3 offres** (« Meilleures offres », docs/86 : une dose juste, pas toute la pile), en liste. Pour décider, il faut ouvrir l'offre, puis chercher « Plus tard » ou « Ignorer » dans le menu « ⋯ ».
- Trier 3 offres demande donc environ 9 gestes ; ApplyNow en demande 3 (garder ou écarter, une offre à la fois).
- Ce qu'on garde de docs/86 : **la dose reste petite**, c'est ce qui distingue jobA1 des plateformes qui poussent au volume.

### G. Après l'envoi

- Préparer a trois étapes : ① Lettre, ② CV, ③ Postuler. « Marquer comme envoyée » ferme le parcours : la carte « Candidature envoyée » (comptée pour l'ORP), puis plus rien.
- Ce qui suit existe, mais ailleurs : la relance proposée à 10 jours (Aujourd'hui, Suivi), les champs manquants pour Job-Room (Suivi, panneau de la candidature), les contacts.
- La personne ne voit pas, au moment où elle envoie, **ce que jobA1 fera ensuite pour elle**.

## La proposition

### D. « Les offres du jour », une à la fois

1. **Où** : dans la carte « À faire » d'Aujourd'hui, à la place de la liste des meilleures offres. Pas de nouvelle page ni de deuxième liste.
2. **Combien** : la dose de docs/86, **3 offres**, et **jusqu'à 5 quand le mois est à rattraper** (« On rattrape », docs/123 Q). Un jour sans recherche, en pause ou sans offre notée : comme aujourd'hui.
3. **Une offre à la fois** : le logo, le titre, l'entreprise, le lieu, la note en mot et sa jauge (docs/121 §C.5), la phrase « pourquoi » (§C.1) et au plus deux manques. « 1 sur 3 » en haut à droite.
4. **Deux boutons, de même taille** :
   - **« Garder »** : l'offre passe en « À préparer » (le statut « preparing », comme « Préparer ma candidature », sans ouvrir Préparer) ;
   - **« Écarter »** : l'offre passe en « Ignorée ».
   - Puis l'offre suivante glisse en place (250 ms ; rien avec « réduire les animations »). « Annuler » pendant 6 secondes dans le bandeau (docs/108).
   - Toucher le titre ouvre la fiche complète, comme aujourd'hui. « Plus tard » reste dans la fiche.
5. **Au clavier** : les deux boutons sont des boutons ordinaires (Tab, Entrée) ; **pas de balayage** obligatoire. Sur téléphone, balayer à droite ou à gauche fait la même chose, en plus des boutons.
6. **Quand c'est fini** : « Tri du jour terminé. » avec le petit visage ravi, le compte (« 2 gardées, 1 écartée ») et un lien vers « Commencées » si une offre a été gardée. Le reste des offres attend dans Offres (docs/86 : la dose est une proposition).
7. **La phrase du jour et son bouton** : « Examiner les offres » mène ici (la carte « À faire »), plus à la liste des Offres.

### G. Une 4e étape « Suivre » dans Préparer

1. **Après « Marquer comme envoyée »**, l'étape ④ **Suivre** s'ouvre (la carte « Candidature envoyée » reste, puis se ferme comme aujourd'hui).
2. **Trois lignes**, une par chose, séparées par un filet (docs/interface.md, Les listes) :
   - **Relance** : « Le 3 novembre, si l'employeur n'a pas répondu. » ; jobA1 la rappellera dans Aujourd'hui (comme aujourd'hui, à 10 jours). Une action : **« Changer la date »** (une date à soi, entre 5 et 30 jours).
   - **Preuve ORP** : « Complète » avec une coche, ou « Il manque l'adresse de l'entreprise » et une action **« Compléter »** (le champ sur place). Ce sont les champs de Job-Room déjà vérifiés dans le Suivi.
   - **Contact** : le nom de la personne de contact s'il est connu ; sinon **« Ajouter un contact »**.
3. **Le ton** : une phrase courte au-dessus des lignes, « Bien joué. jobA1 s'occupe du reste. », pas plus.
4. **Ensuite** : un lien « Voir dans le Suivi ».
5. Sur téléphone, l'étape ④ remplace le bouton fixé « Postuler » une fois la candidature envoyée.

## Garde-fous

- **Rien ne part à l'IA**, rien ne coûte : D et G réutilisent les notes, les phrases et les données déjà là.
- **Rien d'irréversible en un geste** : « Écarter » se rattrape (6 secondes, puis l'offre reste dans Offres › Ignorées).
- **La dose ne grossit pas en cachette** : 5 au plus, et seulement quand le mois ORP est à rattraper.
- Les écrans suivent `docs/interface.md` : un bouton plein au plus (« Garder »), « Écarter » en bouton secondaire de même hauteur ; peu de texte ; les trois audits à zéro avant la PR.

## Ce qui change dans le code (pour mémoire)

- **D** : un composant « offres du jour » dans Aujourd'hui ; la limite passe de 3 à 3 ou 5 selon le rythme du mois ; les changements de statut existent déjà (`PUT` du statut d'une offre).
- **G** : une date de relance propre à la candidature (une colonne `follow_up_on`, migration ; sans elle, 10 jours comme aujourd'hui) ; Aujourd'hui et le Suivi la lisent.

## Livraison proposée

- **0.97.0** : D et G ensemble (le geste quotidien, du tri à l'envoi).

## Les questions

1. **D, la dose** : 3 offres, 5 quand le mois est à rattraper : d'accord, ou 3 toujours ?
2. **D, « Garder »** : l'offre passe en « À préparer » (elle apparaît dans « Commencées ») : d'accord, ou préfères-tu qu'elle reste dans Offres, simplement marquée ?
3. **D, le balayage** sur téléphone, en plus des boutons : oui ou non ?
4. **G, la date de relance** modifiable par candidature (une migration) : d'accord, ou on garde 10 jours pour toutes ?
5. **Une version** : D et G ensemble en 0.97.0 ?

## Écarts (0.97.0)

- **Règles relues avant de construire** (`docs/interface.md`), vérifiées sur captures à 1440 et 390 px : la carte « À faire » avec une offre du jour, la fin du tri, l'étape ④ Suivre.
- **D, sans cadre** : l'offre du jour est posée dans la carte « À faire », sans carte à elle (pas de cadre dans un cadre). Le sous-titre devient « Offres du jour », l'onglet « Du jour » (au lieu de « Mieux notées »).
- **D, ce qui manque** : la phrase « pourquoi » dit déjà ce qui manque (« il manque Bicep ») ; « Il te manque : … » ne s'affiche que pour une offre notée avant score-v5, sans phrase.
- **D, l'enregistrement** : le statut part au serveur au bout de 6 secondes ou à la décision suivante, comme les autres « Annuler » (docs/108) ; s'il échoue, l'offre revient. Une offre gardée apparaît dans « Commencées » dès qu'elle est enregistrée. La fin du tri : « Tri du jour terminé. 2 gardées, 1 écartée. » avec le petit visage ravi et « Voir les commencées ».
- **D, le bouton de la phrase du jour** « Examiner les offres » mène à la carte « À faire » d'Aujourd'hui (`/aujourdhui#offres-du-jour`).
- **G, l'onglet ④ Suivre** n'apparaît qu'une fois la candidature envoyée ; « Marquer comme envoyée » y mène directement (la carte « Candidature envoyée » s'affiche par-dessus, comme avant).
- **G, la relance** : « Le 29 octobre, si l'employeur n'a pas répondu. » et « Changer la date » (un jour entre 5 et 30 jours après l'envoi, vérifié par le serveur). Le jour choisi vaut partout : Aujourd'hui, le Suivi, le rappel du téléphone, l'assistant et le bilan (une seule règle, `followups/remind.py`). Une nouvelle date remet le rappel à zéro. Une candidature déjà relancée ou avec une réponse : « Plus de relance prévue. ». Migration 0067 (`applications.follow_up_on`).
- **G, la preuve ORP** : la seule donnée qui peut manquer est l'adresse de l'entreprise (`core/orp.py`) ; « Compléter » ouvre le champ sur place.
- **G, le contact** : le nom de la personne de contact de la candidature, sinon celui d'une prise de contact ; « Ajouter un contact » mène aux contacts à côté (la carte « Contacts chez … »).
- **G, pas de « Voir dans le Suivi »** : le haut de la page a déjà « Voir le suivi » ; un deuxième lien aurait fait doublon.
- **Préparer sur téléphone** : avec quatre étapes, les onglets gardent leur numéro et leur nom sans l'icône ; une étape faite a son numéro en vert (sans la coche à côté, le « fait » reste pour les lecteurs d'écran) ; la barre tient à 390 px et défile sur un écran plus étroit, l'étape ouverte restant en vue.

## Vérifié (0.97.0)

- Tests backend : le jour de relance choisi (5 à 30 jours, sinon 422), la relance due ce jour-là et pas avant, de nouveau à 10 jours une fois la date effacée ; la candidature d'une offre. 621 tests, ruff, mypy.
- Tests de l'interface : une offre à la fois (« 1 sur 2 », pourquoi), Garder et Écarter envoyés après coup, « Annuler » qui remet l'offre, la fin du tri ; le balayage au doigt et pas à la souris ; la dose de 5 demandée ; l'étape Suivre (la date à 10 jours, la changer, compléter l'adresse, le contact connu, plus de relance une fois relancée). 433 tests, lint, vue-tsc.
- Les trois audits sur la démo à zéro.
