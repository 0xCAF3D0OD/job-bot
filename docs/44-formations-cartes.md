# 44 — Formations : des cartes calmes, le suivi à part (version 0.36.0)

> Statut : **validé** le 2026-10-15. livré.
> Retour du 2026-10-15 (capture de la CKA « En cours ») : la carte empile le choix Intéressé / En cours / Terminée, le champ « Progression », puis « Préparer la demande à l'ORP » ; quand la formation est terminée s'ajoutent la date, le certificat, la demande de financement et « Ajouter à mon profil ». Trop dense, et la carte devient plus haute que ses voisines.

## 1. La carte ne montre que la formation

- En haut, comme aujourd'hui : type · organisme, **titre**, ligne courte (examen · anglais · payant · niveau).
- **Description sur 3 lignes au plus**, coupée par « … » ; la préparation conseillée n'est plus sur la carte. Les cartes d'une même rangée ont ainsi **la même hauteur**.
- **En bas, une seule ligne**, toujours au même endroit :
  - pas encore suivie : un bouton **« Suivre »** ;
  - suivie : une **pastille d'état** à gauche (« Intéressé », « En cours · module 6/12 », « Terminée · certificat ») et **« Gérer »** à droite.

```
┌──────────────────────────────────────────┐
│ Certification · The Linux Foundation     │
│ Certified Kubernetes Administrator (CKA) │
│ examen en ligne · anglais · payant · …   │
│ Certification de référence pour          │
│ administrer un cluster Kubernetes. Exa…  │
│                                          │
│ ● En cours · module 6/12        Gérer ›  │
└──────────────────────────────────────────┘
```

## 2. Le suivi dans le panneau latéral

« Suivre » ou « Gérer » ouvre le **panneau latéral** déjà utilisé ailleurs (Contacts, Relancer), sur ordinateur comme sur téléphone. Trois sections titrées, l'une sous l'autre, chacune seulement quand elle a un sens :

| Section | Contenu |
|---|---|
| **Mon suivi** | Intéressé · En cours · Terminée ; selon l'état : progression (en cours), date et certificat (terminée) |
| **Financement ORP** (payante) | « Préparer la demande », le texte à copier, puis Demandée / Acceptée / Refusée — comme aujourd'hui (docs/37) |
| **Mon profil** (terminée) | « Ajouter à mon profil », ou le lien vers le bloc créé (docs/37) |

En tête du panneau : le titre, l'organisme, la description complète et la préparation conseillée, et le lien vers la page officielle.

## 3. « Mes formations »

Même carte, même pastille : on voit d'un coup d'œil où l'on en est (en cours d'abord, puis intéressé, puis terminées).

## 4. Rien ne change ailleurs

Pas de changement de base ni d'API : seule la présentation change. Les formations proposées par l'IA gardent « Garder / Écarter » sur la carte tant qu'elles sont « à vérifier ».

## 5. Livraison

Une PR (**0.36.0**). Ordinateur et téléphone (sur téléphone, la ligne de la liste ouvre déjà un panneau : il prend les mêmes trois sections).

## Points à valider

1. **Carte calme** : description sur 3 lignes, une ligne en bas (« Suivre », ou pastille d'état + « Gérer ») (§1).
2. **Panneau latéral** en trois sections : Mon suivi, Financement ORP, Mon profil (§2).
3. **Une PR** (§5).

## Écarts avec la livraison

- **Carte** : description coupée à 3 lignes ; ligne du bas séparée par un trait, à hauteur fixe, toujours en bas de la carte : « Suivre », ou la pastille (point violet, « En cours · module 6/12 », « Terminée · certificat ») et « Gérer › ». Les cartes d'une rangée ont la même hauteur (vérifié sur la rangée de la CKA).
- **Panneau** : en tête, l'organisme, la ligne courte, la description complète, la préparation conseillée et « Page officielle › » (le titre est déjà celui du panneau) ; puis **Mon suivi**, **Financement ORP** (payante et suivie), **Mon profil** (terminée), chacune titrée et séparée par un trait. Même panneau sur téléphone.
- **Mes formations** : en cours, puis intéressé, puis terminées.
- « Garder / Écarter » reste sur la carte des formations proposées par l'IA.
