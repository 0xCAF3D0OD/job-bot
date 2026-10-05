# 14 — Page Offres : mise en page, tri des candidatures en cours, logos (version 0.7.4)

> Statut : **à valider**. Aucun code avant accord.
> Retours d'usage du 2026-10-05.

## 1. Mise en page : la liste au centre, le détail qui glisse à droite

**Constat** : la colonne de droite affiche « Choisis une offre pour voir son détail » et reste vide la plupart du temps ; la liste est serrée à gauche.

**Proposition** :

- **Sans offre ouverte** : deux colonnes, les filtres à gauche et la liste **centrée** dans l'espace restant (plus large, plus lisible). Plus de cadre vide à droite.
- **Une offre ouverte** : le détail **glisse depuis la droite** (environ 0,25 s), la liste se resserre en douceur pour lui faire de la place ; à la fermeture (×, Échap ou clic sur la même carte), le mouvement inverse.
- Le mouvement est désactivé si le système demande de réduire les animations (réglage d'accessibilité).
- Sur téléphone : rien ne change (le détail s'ouvre en plein écran).

## 2. Trier les candidatures en cours, la plus récente d'abord

**Constat** : l'onglet « En cours » (en préparation et envoyées) est trié comme les autres onglets (date d'apparition de l'offre), pas selon ton activité.

**Proposition** : un tri **« Activité »** : la dernière action d'abord. Une action, c'est :
- passer l'offre en préparation ;
- rédiger ou modifier la lettre ou le CV ;
- marquer la candidature comme envoyée ;
- changer son statut de suivi.

C'est le **tri par défaut de l'onglet « En cours »**. Chaque carte affiche la date de la dernière action (« envoyée le 3 oct. », « lettre modifiée hier »).

## 3. Logo de l'entreprise au lieu de la lettre

**Constat** : la miniature est l'initiale de l'entreprise.

**Sources du logo, dans l'ordre :**
1. **L'annonce jobup** : sa page donne le logo de l'entreprise. La plateforme la lit déjà ; elle relève aussi le logo, sans requête en plus. Les offres déjà lues le reçoivent à la prochaine revérification.
2. **Le site de l'entreprise** : quand il est connu (lien de l'annonce jobup, ou page trouvée pour l'adresse en 0.7.2), la plateforme prend son icône (favicon), en bonne résolution si possible.
3. Sinon, l'**initiale** comme aujourd'hui.

**Confidentialité et rapidité** : les logos sont téléchargés une fois par la plateforme, gardés dans le stockage local (`JOBBOT_STORAGE_PATH/logos/`) et servis par l'API. Ton navigateur ne contacte ni jobup ni les sites des entreprises en parcourant la liste. Un logo par entreprise, au plus 30 nouveaux téléchargements par passage, 200 Ko au plus chacun, images seulement (PNG, JPEG, SVG nettoyé, ICO, WebP).

## 4. Base (migration 0021)

```
offers     + status_changed_at   -- dernière action de Kevin (tri « Activité »)
companies  + website?, logo_key?, logo_checked_at?
```

## 5. Livraison en deux PR

| PR | Contenu |
|---|---|
| **0.7.4-a** | Mise en page et transition ; tri « Activité » de l'onglet En cours |
| **0.7.4-b** | Logos des entreprises |

## Points à valider

1. **Liste centrée, détail qui glisse à droite**, sans cadre vide (§1).
2. **Tri « Activité »**, par défaut dans « En cours » (§2).
3. **Logos** : annonce jobup, puis icône du site de l'entreprise, sinon l'initiale ; téléchargés et gardés par la plateforme (§3).
4. **Deux PR** (§5).
