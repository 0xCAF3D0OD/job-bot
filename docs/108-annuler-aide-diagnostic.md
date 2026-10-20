# 108 — Annuler plutôt que confirmer, l'aide au doigt, le Diagnostic à l'exploitant (version 0.77.0)

> Statut : **validé** le 2026-10-20 : 6 secondes, le tri des 18, le « i » sur téléphone, le Diagnostic à l'exploitant, docs/104 en 0.78.0 et 0.79.0.
> Origine : nos lectures du 2026-10-20 (Laws of UX, « 58 rules », lois de l'interface) et ton choix des points 1 et 2 ; puis ta remarque du même jour : « le bouton Diagnostic technique se trouve aussi du côté utilisateur qui n'est pas moi, je ne crois pas que ça ait du sens ».
> Les versions prévues par docs/104 (l'adresse à jobA1, les premières offres) passent en 0.78.0 et 0.79.0.

## 1. Annuler plutôt que confirmer

### Le constat

**18 fenêtres `window.confirm`** du navigateur, dans 14 fichiers. Elles bloquent la page, changent d'aspect selon le navigateur, sont petites et grises sur téléphone, et on finit par cliquer « OK » sans lire. La loi du retour veut au contraire qu'une action se fasse **tout de suite**, avec un retour visible et un moyen de revenir en arrière.

### La règle (ajoutée à `docs/interface.md`)

1. **Ce qui se rattrape se fait tout de suite**, sans question. Un bandeau en bas de l'écran le dit, avec **« Annuler »**, pendant **6 secondes** : « Contact retiré · Annuler ».
2. **Ce qui ne se rattrape pas, ou touche quelqu'un d'autre**, demande une confirmation **dans la page**, à l'endroit du bouton, comme pour fermer son compte : la phrase de ce qui va se passer, le bouton rouge « Supprimer », « Garder ».
3. **Plus aucun `window.confirm`.** Un test le vérifie.

### Le bandeau « Annuler »

- **Un seul composant** (`UndoToast`), en bas au centre, au-dessus de la barre d'onglets sur téléphone. Un bandeau à la fois : une nouvelle action remplace le précédent, qui est alors validé.
- **Comment ça marche** : l'élément disparaît de la liste tout de suite ; la suppression part au serveur **à la fin des 6 secondes**. « Annuler » le remet à sa place, et rien ne part. Si la page se ferme avant, la suppression part quand même (envoi `keepalive`).
- **Accessibilité** : le bandeau est lu (`role="status"`) ; « Annuler » prend le focus au clavier avec Échap pour fermer ; les 6 secondes s'arrêtent tant que la souris ou le focus est dessus.
- **Le serveur ne change pas** : les routes de suppression restent les mêmes.

### Les 18 confirmations, une par une

| Où | Action | Après |
|---|---|---|
| Réglages › Actualités | Ne plus suivre une source | **Annuler** |
| Réglages › Recherche d'emploi | Ne plus suivre un site | **Annuler** |
| Alertes | Supprimer une recherche | **Annuler** |
| Contacts | Retirer un contact | **Annuler** |
| Profil › Parcours | Supprimer un bloc | **Annuler** |
| Profil | Supprimer un document (CV, certificat) | **Annuler** |
| Profils d'essai | Supprimer un profil | **Annuler** |
| Entretiens | Supprimer un entraînement | **Annuler** |
| Entretiens | Supprimer un retour d'entretien | **Annuler** |
| Suivi | Supprimer une candidature (l'offre revient « en préparation ») | **Annuler** |
| Outils | Révoquer un jeton d'agenda | **Annuler** (la révocation part au bout des 6 s) |
| Outils | Révoquer un jeton de l'extension | **Annuler** (idem) |
| Compte › Connexion | Fermer toutes les sessions, celle-ci comprise | **Confirmation dans la page** (on est déconnecté) |
| Preuves ORP | Annuler la remise du mois | **Confirmation dans la page** |
| Lettre et CV (2 endroits) | Rédiger une nouvelle version malgré des modifications non enregistrées | **Choix dans la page** : « Enregistrer d'abord » (plein) · « Rédiger sans enregistrer » |
| Plateforme | Suspendre ou réactiver un compte | **Confirmation dans la page** (touche quelqu'un d'autre) |
| Plateforme | Refuser une demande de compte | **Confirmation dans la page** (le compte est effacé) |

## 2. L'aide au doigt

### Le constat

**26 descriptions au survol** (`HoverNote`, docs/53) : sous un titre en pointillés, une bulle s'ouvre après 3 secondes de souris immobile. **Au toucher, rien** : sur téléphone, où sont la plupart des utilisateurs, ces aides n'existent pas. Les règles « indices contextuels » et « clarté » veulent une aide **là où on en a besoin**, sans encombrer.

### La proposition

- **Sur ordinateur, rien ne change** : la bulle au survol, les lecteurs d'écran qui la lisent avec le titre.
- **Sur téléphone (sous 820 px)** : un petit **« i »** cerclé de 1 rem, gris clair, à droite du titre, dans une cible de 2,75 rem. Un appui ouvre la description **sous le titre, en une ligne grise**, dans la page (pas de bulle qui cache le reste) ; un second appui la referme. Une seule ouverte à la fois.
- **Les pointillés** sous le titre restent sur ordinateur, disparaissent sur téléphone (le « i » les remplace).

## 3. Le Diagnostic à l'exploitant

### Le constat

« Diagnostic technique (collecte, IA, tâches) » est proposé à tout le monde : en bas des Réglages et dans le menu du compte. Pour un compte invité, la page montre la version, l'état de la base, du worker et de la collecte de la plateforme, ce qu'il ne peut ni comprendre ni réparer. L'historique des tâches lui est déjà refusé par le serveur.

### Après

- **Le lien « Diagnostic technique »** des Réglages et **la ligne « Diagnostic »** du menu du compte : pour l'exploitant seulement (et pour l'installation sans connexion, où l'on est l'exploitant).
- **La page `/reglages/diagnostic`** : un compte invité qui l'ouvre par son adresse revient aux Réglages.
- **Le serveur** : `/api/status` reste ouvert (il répond aussi pendant une maintenance), mais pour un compte invité il ne donne plus que l'essentiel (« la plateforme fonctionne »), sans version, base ni worker. Ce qui compte pour lui (ses alertes reçues) est déjà dans Alertes.

## Vérifié avant la PR (prévu)

- Tests : plus aucun `window.confirm` dans l'interface ; le bandeau (supprimer, annuler, 6 s, envoi à la fermeture) ; une confirmation dans la page ; le « i » sur téléphone ; le Diagnostic absent pour un invité, présent pour l'exploitant, la page qui renvoie aux Réglages ; `/api/status` réduit pour un invité.
- Captures sur téléphone et ordinateur, en clair et en sombre : le bandeau, une confirmation dans la page, une aide ouverte au doigt.

## Décisions (2026-10-20)

Tout est validé tel quel (« oui pour tout, 6 secondes »).

### Les questions posées

1. **6 secondes** pour « Annuler » : d'accord, ou plus long (10 s) ?
2. **Le tri des 18** du tableau : d'accord ? En particulier, la révocation des jetons avec « Annuler » plutôt qu'une confirmation.
3. **L'aide au doigt** : le petit « i » à droite du titre, qui ouvre une ligne sous le titre ? (docs/53 avait retiré les « ? » ; le « i » ne s'affiche que sur téléphone.)
4. **Le Diagnostic** : réservé à l'exploitant, et `/api/status` réduit pour les invités ?
5. **La renumérotation** : docs/104 passe en 0.78.0 et 0.79.0 ?
