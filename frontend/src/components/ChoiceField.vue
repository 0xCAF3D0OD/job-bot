<script setup lang="ts" generic="T extends string">
import { computed } from "vue";

import ChoiceMenu from "./ChoiceMenu.vue";

// Un champ à choix dans un formulaire (audit du 17.11, K13 et N21 ; LISEZMOI §65 : plus de menu du système) : la valeur
// dans une boîte de champ, un chevron vers le bas ; le bouton ouvre le menu de l’app (ChoiceMenu, celui des Réglages).
// `stacked` (ordinateur, planche CandidaturesOrdinateurAjouter) : libellé 14/700 au-dessus, 8 px, boîte de 48 px, trait
// de 1,5 px gris, rayon 8, texte 16, chevron de 16 à 16 px du bord. Sinon (téléphone), la boîte de 56 px des champs
// communs, rayon 12, le libellé posé sur le trait du haut (FormField). Le nom du bouton dit le libellé et la valeur.
const props = defineProps<{ label: string; choices: Record<T, string>; modelValue: T; stacked?: boolean; testId?: string }>();
const emit = defineEmits<{ "update:modelValue": [value: T] }>();
const list = computed(() => (Object.entries(props.choices) as [T, string][]).map(([value, label]) => ({ value, label })));
</script>

<template>
  <div :class="['choice-field', { 'choice-field-stacked': stacked }]">
    <span
      class="choice-field-label"
      aria-hidden="true"
    >{{ label }}</span>
    <ChoiceMenu
      :label="label"
      :choices="list"
      :model-value="modelValue"
      :test-id="testId"
      @update:model-value="emit('update:modelValue', $event as T)"
    />
  </div>
</template>

<style>
.choice-field { --cf-h: var(--ff-h); --cf-radius: var(--ff-radius); --cf-chevron: 16px; position: relative; display: grid; grid-template-columns: minmax(0, 1fr); min-width: 0; }
.choice-field > .choice-menu { display: block; min-width: 0; }
.choice-field .choice-menu-button {
  display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); box-sizing: border-box; width: 100%;
  height: var(--cf-h); min-height: var(--cf-h); padding: 0 var(--space-4) 0 var(--ff-pad-x); border: var(--field-line) solid var(--field-border);
  border-radius: var(--cf-radius); background: var(--surface); color: var(--text); font-size: var(--font-body); text-align: left;
}
.choice-field .choice-menu-value { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.choice-field .choice-menu-button:hover { border-color: var(--field-border-hover); }
.choice-field .choice-menu-button:focus-visible { outline: none; border-color: var(--primary-graphic); box-shadow: inset 0 0 0 0.5px var(--primary-graphic); }
.choice-field .choice-menu-button .icon { flex: none; width: var(--cf-chevron); height: var(--cf-chevron); transform: rotate(90deg); }
.choice-field .choice-menu .menu { left: 0; right: 0; top: calc(100% + var(--space-1)); min-width: 0; }
.choice-field .choice-menu .menu.up { top: auto; bottom: calc(100% + var(--space-1)); }
/* Téléphone : le libellé sur le trait du haut, comme un champ commun rempli (FormField). */
.choice-field:not(.choice-field-stacked) > .choice-field-label {
  position: absolute; z-index: 1; left: var(--ff-label-x); top: var(--ff-float-top); padding: 0 var(--space-1); max-width: calc(100% - 2 * var(--ff-label-x));
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; background: linear-gradient(to bottom, transparent 50%, var(--surface) 50%);
  font-size: var(--ff-float-size); line-height: var(--space-4); font-weight: var(--weight-bold); color: var(--text-lead); pointer-events: none;
}
.choice-field:not(.choice-field-stacked):focus-within > .choice-field-label { color: var(--primary-text); }
/* Ordinateur (planche CandidaturesOrdinateurAjouter) : libellé au-dessus, boîte de 48, trait gris foncé, rayon 8. */
.choice-field-stacked { --cf-h: var(--space-12); --cf-radius: var(--radius-sm); gap: var(--space-2); }
.choice-field-stacked > .choice-field-label { font-size: var(--font-small); line-height: var(--space-5); font-weight: var(--weight-bold); color: var(--text); }
.choice-field-stacked .choice-menu-button { border-color: var(--text-secondary); }
.choice-field-stacked .choice-menu-button .icon { color: var(--text-secondary); }
</style>
