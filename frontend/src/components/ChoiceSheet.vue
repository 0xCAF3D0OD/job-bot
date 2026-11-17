<script setup lang="ts">
import { nextTick, ref, watch } from "vue";

import BottomSheet from "./BottomSheet.vue";

// La feuille à boutons radio des Réglages sur téléphone (LISEZMOI §56 du 17.11, planche Reglages) : la feuille en îlot
// du §45 (BottomSheet, `size="fit"`), le titre, la précision dessous, puis une ligne de 56 px par choix (rond, libellé,
// précision en gris). Choisir ferme la feuille. Des boutons role="radio" : les flèches déplacent le focus, Entrée ou
// Espace choisissent (sans fermer la feuille à chaque flèche).
export type SheetChoice = { value: string; label: string; hint?: string; test?: string };

const props = defineProps<{ open: boolean; title: string; hint?: string; choices: SheetChoice[]; modelValue: string }>();
const emit = defineEmits<{ close: []; "update:modelValue": [value: string] }>();
const group = ref<HTMLElement | null>(null);

function pick(value: string): void {
  if (value !== props.modelValue) emit("update:modelValue", value);
  emit("close");
}

function radios(): HTMLElement[] {
  return [...(group.value?.querySelectorAll<HTMLElement>("[role=radio]") ?? [])];
}

function onKeydown(event: KeyboardEvent): void {
  if (!["ArrowDown", "ArrowUp", "ArrowRight", "ArrowLeft", "Home", "End"].includes(event.key)) return;
  event.preventDefault();
  const list = radios();
  const at = list.indexOf(document.activeElement as HTMLElement);
  const forward = event.key === "ArrowDown" || event.key === "ArrowRight";
  const next = event.key === "Home" ? 0 : event.key === "End" ? list.length - 1 : forward ? at + 1 : at - 1;
  list[(next + list.length) % list.length]?.focus();
}

// À l'ouverture, le focus va sur le choix actuel.
watch(
  () => props.open,
  async (open) => {
    if (!open) return;
    await nextTick();
    radios().find((radio) => radio.getAttribute("aria-checked") === "true")?.focus();
  },
);
</script>

<template>
  <BottomSheet
    :open="open"
    :title="title"
    :subtitle="hint"
    @close="emit('close')"
  >
    <div
      ref="group"
      class="choice-sheet"
      role="radiogroup"
      :aria-label="title"
      data-test="choice-sheet"
      @keydown="onKeydown"
    >
      <button
        v-for="choice in choices"
        :key="choice.value"
        type="button"
        role="radio"
        class="choice-sheet-row"
        :aria-checked="modelValue === choice.value"
        :tabindex="modelValue === choice.value ? 0 : -1"
        :data-test="choice.test ?? `choice-${choice.value}`"
        @click="pick(choice.value)"
      >
        <span
          class="choice-sheet-dot"
          aria-hidden="true"
        />
        <span class="choice-sheet-text">
          <span class="choice-sheet-label">{{ choice.label }}</span>
          <span
            v-if="choice.hint"
            class="choice-sheet-hint"
          >{{ choice.hint }}</span>
        </span>
      </button>
    </div>
  </BottomSheet>
</template>

<style>
/* Planche Reglages (§56) : lignes de 56 px séparées d’un trait --line-soft ; rond de 22 px posé sur la grille de 4
   (24 px), trait 2 px --button-outline, à l’encre (--text) avec un point de 10 → 12 px quand il est choisi ; libellé
   16 px, en gras quand il est choisi ; précision 13 px en gris. */
.choice-sheet { --cs-dot: 24px; --cs-in: 12px; --cs-hint: 13px; --cs-label-weight: 500; display: grid; }
.choice-sheet-row { display: flex; align-items: center; gap: var(--space-3); width: 100%; min-height: 56px; padding: 0; border: 0; border-top: 1px solid var(--line-soft); background: transparent; font: inherit; text-align: left; color: var(--text); cursor: pointer; }
.choice-sheet-dot { flex: none; display: grid; place-items: center; box-sizing: border-box; width: var(--cs-dot); height: var(--cs-dot); border: 2px solid var(--button-outline); border-radius: 50%; }
.choice-sheet-row[aria-checked="true"] .choice-sheet-dot { border-color: var(--text); }
.choice-sheet-row[aria-checked="true"] .choice-sheet-dot::after { content: ""; width: var(--cs-in); height: var(--cs-in); border-radius: 50%; background: var(--text); }
.choice-sheet-text { display: grid; flex: 1; min-width: 0; }
.choice-sheet-label { font-size: var(--font-body); font-weight: var(--cs-label-weight); }
.choice-sheet-row[aria-checked="true"] .choice-sheet-label { font-weight: var(--weight-bold); }
.choice-sheet-hint { font-size: var(--cs-hint); color: var(--text-secondary); }
</style>
