<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";

// Le temps du chargement (docs/43 n° 3, planche « vide et chargement ») : rien avant 300 ms
// (NN/g, Response Time Limits), puis des blocs gris à la forme du contenu, remplacés sans saut.
// Une seule annonce « Chargement… » par zone (WCAG 4.1.3), une fois les blocs affichés.
withDefaults(defineProps<{ heights?: string[]; columns?: number }>(), {
  heights: () => ["6rem", "6rem", "6rem"],
  columns: 1,
});

const LOADING_DELAY_MS = 300;
const shown = ref(false);
let timer: ReturnType<typeof setTimeout> | undefined;
onMounted(() => {
  timer = setTimeout(() => (shown.value = true), LOADING_DELAY_MS);
});
onUnmounted(() => clearTimeout(timer));
</script>

<template>
  <div
    class="loading-blocks"
    :style="{ '--loading-columns': columns }"
    role="status"
    data-test="loading"
  >
    <template v-if="shown">
      <span class="visually-hidden">Chargement…</span>
      <span
        v-for="(height, index) in heights"
        :key="index"
        class="loading-block"
        :style="{ height }"
        aria-hidden="true"
      />
    </template>
  </div>
</template>

<style>
/* Sorti de style.css (allègement du 16.11, issue #797) : ces règles ne servent qu'ici, chargées avec ce composant. */
@media (prefers-reduced-motion: reduce) {
.loading-block { animation: none; }
}
</style>
