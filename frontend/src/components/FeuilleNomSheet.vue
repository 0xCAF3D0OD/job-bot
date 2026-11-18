<script setup lang="ts">
import { useId, watch } from "vue";

import { type IdentityField, useSheetIdentity } from "../sheetIdentity";
import BottomSheet from "./BottomSheet.vue";
import FieldSaveStatus from "./FieldSaveStatus.vue";

// « Ton nom sur la feuille » (LISEZMOI §70, planches FeuilleNom et FeuilleNomSombre ; Kevin, 18.11.2026) : une page
// entière ouverte depuis « Préparer le rendez-vous », flèche « Retour » à gauche du titre. La pastille « Tout est
// enregistré dès que tu quittes un champ », puis trois cartes : Prénom et nom, Ton conseiller ORP (pré-rempli par le
// rendez-vous s'il est connu), Office régional. Chaque champ s'enregistre dans le compte quand on le quitte.
const props = defineProps<{ open: boolean }>();
const emit = defineEmits<{ close: [] }>();

const { values, states, load, save, edit } = useSheetIdentity();
watch(
  () => props.open,
  (open) => {
    if (open) void load();
  },
  { immediate: true },
);

const base = useId();
const fields: { field: IdentityField; label: string; autocomplete: string }[] = [
  { field: "name", label: "Prénom et nom", autocomplete: "name" },
  { field: "advisor", label: "Ton conseiller ORP", autocomplete: "off" },
  { field: "office", label: "Office régional", autocomplete: "off" },
];

// Entrée : on quitte le champ (il s'enregistre), comme un toucher ailleurs.
function leave(event: Event): void {
  (event.target as HTMLInputElement).blur();
}
</script>

<template>
  <BottomSheet
    :open="open"
    title="Ton nom sur la feuille"
    full
    back
    class="feuille-nom"
    data-test="feuille-nom"
    @close="emit('close')"
  >
    <p class="feuille-nom-note">
      Tout est enregistré dès que tu quittes un champ
    </p>
    <form
      class="feuille-nom-fields"
      @submit.prevent
    >
      <div
        v-for="item in fields"
        :key="item.field"
        class="feuille-nom-card"
      >
        <label
          class="feuille-nom-label"
          :for="`${base}-${item.field}`"
        >{{ item.label }}</label>
        <input
          :id="`${base}-${item.field}`"
          v-model="values[item.field]"
          type="text"
          maxlength="120"
          :autocomplete="item.autocomplete"
          :aria-describedby="`${base}-${item.field}-status`"
          :data-test="`feuille-nom-${item.field}`"
          @input="edit(item.field)"
          @change="save(item.field)"
          @keydown.enter.prevent="leave"
        >
        <FieldSaveStatus
          :id="`${base}-${item.field}-status`"
          :state="states[item.field]"
          reserve
          @retry="save(item.field)"
        />
      </div>
    </form>
  </BottomSheet>
</template>

<style scoped>
/* Planche FeuilleNom : pastille neutre de 30 px (13 px, graisse 600) ; cartes blanches, trait 1 px, rayon 20, 16 px de
   marge intérieure, 12 px entre elles ; libellé 13 px gris au-dessus d'un champ de 52 px, rayon 14, texte 17 px. */
.feuille-nom { --fn-note-top: 6px; --fn-note-bottom: 14px; --fn-note-pad: 5px; --fn-card-radius: 20px; --fn-field-h: 52px; --fn-field-pad: 14px; --fn-field-radius: 14px; }
.feuille-nom :deep(.sheet-body) { gap: 0; padding-inline: var(--space-4); }
.feuille-nom-note {
  justify-self: start; display: inline-flex; align-items: center; min-height: 30px; margin: var(--fn-note-top) 0 var(--fn-note-bottom); padding: var(--fn-note-pad) var(--space-3);
  border-radius: var(--radius-pill); background: var(--surface-muted); color: var(--text-lead);
  font-size: calc(var(--font-small) - 1px); font-weight: var(--weight-semibold);
}
.feuille-nom-fields { display: grid; gap: var(--space-3); margin: 0; }
.feuille-nom-card { padding: var(--space-4); border: 1px solid var(--line); border-radius: var(--fn-card-radius); background: var(--surface); }
.feuille-nom-label { display: block; font-size: calc(var(--font-small) - 1px); color: var(--text-secondary); }
.feuille-nom-card input { display: block; width: 100%; height: var(--fn-field-h); margin-top: var(--space-2); padding: 0 var(--fn-field-pad); border-radius: var(--fn-field-radius); font-size: calc(var(--font-body) + 1px); }
</style>
