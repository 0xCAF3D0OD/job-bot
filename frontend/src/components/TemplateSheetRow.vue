<script setup lang="ts">
import { computed, ref } from "vue";

import { DOC_TEMPLATES, useDocTemplate } from "../composables/useDocTemplate";
import AppIcon from "./AppIcon.vue";
import BottomSheet from "./BottomSheet.vue";
import TemplatePicker from "./TemplatePicker.vue";

// « Mise en page » sur téléphone (MODIFICATIONS du 8 novembre au soir, §10.7 ; maquettes Preparer et
// PreparerMiseEnPage) : à la place des quatre vignettes en haut de l'écran, une carte cliquable (D29)
// « Mise en page · CV et lettre » et le modèle choisi ; elle ouvre la feuille « Mise en page » : la phrase, les
// quatre modèles en grille de deux colonnes (choix appliqué tout de suite), « Tient sur une page A4. ».
defineProps<{ name?: string | null }>();
const { template } = useDocTemplate();
const open = ref(false);
const label = computed(() => DOC_TEMPLATES.find((t) => t.value === template.value)?.label ?? "");
</script>

<template>
  <button
    type="button"
    class="tpl-row grille-row"
    aria-haspopup="dialog"
    data-test="template-row"
    @click="open = true"
  >
    <span class="tpl-row-text">
      <span class="tpl-row-key">Mise en page · CV et lettre</span>
      <span
        class="tpl-row-value"
        data-test="template-current"
      >{{ label }}</span>
    </span>
    <span
      class="arrow-circle"
      aria-hidden="true"
    ><AppIcon name="arrow-right" /></span>
  </button>
  <BottomSheet
    :open="open"
    title="Mise en page"
    data-test="template-sheet"
    @close="open = false"
  >
    <p class="tpl-sheet-note">
      Le même modèle s’applique à ta lettre et à ton CV.
    </p>
    <TemplatePicker
      :name="name"
      grid
    />
    <p class="tpl-sheet-note tpl-sheet-a4">
      Tient sur une page A4.
    </p>
  </BottomSheet>
</template>

<style>
/* Valeurs du HTML de Preparer : carte de 72 px, 18,5 + 1,5 de trait, 16 px avant le cercle ; libellé 13/16 au-dessus
   du modèle 16/22 700, 4 px entre eux. Feuille (PreparerMiseEnPage) : phrase 14/20, 12 px dessous ; « Tient sur une
   page A4. » 8 px au-dessus. */
.tpl-row {
  --tpl-row-72: 72px; --tpl-row-pad-y: 14.5px; --tpl-row-pad-x: 18.5px; --tpl-row-16: 16px; --tpl-row-22: 22px;
  display: flex; align-items: center; gap: var(--space-4); width: 100%; min-height: var(--tpl-row-72); box-sizing: border-box;
  padding: var(--tpl-row-pad-y) var(--tpl-row-pad-x); background: var(--surface); border: 1.5px solid var(--card-line);
  border-radius: var(--radius-sm); color: var(--text); font: inherit; text-align: left; cursor: pointer;
}
.tpl-row-text { flex: 1; min-width: 0; }
.tpl-row-key { display: block; font-size: var(--label-caps); line-height: var(--tpl-row-16); color: var(--text-secondary); }
.tpl-row-value { display: block; margin-top: var(--space-1); font-size: var(--font-body); line-height: var(--tpl-row-22); font-weight: var(--weight-bold); }
.tpl-sheet-note { margin: 0 0 var(--space-3); font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.tpl-sheet-a4 { margin: var(--space-2) 0 0; }
</style>
