<script setup lang="ts">
import { computed, onMounted, onUpdated, ref, useId } from "vue";

// Un champ de formulaire commun, à libellé flottant (maquettes du 10 novembre, PR 27 ; Material 3,
// champ « outlined ») : vide, le libellé est dans le champ ; au focus ou rempli, il remonte dans la
// bordure. C'est un vrai <label for> et il ne disparaît jamais (WCAG 3.3.2). Pas d'exemple en gris dans
// le champ : l'exemple va dessous, dans `hint` (« Ex. : … »). « (facultatif) » sur un champ facultatif
// (pas d'astérisque), puis l'erreur sous le champ, avec une icône (WCAG 1.4.1, 3.3.1). `width` : la largeur dit la réponse attendue, en caractères
// (Baymard Institute, Form Field Width). Le slot reçoit l'id, la description et l'état invalide. `badge` : une marque
// à côté du libellé, comme « Du CV » (maquette CoordonneesOrdinateur du 10 novembre au soir).
const props = withDefaults(
  defineProps<{ label: string; optional?: boolean; hint?: string; error?: string; width?: 5 | 10 | 20 | 30; badge?: string; fieldId?: string }>(),
  { optional: false, hint: "", error: "", width: undefined, badge: "", fieldId: "" },
);

// `fieldId` : garder l'id d'un champ qui en avait déjà un (ancres, tests).
const generated = useId();
const id = props.fieldId || generated;
const hintId = `${id}-hint`;
const errorId = `${id}-error`;
// Le libellé redescend dans un champ vide grâce à :placeholder-shown, qui demande un placeholder : une
// espace, jamais un exemple (il passerait sous le libellé).
const box = ref<HTMLElement | null>(null);
function blankPlaceholders() {
  for (const el of box.value?.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>("input, textarea") ?? []) {
    if (el.placeholder !== " ") el.placeholder = " ";
  }
}
onMounted(blankPlaceholders);
onUpdated(blankPlaceholders);

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
    <div
      ref="box"
      class="form-field-box"
    >
      <slot v-bind="control" />
      <label
        class="form-field-label"
        :for="id"
      ><span class="form-field-text">{{ label }}<span
        v-if="optional"
        class="form-field-optional"
      > (facultatif)</span></span><span
        v-if="badge"
        class="form-field-badge"
      >{{ badge }}</span></label>
    </div>
    <p
      v-if="hint"
      :id="hintId"
      class="form-field-hint"
    >
      {{ hint }}
    </p>
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
