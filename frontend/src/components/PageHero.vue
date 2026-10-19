<script setup lang="ts">
// En-tête commun à toutes les pages (docs/43 n° 1) : titre à gauche, puis les onglets de la
// page (slot), comme Candidatures. `short` : le titre sur téléphone. Le titre reprend l'entrée
// du menu (docs/88) ; `eyebrow` : une petite précision au-dessus, la date d'Aujourd'hui.
// `subtitle` : seulement pour une page de présentation, comme la connexion.
defineProps<{ title: string; subtitle?: string; short?: string; eyebrow?: string }>();
</script>

<template>
  <header class="jobs-head page-head">
    <p
      v-if="eyebrow"
      class="page-head-eyebrow"
      data-test="page-eyebrow"
    >
      {{ eyebrow }}
    </p>
    <h1 v-if="short">
      <span class="label-long">{{ title }}</span>
      <span class="label-short">{{ short }}</span>
    </h1>
    <h1 v-else>
      {{ title }}
    </h1>
    <p
      v-if="subtitle"
      class="page-head-sub"
    >
      {{ subtitle }}
    </p>
    <slot />
  </header>
</template>
