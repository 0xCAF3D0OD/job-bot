# 119 — Une structure cohérente, et toutes les règles au même endroit (version 0.89.1)

> Origine : ton retour du 2026-10-21 sur Aujourd'hui : « regarde comment le texte est proche du bord, quelle utilité d'avoir une carte si grande, on n'en a pas discuté plus tôt ? Pourquoi un énorme vide gris entre les cartes ? J'aimerais une structure claire et surtout cohérente sur toute la plateforme. Il n'y a pas une règle pour ce genre de chose dans la doc ? Reprends toutes les docs UI/UX. »

## Pourquoi c'est arrivé

Les règles existaient : 1,5 rem de marge dans une carte et 1,25 rem entre les cartes (docs/93), la même hauteur pour les cartes d'une rangée (docs/32, 43, 93), 2 rem entre les grands blocs d'Aujourd'hui (docs/95), une liste courte qui ne laisse pas la moitié d'une carte vide (docs/63). Mais elles n'étaient écrites que dans leur document d'origine ; `docs/interface.md`, que je relis avant chaque interface, n'en avait pas la moitié. Relu : 14 documents d'interface ; **18 règles** manquaient. Elles sont reportées dans `docs/interface.md`, section « La structure ».

Une contradiction tranchée : docs/63 (0.48.2) laissait chaque carte d'Aujourd'hui « à sa hauteur » ; docs/93 (0.70.6, plus récent) veut la même hauteur dans une rangée. La plus récente l'emporte.

## Ce qui change

- **Les repliables** (« Comment ça marche », « Pour bien démarrer », le journal, Alertes existantes, partout) : 1,5 rem de marge, comme les cartes, au lieu de 0,9 rem. Le texte n'est plus collé au bord.
- **« Masquer »** : sur la ligne du titre du repliable ouvert, plus sur une ligne vide à lui.
- **« Pour bien démarrer »** ouvert, sur ordinateur : les six étapes en deux colonnes ; la carte fait moitié moins haut.
- **Aujourd'hui** : « À faire » et « Mois ORP » de la même hauteur ; 2 rem entre chaque grand bloc (la phrase du jour, les bandeaux, les cartes, les guides), au lieu de 3,25 rem sous les cartes.
- **Rendez-vous ORP** : les cartes côte à côte de la même hauteur, 1,25 rem entre elles ; « Ce qui revient dans les offres et te manque » devient « Compétences demandées qui manquent ».
- **Bilan et tableaux** : 1,5 rem de marge dans les cartes, aussi sur téléphone (1,1 rem avant).
- **L'audit des règles** (`regles.py`) vérifie en plus le texte à 1,25 rem au moins du bord de sa carte, la même hauteur dans une rangée, et « te, me » dans les titres.

## La Cheatsheet

docs/59 et docs/63 citent *The UI & UX Cheatsheet* (Marc Andrew, 21 conseils), que tu m'avais donnée. Elle n'est pas dans le dépôt : seuls les numéros cités le sont (n° 4, 5, 8, 15, 16, 18, 21). Si tu veux que ses conseils soient repris dans `docs/interface.md`, redonne-la-moi.

## Vérifié

- Les trois audits sur la démo, 1440 et 390 px : règles 0, rangées 0, accessibilité 0 grave, 0 mineur, clavier sans blocage.
- Captures d'Aujourd'hui (ordinateur et téléphone, « Pour bien démarrer » ouvert) et du Rendez-vous ORP.
- 409 tests de l'interface, lint, vue-tsc.

## Complément 0.90.2 : les pastilles du calendrier

Ton retour du 2026-10-22, capture du Suivi à l'appui : les pastilles ne respectaient pas les règles.

- **Le « ! »** sur une pastille (ligne ORP à compléter) était un caractère utilisé comme icône (iconographie 1), dans un badge rouge qui débordait sur la pastille voisine. Il devient **un anneau orange** autour de la pastille : l'orange est la couleur de ce qui demande d'agir (structure 16), comme « relancer ». Le rouge reste au seul « Refus ».
- **« En attente »** : un blanc écrit en dur, éblouissant en sombre ; désormais le fond de la carte avec un contour gris.
- **L'espacement** : 0,65 rem entre deux pastilles (0,2 rem avant, puis deux règles qui se contredisaient, fusionnées en une) ; les anneaux ne se touchent plus.
- **Pour les lecteurs d'écran**, le jour dit aussi « à compléter pour l'ORP ».

Vérifié : captures en sombre et en clair, à 1440 et 390 px, un jour à trois pastilles dont deux à compléter ; les trois audits à zéro ; 409 tests, lint, vue-tsc.
