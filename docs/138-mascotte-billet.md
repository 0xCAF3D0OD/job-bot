# 138 — La mascotte de l'entraînement : le billet (brief pour l'illustration)

> Statut : **direction choisie** le 2026-10-30 ; le dessin final est à commander.
> Origine : ta demande du 30 octobre (« aide-moi à avancer sur la mascotte »). Trois pistes proposées (le billet, la mallette, le galet qui pousse) ; tu as retenu le billet.
> Se construit sur docs/137 (l'entraînement, la ligne jusqu'au jour J, le mouvement) et sur la page Figma « Planche · Entraînement · Écrans (style freud) », section « Mascotte · le billet ».

## 1. En clair

- **Un billet de train qui fait le trajet avec la personne**, de sa première séance jusqu'à l'entretien. À chaque arrêt terminé, il est **poinçonné** ; le jour J, il est complet.
- Il remplace le robot provisoire, trop proche du robot vert du kit de référence, que le brief demandait de ne pas reprendre.
- **Il n'existe que dans l'entraînement.** Ailleurs dans jobA1, la mascotte reste le visage du 1. Les deux ne sont jamais dans le même écran.
- Les croquis de Figma fixent la direction ; **le dessin final est à confier à un illustrateur ou une illustratrice**, avec ce brief.

## 2. Le personnage

| | |
|---|---|
| **Ce qu'il est** | un billet de train, carré aux coins très arrondis, avec les deux encoches latérales d'un billet et une ligne de pointillés en haut (la zone à détacher) |
| **Son rôle** | un compagnon de voyage calme, pas un coach : il rassure, il ne juge pas, il ne presse jamais |
| **Sa personnalité** | bienveillant, un peu malicieux, jamais moqueur ; il se réjouit des petits progrès |
| **Ce qu'il n'est pas** | ni un robot, ni un animal, ni un personnage humain ; aucune ressemblance avec la mascotte de Duolingo, avec le robot du kit « freud » ni avec un billet de transport réel (logo ou couleurs des CFF, par exemple) |

## 3. Ce qu'il faut dessiner

### Les expressions (4)

| Expression | Quand | Indications |
|---|---|---|
| **Contente** | par défaut : consigne, parcours | yeux ronds, petit sourire, joues roses |
| **Réfléchit** | pendant que l'IA lit une réponse | regard vers le haut, bouche en petit « o » |
| **On s'accroche** | après une réponse à revoir | sourcils froncés, bouche droite : déterminé, jamais triste ni déçu |
| **Ravie** | réponse juste, fin de séance, jour J | yeux plissés, grand sourire ouvert |

### Les poinçons (0 à 5)

- Une rangée de **5 emplacements** en bas du billet, un par arrêt (l'entreprise, le poste, toi, les questions qui piquent, l'entretien blanc).
- Un emplacement vide est un petit cercle en pointillés ; un emplacement poinçonné est **un vrai trou**, qui laisse voir le fond de l'écran.
- À 5 sur 5, le billet est « complet » : c'est le jour J.

### Les tailles

Il doit rester lisible de **44 px** (sur la ligne, à l'arrêt en cours) à **132 px** (fin de séance, jour J), en passant par 56 px (à côté de la consigne). À 44 px, les poinçons peuvent se simplifier, mais le visage doit rester clair.

### Le mouvement (un seul)

Au retour d'une séance terminée, **le billet est poinçonné** : le trou apparaît (250 ms), le billet passe en « ravie », puis glisse le long du rail jusqu'à l'arrêt suivant (500 ms) et redevient « contente ». Rien ne bouge en boucle. Le détail est dans docs/137 et dans la planche Figma « Mouvement · fin de séance ».

## 4. Les contraintes techniques

- **Couleurs** : celles du mode Entraînement de Figma, pas de couleur en dur.
  - le corps en `mustard` ;
  - les joues en `orange`, à 35 % ;
  - les encoches et les trous en `bg`, pour qu'ils laissent voir le fond, en clair comme en sombre.

  L'encre du visage et les pointillés gardent la même couleur dans tous les thèmes, parce que le corps reste clair : `ticket-ink` (`#4B3425`) et `ticket-dash` (`#C78A00`). Ce sont deux variables créées par la session Design, avec la même valeur dans les quatre modes. Il ne reste aucune couleur en dur.
- **Livrable** : du vectoriel, en SVG plat, sans dégradé ni ombre, à l'épaisseur de trait régulière, avec des calques nommés (corps, encoches, pointillés, joues, yeux, bouche, poinçon 1 à 5). Il doit pouvoir se recolorer par les variables.
- **Accessibilité** : le billet est **décoratif** (`aria-hidden`, nom vide). L'avancée est toujours dite aussi en texte (« 2 arrêts sur 5 »), jamais par les seuls poinçons.
- **Droits** : une création originale, avec cession des droits d'usage pour jobA1 (application, site, communication).

## 5. Ce qu'on demande à l'illustrateur ou l'illustratrice

1. Deux ou trois propositions de dessin du billet « contente », dans l'esprit des croquis (rond, plat, chaleureux).
2. Après le choix : les 4 expressions, les poinçons de 0 à 5, et une vérification à 44 et à 132 px, en clair et en sombre.
3. Les fichiers SVG, avec les calques nommés.

## Points à valider

1. **Le billet** comme mascotte de l'entraînement, et seulement de l'entraînement (§1).
2. **Les 4 expressions** et leur usage (§3).
3. **Les poinçons** comme marque d'avancée, toujours doublés d'un texte (§3, §4).
4. **L'encre et les pointillés fixes**, par les variables `ticket-ink` et `ticket-dash` (§4).
5. **Commander le dessin final** à un illustrateur ou une illustratrice, avec ce brief (§5).

## Écarts

- **Planche validée** le 30 octobre. La session Design a créé le composant « Mascotte · billet » dans la page Composants : 24 variantes (Expression × Poinçons de 0 à 5), à 120 × 132.
- La taille ne passe pas par une variante, mais par la mise à l'échelle de l'instance (44, 56, 88 ou 132 px de haut). Le thème suit le mode du cadre : pas de variante non plus.
- Les 35 billets des écrans de l'entraînement, et ceux des planches, sont des instances de ce composant. Le jour où l'illustration finale arrive, il suffit de mettre à jour le composant.
