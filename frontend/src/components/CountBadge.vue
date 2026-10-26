<script setup lang="ts">
// La pastille de nombre, une seule partout (1.6.33, NN/g heuristique 4 « Cohérence et standards ») :
// pleine, bordée de la couleur du fond pour se détacher de l'icône qu'elle chevauche. Orange pour la
// cloche, accent ailleurs. La place (sur l'icône ou après le nom) vient de la classe ajoutée par le parent.
withDefaults(defineProps<{ count: number | string; tone?: "accent" | "orange" }>(), { tone: "accent" });
</script>

<template>
  <span :class="['count-badge', tone]">{{ count }}</span>
</template>
