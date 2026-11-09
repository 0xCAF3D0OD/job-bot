<script setup lang="ts">
import CopyButton from "./CopyButton.vue";

// Un champ à recopier (D32, MODIFICATIONS du 8 novembre au soir, §2.4) : le libellé au-dessus de la valeur ; à droite,
// le bouton copier (niveau 2, « Copier <libellé> », « Copié » annoncé). `choice` : une case à cocher sur Job-Room,
// dite par une étiquette grise, sans bouton. Une valeur absente s'écrit « Non renseigné ».
const props = defineProps<{ label: string; value: string; choice?: boolean }>();
const copyLabel = `Copier ${props.label.charAt(0).toLowerCase()}${props.label.slice(1)}`;
</script>

<template>
  <div
    class="block-field"
    data-test="copy-field"
  >
    <div class="block-field-text">
      <div class="block-field-label">
        {{ label }}
      </div>
      <div :class="['block-field-value', { 'block-field-none': !value }]">
        {{ value || "Non renseigné" }}
      </div>
      <span
        v-if="choice && value"
        class="block-tick"
      >☐ case à cocher dans Job-Room</span>
    </div>
    <CopyButton
      v-if="value && !choice"
      :value="value"
      :label="copyLabel"
      test-id="field-copy"
    />
  </div>
</template>
