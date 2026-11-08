<script setup lang="ts">
import { DOC_TEMPLATES, useDocTemplate } from "../composables/useDocTemplate";

// « Mise en page » de Préparer sur ordinateur (MODIFICATIONS du 8 novembre au soir, lot 15.1 ; capture
// PreparerOrdinateur) : les quatre modèles du téléphone en pastilles de 40 px (aria-pressed), puis, après un trait,
// la ligne de la page (« Tient sur une page A4 · 248 mots »). Visible aux étapes Lettre et CV.
defineProps<{ note?: string }>();
const { template } = useDocTemplate();
</script>

<template>
  <section
    class="side-card layout-card"
    aria-labelledby="layout-card-title"
    data-test="layout-card"
  >
    <h2 id="layout-card-title">
      Mise en page
    </h2>
    <p class="layout-card-help">
      Le modèle s’applique à la lettre et au CV.
    </p>
    <div
      class="layout-card-pills"
      role="group"
      aria-labelledby="layout-card-title"
    >
      <button
        v-for="item in DOC_TEMPLATES"
        :key="item.value"
        type="button"
        :aria-pressed="template === item.value"
        :data-test="`layout-${item.value}`"
        @click="template = item.value"
      >
        {{ item.label }}
      </button>
    </div>
    <p
      v-if="note || $slots.default"
      class="layout-card-note"
      data-test="layout-note"
    >
      <span v-if="note">{{ note }}</span>
      <slot />
    </p>
  </section>
</template>

<style>
/* Valeurs du lot 15.1 : phrase d'aide 14 --text-secondary ; pastilles de 40, 8 d'écart, contour --line, sélection
   --primary-soft et contour --primary-graphic ; trait --line-soft puis la ligne de la page en 14. */
.layout-card { --layout-40: 40px; }
.layout-card-help { margin: 0; font-size: var(--font-small); color: var(--text-secondary); }
.layout-card-pills { display: flex; flex-wrap: wrap; gap: var(--space-2); margin-top: var(--space-2); }
.layout-card-pills button { min-height: var(--layout-40); padding: 0 var(--space-4); border: 1px solid var(--line); border-radius: var(--radius-pill); background: var(--surface); color: var(--text); font-size: var(--font-small); font-weight: var(--weight-semibold); }
.layout-card-pills button[aria-pressed="true"] { border-color: var(--primary-graphic); background: var(--primary-soft); color: var(--primary-text); }
.layout-card-note { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-2); margin: var(--space-2) 0 0; padding-top: var(--space-4); border-top: 1px solid var(--line-soft); font-size: var(--font-small); color: var(--text-secondary); }
</style>
