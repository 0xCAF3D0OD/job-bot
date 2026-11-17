## Tableau des retours d'entretien, données (Kevin, 17.11.2026, 10 h 10)

- Une PR serveur seule, sans écran. L'écran attend la planche de Kevin : volet à droite sur ordinateur, page entière
  sur téléphone. Accès provisoire : une ligne « Retours d'entretien » dans Bilan › Résultats.
- Deux états par ligne :
  - `point` : `a_venir` | `a_faire` | `fait` (le retour « Faire le point ») ;
  - `issue` : `en_attente` | `retenu` | `pas_retenu` (la réponse de l'entreprise).
- La liste donne : entreprise, poste, date, type, ressenti, stress, suite, prochaine étape, remerciement envoyé
  (oui/non), point, issue et le nombre de questions notées. Aucun texte libre dans la liste : notes et questions
  seulement dans le détail.
- Lecture seule : aucune écriture en base, rien envoyé à l'IA, rien journalisé (ni contenu, ni identifiant
  d'entretien dans les journaux).
- Seulement les entretiens de la personne connectée : un autre compte reçoit 404 (test).
- Tri du plus récent au plus ancien, pages de 20.
- Une ligne ouvre le retour complet ; pour le modifier, on repasse par « Faire le point ».
- Le bloc « Entretiens » retiré de Bilan › Résultats sur ordinateur est voulu (point 3 du récapitulatif du
  11 novembre, #651) : pas de régression, pas d'issue.
