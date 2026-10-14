# 28 — Accessibilité : contraste, couleur seule, zones de clic (version 0.21.0)

> Statut : **validé** le 2026-10-14. livré.
> Retours d'usage du 2026-10-14 : comparaison avec le guide [Clay — UI elements](https://clay.global/blog/ux-guide/ui-elements) ; corriger trois écarts : le contraste du texte (§2), les informations données par la couleur seule (§3), les zones de clic trop petites sur téléphone (§4).

## 1. Le constat

| Règle du guide | Où ça coince |
|---|---|
| Texte contrasté à **4,5:1** au moins (WCAG 2.2) | gris très clair (compteurs, dates, aides) **2,8:1** ; orange des alertes en texte **2,7:1** ; vert **3,2:1** ; rouge **3,9:1** ; en mode sombre, le gris très clair **4,0:1** |
| **Jamais la couleur seule** pour dire un état | pastilles du calendrier du Suivi (statut d'une candidature = couleur), point rouge « à compléter » ; les étiquettes « manque » d'une offre (orange) ; le statut au survol seulement (invisible sur téléphone) |
| Zones de clic **44 × 44 px** sur téléphone | pastilles (mots-clés, suggestions de l'Assistant) ≈ 28 px ; liens « Copier », « Retirer », « Ajouter » ≈ 20 px ; × des panneaux ; poignées de la courbe des notes 18 px |

Rien ne change dans l'organisation des pages : seulement des couleurs, de petits symboles et des zones de clic agrandies.

## 2. Contraste du texte

**Une règle** : tout texte lisible atteint 4,5:1 sur le blanc **et** sur le gris clair des bandes, en mode clair comme en mode sombre. Les couleurs vives restent pour les fonds, bordures et pastilles ; le texte prend une version plus foncée de la même couleur.

| Usage | Aujourd'hui | Proposé (mode clair) | Contraste blanc / bande | Mode sombre |
|---|---|---|---|---|
| Texte secondaire très clair (compteurs, dates, aides) | `#9a9aae` — 2,8:1 | le gris secondaire actuel `#6e6e82` | 5,0 / 4,7 | `#9a9aae` (6,3:1) au lieu de `#76768e` (4,0:1) |
| Orange en texte (manques, offre expirée, « à relancer ») | `#e08a2e` — 2,7:1 | `#b45309` | 5,0 / 4,7 | `#f0a35a` (8,4:1) |
| Vert en texte (« reçue », « remis ») | `#19a385` — 3,2:1 | `#0f7a62` | 5,3 / 4,9 | `#3fc2a3` (7,9:1) |
| Rouge en texte (« Supprimer », erreurs) | `#e5484d` — 3,9:1 | `#c4373b` | 5,3 / 5,0 | `#ff7a7e` (6,9:1) |
| Violet sur fond sombre (liens) | `#8780ff` — 5,5:1 | inchangé | — | inchangé |

- Le gris très clair reste pour ce qui n'est **pas du texte** (traits, bordures, la flèche › décorative).
- Une petite vérification automatique est ajoutée aux tests : chaque couleur de texte du thème est mesurée contre ses fonds, et le test échoue sous 4,5:1.

## 3. Jamais la couleur seule

### 3.1 Calendrier du Suivi

- Chaque pastille porte **un symbole** en plus de sa couleur, lisible même en noir et blanc :

| Statut | Symbole |
|---|---|
| En attente | ○ (cercle vide) |
| Relancée | ↻ |
| Entretien | ◆ |
| Refus | ✕ |
| Engagement | ✓ |
| Sans réponse | – |

- « À compléter pour l'ORP » : un petit **« ! »** au coin de la pastille, plutôt qu'un point rouge.
- **Légende** sous le calendrier, sur une ligne et repliable : les six symboles avec leur nom.
- Sur **téléphone**, le statut au survol n'existe pas : un appui sur le jour affiche déjà ses cartes, avec le statut écrit. Les infobulles des pastilles restent pour la souris, mais n'apportent plus rien d'indispensable.

### 3.2 Ailleurs

- **Étiquettes « Demande » d'une offre** : une exigence non couverte par ton profil est aujourd'hui seulement orange ; elle reçoit un petit **✗** devant (« ✗ allemand B2 ») et son explication en texte pour les lecteurs d'écran.
- **Note des offres** : déjà le nombre en plus de la couleur ; rien à changer.
- **Résumé des alertes** : déjà l'état écrit à côté du point ; rien à changer.
- **Diagnostic** : chaque voyant a déjà son texte ; vérifié, rien à changer.

## 4. Zones de clic sur téléphone

Sur les écrans tactiles seulement (détectés par le navigateur), sans changer l'aspect :

- **Zone invisible agrandie** autour des petits éléments, jusqu'à 44 × 44 px : liens texte (« Copier », « Retirer », « Ajouter », « Masquer »…), pastilles, × des panneaux et de l'Assistant, cases à cocher.
- **Poignées de la courbe des notes** : 28 px au toucher (au lieu de 18).
- **Pastilles** (mots-clés de Mon domaine, suggestions de l'Assistant) : 44 px de haut au toucher, en gardant le même texte.
- Là où deux petits liens se touchent (par exemple « Nouvelle discussion » et « Effacer »), un écart suffisant pour que leurs zones ne se chevauchent pas.

## 5. Livraison

Une seule PR (**0.21.0**), sans migration et sans changement d'API.

## Points à valider

1. **Couleurs de texte** proposées (§2), le gris très clair réservé aux traits.
2. **Symboles du calendrier** et légende repliable (§3.1).
3. **✗ devant une exigence non couverte** (§3.2).
4. **Zones de clic agrandies** sur écran tactile seulement, sans changer l'aspect (§4).
5. **Une PR** (§5).

## Écarts avec la livraison

- **Couleurs de texte** un peu plus foncées que prévu pour l'orange et le vert (`#a34b07`, `#0b6f59`) : elles doivent aussi tenir 4,5:1 sur les **fonds teintés** des pastilles (« relancer », « suite attendue »), pas seulement sur le blanc. Ajout de **`--accent-text`** (`#5148f0`) pour le violet en texte sur fond violet pâle (pastilles, étiquettes « Offre », élément choisi) : 4,1:1 avant, 5,2:1 après. Couleurs en dur du calendrier et des alertes remplacées par ces jetons.
- **Test de contraste** (`contrast.test.ts`) : lit les couleurs du thème dans la feuille de style et vérifie, en mode clair et sombre, chaque couleur de texte sur les fonds de page et sur les fonds teintés des pastilles.
- **Calendrier** : pastilles un peu plus grandes (pour le symbole), « En attente » en cercle vide ; description lue par les lecteurs d'écran enrichie des statuts du jour (« 2 candidature(s) : en attente, entretien »). Légende repliable sous le calendrier, avec le « ! » à compléter.
- **✗** devant une exigence non couverte, et « Pas couvert par ton profil : » lu par les lecteurs d'écran.
- **Zones de clic** : seulement si le navigateur annonce un écran tactile (`pointer: coarse`) ; zone invisible de 44 px autour des liens texte et des ×, pastilles de 44 px de haut, cases à cocher et interrupteur plus grands, poignées de la courbe à 28 px, plus d'écart entre « Nouvelle discussion » et « Effacer ».
