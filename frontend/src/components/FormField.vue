<script setup lang="ts">
import { computed, onMounted, onUpdated, ref, useId } from "vue";

// Un champ de formulaire commun, à libellé flottant (maquettes du 10 novembre, PR 27 ; Material 3,
// champ « outlined ») : vide, le libellé est dans le champ ; au focus ou rempli, il remonte dans la
// bordure. Une zone de texte (textarea) le garde toujours dans la bordure (planches du 13.11, accord de Kevin du 14.11). C'est un vrai <label for> et il ne disparaît jamais (WCAG 3.3.2). Pas d'exemple en gris dans
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
// Un champ étroit (5 ou 10 caractères) s'élargit jusqu'à la longueur de son libellé : le libellé au repos n'est
// jamais coupé (audit du 17.11, N30 : « Nombre de personnes » devenait « Nomb… »).
const labelChars = computed(() => props.label.length + (props.optional ? " (facultatif)".length : 0) + (props.badge ? props.badge.length + 2 : 0));
</script>

<template>
  <div
    class="form-field"
    :class="width ? `field-w-${width}` : undefined"
    :style="width === 5 || width === 10 ? { '--label-ch': labelChars } : undefined"
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

<style>
/* Sorti de style.css (allègement du 16.11, issue #797) : ces règles ne servent qu'ici, chargées avec ce composant. */
.form-field-box:has(:is(input, select, textarea):disabled) { --ff-bg: var(--field-disabled-bg); }
.form-field-hint { margin: 0; padding-inline: var(--space-4); font-size: var(--font-small); color: var(--text-secondary); line-height: var(--leading-normal); }
.form-field:is(.field-w-5, .field-w-10) > .form-field-box { width: min(100%, max(var(--field-w), calc(var(--label-ch, 0) * 1ch + 2 * var(--ff-label-x) + 2 * var(--space-1)))); }
@media (prefers-reduced-motion: reduce) {
.form-field-label { transition: none; }
}
.field-w-5 { --field-w: var(--field-5); }
.field-w-10 { --field-w: var(--field-10); }
/* Une date native garde son icône de calendrier à droite : 10 caractères plus l'icône, pour que l'année
   ne soit jamais coupée (« 28.10.2026 »). */
.field-w-10:has(input[type="date"]) { --field-w: calc(var(--field-10) + var(--control-h)); }
.field-w-20 { --field-w: var(--field-20); }
.field-w-30 { --field-w: var(--field-30); }
</style>
