# 147 — jobA1 en sept langues

> Statut : **plan validé par Kevin le 2026-11-17** (13 h 30), avec six ajouts obligatoires et ses réponses aux questions. Aucun code encore : la PR 1 attend la planche ReglagesLangue redessinée par Kevin, la fusion de #833 et celle du fil Compte et Réglages.
> Origine : la demande de Kevin du 2026-11-17 : « commencer à pouvoir choisir la langue de la plateforme […] anglais, allemand, italien, albanais, portugais et espagnol, en plus du français ».
> Décisions : `docs/decisions/2026-11-17-1330-langues-plateforme.md`, `docs/decisions/2026-11-17-1330-poids-catalogues-langues.md`.
> Glossaire : `docs/i18n/` (un fichier par langue).

## 1. Les langues

| Langue | Code du texte | Formats (Intl) | Tutoiement | Activée |
|---|---|---|---|---|
| Français | fr-CH | fr-CH | tu | oui (langue source) |
| Allemand | de-CH (sans « ß », toujours « ss ») | de-CH | du | après relecture, en premier |
| Italien | it-CH | it-CH | tu | après relecture, en premier |
| Anglais | en-GB | en-CH (voir §4) | you | après relecture |
| Albanais | sq | sq | ti | après relecture |
| Portugais | pt-PT | pt-PT | tu | après relecture |
| Espagnol | es-ES | es-ES | tú | après relecture |

Une langue non relue reste visible et grisée « Bientôt » dans le sélecteur, même si ses textes sont prêts. Elle n'est activée qu'après la relecture d'une personne dont c'est la langue maternelle (qui relit : à compléter par Kevin).

## 2. Deux langues séparées

- **La langue de l'interface** : écrans, notifications, réponses de l'IA. Réglage « Langue » de Réglages.
- **La langue des documents** : lettre et CV, choisie dans Préparer (FR, DE, EN). Changer la langue de l'interface ne change jamais la langue d'un document. L'italien n'est pas ajouté aux lettres pour l'instant.
- Restent aussi dans leur langue propre : la fiche et les documents pour l'ORP (la langue du canton), le texte des annonces (langue d'origine), l'analyse des certificats.

## 3. Comment c'est construit

1. **Une fonction maison `t()`**, pas de vue-i18n (environ 15 Ko gzip sur chaque page).
2. **Le français reste le texte du code** : `t("Écarter l’offre")`. En français, rien de plus n'est téléchargé et les captures restent identiques au pixel.
3. **Un catalogue par page et par langue**, découpé comme le code (les pages de `poids.mjs`), chargé seulement quand la langue n'est pas le français. Une traduction manquante affiche le français, jamais un vide.
4. **Premier lancement** : la langue du navigateur si elle fait partie des sept, sinon le français. Un choix enregistré passe toujours avant.
5. **Où la langue est gardée** : sur l'appareil dès la PR 1, puis sur le compte (S1, voir §6), pour que le serveur écrive dans la bonne langue.
6. **`<html lang>`** suit la langue de l'interface. Un bloc dans une autre langue (texte d'une annonce, lettre affichée) porte son propre attribut `lang` (WCAG 3.1.2).
7. **Pages légales** : traduction relue, avec la mention « La version française fait foi. »

## 4. Formats, pluriels, accords

- **Dates, nombres, montants : toujours par `Intl`**, jamais écrits à la main dans une traduction. Les 15 fichiers qui écrivent `"fr-CH"` en dur (dont `format.ts` et `dates.ts`) passent par une seule fonction qui donne la locale de formatage.
- Variante suisse : fr-CH, de-CH, it-CH. En allemand, `Intl` donne « 12'345.5 » et « CHF 1'000.00 ».
- Proposition pour l'anglais : texte en-GB, formats **en-CH** (« 1'000 », « 17.11.2026 »), parce qu'en-GB donnerait « 1,000 », trompeur en Suisse. ICU n'a pas de variante suisse utile pour l'albanais, le portugais et l'espagnol : formats sq, pt-PT, es-ES.
- **Pluriels par `Intl.PluralRules`** : chaque texte qui dépend d'un nombre a une forme par catégorie de la langue (`one`, `other`, et `many` en français, italien, portugais et espagnol). Plus de phrases construites en collant des morceaux (`plural()` de `format.ts` sera remplacée écran par écran).
- **Accords** : une phrase entière par cas, avec des variables nommées (`{entreprise}`, `{n}`), jamais un mot glissé dans une phrase traduite à part.

## 5. Glossaire figé

- `docs/i18n/glossaire-<langue>.md` : un tableau par langue, une ligne par terme, avec un identifiant stable, le terme français, le terme retenu, sa source et son statut.
- Termes officiels du SECO (arbeit.swiss) et des cantons quand ils existent. Pour l'anglais, l'albanais, le portugais et l'espagnol, le SECO ne publie presque rien : ces termes sont des propositions, marquées « à relire ».
- Le glossaire est figé : un terme ne change que par une décision de Kevin, puis dans tous les écrans à la fois.
- `make i18n-check` (ajouté à `make audits-ci` en PR 1) lit ces tableaux et refuse une traduction qui contient le terme français d'une ligne du glossaire sans le terme retenu de sa langue.

## 6. Découpage en PR

**PR 1, l'outil et le sélecteur** : après la planche ReglagesLangue à sept langues de Kevin, #833 et le fil Compte et Réglages. `t()` et ses pluriels, catalogues à la demande, langue de l'appareil et du navigateur, `<html lang>`, locale de formatage, sélecteur, mesure de poids des catalogues, `make i18n-check`. Aucun écran traduit. Le surpoids de `t()` est compensé dans la PR.

**Une PR par écran ensuite**, les sept langues à la fois, et dans la même PR les notifications et les réponses de l'IA qui concernent cet écran (pas de PR à part plus tard). Ordre :

- **Lot A, dès la PR 1 fusionnée** (aucun fil n'y touche) : Connexion, Inscription, Accès ; pages légales et page introuvable ; Alertes ; Bilan, Bilan ORP, Formations, Résultats ; Rendez-vous ORP ; Relances ; Entraînement ; Notifications.
- **Lot B, après la migration des feuilles du bas** : Trier, Offres et fiche d'offre, Candidatures et Envoyées, Préparer.
- **Lot C, en dernier** : Aujourd'hui, Premiers pas, Compte et Réglages, écrans de chargement, puis les composants communs (barre du bas, onglets, en-tête, messages, erreurs).

**S1, la langue du compte** : une colonne sur le compte (migration), envoyée quand on change de langue. Elle part avec le premier écran qui a des notifications (Alertes, lot A). Cite les règles de `docs/regles-securite-donnees.md` concernées.

**L'IA** : chaque écran qui affiche un texte de l'IA (assistant, « pourquoi » de la note, relances, entraînement) le fait écrire dans la langue de l'interface au moment où il est produit. Les textes déjà écrits ne sont pas réécrits (pas de coût en plus). Une nouvelle version de prompt suit la règle habituelle : mesure lancée par Kevin avant la bascule.

## 7. Ce que chaque PR montre

- Captures en français identiques au pixel : 1440 et 390 px, clair et sombre.
- Captures en allemand avant fusion, sur les écrans où le texte s'allonge : onglets dossier, boutons pleine largeur, pastilles des offres, titre manuscrit de l'Accueil, feuilles du bas. **Jamais de « … » dans un onglet ou un bouton.** Un audit le vérifie sur les captures en allemand.
- Le poids avant et après de la page, et de chacun de ses catalogues.
- `make audits-ci` passé, dont `make i18n-check`.

## 8. Poids

Voir `docs/decisions/2026-11-17-1330-poids-catalogues-langues.md`. En résumé : la limite de chaque page, mesurée en français, ne bouge pas ; chaque catalogue (page × langue) reçoit sa limite dans la PR qui le crée (sa mesure + 5 %, jamais relevée) ; le code et le catalogue d'une page restent ensemble sous 365 Kio.

## 9. Reste ouvert

- Qui relit chaque langue (Kevin complète).
- Le sigle de l'office en anglais, albanais, portugais et espagnol : voir la question dans `docs/i18n/README.md`.
- La planche ReglagesLangue à sept langues (Kevin la dessine).
