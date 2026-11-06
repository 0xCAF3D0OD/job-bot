<script setup lang="ts">
import type { DocTemplate } from "../composables/useDocTemplate";

// L'aperçu d'une lettre ou d'un CV dans le modèle choisi (maquette Preparer) : la page, son en-tête (le nom,
// une ligne dessous) et le début du texte. Vide (pas encore rédigé) : des lignes grises à la place du texte.
defineProps<{ template: DocTemplate; name: string; sub?: string | null; paragraphs: string[]; label: string }>();
defineEmits<{ open: [] }>();
</script>

<template>
  <button
    type="button"
    class="doc-preview"
    :aria-label="label"
    :data-template="template"
    data-test="doc-preview"
    @click="$emit('open')"
  >
    <span :class="['doc-preview-page', `tpl-${template}`]">
      <span class="doc-preview-head">
        <strong>{{ name }}</strong>
        <span v-if="sub">{{ sub }}</span>
      </span>
      <span
        v-if="paragraphs.length"
        class="doc-preview-body"
      >
        <span
          v-for="(text, index) in paragraphs"
          :key="index"
        >{{ text }}</span>
      </span>
      <span
        v-else
        class="doc-preview-empty"
        data-test="doc-preview-empty"
      ><i /><i /><i /><i /></span>
    </span>
  </button>
</template>

<style scoped>
/* L'aperçu (maquette Preparer) : une page réduite de 168 px, le texte replié à la largeur de la page. Le bouton
   ne garde pas le « nowrap » des boutons : sans ça, chaque paragraphe tenait sur une ligne coupée à droite. */
.doc-preview { display: block; width: 100%; height: 10.5rem; padding: var(--space-3) var(--space-5) 0; border: 0; border-radius: var(--radius-card); background: var(--surface-muted); text-align: left; white-space: normal; font: inherit; overflow: hidden; cursor: pointer; }
/* Le papier en clair, puis en sombre (PreparerSombre : la page brune, le bleu éclairci du Moderne). */
.doc-preview-page { --paper: #fff; --ink: #1B1F2A; --ink-body: #3D4250; --ink-sub: #596070; --blue: #2445C2; --serif-paper: #FFFDF8; }
:root[data-theme="dark"] .doc-preview-page { --paper: var(--surface); --ink: var(--text); --ink-body: #D6CFC4; --ink-sub: var(--text-secondary); --blue: var(--primary-graphic); --serif-paper: #26211C; }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) .doc-preview-page { --paper: var(--surface); --ink: var(--text); --ink-body: #D6CFC4; --ink-sub: var(--text-secondary); --blue: var(--primary-graphic); --serif-paper: #26211C; }
}
.doc-preview-page { display: grid; align-content: start; height: 100%; border-radius: var(--radius-sm) var(--radius-sm) 0 0; background: var(--paper); color: var(--ink); box-shadow: 0 2px 8px rgb(27 31 42 / 12%); overflow: hidden; transition: background-color var(--t-state); }
.doc-preview-head { display: grid; gap: var(--space-1); padding: var(--space-3) var(--space-4) var(--space-2); }
.doc-preview-head strong { font-size: var(--font-body); font-weight: var(--weight-bold); }
.doc-preview-head span { font-size: var(--font-caption); }
.doc-preview-body { display: grid; gap: var(--space-2); padding: var(--space-2) var(--space-4) var(--space-4); overflow-wrap: anywhere; font-size: var(--font-caption); line-height: var(--leading-normal); color: var(--ink-body); }
.doc-preview-empty { display: grid; gap: var(--space-2); padding: var(--space-3) var(--space-4); }
.doc-preview-empty i { display: block; height: 6px; border-radius: var(--radius-pill); background: #E4E6EC; }
.doc-preview-empty i:nth-child(2) { width: 90%; }
.doc-preview-empty i:nth-child(3) { width: 75%; }
.doc-preview-empty i:nth-child(4) { width: 55%; }
.tpl-moderne { border-left: 14px solid var(--blue); }
.tpl-moderne .doc-preview-head { color: var(--blue); }
.tpl-bandeau .doc-preview-head { background: #F3B08A; color: #1B1F2A; }
.tpl-classique { background: var(--serif-paper); font-family: Georgia, "Times New Roman", serif; }
.tpl-classique .doc-preview-head { justify-items: center; margin: 0 var(--space-4); padding-inline: 0; border-bottom: 1px solid var(--ink); }
.tpl-classique .doc-preview-head strong { font-weight: var(--weight-semibold); }
.tpl-sobre .doc-preview-head span { color: var(--ink-sub); }
</style>
