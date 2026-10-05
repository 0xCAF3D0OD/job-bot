# 09 — Export ORP et rappels (version 0.6.0)

> Statut : **validé** le 2026-10-05. PR a (page ORP, PDF, CSV, Job-Room, remise) livrée ; PR b (rappels) à venir.
> S'appuie sur [01-cadrage.md](01-cadrage.md) §6 et sur les candidatures de la 0.5 ([08-candidatures.md](08-candidatures.md) §5), qui enregistrent déjà tous les champs du formulaire.

## 1. Objectif

Chaque mois, remettre à l'ORP les **preuves de tes recherches d'emploi** sans rien ressaisir :

1. La page **ORP** (déjà dans le menu) montre les candidatures du mois, sous la forme du formulaire « Preuves des recherches personnelles effectuées en vue de trouver un emploi ».
2. Elle signale ce qui manque (adresse de l'entreprise, contact…) avant la remise.
3. Tu télécharges le **PDF** (à envoyer ou imprimer) ou le **CSV**, ou tu recopies les lignes dans **Job-Room** avec des boutons « copier ».
4. Tu marques le mois comme **remis**.
5. Des **rappels** ntfy te préviennent si tu es sous l'objectif, et avant la date de remise.

La plateforme ne transmet rien à l'ORP ni à Job-Room : la remise reste faite par toi.

## 2. Page ORP

En haut : le mois (navigation ← →, par défaut le mois précédent tant que celui-ci n'est pas remis, puis le mois en cours), le compteur « 14 / 20 », l'état du mois (*en cours*, *à remettre avant le 5 novembre*, *remis le 3 novembre*).

Une ligne par candidature dont la **date d'envoi** tombe dans le mois, triées par date, avec les colonnes du formulaire :

| Colonne | Source |
|---|---|
| Date | date d'envoi |
| Entreprise, adresse | candidature |
| Personne de contact, téléphone | candidature |
| Poste | candidature |
| Taux | « plein temps » ou « temps partiel (80 %) » |
| Mode | écrit, électronique, téléphone, en personne |
| Assignée par l'ORP | oui / non |
| Résultat | voir ci-dessous |

**Résultat**, à partir du statut de suivi :

| Statut (page Candidatures) | Sur le formulaire |
|---|---|
| en attente, relancée | en suspens |
| entretien | en suspens (entretien le 12.11) |
| sans réponse | en suspens (sans réponse) |
| refus | refus : motif |
| engagement | engagement |

**Contrôle avant remise** : une ligne à qui il manque l'adresse de l'entreprise est marquée « à compléter » ; un clic ouvre le formulaire de la candidature. Le contact et le téléphone sont facultatifs (souvent absents d'une candidature en ligne) : ils ne bloquent rien.

## 3. Sorties

- **PDF** : une page A4 en paysage, mise en page proche du formulaire officiel. En-tête : ton nom, ton adresse, le mois ; puis le tableau ; en bas, la date et une ligne de signature. Comme pour la lettre, il passe par l'impression du navigateur (« Enregistrer au format PDF »).
- **CSV** : mêmes colonnes, séparateur `;` et encodage UTF-8 avec BOM, pour s'ouvrir directement dans Excel en Suisse.
- **Job-Room** : pour chaque ligne, un bouton « copier » par champ, dans l'ordre du formulaire de saisie de Job-Room. Envoie-moi une capture de ce formulaire (sans tes données) pour que l'ordre et les libellés correspondent exactement.

**Numéro AVS** : le formulaire papier le demande. Je propose de **ne pas l'enregistrer** : le PDF laisse la case vide, à compléter à la main (donnée sensible, et un seul champ par mois).

**Journal des recherches** : en option (case à cocher), une deuxième page liste les recherches effectuées dans le mois (alertes reçues, offres examinées), pour le cas où ton conseiller demande une preuve d'activité.

## 4. Mois remis

Le bouton **« Marquer comme remis »** enregistre la date de remise. Ensuite :

- le mois affiche « remis le … » et n'apparaît plus dans les rappels ;
- si tu modifies, ajoutes ou supprimes une candidature de ce mois, la page le signale (« modifié après la remise ») pour que tu puisses renvoyer une version corrigée ;
- tu peux annuler la remise en cas d'erreur.

## 5. Rappels ntfy

| Quand | Message, si… |
|---|---|
| Le **25** du mois, vers 9 h | « 12 / 20 candidatures en octobre, il reste 6 jours », si tu es sous l'objectif |
| Le **1er** du mois suivant | « Preuves d'octobre à remettre avant le 5 : 20 candidatures, 2 lignes à compléter » |
| La **veille** de la date limite | même rappel, si le mois n'est pas marqué remis |

La **date limite** est un réglage (jour **5** par défaut, à confirmer avec ton conseiller). Sans objectif ORP saisi, le rappel du 25 n'est pas envoyé. Chaque rappel n'est envoyé qu'une fois. Un clic sur la notification ouvre la page ORP du bon mois.

## 6. Base (migration 0012)

```
orp_months   month (AAAA-MM) PRIMARY, submitted_at?, exported_at?, changed_after_submit (bool),
             reminders_sent JSONB   -- {"under_target": "...", "due": "...", "eve": "..."}
settings     + orp_due_day (défaut 5)
```

Les candidatures ne changent pas : `orp_month` existe déjà.

## 7. Livraison en deux PR

| PR | Contenu | Prérequis de ton côté |
|---|---|---|
| **0.6.0-a** | Page ORP, contrôle avant remise, PDF, CSV, copie pour Job-Room, mois remis | une capture du formulaire Job-Room (facultatif) |
| **0.6.0-b** | Rappels ntfy (objectif, remise, veille) et réglage de la date limite | aucun |

## Points à valider

1. **Mois affiché par défaut** : le mois précédent tant qu'il n'est pas remis (§2).
2. **Correspondance des résultats** (§2), en particulier « sans réponse » → « en suspens (sans réponse) ».
3. **Adresse de l'entreprise obligatoire** avant remise ; contact et téléphone facultatifs (§2).
4. **PDF par l'impression du navigateur**, en A4 paysage, et **CSV pour Excel** (§3).
5. **Numéro AVS non enregistré**, case laissée vide sur le PDF (§3).
6. **Journal des recherches** en annexe facultative (§3).
7. **Rappels** le 25, le 1er et la veille de la date limite, **jour 5 par défaut** (§5).
8. **Deux PR** (§7).

## Écarts avec la PR a

- **Job-Room** : sans capture du formulaire, les boutons « copier » suivent l'ordre des colonnes du formulaire papier. À ajuster quand tu m'envoies la capture.
- **Journal des recherches** : l'annexe liste les alertes reçues dans le mois (date, site, alerte, nombre d'offres). Les « offres examinées » ne sont pas encore datées en base : elles n'y figurent pas.
- **Mois par défaut** : le mois précédent seulement s'il contient des candidatures ; sinon le mois en cours.
- **Export** : la date du dernier export est notée au téléchargement du CSV et à l'impression du PDF ; elle servira aux rappels (PR b).
- **Date limite** : fixée au 5 du mois suivant ; le réglage arrive avec la PR b.
