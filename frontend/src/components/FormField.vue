<script setup lang="ts">
import { computed, useId } from "vue";

// Un champ de formulaire commun (planche « Formulaires », règles §4) : le libellé au-dessus en
// semi-gras, « (facultatif) » en gris sur un champ facultatif (pas d'astérisque, Material 3), une
// aide d'une ligne sous le libellé, le champ, puis l'erreur sous le champ, avec une icône (WCAG 1.4.1,
// 3.3.1 ; Material 3 et Polaris). `width` : la largeur dit la réponse attendue, en caractères
// (Baymard Institute, Form Field Width). Le slot reçoit l'id, la description et l'état invalide.
const props = withDefaults(
  defineProps<{ label: string; optional?: boolean; hint?: string; error?: string; width?: 5 | 10 | 20 | 30 }>(),
  { optional: false, hint: "", error: "", width: undefined },
);

const id = useId();
const hintId = `${id}-hint`;
const errorId = `${id}-error`;
const control = computed(() => ({
  id,
  describedby: [props.hint ? hintId : "", props.error ? errorId : ""].filter(Boolean).join(" ") || undefined,
  invalid: props.error ? true : undefined,
}));
</script>

<template>
  <div
    class="form-field"
    :class="width ? `field-w-${width}` : undefined"
  >
    <label
      class="form-field-label"
      :for="id"
    >{{ label }}<span
      v-if="optional"
      class="form-field-optional"
    > (facultatif)</span></label>
    <p
      v-if="hint"
      :id="hintId"
      class="form-field-hint"
    >
      {{ hint }}
    </p>
    <slot v-bind="control" />
    <p
      v-if="error"
      :id="errorId"
      class="field-error"
      data-test="field-error"
    >
      {{ error }}
    </p>
  </div>
</template>
