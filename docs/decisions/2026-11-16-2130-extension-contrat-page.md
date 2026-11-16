## Extension et page jobA1 : détection et suivi de l'alerte (Kevin, 16.11.2026, 21 h 30)

Section 42 de la maquette : à l'étape « Crée ton alerte sur jobup » des premiers pas, sur ordinateur seulement, le
choix « Avec l'extension · environ 1 minute » / « À la main · environ 2 minutes ». Le contrat entre l'extension
(`extension/page-joba1.js`) et la page (`useJobA1Extension`), sans requête au serveur pour la détection :

1. **Détection.** Sur l'adresse de la plateforme reliée, au chargement (`document_start`), l'extension pose
   `data-joba1-extension="x.y.z"` sur `<html>` et envoie
   `postMessage({ source: "joba1-extension", type: "ready", version }, location.origin)`. La page lit d'abord
   l'attribut, puis écoute `ready` (extension installée pendant que la page est ouverte). Par défaut, le choix est
   « Avec l'extension » si l'extension est détectée (« installée · environ 1 minute »), sinon « À la main ».
2. **Suivi.** L'extension envoie
   `postMessage({ source: "joba1-extension", type: "alert-progress", site: "jobup", step })`, avec `step` parmi
   `filled`, `sent`, `code-pasted`, `fallback`, `created`. Jamais le code, jamais l'adresse.
3. **Demande.** La page peut demander l'étape courante :
   `postMessage({ source: "joba1-page", type: "alert-progress?" }, location.origin)`. Des deux côtés, un message ne
   compte que si `event.source === window`, la même origine et le bon `source`.
4. **Alerte créée.** À `created`, l'extension appelle `PUT /api/extension/alerts/jobup` (route existante
   `mark_created`). La page passe d'elle-même à l'étape suivante, sans bouton « J'ai créé l'alerte ». En secours,
   quand on revient sur l'onglet, la page relit `/api/alert-searches` et avance si jobup est noté créé.
5. **Ouvrir jobup.** Le bouton « Ouvrir jobup avec ma recherche » garde l'adresse `cells[].url` de
   `/api/alert-searches`.
6. **Secours.** `fallback` (champ du code introuvable sur jobup) : la ligne « Code collé dans jobup » devient
   « Le code est dans la fenêtre de l'extension ».

Le suivi en direct affiche : Formulaire rempli, Alerte envoyée à jobup, Code collé dans jobup, En attente de ta
confirmation sur jobup. Changer d'option garde l'avancée de chaque parcours. Téléphone : pas de choix, parcours à la
main seul. Ordinateur (Kevin, 16.11, 23 h 29) : l'extension n'existe que pour Firefox, donc le choix ne s'affiche que sur
Firefox, ou sur tout navigateur où l'extension est détectée ; ailleurs, parcours à la main seul. Texte : « Gratuite,
pour Firefox. ». Les règles de l'extension elle-même sont dans `2026-11-16-2125-extension-alerte-jobup.md`.
