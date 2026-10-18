# 74 — Les actions rangées dans « ⋯ » (version 0.61.0)

> Statut : **validé** le 2026-10-18.
> Origine : retour du 2026-10-18 sur le panneau d'une offre. Dans la partie « Entreprise », l'adresse est noyée sous quatre liens (« Modifier », « Chercher l'adresse », « Chercher l'offre chez l'employeur », « Contacts »). Consigne : dans chaque partie, garder le contenu visible et ranger les actions dans « ⋯ », sauf une action importante, qui peut rester visible. Appliquer la même règle partout où le cas se présente.

## 1. Le constat

- **Les actions se mélangent au contenu.** Dans plusieurs parties, une ligne de liens bleus suit chaque information. L'œil ne sait plus ce qu'il faut lire et ce qu'on peut faire.
- **Le menu « ⋯ » existe déjà**, mais seulement à deux endroits : en haut du panneau d'une offre (J'ai postulé, Plus tard, Ignorer…) et en haut du panneau d'une candidature (Modifier, Supprimer). Ailleurs, chaque action a son lien.
- **Le cas se répète** : l'inventaire de la plateforme trouve une dizaine de parties ou de lignes de tableau avec trois à cinq actions visibles côte à côte (§4).

## 2. La règle

Pour chaque partie (ou chaque ligne d'un tableau) :

1. **Le contenu reste visible** : l'adresse, le statut, les dates, le texte.
2. **Au plus une action importante reste visible**, quand elle fait avancer la recherche : « Préparer l'entretien », « Utiliser », « Ajouter l'adresse » quand elle manque.
3. **Le reste va dans « ⋯ »**, en haut à droite de la partie (ou au bout de la ligne, dans un tableau).
4. **Les suppressions vont toujours dans « ⋯ »**, en dernier, en rouge, séparées des autres par un filet. Elles demandent toujours une confirmation, comme aujourd'hui.
5. **Un « ⋯ » n'apparaît que s'il contient au moins une action.** Une partie qui n'a qu'une action la garde visible, sans menu.

**Ce qui se passe après un clic dans « ⋯ »** se voit dans la partie elle-même, comme aujourd'hui. Par exemple, « Recherche en cours… » puis « Adresse trouvée dans le registre IDE » s'affichent sous l'adresse. Le formulaire « Modifier l'adresse » s'ouvre aussi à la place de l'adresse.

## 3. Ce qui reste visible, sans menu

Certaines actions sont le contenu lui-même, ou une étape d'un parcours. Elles ne bougent pas :
- les **« Copier »** à côté de chaque champ (Pour l'ORP, recopie dans Job-Room, À recopier sur le site de l'employeur) ;
- les **téléchargements qui sont le but de la carte** : « PDF » et « Word » de la lettre et du CV ;
- les **listes de liens** qui sont le contenu, comme « Trouver quelqu'un » dans les contacts ;
- les **choix d'un parcours** : l'assistant des alertes, la relance (« Ouvrir dans ma messagerie », « Copier », « Marquer comme relancée »), « Garder » ou « Écarter » une formation, « Acceptée » ou « Refusée » pour un financement ;
- les **boutons d'un formulaire** (« Enregistrer », « Annuler ») ;
- la **barre principale du panneau d'une offre** : « Préparer ma candidature » et « Postuler chez l'employeur ».

## 4. Ce qui change, partie par partie

| Où | Reste visible | Va dans « ⋯ » |
|---|---|---|
| **Offre › Entreprise** | l'adresse et sa source ; la ligne « trouvée chez l'employeur » ou « pas trouvée » ; **« Ajouter l'adresse »** seulement si elle manque | Modifier l'adresse · Chercher l'adresse (registre IDE) · Chercher l'offre chez l'employeur (ou « Chercher à nouveau ») · Contacts (2) · Vérifier la source ↗ |
| **Offre › Annonce** | le texte, « Lire toute l'annonce » | Voir sur jobs.ch ↗, Voir sur LinkedIn ↗… (un lien par site) |
| **Offre › menu du haut** | inchangé | « Chercher chez l'employeur » en sort : il passe dans « Entreprise » |
| **Suivi › tableau des candidatures**, chaque ligne | l'entreprise (qui ouvre le panneau), le poste, le statut | Lettre (Word) · CV (Word) · Ouvrir l'annonce ↗ · Modifier · Supprimer |
| **Candidature › Entretiens** | la date ; **« Préparer l'entretien »** s'il est à venir, **« Faire le point »** s'il est passé sans retour | Ajouter à mon agenda · Voir le retour · Ajouter un autre entretien |
| **Contacts**, chaque prise de contact | le nom, la note ; **« A répondu »** tant qu'il n'a pas répondu | Modifier la note · Retirer |
| **Preuves ORP**, la barre du mois | **l'étape suivante** (« Compléter 3 lignes » ou « Marquer comme remis ») ; **« Recopier dans Job-Room »** | Télécharger le PDF, puis ce qui est aujourd'hui dans « Plus d'options » : export CSV, journal des recherches, choisir les colonnes. « Plus d'options » disparaît. |
| **Alertes › Mes alertes**, chaque ligne | la recherche, les sites et leurs cases | Modifier · Mettre de côté · Supprimer |
| **Réglages › Tes profils**, chaque profil | le nom ; **« Utiliser »** | Dupliquer · Renommer · Supprimer |
| **Réglages › Comptes** (exploitant), chaque compte | le nom, le plafond de l'IA | Lien de nouveau mot de passe · Suspendre (ou Réactiver) · Supprimer |
| **Réglages › Sources des Actualités** | **« Parcourir les suggestions »** | Nouvelle veille · Ajouter par adresse |
| **Profil › un document du parcours** | le texte ; **« Créer un bloc avec la sélection »** quand du texte est sélectionné | Ouvrir le fichier ↗ · Supprimer ce document |
| **Assistant**, en haut | **« Nouvelle discussion »**, la croix | Effacer la discussion |

**Inchangés**, parce qu'ils n'ont qu'une action par partie : Aujourd'hui, la liste des offres, la préparation d'une candidature, les Formations, les Actualités, le Bilan, Agenda et Extension dans les Réglages.

## 5. Le menu « ⋯ » lui-même

Le composant commun `MoreMenu` (docs/50) est réutilisé partout, avec ses comportements actuels : Échap ferme le menu seul et rend le focus à « ⋯ », un clic ailleurs le ferme, les flèches passent d'une action à l'autre.

Ce qui s'ajoute :
- **des liens dans le menu** : une page externe s'ouvre dans un nouvel onglet, avec « ↗ » ; un fichier se télécharge (Lettre, CV, agenda) ;
- **un filet avant les suppressions**, en rouge, en dernier ;
- **un nombre à côté d'une action** : « Contacts (2) » ;
- **sur téléphone** : un « ⋯ » assez grand pour le doigt (2,75 rem), et un menu qui ne sort jamais de l'écran. Il s'ouvre vers le haut s'il n'a pas la place en dessous.
- **un nom pour chaque « ⋯ »**, lu par les lecteurs d'écran : « Actions sur l'entreprise », « Actions sur la candidature Exemple SA »…

## 6. Ce qui ne change pas

- Les actions elles-mêmes : mêmes libellés, mêmes confirmations, mêmes résultats.
- Le serveur et les données : la PR ne touche que l'interface.

## 7. Livraison

Une PR, **0.61.0**, sans migration.

Vérification :
- sur captures, ordinateur et téléphone, avec la démo (`make demo`), partie par partie, avant et après ;
- au clavier, pour chaque menu ajouté ;
- les tests existants adaptés : chaque action garde son `data-test`, désormais dans le menu.

## Points à valider

1. **La règle** : contenu visible, au plus une action importante visible, le reste dans « ⋯ », suppressions toujours dans « ⋯ » (§2).
2. **Ce qui reste visible sans menu** : les « Copier », les téléchargements PDF et Word, les listes de liens, les parcours, les formulaires (§3).
3. **Le tableau du §4**, partie par partie. En particulier :
   - « Contacts » rangé dans le « ⋯ » d'Entreprise, avec son nombre ;
   - « Recopier dans Job-Room » gardé visible dans les Preuves ORP ;
   - « Plus d'options » des Preuves ORP remplacé par le « ⋯ ».
4. **Le menu « ⋯ »** avec des liens, un filet avant les suppressions, et adapté au téléphone (§5).
5. **Une PR 0.61.0**, sans migration (§7).

## Écarts avec le cadrage

- **Entreprise** : le menu reprend les actions possibles pour l'offre. « Chercher l'adresse » n'y est pas quand l'adresse vient de l'annonce ou a été saisie à la main, comme avant. La recherche en cours s'affiche sous l'adresse (« Recherche dans le registre IDE… », « Recherche chez l'employeur en cours… »). « Contacts » porte son nombre : « Contacts (2) ».
- **Annonce** : le « ⋯ » n'apparaît que s'il y a un autre site que celui du bouton « Postuler ».
- **Preuves ORP** : la case « Joindre au PDF le journal des recherches » devient une action du menu, « PDF avec le journal des recherches (42) ». « Colonnes affichées » ouvre la liste des colonnes sous la barre, avec « Terminé » pour la refermer.
- **Contacts** : « Modifier la note » passe dans le menu une fois la réponse notée ; « Retirer » y est toujours.
- **Sur téléphone** : le menu se place au-dessus de la barre du bas (« Préparer ma candidature »), et la page défile si besoin pour le montrer en entier ; les « ⋯ » font 2,75 rem au doigt.
- **Lecteurs d'écran** : un lien de menu vers une autre page annonce « (nouvel onglet) ».
- **Vérifié** sur captures avec la démo, ordinateur et téléphone : Entreprise, tableau du Suivi, Preuves ORP. Les profils d'essai et les comptes ne s'affichent que pour l'exploitant : vérifiés par les tests.

- **Alignement** (retour du 2026-10-18) : le « ⋯ » était un caractère de texte, posé plus bas que le centre selon la police. Ce sont maintenant trois points dessinés, centrés dans un bouton de 2,25 rem. Mesuré dans le navigateur, ordinateur et téléphone : écart de 0 px avec le texte voisin (« ← Offres », titres des parties, « Recopier dans Job-Room », lignes du Suivi, contacts). Dans l'en-tête d'une candidature, il est centré sur la première ligne quand le texte passe à la ligne. Le « ⋯ » d'un contact est sur la ligne de son nom.
- **Panneau d'une candidature trop large** (vu en vérifiant l'alignement) : un long lien dans « Pour l'ORP » élargissait le panneau au-delà de l'écran et coupait le « ⋯ » et les « Copier ». Le lien passe maintenant à la ligne.
