# 41 — Revue des versions 0.24 à 0.33 (version 0.33.1)

> Statut : **validé** le 2026-10-15. Livré : PR a, PR b.
> Dix versions livrées en peu de temps (contacts, allègement, téléphone, actualités, formations, relances, candidatures spontanées, agenda). Revue en lecture seule du serveur, de l'interface, des tests et de la documentation, le 2026-10-15. Chaque point retenu a été relu dans le code ; les plus visibles ont été vérifiés une seconde fois.

**Rien de grave côté sécurité** : pas de contournement de la connexion, jeton d'agenda bien protégé (empreinte seule, révocable), aucune injection, et les promesses de confidentialité tiennent (ni nom ni coordonnées envoyés à l'IA ; ni adresse ni contact dans l'agenda).

## 1. Ce que tu pourrais remarquer (à corriger)

| # | Où | Le problème | La correction |
|---|---|---|---|
| 1 | **Candidature spontanée** | Pas encore envoyée, elle passe **« expirée » au bout de 30 jours** (la règle des offres sans page s'applique à elle). | L'exclure de l'expiration ; remettre à zéro celles déjà touchées. |
| 2 | **Téléphone, cloche** | Toucher dans la carte des alertes (« Tout marquer comme lu », une zone vide) **la referme**. | Reconnaître la carte comme « dedans ». |
| 3 | **Échap** | Une seule pression ferme **plusieurs couches** : le panneau Contacts *et* la fiche de l'offre ; pire, fermer une bulle « ? » dans « Candidature spontanée » **ferme le panneau et perd la saisie**. | Échap ne ferme que la couche du dessus. |
| 4 | **Relance, IA surchargée** | Si l'IA répond « surchargée » ou ne répond pas, « Rédiger la relance » donne une **erreur** au lieu du modèle gratuit promis ; même chose pour le message à un contact. | Toute indisponibilité passagère → modèle gratuit (relance) ou « réessaie » (contact). |
| 5 | **Candidature spontanée** | Fermer le panneau après « Continuer » sans cliquer « Préparer » : elle **n'apparaît pas** dans la liste ; on risque de la recréer (doublon dans le formulaire ORP). | Recharger la liste dès la création. |
| 6 | **Panneau « Relancer »** | Il hérite d'un **ancien style** (cadre à bord orange, texte gris réduit). | Classe propre au panneau ; ancien style supprimé (inutilisé). |
| 7 | **Bulles « ? »** dans les lignes dépliables | La bulle est **coupée** par la ligne (Formation et chômage sur téléphone, Réglages). | Ne rogner la ligne que pendant l'animation. |
| 8 | **Téléphone, Offres et Formations** | À chaque arrivée, la carte « Filtrer » **apparaît puis se replie** (la page croit d'abord être sur ordinateur). | Savoir dès le premier affichage si c'est un téléphone. |
| 9 | **Agenda** | Les candidatures en attente depuis des mois reposent **chaque jour** « Relancer X ? » ; entretiens et suites attendues restent affichés **après un refus ou un engagement**. | Relance proposée jusqu'à 30 jours après l'envoi ; dossiers clos retirés. |
| 10 | **Relance, statuts** | Repasser « En attente » puis « Relancée » garde l'**ancienne date** (« Sans réponse » proposé tout de suite) ; « Marquer comme relancée » marche même sur un **Refus**. | Date effacée en quittant « Relancée » ; relance seulement depuis « En attente ». |
| 11 | **Formation → profil** | Un double clic crée **deux blocs** identiques (envoyés en double à l'IA). | Un seul bloc par formation. |
| 12 | **Aujourd'hui** | « N à relancer » ne compte pas les relancées restées sans réponse, que la liste montre : **le nombre diffère** de la liste. | Même règle des deux côtés. |

## 2. Petits défauts

- **Panneau Contacts** : erreur de chargement ou d'ajout sans message ; « Retirer » sans confirmation. Ajouter message et confirmation.
- **Agenda, Réglages** : un double clic crée deux adresses ; toutes s'appellent « Mon agenda ». Bouton bloqué pendant la création ; nom avec la date (« Agenda du 15 oct. »).
- **Liens LinkedIn** trop longs qui débordent sur téléphone (« L'équipe du poste (titre complet) ») : passer à la ligne.
- **Accessibilité des panneaux** : au clavier, le focus n'est pas rendu au bouton d'origine après fermeture et peut sortir du panneau ; le garder dedans et le rendre.
- **Contact rattaché** à un identifiant inexistant : erreur serveur au lieu d'un refus clair ; incohérence offre / candidature acceptée.
- **Rappel de financement** demandé depuis un **profil d'essai** : le lien ouvre le profil principal, où la demande n'est pas. Rappels réservés au profil principal.
- **Argument de financement** : lit toutes les offres des 90 derniers jours à chaque clic ; limiter.
- **Date en UTC** dans « À relancer » (décalage d'un jour entre minuit et 2 h).
- **Migration 0041** : une relance ancienne sans date de statut garde une date vide ; prendre la date d'envoi à défaut.

## 3. Tests à ajouter

Sur ce qui protège vraiment : la **ligne ORP** d'une candidature spontanée (complète, rien de manquant) ; la règle des **14 jours** après relance (côté liste et carte) ; le **plafond de l'IA** (relance → modèle gratuit, contact → refus, sans appel) ; l'**agenda** sans un mois ORP déjà remis ; les tests qui laissent ton identité ou le catalogue de formations derrière eux (ordre des tests).

## 4. Documentation

- **Exploitation** (`docs/exploitation.md`) : la route publique de l'agenda et ses jetons, les rappels de contact (7 j) et de financement (14 j), les nouvelles tables ; version décrite à jour.
- **README** : la ligne « Version en cours » pointe encore la 0.2.0 ; l'état de Job-Room est contradictoire.
- **Nom** : « job-bot » restant là où tu vois « jobA1 » (extension, écran d'accueil) ; doc 14 en double marqué « à valider ».

## 5. Livraison en deux PR

| PR | Contenu |
|---|---|
| **0.33.1-a** | Corrections (§1, §2), avec un test pour chacune quand c'est possible ; migration 0044 (spontanées expirées par erreur remises à zéro, dates de relance manquantes) |
| **0.33.1-b** | Tests manquants (§3) et documentation (§4) |

## Points à valider

1. **Les 12 corrections** du §1 et les petits défauts du §2.
2. **Tests** (§3) et **documentation** (§4).
3. **Deux PR** (§5).

## Écarts avec la PR a

- **Bulles « ? »** dans une ligne dépliée : la ligne reste rognée pendant qu'elle glisse, puis laisse dépasser son contenu une fois ouverte (0,2 s). Les coins de la première et de la dernière ligne d'une liste sont arrondis pour rester dans le cadre.
- **Panneaux** : Échap ferme la bulle « ? » ouverte, puis le panneau du dessus seulement ; Tab reste dans le panneau ; le focus revient au bouton d'origine, même quand le panneau disparaît de la page.
- **Relance** : changer de statut hors de « Relancée » efface la date de relance ; y revenir la remet au jour du changement. « Marquer comme relancée » refusé hors de « En attente ».
- **Message à un contact**, IA surchargée ou injoignable : « IA momentanément indisponible, réessaie », sans appel compté.
- **Contacts** : « Retirer » demande confirmation ; un échec de chargement, d'ajout ou de retrait s'affiche.
- **Migration 0044** : spontanées expirées « par âge » remises à zéro ; relances sans date reprennent la date d'envoi.
- **Vérifié** dans le navigateur (téléphone et ordinateur) : panneau « Relancer » au bon style, Échap bulle puis panneau, focus rendu, cloche qui reste ouverte au toucher dans la carte, bulle de Réglages entière. Modèle simple affiché sans IA.

## Écarts avec la PR b

- **Tests ajoutés** : ligne ORP d'une candidature spontanée complète ; plafond de l'IA atteint (relance → modèle gratuit, contact → refus, aucun appel) ; agenda sans le mois ORP déjà remis ; « Sans réponse » proposé 14 jours après la relance, pas 13 (liste et carte).
- **Ordre des tests** : ton identité saisie par les tests des relances et des contacts est effacée après eux ; le catalogue de formations est rechargé avant chaque test (un test qui vide la table ne laisse plus les suivants sans catalogue). Le test du plafond rend au réglage sa valeur.
- **Exploitation** : version 0.33.1 ; route publique de l'agenda (seule à exposer pour Google et Outlook), jetons `jba_…` et table `calendar_tokens` ; rappels de contact (7 j) et de financement (14 j) ; appels à l'IA complétés ; table `contacts` dans les données personnelles. Aucune nouvelle variable d'environnement depuis 0.11.
- **README** : « Version en cours » pointe ce document ; Job-Room dit tel qu'il est (pas d'analyseur dédié, site en pause), sans contradiction avec l'introduction.
- **Nom** : jobA1 dans les docs 25 et 33 là où tu le vois (icône, extension) et dans l'exemple d'adresse de l'extension. L'identifiant Firefox de l'extension (`job-bot@jobbot.app`) **ne change pas** : le changer ferait d'elle une autre extension à réinstaller. Les anciens documents de cadrage gardent « job-bot » (historique), comme le libellé Gmail `job-bot`.
- **Doc 14** : l'ancien brouillon « à valider » (`14-offres-mise-en-page.md`) est supprimé ; `14-offres-logos.md` reste la version validée.
