<script setup lang="ts">
import AppIcon from "./AppIcon.vue";

// Les raccourcis sous deux actions de même largeur (règles §4) : « ← Écarter » à gauche, « → Garder »
// à droite, en gris. Seulement avec un clavier et une souris (pointeur fin) ; les lecteurs d'écran ont
// aria-keyshortcuts sur les boutons, d'où aria-hidden ici.
defineProps<{ left: string; right: string }>();
</script>

<template>
  <p
    class="key-hints"
    aria-hidden="true"
    data-test="key-hints"
  >
    <span><kbd><AppIcon name="arrow-left" /></kbd> {{ left }}</span>
    <span><kbd><AppIcon name="arrow-right" /></kbd> {{ right }}</span>
  </p>
</template>

<!-- Styles gardés ici : le composant n’est monté nulle part dans l’application (allègement du CSS commun, 14.11). -->
<style>
/* Raccourcis ← → sous deux actions : avec clavier et souris seulement. */
.key-hints { display: flex; justify-content: space-between; margin: 0; color: var(--muted); font-size: var(--font-small); }
.key-hints > span { display: inline-flex; align-items: center; gap: var(--space-1); }
.key-hints kbd { display: inline-flex; font: inherit; }
@media not ((hover: hover) and (pointer: fine)) { .key-hints { display: none; } }
</style>
