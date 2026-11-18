<script setup lang="ts">
import type { SaveState } from "../sheetIdentity";
import AppIcon from "./AppIcon.vue";

// Sous un champ qui s'enregistre quand on le quitte (planche FeuilleNom, §70 ; K31 de l'audit) : roue et
// « Enregistrement… », puis coche verte et « Enregistré » ; en cas d'échec, « Pas enregistré · Réessayer ». La zone
// role="status" est toujours là, pour que chaque changement soit annoncé (WCAG 4.1.3) ; vide, elle ne prend pas de place.
// `reserve` : la ligne garde sa place même vide : rien ne bouge quand elle parle (fluidité, Kevin 18.11).
defineProps<{ state: SaveState; reserve?: boolean }>();
const emit = defineEmits<{ retry: [] }>();
</script>

<template>
  <div
    :class="['field-save', `field-save-${state}`, { 'field-save-reserve': reserve }]"
    role="status"
    data-test="field-save"
  >
    <template v-if="state === 'saving'">
      <svg
        class="field-save-spin"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle
          cx="12"
          cy="12"
          r="9"
        />
        <path d="M12 3a9 9 0 0 1 9 9" />
      </svg>Enregistrement…
    </template>
    <template v-else-if="state === 'saved'">
      <AppIcon name="done" />Enregistré
    </template>
    <template v-else-if="state === 'failed'">
      Pas enregistré ·
      <button
        type="button"
        class="field-save-retry"
        data-test="field-save-retry"
        @click="emit('retry')"
      >
        Réessayer
      </button>
    </template>
  </div>
</template>

<style scoped>
/* Planche FeuilleNom : 14 px, 10 px sous le champ ; gris pendant l'enregistrement, vert gras une fois enregistré. */
.field-save { --fs-top: 10px; --fs-check-gap: 6px; display: flex; align-items: center; gap: var(--space-2); height: var(--space-5); line-height: var(--space-5); white-space: nowrap; margin-top: var(--fs-top); font-size: var(--font-small); color: var(--text-secondary); }
.field-save-idle:not(.field-save-reserve) { display: none; }
.field-save-saved { gap: var(--fs-check-gap); color: var(--success); font-weight: var(--weight-bold); }
.field-save-saved :deep(.icon) { width: 16px; height: 16px; }
.field-save-failed { color: var(--danger); font-weight: var(--weight-bold); }
.field-save-spin { flex: none; width: 18px; height: 18px; fill: none; stroke-width: 3; stroke-linecap: round; animation: field-save-turn 900ms linear infinite; }
.field-save-spin circle { stroke: var(--line); }
.field-save-spin path { stroke: var(--primary-graphic); }
@keyframes field-save-turn { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .field-save-spin { animation: none; } }
/* « Réessayer » : un lien d'action, cible de 44 px de haut sans décaler la ligne. */
.field-save-retry { position: relative; padding: 0; border: 0; background: none; color: var(--primary-text); font: inherit; font-weight: var(--weight-bold); cursor: pointer; }
.field-save-retry::before { content: ""; position: absolute; inset: 50% -8px auto; height: var(--target-min); transform: translateY(-50%); }
</style>
