<script setup lang="ts">
import { defineAsyncComponent, useId } from "vue";

import SidePanel from "./SidePanel.vue";

// La feuille n'est chargée que sur téléphone : Réglages sur ordinateur ne la télécharge pas.
const BottomSheet = defineAsyncComponent(() => import("./BottomSheet.vue"));

// Un panneau à boutons radio (maquette ReglagesOrdinateur, panneaux `lg` et `tx`) : le titre du panneau, un sur-titre
// en capitales grises, puis une ligne de 68 px par choix (cercle de 24 px, libellé 16/22 et précision 14/20). Le choix
// s'applique tout de suite ; un choix indisponible reste visible, grisé. Des boutons radio natifs : flèches du
// clavier, nom et état lus par les lecteurs d'écran.
export type Choice = { value: string; label: string; hint: string; disabled?: boolean };

// `sheet` (planche ReglagesLangue, §46 du 17.11) : sur téléphone, une feuille du bas courte au lieu du panneau de droite.
defineProps<{ open: boolean; title: string; heading: string; choices: Choice[]; modelValue: string; note?: string; sheet?: boolean }>();
const emit = defineEmits<{ close: []; "update:modelValue": [value: string] }>();
const name = useId();
const headingId = `${name}-heading`;
</script>

<template>
  <component
    :is="sheet ? BottomSheet : SidePanel"
    :open="open"
    :title="title"
    @close="emit('close')"
  >
    <div
      class="choice-panel"
      data-test="choice-panel"
    >
      <h3
        :id="headingId"
        class="choice-panel-heading"
      >
        {{ heading }}
      </h3>
      <div
        role="radiogroup"
        :aria-labelledby="headingId"
      >
        <label
          v-for="choice in choices"
          :key="choice.value"
          :class="['choice-rad', { disabled: choice.disabled }]"
          :data-test="`choice-${choice.value}`"
        >
          <input
            type="radio"
            :name="name"
            :value="choice.value"
            :checked="modelValue === choice.value"
            :disabled="choice.disabled"
            @change="emit('update:modelValue', choice.value)"
          >
          <span class="choice-rad-text">
            <b>{{ choice.label }}</b>
            <span>{{ choice.hint }}</span>
          </span>
        </label>
      </div>
      <p
        v-if="note"
        class="choice-panel-note"
      >
        {{ note }}
      </p>
    </div>
  </component>
</template>
