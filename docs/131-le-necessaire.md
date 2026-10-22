# 131 — Le nécessaire : chaque information aide à décider (version 1.4.0)

> Statut : **validé d'avance** le 2026-10-22 (« écris le cadrage 131 et exécute-le »). Les choix sont tranchés ici ; les écarts sont notés à la fin.
> Origine : ta question « est-ce que tous les éléments informatifs sont indispensables pour l'utilisateur ? », et le tour des pages de la démo après la 1.3.1.

## La phrase qui guide

**Une information reste si elle aide à décider quoi faire maintenant.** Sinon, elle part, passe au survol, ou ne s'affiche que quand quelque chose ne va pas.

## A. Ce qui se répète

1. **Aujourd'hui, l'action sous la phrase du jour** : « Examiner les offres » mène à la carte « Offres du jour », affichée juste dessous ; « Relancer » mène aux relances, affichées aussi. L'action ne s'affiche plus quand sa carte est sur la page (Structure 17 : une seule action, et seulement si elle apporte quelque chose).
2. **La semaine, dite deux fois** : « encore 2 candidatures pour tenir ta semaine » (la phrase) et « Cette semaine 1 / 3 » (le mois ORP). La phrase ne parle plus de la semaine ; le mois ORP la montre.
3. **La fiche d'une offre** : la ligne « Offre » (taux, télétravail, contrat) répète « À savoir », juste dessous. Elle part quand « À savoir » a ces pastilles.
4. **La note en chiffre** (« 76/100 » dans un cercle) dans la fiche et dans Préparer : le mot de la note à la place (« Proche »), le chiffre au survol, comme dans les listes (docs/121 §C.5).
5. **Rendez-vous › « Mois en bref »** : deux longues phrases qui redisent le Bilan. Une ligne de chiffres par mois (« Septembre 2026 · 10 candidatures sur 10 · 4 réponses · 1 entretien ») ; le texte complet reste dans la feuille PDF et le message.

## B. Ce qui n'aide pas à décider

6. **« Collecte il y a 10 heures »** au-dessus du titre d'Aujourd'hui : seulement quand la collecte a plus de 24 heures de retard, ou pendant une collecte.
7. **« Blocs : … »** sous chaque paragraphe de la lettre et sous les points forts : au survol du texte.
8. **« Ce qui bloque » et « Compétences qui manquent »** vides (« Rien de net pour l'instant… ») : ne s'affichent pas ; « Ce qui marche » reste quand il y a quelque chose.
9. **Les obligations déjà faites** (« Fait : preuves de septembre… ») : seulement ce qui reste à faire.
10. **« Enseignements »** (les retours d'entretien) quitte le Suivi pour le Bilan › Résultats, sous « Le détail » : c'est une analyse.
11. **« Code de vérification »** n'est plus une carte toujours visible dans Alertes : une ligne repliable sous les alertes, ouverte d'office quand un code est arrivé ou attendu.

## C. Ce qui est trop poussé

12. **Le filtre « Note »** des Offres (une courbe, deux poignées, deux champs de 0 à 100) : trois choix, « Toutes », « Proche et plus » (70), « Très proche » (85). Une adresse `?note=…` d'avant reste lue.
13. **« Chercher l'annonce chez l'employeur à partir de 70 / 100 »** : de Recherche d'emploi vers Outils, avec les réglages d'expert.

## D. Ce que j'avais ajouté

14. **« Ensuite »** (l'offre suivante, sous l'offre du jour, 1.2.0) part : il remplissait un vide sans aider à décider.

## Ce qui reste, indispensable

La phrase du jour, le mois ORP, l'offre du jour et son « pourquoi », les lignes à préparer et à relancer, « À déclarer dans Job-Room », la feuille du rendez-vous, « Il te manque : … » sur les offres.

## Garde-fous

- Rien ne disparaît sans chemin : le chiffre de la note au survol, les blocs au survol, le texte du mois dans la feuille, les enseignements dans le Bilan, le code dans sa ligne repliable.
- Les écrans suivent `docs/interface.md` ; les trois audits à zéro sur la démo et sur un compte neuf ; captures à 1440 et 390 px.
- Le test avec 5 personnes (docs/127) dira si d'autres éléments sont de trop.

## Écarts (1.4.0)

- **Règles relues avant de construire** ; captures à 1440 et 390 px de la démo (Aujourd'hui, Offres et la fiche, Suivi, Alertes, Rendez-vous, Bilan) ; les trois audits à zéro sur la démo et sur un compte neuf.
- **L'action sous la phrase du jour** ne reste que pour des offres à examiner pas encore notées (« Examiner les offres » mène alors aux Offres). « Relancer » disparaît : ses lignes sont toujours dans la carte « À relancer ».
- **« Voir le bilan »** quitte aussi la carte du mois ORP (le Bilan est dans le menu) : sans « Ensuite », la carte de l'offre du jour gardait un vide plus grand à côté. Il reste un vide plus court sous les boutons de l'offre ; c'est le prix de ne rien y mettre d'inutile.
- **Les blocs d'un paragraphe de la lettre** : un paragraphe est un champ de texte, une info-bulle n'y tient pas ; la ligne « Blocs : … » apparaît au survol du paragraphe et quand on l'écrit.
- **« Mois en bref »** : le serveur envoie les chiffres de chaque mois (candidatures, objectif, réponses, entretiens) ; la page en fait une ligne, la feuille PDF et le message gardent le texte complet.
- **« Ce qui bloque »** reste quand seul « Ce qui marche » a quelque chose à dire, sans la phrase « Rien de net pour l'instant ».
- **Les e-mails des sites** : la ligne repliable s'appelle « Les e-mails des sites » (« aucun code en attente » à droite) ; pour une personne invitée, la boîte de jobA1 y est expliquée au survol. Dès qu'un code est attendu ou arrivé, ou qu'un message est là, la carte complète revient.
- **Le filtre « Note »** : trois pastilles qui passent à la ligne (dans une colonne étroite, un sélecteur à trois cases coupait « Proche et plus ») ; la courbe et son composant sont supprimés.
- **L'assistant** : consigne `assistant-v19`.

## Vérifié (1.4.0)

- Tests de l'interface : la phrase sans la semaine et sans action en double, l'action pour des offres pas notées ; la note en mot dans la fiche et dans Préparer ; le bloc d'un point fort au survol ; le Rendez-vous (une ligne par mois, pas de partie vide, les obligations à faire) ; « Enseignements » dans le Bilan ; les e-mails des sites repliés ; les Réglages. 449 tests, lint, vue-tsc.
- Backend : les chiffres du mois du Rendez-vous, la consigne de l'assistant. 632 tests, ruff, mypy.
- Les trois audits à zéro sur la démo et sur un compte neuf.
