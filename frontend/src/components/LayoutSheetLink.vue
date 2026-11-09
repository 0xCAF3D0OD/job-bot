<script setup lang="ts">
import { computed, ref } from "vue";

import { DOC_TEMPLATES, useDocTemplate } from "../composables/useDocTemplate";
import BottomSheet from "./BottomSheet.vue";
import SegmentedControl, { type SegmentOption } from "./SegmentedControl.vue";
import TemplatePicker from "./TemplatePicker.vue";

// « Mise en page et langue » sur téléphone (MODIFICATIONS du 9 novembre, §9 ; maquettes Preparer et
// PreparerMiseEnPage) : sous le titre du document, « Moderne · Français » en gris et, à droite, le lien « Changer »
// de 44 px. Il ouvre la feuille : la phrase, les quatre modèles en grille de deux colonnes (appliqués tout de suite),
// « Tient sur une page A4. », puis la langue en trois boutons. Choisir une langue ne rédige rien (C3) : le bouton du
// bas propose « Rédiger à nouveau en … ». La ligne « Retoucher dans Canva » attend la connexion Canva.
const props = defineProps<{ title: string; titleId: string; name?: string | null; options: SegmentOption[]; languageLabel: string }>();
const language = defineModel<string>({ required: true });
const { template } = useDocTemplate();
const open = ref(false);
const summary = computed(() => {
  const tpl = DOC_TEMPLATES.find((t) => t.value === template.value)?.label ?? "";
  const lang = props.options.find((o) => o.value === language.value)?.name ?? "";
  return [tpl, lang].filter(Boolean).join(" · ");
});
</script>

<template>
  <div class="doc-layout-head">
    <span class="doc-layout-titles">
      <h2 :id="titleId">{{ title }}</h2>
      <span
        class="doc-layout-summary"
        data-test="layout-summary"
      >{{ summary }}</span>
    </span>
    <button
      type="button"
      class="doc-layout-change"
      aria-haspopup="dialog"
      :aria-label="`Changer la mise en page et la langue, ${summary}`"
      data-test="layout-change"
      @click="open = true"
    >
      Changer
    </button>
  </div>
  <BottomSheet
    :open="open"
    title="Mise en page et langue"
    data-test="layout-sheet"
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
    <p class="layout-sheet-key">
      {{ languageLabel }}
    </p>
    <SegmentedControl
      v-model="language"
      :options="options"
      :label="languageLabel"
      full
      class="layout-sheet-language"
    />
  </BottomSheet>
</template>

<style>
/* Valeurs du HTML de Preparer : titre 16/22 700 et, 2 px dessous, le modèle et la langue en 14/20 gris (ici 14/22 sans écart, même hauteur, grille de 4) ; « Changer »
   en 15/700 bleu, 44 px de haut, 4 px de marge. Feuille (PreparerMiseEnPage) : phrase 14/20, 12 px dessous ;
   « Tient sur une page A4. » 8 px au-dessus ; « Langue de … » en 16/22 700, 20 px au-dessus et 8 px avant les boutons. */
.doc-layout-head { --layout-22: 22px; --layout-15: 15px; display: flex; align-items: center; justify-content: space-between; gap: var(--space-2); }
.doc-layout-titles { display: flex; flex-direction: column; min-width: 0; }
.doc-layout-titles h2 { margin: 0; font-size: var(--font-body); line-height: var(--layout-22); font-weight: var(--weight-bold); }
.doc-layout-summary { font-size: var(--font-small); line-height: var(--layout-22); color: var(--text-secondary); }
.doc-layout-change {
  flex: none; display: flex; align-items: center; min-height: var(--target-min); padding: 0 var(--space-1); border: 0; background: transparent;
  font: inherit; font-size: var(--layout-15); font-weight: var(--weight-bold); color: var(--primary-text); cursor: pointer;
}
.tpl-sheet-note { margin: 0 0 var(--space-3); font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.tpl-sheet-a4 { margin: var(--space-2) 0 0; }
.layout-sheet-key { --layout-22: 22px; margin: var(--space-5) 0 var(--space-2); font-size: var(--font-body); line-height: var(--layout-22); font-weight: var(--weight-bold); }
</style>
