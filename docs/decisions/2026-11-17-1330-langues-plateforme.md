## jobA1 en sept langues : plan validé (Kevin, 17.11.2026, 13 h 30)

- Langues : français (par défaut), allemand, italien, anglais, albanais, portugais, espagnol. Cadrage : docs/147-langues-plateforme.md.
- Plan accepté sur le principe : fonction maison `t()`, pas de vue-i18n ; catalogues chargés par page ; français inchangé (texte du code) ; une PR par écran ; une langue reste grisée « Bientôt » tant qu'une personne dont c'est la langue maternelle ne l'a pas relue.
- Ordre : l'outil et le sélecteur (PR 1) après #833 et le fil Compte et Réglages ; les écrans sur lesquels un autre fil travaille passent en dernier.
- Ajouts obligatoires avant le premier jet :
  1. Glossaire figé par langue, versionné dans le dépôt (docs/i18n/), utilisé pour tous les écrans : ORP / RAV / URC, justificatifs, recherches d'emploi, gain intermédiaire, formulaire de preuves de recherches, conseiller. Termes officiels du SECO et des cantons. Le contrôle automatique vérifie que le glossaire est respecté.
  2. Dates, nombres et montants par Intl, jamais traduits à la main, avec la variante suisse (de-CH, fr-CH, it-CH ; « 1'000 » en allemand).
  3. Pluriels et accords par Intl.PluralRules, pas par phrases concaténées.
  4. Deux réglages séparés : langue de l'interface et langue des documents (lettre, CV). Changer l'interface ne change jamais la langue des documents.
  5. Notifications et réponses de l'IA dans la langue de l'interface, dans la PR de l'écran concerné, pas dans une PR à part plus tard.
  6. Captures en allemand avant fusion sur les écrans où le texte s'allonge : onglets dossier, boutons pleine largeur, pastilles des offres, titre manuscrit de l'Accueil, feuilles du bas. Jamais de « … » dans un onglet ou un bouton.
- Réponses aux questions du plan :
  1. Premier lancement : langue du navigateur si elle fait partie des sept, sinon le français ; un choix enregistré passe toujours avant. Texte dans une autre langue que l'interface (annonces, lettres affichées) : attribut `lang` sur le bloc (WCAG 3.1.2). Pages légales : traduction relue et mention « la version française fait foi ».
  2. La langue est enregistrée sur le compte (S1), pour les notifications.
  3. Poids : voir 2026-11-17-1330-poids-catalogues-langues.md.
  4. Kevin redessine la planche ReglagesLangue avec les sept langues (nom dans sa propre langue, grisées « Bientôt » tant qu'elles ne sont pas relues). La PR 1 l'attend.
  5. Variantes : fr-CH, de-CH (sans ß), it-CH, en-GB, pt-PT, es-ES, sq.
  6. Relecture : qui relit, à compléter par Kevin. Une langue n'est activée qu'après relecture ; l'allemand et l'italien d'abord.
  7. Italien dans les lettres : pas maintenant.
