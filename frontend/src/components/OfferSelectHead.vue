<script setup lang="ts">
import AppIcon from "./AppIcon.vue";

// L'en-tête de la sélection multiple (§72q, planches CandidaturesSelection et CandidaturesOrdinateurSelection du 19.11) :
// la croix ronde « Quitter la sélection » et « N sélectionnées » ; dessous, la pastille-bouton « Toutes les expirées · N »
// (masquée s'il n'y en a aucune). Sur ordinateur, « Annuler » et « Écarter N offres » sont sur la même ligne ; sur
// téléphone, ils sont dans la barre du bas (OfferSelectBar).
const props = defineProps<{ count: number; expired: number; allExpired: boolean; actions: boolean }>();
const emit = defineEmits<{ quit: []; expired: []; discard: [] }>();

function discard(): void {
  if (props.count > 0) emit("discard");
}
</script>

<template>
  <div
    :class="['multi-head', { 'multi-head-wide': actions }]"
    data-test="multi-head"
  >
    <div class="multi-head-row">
      <button
        type="button"
        class="multi-quit"
        aria-label="Quitter la sélection"
        data-test="multi-quit"
        @click="emit('quit')"
      >
        <AppIcon name="close" />
      </button>
      <component
        :is="actions ? 'span' : 'h1'"
        class="multi-count"
        role="status"
        data-test="multi-count"
      >
        {{ count > 1 ? `${count} sélectionnées` : `${count} sélectionnée` }}
      </component>
      <template v-if="actions">
        <button
          type="button"
          class="multi-cancel"
          data-test="multi-cancel"
          @click="emit('quit')"
        >
          Annuler
        </button>
        <button
          type="button"
          class="multi-discard"
          :aria-disabled="count === 0 ? 'true' : undefined"
          data-test="multi-discard"
          @click="discard"
        >
          {{ count > 1 ? `Écarter ${count} offres` : `Écarter ${count} offre` }}
        </button>
      </template>
    </div>
    <div v-if="expired > 0">
      <button
        type="button"
        class="multi-expired"
        :aria-pressed="allExpired"
        data-test="multi-expired"
        @click="emit('expired')"
      >
        <svg
          v-if="allExpired"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="3"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        ><path d="m5 12 5 5 9-10" /></svg>Toutes les expirées · {{ expired }}
      </button>
    </div>
  </div>
</template>

<style>
/* Téléphone (CandidaturesSelection) : 14 px entre la ligne du titre (48 px) et la pastille ; croix ronde de 44 px, trait
   de 1,5 px, icône de 20 ; titre 24/30 800 à 12 px ; pastille de 44 px, 16 px dedans, texte 15 px gras, pressée : fond
   --primary-soft, texte --primary-text, contour de 2 px --action et coche de 16. Ordinateur (CandidaturesOrdinateurSelection) :
   10 px entre les lignes et entre les éléments, « N sélectionnées » 18 px 800, boutons de 44 px 15 px gras, pastille de
   40 px, 14 px dedans, texte 14 px. */
.multi-head { --sh-gap: 14px; --sh-row: 48px; --sh-pill: 44px; --sh-pill-x: 16px; --sh-pill-font: 15px; --sh-title: 24px; --sh-title-lh: 30px; display: flex; flex-direction: column; gap: var(--sh-gap); }
.multi-head-row { display: flex; align-items: center; gap: var(--space-3); min-height: var(--sh-row); }
.multi-quit { flex: none; display: grid; place-items: center; width: var(--target-min); height: var(--target-min); padding: 0; border: 0; border-radius: 50%; background: transparent; box-shadow: inset 0 0 0 1.5px var(--card-line); color: var(--text); }
.multi-quit .icon { width: 20px; height: 20px; }
.multi-count { flex: 1; min-width: 0; margin: 0; font-size: var(--sh-title); line-height: var(--sh-title-lh); font-weight: var(--weight-heavy); }
.multi-expired { display: inline-flex; align-items: center; gap: var(--space-1); height: var(--sh-pill); padding: 0 var(--sh-pill-x); border: 0; border-radius: var(--radius-pill); background: var(--surface); box-shadow: inset 0 0 0 1.5px var(--card-line); color: var(--primary-text); font-size: var(--sh-pill-font); font-weight: var(--weight-bold); white-space: nowrap; }
.multi-expired[aria-pressed="true"] { background: var(--primary-soft); box-shadow: inset 0 0 0 2px var(--action); }
.multi-cancel, .multi-discard { flex: none; height: var(--target-min); padding: 0 var(--space-4); border: 0; border-radius: var(--radius-pill); font-size: var(--font-label); font-weight: var(--weight-bold); white-space: nowrap; }
.multi-cancel { background: var(--surface); box-shadow: inset 0 0 0 1.5px var(--action); color: var(--primary-text); }
.multi-discard { --sd-x: 18px; padding: 0 var(--sd-x); background: var(--action); color: var(--on-action); }
.multi-discard[aria-disabled="true"] { background: var(--line-soft); color: var(--text-secondary); cursor: default; }
.multi-head-wide { --sh-gap: 10px; --sh-row: 44px; --sh-pill: 40px; --sh-pill-x: 14px; --sh-pill-font: 14px; --sh-title: 18px; --sh-title-lh: normal; box-sizing: border-box; width: 100%; padding-bottom: var(--space-1); }
.multi-head-wide .multi-head-row { gap: var(--sh-gap); }
</style>
