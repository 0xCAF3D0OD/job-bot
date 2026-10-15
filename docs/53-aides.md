# 53 — Moins de « ? » : l'assistant explique, une description au survol pour le reste (version 0.43.0)

> Statut : **validé** le 2026-10-15, livré.
> Retour du 2026-10-15 : « les ? n'ont plus lieu d'être si l'assistant permet d'expliquer le contenu ; à la limite, pour les plus complexes à comprendre, pouvoir avoir une description brève en passant 3 secondes sur le texte ».

## 1. Ce qu'il y a aujourd'hui

**55 boutons « ? »** dans 30 écrans, plus un « ? » dans l'en-tête de certains panneaux latéraux (Contacts, Candidature spontanée…). Ils datent de docs/29 (« aides visibles »), quand l'assistant n'existait pas. Beaucoup répètent ce que la page dit déjà, ou rassurent sur la confidentialité (« l'IA ne reçoit pas tes coordonnées »), ce que l'assistant sait expliquer.

## 2. Ce qui change

- **Tous les « ? » disparaissent**, ceux des panneaux latéraux compris.
- **Quatorze descriptions restent**, pour ce qui n'est pas évident à la lecture : elles s'affichent quand la souris reste **3 secondes** sur le libellé, dans une petite bulle sous le texte. Le libellé est **souligné en pointillé fin**, pour qu'on sache qu'il y a quelque chose.

| Écran | Libellé | Pourquoi la garder |
|---|---|---|
| Profil › Ce que je cherche | Lieux | le format (communes, ou cantons en deux lettres) |
| | Télétravail complet | ce que veut dire « si ouvert depuis la Suisse » |
| | Taux d'activité | la règle (« 60-80 % » passe avec un minimum de 80) |
| | Types d'offres, Langues | ce qui est écarté exactement |
| Profil › Parcours | Type (d'un bloc) | à quoi sert chaque type |
| Offre › Pour toi | la note | comment elle est calculée |
| Réglages | Chercher l'annonce chez l'employeur à partir de | le coût (≈ 0,02 $) |
| | Plafond mensuel de l'IA | ce qui s'arrête au-delà |
| | Sites suivis | lecteur intégré ou lu par l'IA (≈ 0,01 $ par e-mail) |
| | Marché de l'emploi (source) | l'effet avec « Mon domaine » |
| | ID de chaîne YouTube | où le trouver |
| Formations | Formation et chômage | l'ORP décide, pas la plateforme |
| Connexion | Création du compte | l'assistant n'est pas là avant la connexion |

- **Le reste passe à l'assistant** : la plupart des pages ont déjà leurs suggestions de questions ; on y ajoute « Comment ça marche ici ? » partout.
- **Téléphone** : pas de survol ; les descriptions ne s'affichent pas, l'assistant répond.
- **Lecteurs d'écran** : la description reste liée au libellé (lue avec lui), sans attendre.

## 3. Rien ne change ailleurs

Pas de changement de base ni d'API. Les textes gardés sont repris tels quels, raccourcis quand ils dépassent deux lignes.

## 4. Livraison

Une PR (**0.43.0**). Ordinateur et téléphone, captures avant / après.

## Points à valider

1. **Plus aucun « ? »**, panneaux latéraux compris (§2).
2. **Quatorze descriptions** gardées (le tableau), au survol de **3 secondes**, libellé **souligné en pointillé** (§2).
3. **« Comment ça marche ici ? »** ajouté aux suggestions de l'assistant (§2).
4. **Une PR** (§4).

## Écarts avec la livraison

- **Composant** `HoverNote` (remplace `HelpTip`, supprimé) : bulle après 3 s de souris immobile, fermée en sortant ; rien au toucher. Le pointillé n'apparaît que sur les écrans à souris (`hover: hover`).
- **Lecteurs d'écran** : la description passe par `aria-description` : lue avec le libellé, sans s'ajouter au texte d'un titre (« Pour toi »).
- **Fiche d'offre** : la description de la note est sur le titre « Pour toi » (le « ? » était à côté du résumé).
- **Connexion** : la description est sur « Crée-le une fois » ; **Formations** : sur « Formation et chômage ».
- **Panneaux latéraux** : l'aide de leur en-tête est retirée avec sa propriété (`help`) ; l'explication des Contacts (`CONTACTS_HELP`) aussi.
- **Assistant** : « Comment ça marche ici ? » en dernière suggestion sur chaque page.
- Vérifié dans le navigateur : rien à 1,5 s, la bulle à 3 s, plus aucun bouton « Aide ».
