<script setup lang="ts">
import type { Offer } from "../api/client";
import type { MoreMenuItem } from "./MoreMenu.vue";
import AppIcon from "./AppIcon.vue";
import BottomSheet from "./BottomSheet.vue";
import CompanyLogo from "./CompanyLogo.vue";
import { companyPlace } from "../format";

// La feuille d'actions d'une offre (ActionsOffre, §45 du 17.11) : ouverte par le « ⋯ » de la page de l'offre, jamais
// depuis la carte de la liste. Une feuille en îlot, courte, sans poignée : en-tête logo de 40 px, poste, entreprise · lieu
// et croix ronde (plus de « Annuler »). Les actions en lignes simples, « J'ai déjà postulé » puis celles de la fiche
// (`extra`, dans leur ordre : Signaler comme expirée, Cette note ne me correspond pas, Partager…) ; après une bande de
// 8 px, « Écarter l'offre » en rouge, en dernier (« Annuler » 6 s dans le message, docs/108).
withDefaults(defineProps<{ offer: Offer | null; extra?: MoreMenuItem[]; sentTitle?: string }>(), {
  extra: () => [],
  sentTitle: "Marquer comme envoyée",
});
const emit = defineEmits<{ close: []; discard: [offer: Offer]; sent: [offer: Offer] }>();
</script>

<template>
  <BottomSheet
    :open="offer !== null"
    :title="offer?.title ?? ''"
    :subtitle="offer ? companyPlace(offer.company, offer.location) : ''"
    class="offer-actions-sheet"
    data-test="offer-actions"
    @close="emit('close')"
  >
    <template #lead>
      <CompanyLogo
        v-if="offer"
        :offer="offer"
      />
    </template>
    <template v-if="offer">
      <div class="offer-actions-list">
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
      <div
        v-if="offer.status !== 'ignored'"
        class="offer-actions-end"
      >
        <button
          type="button"
          class="offer-action offer-actions-discard"
          data-test="offer-action-discard"
          @click="emit('discard', offer)"
        >
          <AppIcon name="close" />Écarter l’offre
        </button>
      </div>
    </template>
  </BottomSheet>
</template>

<style scoped>
/* ActionsOffre : en-tête logo 40 px (rayon 11) et titre 18/24 ; lignes de 56 px, 16/600, icône 22 bleue à 12 px du texte,
   trait #E5E2D9 au-dessus de chacune ; bande #ECE9E1 de 8 px, 12 px sous la dernière ligne, puis « Écarter » rouge. */
.offer-actions-sheet { --act-row: 56px; }
.offer-actions-sheet :deep(.sheet-head) { gap: var(--space-3); }
.offer-actions-sheet :deep(.logo) { flex: none; width: var(--btn-compact); height: var(--btn-compact); }
.offer-actions-sheet :deep(.sheet-title) { font-size: var(--font-title); line-height: var(--space-6); }
.offer-actions-sheet :deep(.sheet-subtitle) { margin: 0; }
.offer-actions-sheet :deep(.sheet-body) { display: block; padding-top: 0; }
.offer-action {
  display: flex; gap: var(--space-3); width: 100%; min-height: var(--act-row); padding: 0 var(--space-1);
  border: 0; border-top: 1px solid var(--line); border-radius: 0; background: transparent;
  color: var(--text); font-size: var(--font-body); font-weight: var(--weight-semibold); text-align: left;
}
.offer-action .icon { flex: none; width: var(--title-sub); height: var(--title-sub); color: var(--primary-graphic); stroke-width: 2.2; }
.offer-actions-end { margin: var(--space-3) calc(var(--sheet-pad) * -1) 0; padding: 0 var(--sheet-pad); border-top: var(--space-2) solid var(--surface-muted); }
.offer-actions-end .offer-action { border-top: 0; }
.offer-actions-discard, .offer-actions-discard .icon { color: var(--danger); }
</style>
