<script setup lang="ts">
// En-tête commun à toutes les pages (docs/43 n° 1) : étiquette, titre à gauche, sous-titre,
// puis les onglets de la page (slot), comme Candidatures. `short` : le titre sur téléphone.
defineProps<{ eyebrow: string; title: string; subtitle?: string; short?: string }>();
</script>

<template>
  <header class="jobs-head page-head">
    <span class="eyebrow">{{ eyebrow }}</span>
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
