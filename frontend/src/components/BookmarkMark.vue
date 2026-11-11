<script setup lang="ts">
// Le marque-page (lot du 11 novembre au soir, §1) : un seul dessin, réutilisé partout. Corps orange, repli plus
// sombre en haut à gauche, étoile blanche, bas en V ; largeur 1, hauteur 1,82. Décoratif : les couleurs sont
// celles du dessin, les mêmes en clair et en sombre.
withDefaults(defineProps<{ width?: number }>(), { width: 38 });
</script>

<template>
  <svg
    class="bookmark-mark"
    :width="width"
    :height="Math.round(width * 1.82)"
    viewBox="0 0 56 102"
    aria-hidden="true"
    focusable="false"
  >
    <path
      d="M12 3Q3 3 1 12l8 20h4V3z"
      fill="#C4582A"
    />
    <path
      d="M10 10a9 9 0 0 1 9-9h28a9 9 0 0 1 9 9v90L33 84 10 100z"
      fill="#F2853A"
    />
    <path
      d="m33 17 4.3 8.8 9.7 1.3-7.100 6.700 1.800 9.600L33 38.800l-8.700 4.600 1.800-9.600-7.100-6.700 9.700-1.300z"
      fill="#fff"
      stroke="#fff"
      stroke-width="2.5"
      stroke-linejoin="round"
    />
  </svg>
</template>

<style scoped>
.bookmark-mark { display: block; filter: drop-shadow(0 4px 5px rgba(27, 31, 42, 0.22)); }
</style>
