<script setup lang="ts">
import { computed, useId } from "vue";

import AppIcon from "./AppIcon.vue";

// Une ligne de réglage (1.6.65, planche « 5. Réglages ») : le titre en gras, une phrase dessous,
// le contrôle à droite sur la même ligne (loi de proximité). `stack` : sur téléphone, le contrôle
// passe sous le texte (un champ et son texte ne tiennent pas à côté du titre en 390 px). `wide`
// (1.6.68) : un contrôle large (jeton, adresse, zone de texte) passe sous le texte à toutes les tailles.
// `inline` (1.6.71) : un état court reste à droite même sur téléphone ; s'il est trop long, il passe dessous.
// L'enregistrement est immédiat : la page passe `saved` quand la valeur est enregistrée et `error`
// quand elle est refusée. « Enregistré » est dit aux lecteurs d'écran (message d'état, WCAG
// 4.1.3) ; l'erreur s'affiche sous le champ et lui est reliée (WCAG 3.3.1).
const props = withDefaults(
  defineProps<{ title: string; description?: string; saved?: boolean; error?: string; stack?: boolean; wide?: boolean; inline?: boolean }>(),
  { description: "", saved: false, error: "", stack: false, wide: false, inline: false },
);

const id = useId();
const titleId = `${id}-title`;
const descriptionId = `${id}-description`;
const errorId = `${id}-error`;
// Ce que le contrôle reçoit : son nom (le titre), sa description et son erreur.
const control = computed(() => ({
  labelledby: titleId,
  describedby: [props.description ? descriptionId : "", props.error ? errorId : ""].filter(Boolean).join(" ") || undefined,
  invalid: props.error ? true : undefined,
}));
</script>

<template>
  <div
    :class="['setting-row', { stack, wide, inline, invalid: !!error }]"
    data-test="setting-row"
  >
    <div class="setting-row-text">
      <span
        :id="titleId"
        class="setting-row-title"
      >{{ title }}</span>
      <span
        v-if="description"
        :id="descriptionId"
        class="setting-row-description"
      >{{ description }}</span>
    </div>
    <div class="setting-row-control">
      <span
        role="status"
        class="setting-row-status"
        data-test="setting-saved"
      ><template v-if="saved && !error"><AppIcon name="done" />Enregistré</template></span>
      <slot v-bind="control" />
    </div>
    <p
      v-if="error"
      :id="errorId"
      class="field-error setting-row-error"
      data-test="setting-error"
    >
      {{ error }}
    </p>
  </div>
</template>
