<script setup lang="ts">
// Le temps du chargement (docs/43 n° 3) : des blocs gris à la forme du contenu, remplacés
// sans saut, au lieu d'une page blanche qui se remplit d'un coup.
withDefaults(defineProps<{ heights?: string[]; columns?: number }>(), {
  heights: () => ["6rem", "6rem", "6rem"],
  columns: 1,
});
</script>

<template>
  <div
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
