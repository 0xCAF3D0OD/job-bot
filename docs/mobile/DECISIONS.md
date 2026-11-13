# Décisions données après la maquette du 13 novembre

Une décision de Kevin donnée dans la conversation après le 13 novembre passe avant le paquet (LISEZMOI §2, CLAUDE.md). Une ligne par décision, la plus récente en bas.

| Date | Décision | Remplace |
|---|---|---|
| 2026-11-13 | Texte en #8C8478 dans la maquette : erreur de contraste (3,69:1). En texte, utiliser le gris secondaire. La maquette sera corrigée. | Le #8C8478 des planches, pour du texte. |
| 2026-11-13 | Le point 6 du LISEZMOI (planches Get'emAll gardées) passe avant le point 1 : les quatre planches Get'emAll et `maquettes/canvas.json` restent dans le dépôt. | La suppression de toute planche absente du paquet. |
| 2026-11-13 | Raccourcis de la préparation de candidature (lettre et CV lancés ensemble, bouton unique "J'ai relu, continuer", "Tout télécharger") : déjà dans main (PR #597, #600), conservés. | La ligne « raccourcis 1, 2 et 4 » du §6 du LISEZMOI, retirée (erreur du paquet). |
| 2026-11-13 | Téléphone, Ma candidature : la ligne "modèle · langue · Changer" de PreparerMiseEnPage est conservée. MaCandidatureV2 sera complétée. | L'absence de cette ligne sur MaCandidatureV2. |
| 2026-11-13 | Téléphone, échec de l'écriture de la lettre ou du CV : même carte et même texte que PreparerOrdinateurLettreVide (« La lettre n'a pas pu être écrite », l'explication, « Réessayer »). Pas de nouveau dessin. | L'état d'échec, dessiné nulle part sur téléphone. |
| 2026-11-13 | Ordinateur, étape Postuler : la ligne du certificat dans « À joindre » est conservée. PreparerOrdinateurPostuler sera complétée. | L'absence de cette ligne sur PreparerOrdinateurPostuler. |
| 2026-11-13 | Chaque PR d'interface est vérifiée contre le paquet du 13 novembre et porte une section « Conformité maquette du 13.11 » (règle dans CLAUDE.md). | — |
| 2026-11-13 | Attente de l'Assistant, cloche sans notification, espacement de l'en-tête : version de #574 conservée, la maquette sera alignée dessus. | Les deux premières lignes des « États pas encore dessinés » du §6 du LISEZMOI. |
| 2026-11-13 | Largeur des volets (code gardé tel quel). 420 px : petit volet ancré à un bouton, avec pastille, sans voile (Nouveau rendez-vous, Ajouter, Pour les formulaires, Compte, Notifications). 440 px : volet standard sur toute la hauteur ; c'est le cas par défaut pour tout nouveau volet. 480 px : réservé à l'Assistant, Pour l'ORP et Compléter le profil ; pas de nouveau volet à 480 sans l'accord de Kevin. | Les largeurs des planches quand elles diffèrent. |
| 2026-11-13 | Panneau des Alertes sur ordinateur (fiche d'un site, Ajouter une recherche) : 440 px. La planche AlertesOrdinateurSite dit 480, c'est une erreur de la maquette, elle sera corrigée. | Les 480 px de AlertesOrdinateurSite. |

`tokens.css` reste la source des couleurs et des tailles : il n'est pas dans le paquet du 13 novembre et n'est pas remplacé.
