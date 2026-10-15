<script setup lang="ts">
// En-tête commun à toutes les pages (docs/43 n° 1) : titre à gauche, sous-titre, puis les
// onglets de la page (slot), comme Candidatures. `short` : le titre sur téléphone. Sans
// pastille au-dessus du titre (retour du 2026-10-15) : le menu dit déjà où l'on est.
defineProps<{ title: string; subtitle?: string; short?: string }>();
</script>

<template>
  <header class="jobs-head page-head">
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
