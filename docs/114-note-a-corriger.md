# 114 — « Cette note ne me correspond pas » (version 0.84.0)

> Statut : **validé** le 2026-10-21 (« oui pour tout ») : le lien sur la fiche de l'offre seulement, les raisons telles quelles, la correction en bloc de profil visible, lieu, taux et contrat en critères, l'offre corrigée renotée aussitôt.
> Origine : ta demande du 2026-10-21, après l'article « The top UX design trends in 2026 » (UX Design Institute) : la personnalisation doit être expliquée **et corrigible** (« give users controls… include an easy way to correct inaccurate suggestions »).
> Se construit sur docs/06 (la note), docs/04 (le profil et les critères), docs/07 (les blocs proposés) et docs/11 §3 (« Renoter »).

## Le constat

- **La note s'explique déjà** : sur la fiche d'une offre, le cercle de la note, « Poste / Demande / Offre », les **points forts** et les **manques**, chacun relié au bloc de profil qui le prouve.
- **Elle ne se corrige pas.** Si l'IA note 78 une offre de vente alors que la personne cherche un poste de communicante, il n'y a rien à faire d'autre qu'ignorer l'offre. L'IA ne l'apprend pas : la prochaine offre de vente aura la même note.
- **Ce que l'IA sait de la personne** vient seulement de ses blocs de profil (expériences, compétences, formations, préférences, rédhibitoires). Une correction utile doit donc finir **dans le profil**, là où la personne la voit et peut la changer.

## La proposition

### 1. Où

- **Sur la fiche d'une offre notée**, sous le cercle de la note : un lien discret **« Cette note ne me correspond pas »**.
- Pas sur les cartes de la liste : la correction se fait en voyant le détail de la note (points forts, manques).

### 2. Deux questions, au clic

Dans la fiche, sans fenêtre par-dessus :

1. **« Elle est… »** : **trop haute** ou **trop basse** (deux pilules).
2. **« Pourquoi ? »** (une pilule à choisir, ou « Autre » avec un champ de 200 caractères) :

| Trop haute | Trop basse |
|---|---|
| Ce n'est pas mon métier | C'est bien mon métier |
| Pas mon niveau (trop junior ou trop senior) | J'ai l'expérience demandée |
| Le secteur ne m'intéresse pas | Le secteur me plaît |
| Le lieu, le taux ou le contrat | — |
| Autre | Autre |

### 3. Ce que jobA1 en fait

- **Le lieu, le taux ou le contrat** ne sont pas l'affaire de l'IA mais **des critères** (docs/04) : jobA1 propose directement le bon réglage, prérempli d'après l'offre (« Ajouter Lausanne aux lieux », « Taux minimum 80 % », « Écarter les CDD »), en un clic. Le filtre fera le reste, sans IA.
- **Les autres raisons** deviennent **un bloc de profil proposé**, à relire avant de l'ajouter :
  - trop haute, pas mon métier, sur « Vendeur·se en magasin » → bloc **Rédhibitoire** « Pas de postes de vente en magasin » ;
  - trop basse, c'est bien mon métier, sur « Chargée de communication » → bloc **Préférence** « Je cherche aussi les postes de chargée de communication ».
  - Le texte est rédigé par l'IA à partir de l'offre et de la raison (environ 0,001 $), ou par un modèle simple si l'IA n'est pas disponible ; la personne le modifie, puis **« Ajouter à mon profil »**, ou renonce.
- **L'offre corrigée est renotée aussitôt** (une note, environ 0,003 $), avec le nouveau bloc : la personne voit l'effet de sa correction.
- **Les offres suivantes** sont notées avec le nouveau profil. Les offres déjà notées le sont avec l'ancien : le bouton **« Renoter »** existant (docs/11 §3) les met à jour, sur clic, pour maîtriser le coût.

### 4. Ce que la personne voit et contrôle

- **Dans Profil**, le bloc ajouté est un bloc comme les autres, avec une mention « Ajouté en corrigeant une note » : modifiable, désactivable, supprimable.
- **Sur l'offre corrigée** : « Tu as corrigé cette note : trop haute, pas ton métier. » avec **« Annuler »** pendant 6 secondes (le bloc n'est pas ajouté, la note reste).
- **Rien n'est appris en cachette** : aucune correction ne change la note sans passer par un bloc visible, ou par un critère visible.

## Garde-fous

- **Une correction par offre** (la dernière remplace la précédente).
- **Le bloc proposé ne contient que ce que la personne a dit** : jamais une conclusion de l'IA sur elle (même règle que les blocs proposés, docs/07).
- **Pas dans la démo.**
- **Le plafond de l'IA s'applique** : au plafond, le bloc est proposé avec le modèle simple et la renotation attend.

## Écarts

- **Où** : sous le cercle de la note et ses explications, dans la fiche de l'offre ; le lien n'existe que pour une offre notée. Une correction déjà faite se lit à cet endroit (« Tu as corrigé cette note : trop haute, ce n'est pas mon métier. ») avec « Corriger à nouveau ».
- **La carte des deux questions** est blanche et bordée (on modifie, docs/110), sur le fond gris de la fiche ; les réponses sont des pilules, la choisie en bleu.
- **« Autre »** demande quelques mots (200 caractères) avant de proposer quoi que ce soit.
- **Le bloc proposé** montre son type (Préférence ou Rédhibitoire), son titre et « Ce que l'IA lira », modifiables ; « Ajouter à mon profil » ou « Annuler ».
- **Lieu, taux, contrat** : jobA1 propose ce qu'il peut préremplir d'après l'offre (« Taux minimum 70 % » si l'offre va jusqu'à 60 % ; « Écarter les stages » si l'annonce parle de stage, de même pour l'apprentissage, le temporaire et l'indépendant), plus **« Régler mes critères »**, qui ouvre Profil. Le lieu se règle là : une liste de lieux acceptés ne se devine pas depuis une seule offre.
- **« Annuler »** : la correction part au serveur au bout de 6 secondes (comme les autres actions, docs/108) ; la fiche la montre aussitôt.
- **L'IA rédige le bloc** avec un court appel (`correction-v1`, compté sous « correction ») qui ne reçoit que le titre, l'entreprise, le résumé du poste et ce que la personne a dit ; sans IA ou au plafond, un modèle simple (« Les postes comme « … » ne correspondent pas à mon métier. »).
- **Dans Profil**, le bloc porte la mention « ajouté en corrigeant une note » ; le supprimer laisse la correction, sans bloc.
- **Une correction par offre** : la dernière remplace la précédente ; un bloc déjà ajouté reste dans le profil (à retirer dans Profil).

## Vérifié

- Tests backend : les raisons selon le sens (une raison de l'autre sens refusée), l'offre inconnue ; le bloc du modèle simple (titre de l'offre, mot de la personne) et celui de l'IA (appel compté, offre renotée) ; lieu, taux, contrat → taux minimum et contrat préremplis, le critère enregistré et l'offre écartée par le filtre ; le bloc ajouté avec sa mention, une correction par offre, le bloc supprimé dans Profil. Nouvelle table personnelle (`score_corrections`, règles par compte). 579 tests, ruff, mypy.
- Tests de l'interface : les deux questions, les raisons qui suivent le sens, le bloc modifié puis envoyé au bout de 6 secondes, le critère en un clic et le lien vers les critères, « Autre » et ses mots, la correction déjà faite. 403 tests, lint, vue-tsc.
- Captures Playwright à 1280 et 414 px : le lien sous la note, les questions, le bloc proposé.

## Décisions (2026-10-21)

Ta réponse : « oui pour tout ». Retenu, là où la question proposait deux voies, la première : le lien sur la fiche seulement, les raisons sans ajout.

### Les questions posées

1. **Où** : seulement sur la fiche d'une offre (sous la note), ou aussi dans le menu « ⋯ » des cartes ?
2. **Les raisons** du tableau : elles te vont ? En ajouter (par exemple « Trop loin de chez moi », séparé du lieu) ?
3. **Une correction devient un bloc de profil**, visible et modifiable, plutôt qu'une liste cachée de corrections envoyée à l'IA : d'accord ?
4. **Lieu, taux, contrat → un critère** proposé en un clic, plutôt qu'un bloc : d'accord ?
5. **L'offre corrigée renotée aussitôt** (environ 0,003 $), les autres seulement sur « Renoter » : d'accord ?
