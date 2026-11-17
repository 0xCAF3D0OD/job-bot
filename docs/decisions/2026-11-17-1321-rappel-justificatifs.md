## Rappel des justificatifs en haut de l'Accueil (Kevin, 17.11.2026, 13 h 21)

- §57 du LISEZMOI_CORRECTIONS du 17.11, planches AccueilJustificatif et AccueilJustificatifSombre : une PR à part.
- Îlot avec les jetons des feuilles en îlot de la #828, sans nouveau CSS d'îlot : 8 px des bords, rayon 24 px, ombre 0 12px 32px rgba(27,31,42,.2) ; en sombre, fond #221E1A et trait #38322B (la planche sombre n'a pas de trait : la décision de Kevin passe avant).
- role="status", pas de prise de focus. Bouton « Exporter », qui ouvre la page ORP du mois, et croix « Fermer pour aujourd'hui ».
- Au plus une fois par jour, seulement quand des justificatifs sont à remettre ou en retard ; disparaît dès que le mois est marqué remis (case cochée §58/§61 ou « Déjà remis »). Lecture retenue : le rappel se montre à la première ouverture de l'Accueil du jour, puis plus avant le lendemain ; la date est gardée dans le navigateur (`jobA1.rappel-orp`), rien sur le serveur.
- Téléphone seulement : aucune planche ordinateur ne le dessine (la tâche n° 1 « Remettre les justificatifs » y suffit, question posée à Kevin).
- Texte non dessiné : avant l'échéance, « À remettre avant le 5 décembre » (« À remettre aujourd'hui » le jour même), la phrase de la tâche n° 1. Le rond de l'icône prend --peach-soft (#FDEDE3 ; #3A281E en sombre) au lieu du #FDF0E2 de la planche, qui garde ce fond clair en sombre.
