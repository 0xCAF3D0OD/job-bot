<script setup lang="ts">
import { DOC_TEMPLATES, useDocTemplate } from "../composables/useDocTemplate";

// Le choix du modèle (maquette Preparer, Kevin 2026-11-05) : quatre vignettes qui défilent, « Le même pour CV
// et lettre ». Un groupe de boutons radio ; les flèches passent d'un modèle à l'autre.
const { template } = useDocTemplate();

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
    class="tpl-picker"
    aria-labelledby="tpl-picker-title"
    data-test="template-picker"
  >
    <div class="tpl-picker-head">
      <h2 id="tpl-picker-title">
        Modèle
      </h2>
      <span>Le même pour CV et lettre</span>
    </div>
    <div
      class="tpl-picker-row"
      role="radiogroup"
      aria-labelledby="tpl-picker-title"
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
          <span class="tpl-thumb-head"><i /><i /></span>
          <span class="tpl-thumb-lines"><i /><i /><i /></span>
        </span>
        <span class="tpl-card-label">{{ item.label }}</span>
      </button>
    </div>
  </section>
</template>
