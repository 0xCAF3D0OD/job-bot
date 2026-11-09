<script setup lang="ts">
import { computed } from "vue";

import { DOC_TEMPLATES, useDocTemplate } from "../composables/useDocTemplate";

// Le choix du modèle (maquette Preparer, Kevin 2026-11-05) : quatre vignettes qui défilent, « Le même pour CV
// et lettre ». Un groupe de boutons radio ; les flèches passent d'un modèle à l'autre.
// La vignette Classique porte les initiales du nom, comme la maquette (« K D »).
// `grid` (feuille « Mise en page », §10.7) : les quatre modèles en deux colonnes, sans le titre.
const props = defineProps<{ name?: string | null; grid?: boolean }>();
const { template } = useDocTemplate();
const initials = computed(() => {
  const words = (props.name || "").split(/\s+/).filter((word) => /^\p{L}/u.test(word));
  return words.length ? [words[0], words[words.length - 1]].map((word) => word!.charAt(0).toUpperCase()).join(" ") : "A Z";
});

function onKey(event: KeyboardEvent, index: number): void {
  const step = event.key === "ArrowRight" || event.key === "ArrowDown" ? 1 : event.key === "ArrowLeft" || event.key === "ArrowUp" ? -1 : 0;
  if (!step) return;
  event.preventDefault();
  const next = DOC_TEMPLATES[(index + step + DOC_TEMPLATES.length) % DOC_TEMPLATES.length]!;
  template.value = next.value;
  ((event.currentTarget as HTMLElement).parentElement?.querySelector(`[data-template="${next.value}"]`) as HTMLElement | null)?.focus();
}
</script>

<template>
  <section
    :class="['tpl-picker', { 'tpl-picker-grid': grid }]"
    :aria-labelledby="grid ? undefined : 'tpl-picker-title'"
    data-test="template-picker"
  >
    <div
      v-if="!grid"
      class="tpl-picker-head"
    >
      <h2 id="tpl-picker-title">
        Modèle
      </h2>
      <span>Le même pour CV et lettre</span>
    </div>
    <div
      class="tpl-picker-row"
      role="radiogroup"
      :aria-labelledby="grid ? undefined : 'tpl-picker-title'"
      :aria-label="grid ? 'Modèle du document' : undefined"
    >
      <button
        v-for="(item, index) in DOC_TEMPLATES"
        :key="item.value"
        type="button"
        role="radio"
        :aria-checked="template === item.value"
        :tabindex="template === item.value ? 0 : -1"
        :class="['tpl-card', { selected: template === item.value }]"
        :data-template="item.value"
        :data-test="`template-${item.value}`"
        @click="template = item.value"
        @keydown="onKey($event, index)"
      >
        <span
          :class="['tpl-thumb', `tpl-${item.value}`]"
          aria-hidden="true"
        >
          <span
            v-if="item.value === 'moderne'"
            class="tpl-thumb-side"
          ><b /><i /><i /></span>
          <span
            v-if="item.value === 'bandeau'"
            class="tpl-thumb-band"
          ><i /></span>
          <span class="tpl-thumb-main">
            <strong
              v-if="item.value === 'classique'"
              class="tpl-thumb-initials"
            >{{ initials }}</strong>
            <span
              v-else-if="item.value !== 'bandeau'"
              class="tpl-thumb-head"
            ><i /><i v-if="item.value === 'sobre'" /></span>
            <span class="tpl-thumb-lines"><i /><i /><i /><i v-if="item.value !== 'moderne'" /></span>
          </span>
        </span>
        <span class="tpl-card-label">{{ item.label }}</span>
      </button>
    </div>
  </section>
</template>

<style scoped>
/* Le modèle de la lettre et du CV (maquette Preparer, Kevin 2026-11-05) : quatre vignettes de 74 × 96. */
.tpl-picker { display: grid; gap: var(--space-2); }
.tpl-picker-head { display: flex; justify-content: space-between; align-items: baseline; gap: var(--space-3); padding: 0 var(--space-1); }
.tpl-picker-head h2 { margin: 0; font-size: var(--label-caps); font-weight: var(--weight-bold); letter-spacing: var(--letter-label); text-transform: uppercase; color: var(--text-secondary); }
.tpl-picker-head span { font-size: var(--label-caps); color: var(--text-secondary); }
.tpl-picker-row { display: flex; gap: var(--space-3); overflow-x: auto; margin: 0 calc(var(--space-4) * -1); padding: var(--space-1) var(--space-4); scrollbar-width: none; }
/* En grille (feuille « Mise en page ») : deux colonnes, 12 px entre les cartes (PreparerMiseEnPage). */
.tpl-picker-grid .tpl-picker-row { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); overflow: visible; margin: 0; padding: var(--space-1) 0 var(--space-2); }
.tpl-card { flex: none; display: grid; justify-items: center; gap: var(--space-2); min-width: 96px; padding: var(--space-2); border: 1px solid var(--line); border-radius: var(--radius-card); background: var(--surface); color: var(--text); font: inherit; font-size: var(--font-small); font-weight: var(--weight-bold); }
.tpl-card.selected { border: 2.5px solid var(--primary-graphic); background: var(--primary-soft); }
/* Les couleurs du papier, en clair puis en sombre (PreparerSombre : un papier brun, des traits estompés). */
.tpl-thumb { --paper: #fff; --ink: #1B1F2A; --ink-soft: #B9BDC8; --rule: #D9DCE6; --dot: #C9D3F6; --serif-paper: #FFFDF8; --serif-ink: #1B1F2A; --serif-rule: #1B1F2A; }
:root[data-theme="dark"] .tpl-thumb { --paper: #221E1A; --ink: #3A342D; --ink-soft: #5E584F; --rule: #36312B; --dot: #3A4A85; --serif-paper: #26211C; --serif-ink: #F3EEE6; --serif-rule: #3A342D; }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) .tpl-thumb { --paper: #221E1A; --ink: #3A342D; --ink-soft: #5E584F; --rule: #36312B; --dot: #3A4A85; --serif-paper: #26211C; --serif-ink: #F3EEE6; --serif-rule: #3A342D; }
}
.tpl-thumb { display: flex; width: 74px; height: 96px; border-radius: var(--radius-sm); background: var(--paper); box-shadow: 0 1px 3px rgb(27 31 42 / 18%); overflow: hidden; }
.tpl-thumb i, .tpl-thumb b { display: block; flex: none; height: 3px; border-radius: var(--radius-pill); background: var(--rule); }
.tpl-thumb-main { flex: 1; display: flex; flex-direction: column; gap: var(--space-1); padding: var(--space-2); }
.tpl-thumb-head, .tpl-thumb-lines { display: flex; flex-direction: column; gap: var(--space-1); }
.tpl-thumb-lines { margin-top: var(--space-1); }
.tpl-thumb-head i:first-child { width: 60%; height: 5px; background: var(--ink); }
.tpl-thumb-head i:nth-child(2) { width: 40%; background: var(--ink-soft); }
.tpl-thumb-lines i:nth-child(3) { width: 80%; }
.tpl-sobre { padding-top: var(--space-1); }
.tpl-moderne .tpl-thumb-side { flex: none; display: flex; flex-direction: column; align-items: center; gap: var(--space-1); width: 22px; padding-top: var(--space-2); background: #2445C2; }
.tpl-moderne .tpl-thumb-side b { width: 12px; height: 12px; border-radius: 50%; background: var(--dot); }
.tpl-moderne .tpl-thumb-side i { width: 12px; height: 2px; border-radius: 0; background: var(--dot); }
.tpl-moderne .tpl-thumb-head i:first-child { width: 80%; background: #2445C2; }
.tpl-moderne .tpl-thumb-lines i:nth-child(3) { width: 70%; }
.tpl-bandeau { flex-direction: column; }
.tpl-bandeau .tpl-thumb-band { flex: none; display: flex; align-items: center; height: 24px; padding: 0 var(--space-2); background: #F3B08A; }
.tpl-bandeau .tpl-thumb-band i { width: 60%; height: 5px; background: var(--ink); }
.tpl-bandeau .tpl-thumb-lines { margin-top: 0; }
.tpl-bandeau .tpl-thumb-lines i:nth-child(3) { width: 70%; }
.tpl-classique { background: var(--serif-paper); }
.tpl-classique .tpl-thumb-main { align-items: center; }
.tpl-classique .tpl-thumb-initials { padding-bottom: var(--space-1); align-self: stretch; text-align: center; border-bottom: 1px solid var(--serif-rule); font-family: Georgia, "Times New Roman", serif; font-size: var(--font-caption); font-weight: var(--weight-semibold); line-height: var(--leading-tight); color: var(--serif-ink); }
.tpl-classique .tpl-thumb-lines { align-self: stretch; }
</style>
