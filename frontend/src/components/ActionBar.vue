<script setup lang="ts">
// L'action principale fixée en bas (règles §4) : sur la fiche d'une offre et le tri, au-dessus de la
// barre d'onglets, pleine largeur sur téléphone seulement (sous 600 px), zone de sécurité respectée.
// Sur un écran plus large, les boutons restent à leur place dans la page.
</script>

<template>
  <div
    class="action-bar"
    data-test="action-bar"
  >
    <slot />
  </div>
</template>
