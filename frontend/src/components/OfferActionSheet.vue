<script setup lang="ts">
import { useId } from "vue";

import type { Offer } from "../api/client";
import type { MoreMenuItem } from "./MoreMenu.vue";
import AppIcon from "./AppIcon.vue";
import BottomSheet from "./BottomSheet.vue";
import CompanyLogo from "./CompanyLogo.vue";
import { companyPlace } from "../format";

// La feuille d'actions d'une offre (ActionsOffre, §17 du 15 novembre) : ouverte par le « ⋯ » de la page de l'offre,
// jamais depuis la carte de la liste. Deux cartes flottantes à 10 px des bords : l'en-tête (logo de 40 px, poste,
// entreprise · lieu) puis les actions dans l'ordre de la planche, « J'ai déjà postulé », « Écarter l'offre » en rouge
// (« Annuler » 6 s dans le message, docs/108), puis celles de la fiche (`extra`) ; « Annuler » dans sa propre carte,
// sans croix. Échap, le voile et le retour du téléphone ferment toujours (BottomSheet).
withDefaults(defineProps<{ offer: Offer | null; extra?: MoreMenuItem[]; sentTitle?: string }>(), {
  extra: () => [],
  sentTitle: "Marquer comme envoyée",
});
const emit = defineEmits<{ close: []; discard: [offer: Offer]; sent: [offer: Offer] }>();
const titleId = useId();
</script>

<template>
  <BottomSheet
    :open="offer !== null"
    title=""
    :labelled-by="titleId"
    class="offer-actions-sheet"
    data-test="offer-actions"
    @close="emit('close')"
  >
    <template v-if="offer">
      <div class="offer-actions-card">
        <div class="offer-actions-head">
          <CompanyLogo :offer="offer" />
          <span class="offer-actions-name">
            <span
              :id="titleId"
              class="offer-actions-title"
            >{{ offer.title }}</span>
            <span class="offer-actions-where">{{ companyPlace(offer.company, offer.location) }}</span>
          </span>
        </div>
        <button
          v-if="offer.status !== 'applied'"
          type="button"
          class="offer-action"
          data-test="offer-action-sent"
          @click="emit('sent', offer)"
        >
          <AppIcon name="send" />{{ sentTitle }}
        </button>
        <button
          v-if="offer.status !== 'ignored'"
          type="button"
          class="offer-action offer-actions-discard"
          data-test="offer-action-discard"
          @click="emit('discard', offer)"
        >
          <AppIcon name="close" />Écarter l’offre
        </button>
        <button
          v-for="item in extra"
          :key="item.test"
          type="button"
          class="offer-action"
          :data-test="`offer-action-${item.test}`"
          @click="emit('close'); item.run?.()"
        >
          <AppIcon :name="item.icon ?? 'more'" />{{ item.label }}
        </button>
      </div>
      <button
        type="button"
        class="offer-actions-cancel"
        data-test="offer-actions-cancel"
        @click="emit('close')"
      >
        Annuler
      </button>
    </template>
  </BottomSheet>
</template>

<style scoped>
/* Valeurs d'ActionsOffre : cartes blanches de rayon 22 à 10 px des bords et 24 px du bas, 8 px entre elles ; en-tête
   16/18 avec trait, logo de 40 px ; lignes de 58 px (56 sur la grille de 4), icône de 22 px bleue à 14 px (16) du
   texte 17/600, trait entre elles ; « Annuler » 17/700 bleu texte. */
.offer-actions-sheet {
  --act-10: 10px; --act-17: 1.0625rem; --act-row: 56px;
  inset: auto var(--act-10) var(--space-6); width: auto; max-width: none; margin: 0; border-radius: 0; background: none; box-shadow: none;
}
.offer-actions-sheet :deep(.sheet-inner) { gap: var(--space-2); padding: 0; }
.offer-actions-sheet :deep(.sheet-inner)::before { display: none; }
.offer-actions-sheet :deep(.sheet-body) { display: flex; flex-direction: column; gap: var(--space-2); margin: 0; padding: 0; overflow: visible; }
.offer-actions-card, .offer-actions-cancel { overflow: hidden; border-radius: var(--title-sub); background: var(--surface); }
.offer-actions-card { display: flex; flex-direction: column; }
.offer-actions-head { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-4); border-bottom: 1px solid var(--line-soft); }
.offer-actions-head :deep(.logo) { flex: none; width: var(--btn-compact); height: var(--btn-compact); }
.offer-actions-name { display: flex; flex-direction: column; min-width: 0; }
.offer-actions-title { font-size: var(--font-body); font-weight: var(--weight-bold); }
.offer-actions-where { font-size: var(--label-caps); color: var(--text-secondary); }
.offer-action, .offer-actions-cancel { display: flex; min-height: var(--act-row); border: 0; font-size: var(--act-17); }
.offer-action {
  gap: var(--space-4); padding: 0 var(--space-4); border-radius: 0; background: transparent; color: var(--text); font-weight: var(--weight-semibold); text-align: left;
}
.offer-action + .offer-action { border-top: 1px solid var(--line-soft); }
.offer-action .icon { flex: none; width: var(--title-sub); height: var(--title-sub); color: var(--primary-graphic); stroke-width: 2.2; }
.offer-actions-discard, .offer-actions-discard .icon { color: var(--danger); }
.offer-actions-cancel { justify-content: center; color: var(--primary-text); font-weight: var(--weight-bold); }
</style>
