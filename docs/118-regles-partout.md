# 118 — Les règles de l'interface, partout (version 0.89.0)

> Statut : **à valider**.
> Origine : ta question du 2026-10-21, après la 0.86.1 : « est-ce qu'on peut regarder pour les règles UI/UX qu'on a commencées un peu plus tôt ? ». La 0.86.1 a appliqué `docs/interface.md` à la page Alertes ; ce cadrage l'étend aux autres pages.

## Le constat

Un relevé automatique sur la démo (19 pages, 1440 et 390 px) compte ce que les règles interdisent ou limitent :

| Page | Mots d'aide | Ce qui ne va pas |
|---|---|---|
| Réglages (toutes les rubriques sur téléphone) | 123 | 9 descriptions, dont 4 de plus de 20 mots (« Dès cette note, l'annonce est cherchée… », « La plateforme lit leurs e-mails d'alerte… », « Vacances, maladie… », le résumé des données) |
| Rendez-vous ORP | 74 | 6 textes d'aide ; un titre avec « ton » : « Le message pour ton conseiller » |
| Profil › Parcours | 56 | une aide de plus de 20 mots (« Avant l'IA, ton nom… ») |
| Profil › Coordonnées | 22 | une aide de plus de 20 mots ; une **barre verticale** dans la carte (le repliable) |
| Suivi | 36 | 8 petites aides ; **deux barres verticales** (les repliables) |
| Aujourd'hui | 16 | une **barre verticale** (« Pour bien démarrer ») |
| Données personnelles | 10 | un titre avec « tu » : « Ce que tu peux faire » |
| Offres, Bilan, Actualités, Formations, Alertes | 0 à 14 | rien à signaler |

Deux choses à noter :

- **Les barres verticales** viennent toutes du même composant (`DisclosureRow`) : son contenu ouvert a un trait à gauche. La règle (Réglages 2) l'interdit dans une carte ; c'est ce que j'ai corrigé à la main pour « Alertes existantes ».
- **Deux règles se contredisent** : « Comme les CFF » (docs/110) veut, dans Réglages, une description grise **toujours visible** sous chaque réglage ; « Titres et textes 5 » (docs/88) veut que **ce qui explique passe au survol ou disparaisse**. Les Réglages suivent la première, d'où leurs 123 mots.

Le relevé ne voit pas les pages absentes de la démo ou qui demandent un clic : la fiche d'une offre (avec « Cette note ne me correspond pas »), Préparer, l'accueil, l'assistant des alertes. Je les relirai sur captures.

## La proposition

### 1. Trancher la contradiction

- **La description d'un réglage reste visible, en une ligne** (12 mots environ) : elle dit ce que fait le réglage. Le reste (le pourquoi, le coût, les exceptions) passe au survol (`HoverNote`, le « i » sur téléphone).
- La règle « Comme les CFF 1 » est réécrite dans ce sens ; « Titres et textes 5 » ne change pas.

### 2. Corriger ce que le relevé a trouvé

- **Plus de barre verticale** dans les repliables (`DisclosureRow`), partout : le contenu s'ouvre sous le titre, au même retrait.
- **Les descriptions longues** coupées à une ligne, le reste au survol : les 4 des Réglages, Parcours, Coordonnées.
- **Les titres** : « Message au conseiller », « Ce qui est possible ».
- **Rendez-vous ORP et Suivi** : chaque petite aide relue ; gardée si elle dit une erreur ou quoi faire, sinon au survol ou retirée.

### 3. Relire les pages hors démo

La fiche d'une offre, Préparer, l'accueil, l'assistant des alertes : captures à 1440 et 390 px, chaque règle de `docs/interface.md` vérifiée, la liste de ce qui change dans ce document avant de corriger.

### 4. Un troisième audit, pour que ça tienne

`frontend/scripts/regles.py`, sur la démo, comme les deux autres : il échoue si une description dépasse 20 mots, si un titre contient « je, tu, ton, ta, tes, mon, ma, mes » ou finit par « ? », s'il y a une barre verticale ou deux cadres l'un dans l'autre dans une carte. Ajouté à la règle « avant une PR d'interface » (contrôles 4 et 5).

## Les questions

1. **§1** : la description d'un réglage en une ligne, le reste au survol : d'accord ?
2. **§2** : plus de barre verticale dans aucun repliable, même hors carte (le journal, la page Alertes) : d'accord ?
3. **§3** : je te montre la liste des pages hors démo avant de corriger, ou je corrige directement ?
4. **§4** : le troisième audit, avec la limite de 20 mots : d'accord, ou une autre limite ?
