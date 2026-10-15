<script setup lang="ts">
import Illustration from "./Illustration.vue";

// Le temps du chargement (docs/43 n° 3) : des blocs gris à la forme du contenu, remplacés
// sans saut, au lieu d'une page blanche qui se remplit d'un coup. Si le chargement dure,
// une illustration animée prend leur place (docs/58 §3.2, `useLoadingGate`).
withDefaults(defineProps<{ heights?: string[]; columns?: number; illustrated?: boolean }>(), {
  heights: () => ["6rem", "6rem", "6rem"],
  columns: 1,
  illustrated: false,
});
</script>

<template>
  <div
    v-if="illustrated"
    class="loading-illu"
    role="status"
    data-test="loading"
  >
    <Illustration name="loading-ui" />
    <span class="hint">Chargement…</span>
  </div>
  <div
    v-else
    class="loading-blocks"
    :style="{ '--loading-columns': columns }"
    role="status"
    data-test="loading"
  >
    <span class="visually-hidden">Chargement…</span>
    <span
      v-for="(height, index) in heights"
      :key="index"
      class="loading-block"
      :style="{ height }"
      aria-hidden="true"
    />
  </div>
</template>
