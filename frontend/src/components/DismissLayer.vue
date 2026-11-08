<script setup lang="ts">
// La couche transparente sous le panneau ou le menu ouvert (docs/143, D24) : un clic à l'extérieur ferme tout.
// Elle est sous l'en-tête (z-index 35 contre 38) : la cloche et le compte basculent directement.
import { anyLayerOpen, closeAllLayers } from "../composables/useDismissLayer";
</script>

<template>
  <div
    v-if="anyLayerOpen"
    class="dismiss-layer"
    aria-hidden="true"
    data-test="dismiss-layer"
    @click="closeAllLayers()"
  />
</template>
