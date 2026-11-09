<script setup lang="ts">
import { DOC_TEMPLATES, useDocTemplate } from "../composables/useDocTemplate";

// « Mise en page » de Préparer sur ordinateur (MODIFICATIONS du 9 novembre, §2.2 ; maquette PreparerOrdinateur) : les
// quatre modèles en vignettes de 48 × 64 sur une ligne (aria-pressed), puis, après un trait, la ligne de la page
// (« Tient sur une page A4 · 248 mots »). Visible aux étapes Lettre et CV.
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
      class="layout-card-thumbs"
      role="group"
      aria-label="Modèle"
    >
      <button
        v-for="item in DOC_TEMPLATES"
        :key="item.value"
        type="button"
        :aria-pressed="template === item.value"
        :data-test="`layout-${item.value}`"
        @click="template = item.value"
      >
        <svg
          width="48"
          height="64"
          viewBox="0 0 48 64"
          aria-hidden="true"
        >
          <rect
            class="thumb-paper"
            x="0.75"
            y="0.75"
            width="46.5"
            height="62.5"
            rx="3"
            stroke-width="1.5"
          />
          <template v-if="item.value === 'moderne'">
            <rect
              class="thumb-accent"
              x="0.75"
              y="0.75"
              width="6"
              height="62.5"
            />
            <rect
              class="thumb-accent"
              x="11"
              y="9"
              width="18"
              height="3.5"
              rx="1.5"
            />
          </template>
          <template v-else-if="item.value === 'bandeau'">
            <rect
              class="thumb-ink"
              x="0.75"
              y="0.75"
              width="46.5"
              height="17"
              rx="3"
            />
            <rect
              class="thumb-on-ink"
              x="8"
              y="7"
              width="18"
              height="3.5"
              rx="1.5"
            />
          </template>
          <template v-else-if="item.value === 'classique'">
            <rect
              class="thumb-ink"
              x="15"
              y="9"
              width="18"
              height="3.5"
              rx="1.5"
            />
            <rect
              class="thumb-line"
              x="18"
              y="15"
              width="12"
              height="2.5"
              rx="1.25"
            />
            <rect
              class="thumb-line"
              x="8"
              y="22"
              width="32"
              height="1"
            />
          </template>
          <template v-else>
            <rect
              class="thumb-ink"
              x="8"
              y="9"
              width="16"
              height="3.5"
              rx="1.5"
            />
            <rect
              class="thumb-line"
              x="8"
              y="15"
              width="12"
              height="2.5"
              rx="1.25"
            />
            <rect
              class="thumb-line"
              x="28"
              y="9"
              width="12"
              height="2.5"
              rx="1.25"
            />
          </template>
          <rect
            v-for="(w, i) in item.value === 'moderne' ? [29, 27, 29, 23, 27] : [32, 30, 32, 26, 30]"
            :key="i"
            class="thumb-line"
            :x="item.value === 'moderne' ? 11 : 8"
            :y="30 + i * 5"
            :width="w"
            height="2.5"
            rx="1.25"
          />
        </svg>
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
/* Valeurs de PreparerOrdinateur : titre 18/24 700, aide 14/20 grise 4 px dessous ; vignettes à 16 px, une ligne de quatre,
   8 px d'écart, chacune 8 6 de marge et 6 px avant le nom (ici 8 8 et 4, même hauteur, grille de 4) en 13/600, contour 1,5 px transparent rayon 12 ; choisie :
   contour --primary-graphic, fond --selected-bg, nom en --primary-text 700. Puis le trait --line et la page à 12 px. */
.layout-card { --layout-12: 12px; --layout-13: 13px; --layout-24: 24px; }
.layout-card > h2 { margin: 0; font-size: var(--font-title); line-height: var(--layout-24); }
.layout-card-help { margin: var(--space-1) 0 0; font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.layout-card-thumbs { display: flex; gap: var(--space-2); margin-top: var(--space-4); }
.layout-card-thumbs button {
  flex: 1; display: flex; flex-direction: column; align-items: center; gap: var(--space-1); min-width: 0; padding: var(--space-2) 0;
  border: 1.5px solid transparent; border-radius: var(--layout-12); background: transparent; color: var(--text);
  font: inherit; font-size: var(--layout-13); font-weight: var(--weight-semibold); cursor: pointer;
}
.layout-card-thumbs button[aria-pressed="true"] { border-color: var(--primary-graphic); background: var(--selected-bg); color: var(--primary-text); font-weight: var(--weight-bold); }
.layout-card-thumbs .thumb-paper { fill: var(--thumb-paper); stroke: var(--card-line); }
.layout-card-thumbs .thumb-ink { fill: var(--text); }
.layout-card-thumbs .thumb-on-ink { fill: var(--thumb-paper); }
.layout-card-thumbs .thumb-accent { fill: var(--primary-graphic); }
.layout-card-thumbs .thumb-line { fill: var(--thumb-line); }
.layout-card-note { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-2); margin: var(--space-3) 0 0; padding-top: var(--space-3); border-top: 1px solid var(--line); font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
</style>
