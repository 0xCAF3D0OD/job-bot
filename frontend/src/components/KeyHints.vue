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
