# 52 — L'assistant propose, tu confirmes (version 0.42.0)

> Statut : **validé** le 2026-10-15, livré.
> Suite annoncée dans docs/24 §3 : « Des actions avec ta confirmation pourront venir plus tard. » Aujourd'hui l'assistant répond, explique et rédige, mais **ne modifie rien** : quand il conseille « passe ces trois offres en Plus tard » ou « celle-ci est sans réponse depuis 3 semaines », il faut aller le faire à la main, offre par offre.

## 1. Le principe

- L'assistant peut **proposer** une action ; il ne l'exécute **jamais** lui-même.
- La proposition s'affiche dans la discussion comme une **carte** : ce qui va changer, en une phrase, avec **« Confirmer »** et **« Non merci »**.
- Seul ton clic sur « Confirmer » fait le changement, par les mêmes règles que les boutons de la plateforme. Une fois fait : « Fait · **Annuler** », qui remet l'état d'avant.

```
┌ Proposition ─────────────────────────────────────┐
│ Passer « Cloud Architect » (Jura Data SA)         │
│ en Plus tard                                      │
│                       [ Non merci ]  [ Confirmer ]│
└───────────────────────────────────────────────────┘
        ↓ après « Confirmer »
│ ✓ Fait : en Plus tard.                    Annuler │
```

## 2. Les actions possibles (première version)

Seulement des changements **internes et réversibles**, déjà faisables d'un clic ailleurs :

| Action | Sur | Valeurs |
|---|---|---|
| **Trier une offre** | une offre | Plus tard · Ignorer · Remettre à examiner |
| **Signaler une offre expirée** | une offre | expirée / pas expirée |
| **Changer le statut d'une candidature** | une candidature | Relancée · Sans réponse · Refus · Engagement |

**Jamais**, même avec confirmation : créer ou supprimer une candidature (elle compte dans tes preuves ORP), envoyer un message, toucher au profil, aux coordonnées ou aux réglages, dépenser de l'IA (rédiger une lettre). Pour celles-là, l'assistant donne le lien vers la bonne page.

- **Trois propositions au plus** par réponse ; pour un lot plus grand, il renvoie vers la liste filtrée.
- Une proposition qui ne vaut plus (offre déjà triée, candidature déjà passée à un autre statut) le dit au moment de « Confirmer » et ne fait rien.

## 3. Ce qui se passe derrière

- Un nouvel **outil** de l'assistant, `proposer_action` : il vérifie que la cible existe et que le changement est permis, enregistre la proposition et répond à l'IA « proposition affichée, en attente de ta confirmation ». L'IA ne peut pas confirmer.
- La proposition arrive dans le fil comme un nouvel événement (`action`) ; elle reste visible quand tu rouvres la discussion, avec son état (proposée, faite, annulée, refusée).
- « Confirmer » et « Annuler » passent par l'API de la plateforme (`POST /api/assistant/actions/{id}/confirm` et `…/undo`), qui applique la même logique que les boutons des pages (journal, relances, compteurs).
- **Base** (migration 0045) :

```
chat_actions  id, conversation_id, kind (offer_status|offer_expiry|application_status),
              target_id, value, previous?, label, state (proposed|done|undone|declined|stale),
              created_at, decided_at?
```

## 4. Coût, confidentialité

- Rien de plus envoyé à l'IA : elle voit les mêmes données qu'avant. Coût inchangé (une proposition est un appel d'outil dans la même réponse).
- Effacées avec la discussion (30 jours, docs/24 §4).

## 5. Livraison

Une PR (**0.42.0**) : backend (outil, table, deux routes, tests), interface (carte dans la discussion), consigne de l'assistant mise à jour (`assistant-v3`), docs/exploitation.

## Points à valider

1. **Proposer, jamais exécuter** ; « Confirmer » puis « Annuler » possible (§1).
2. **Trois actions** : trier une offre, la signaler expirée, changer le statut d'une candidature ; rien qui crée, supprime, envoie ou dépense (§2).
3. **Trois propositions au plus** par réponse (§2).
4. **Une PR** (§5).

## Écarts avec la livraison

- **États** : « Confirmer » sur une proposition qui ne vaut plus (offre triée entre-temps, candidature passée à un autre statut) la passe en « Plus à faire : rien n'a été changé ». « Annuler » refuse si la cible a changé depuis (« … a changé depuis : rien n'est annulé »).
- **Pages ouvertes** : après « Confirmer » ou « Annuler », les Offres, le Suivi et Aujourd'hui se rechargent d'eux-mêmes.
- **Statut d'une candidature** : mêmes règles que « Modifier la candidature » (date du statut, date de relance gardée si elle existait, mois ORP marqué changé s'il était remis).
- **Discussion rouverte** : chaque proposition revient sous la réponse qui l'a faite, avec son état.
- **Consigne de l'assistant** passée en `assistant-v3` : les propositions, et le guide de la plateforme mis à jour (fiche d'offre, Préparer en trois onglets, cartes du Suivi, Réglages par rubrique).
- **Vérification** : l'IA n'est pas configurée sur l'instance de test (pas de clé manipulée) ; le flux complet est couvert par les tests (IA simulée), et les routes Confirmer / Annuler / effacement ont été essayées sur la base de test avec une proposition insérée à la main.
