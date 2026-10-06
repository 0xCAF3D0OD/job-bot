# 18 — Page de connexion, Candidatures et ORP réunies (version 0.11.0)

> Statut : **validé** le 2026-10-06 (Offres réservées aussi). livré : PR b (Candidatures et ORP réunies), avancée avant la PR a à ta demande.
> Retours d'usage du 2026-10-06, en validant le cadrage 17. Vient après la 0.10.0 (profils d'essai).

## 1. Page de connexion

**Constat** : la plateforme n'a pas de connexion ; seul le tunnel privé protège tes données.

**Proposition** : une page **Connexion** (identifiant, mot de passe) et des pages réservées.

| Sans connexion | Après connexion |
|---|---|
| **Actualités** (profil principal, en lecture), page de connexion | tout le reste : Aujourd'hui, Offres, Candidatures, Formations, Profil, Réglages, profils d'essai |

- **Un seul compte pour l'instant, le tien.** Pas d'inscription depuis le site (personne ne peut se créer un compte).
- **Ton mot de passe, c'est toi qui le choisis**, en ligne de commande : `jobbot set-password` le demande sans l'afficher. Ne me le donne jamais, ni dans la conversation ni dans un fichier du dépôt. Il est enregistré **haché** (scrypt), jamais en clair.
- **Session** : un cookie protégé (illisible par le JavaScript, envoyé seulement en HTTPS hors de ta machine), valable 30 jours, renouvelé à l'usage ; bouton **Se déconnecter** ; « Se déconnecter partout » dans les Réglages.
- **Protection** :
  - l'API refuse toute route réservée sans session (réponse 401), pas seulement l'interface ;
  - les modifications exigent que la requête vienne de la plateforme elle-même (contrôle de l'origine), contre les pages piégées d'autres sites ;
  - après 5 essais ratés, attente croissante avant le suivant ; les essais sont notés dans les journaux, sans le mot de passe.
- **Sans compte créé**, la page de connexion explique la commande à lancer.
- Le worker, les tâches planifiées, `/healthz` et les métriques ne changent pas.
- **Plus tard** (vrais comptes, cadrage 17, option B) : la table des comptes est déjà prête à en recevoir d'autres.

## 2. Candidatures et ORP au même endroit

**Constat** : les deux pages montrent les mêmes candidatures, l'une pour le suivi, l'autre pour le formulaire du mois.

**Proposition** : une seule page **Candidatures** ; l'entrée **ORP** disparaît du menu.

- **En haut** : le **mois** (← →), le compteur **« 14 / 20 »**, l'état des preuves (*en cours*, *à remettre avant le 5*, *remis le 3*), et l'encart **« à relancer »** (candidatures sans réponse depuis 10 jours).
- **Deux vues du même mois**, en onglets :
  - **Suivi** : la liste actuelle (statut, relance, entretien, modifier) ;
  - **Preuves ORP** : le formulaire actuel (lignes à compléter, colonnes, PDF, CSV, copie Job-Room, « Marquer comme remis », journal des recherches).
- Une option **« Tous les mois »** dans Suivi, pour retrouver une ancienne candidature.
- Le bouton **Ajouter une candidature** et la fenêtre de modification sont communs aux deux vues.
- Les anciens liens (`/orp`, notifications de la cloche, rappels ntfy) mènent à l'onglet Preuves ORP du bon mois.
- Le menu passe à **huit entrées**.

## 3. Base (migration 0029)

```
users      id, username UNIQUE, password_hash, created_at, password_changed_at
sessions   token_hash PRIMARY, user_id, created_at, last_seen_at, expires_at, user_agent?
```

## 4. Livraison en deux PR

| PR | Contenu | De ton côté |
|---|---|---|
| **0.11.0-a** | Connexion, pages et API réservées, déconnexion | `jobbot set-password` une fois |
| **0.11.0-b** | Page Candidatures réunie (Suivi, Preuves ORP) | aucun |

## Points à valider

1. **Visible sans connexion : seulement les Actualités** (et la page de connexion) ; tout le reste réservé (§1). Les **Offres** aussi réservées ?
2. **Un seul compte**, mot de passe choisi par toi en ligne de commande, haché, jamais transmis (§1).
3. **Session de 30 jours**, déconnexion, protections (§1).
4. **Une page Candidatures** avec les onglets **Suivi** et **Preuves ORP** sur le même mois ; ORP retiré du menu (§2).
5. **Deux PR**, après la 0.10.0 (§4).

## Écarts avec la PR b

- **Ordre** : livrée avant la connexion (PR a), à ta demande ; les deux sont indépendantes.
- **Trois onglets** : Suivi, Preuves ORP et **Journal des recherches** (qui était un onglet de la page ORP).
- **Mois par défaut** : celui de la page ORP d'avant (le mois précédent tant que ses preuves ne sont pas remises et qu'il contient des candidatures, sinon le mois en cours), pour les deux onglets.
- **En-tête commun** : mois, compteur, état des preuves, bouton « Ajouter une candidature » ; l'onglet Preuves ORP affiche le nombre de lignes à compléter.
- **À relancer** : les candidatures « en attente » envoyées il y a 10 jours ou plus, tous mois confondus ; un clic ouvre la candidature.
- **Liens** : `/orp` et `/journal` redirigent vers la page Candidatures (onglet et mois conservés) ; les nouveaux rappels ORP et alertes de la cloche pointent directement sur `/candidatures?vue=orp&mois=…`.
- **Menu** : huit entrées.
