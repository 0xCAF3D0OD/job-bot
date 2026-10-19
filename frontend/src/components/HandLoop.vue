<script setup lang="ts">
// La boucle à main levée (docs/96) : entoure la page en cours dans le menu et l'icône de
// l'onglet choisi sur téléphone. Une ellipse un peu irrégulière qui ne se referme pas tout à
// fait et dépasse son départ, comme un trait de stylo ; elle se dessine à son arrivée (0,6 s),
// d'emblée si « réduire les animations ». Décorative : la page en cours est dite par
// aria-current.
const LOOP =
  "M 12 22 C 10 9, 40 3, 62 4 C 84 5, 98 12, 97 24 C 96 37, 70 43, 46 42 C 22 41, 3 35, 4 23 C 5 12, 22 6, 40 6";
</script>

<template>
  <svg
    class="hand-loop"
    viewBox="0 0 100 46"
    preserveAspectRatio="none"
    aria-hidden="true"
    data-test="hand-loop"
  >
    <path
      :d="LOOP"
      pathLength="1"
      vector-effect="non-scaling-stroke"
    />
  </svg>
</template>
