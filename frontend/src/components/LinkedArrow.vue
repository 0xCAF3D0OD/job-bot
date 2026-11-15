<script setup lang="ts">
// La flèche de la carte choisie dans une liste reliée au détail (ordinateur, §18 du 15 novembre) : tracé exact de la
// planche (data-arrow, 22 × 60) ; le contour de la carte s’incurve vers la pointe, pente à 45°, pointe arrondie, un
// seul trait de 2 px. Décorative : la sélection est dite par aria-current sur la carte.
</script>

<template>
  <svg
    data-arrow
    aria-hidden="true"
    class="list-card-arrow"
    width="22"
    height="60"
    viewBox="0 0 22 60"
  >
    <path
      class="list-card-arrow-fill"
      style="fill: var(--linked-selected-bg)"
      d="M-1 4 L1 4 L1 7 Q1 12 4.54 15.54 L16.17 27.17 Q19 30 16.17 32.83 L4.54 44.46 Q1 48 1 53 L1 56 L-1 56 Z"
    />
    <path
      class="list-card-arrow-line"
      style="stroke: var(--primary-graphic)"
      d="M1 4 L1 7 Q1 12 4.54 15.54 L16.17 27.17 Q19 30 16.17 32.83 L4.54 44.46 Q1 48 1 53 L1 56"
      fill="none"
      stroke-width="2"
      stroke-linejoin="round"
    />
  </svg>
</template>
