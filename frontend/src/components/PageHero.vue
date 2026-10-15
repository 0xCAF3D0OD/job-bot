<script setup lang="ts">
// `short` : le titre sur téléphone, sur une ligne (docs/43 n° 18).
defineProps<{ eyebrow: string; title: string; subtitle?: string; short?: string }>();
</script>

<template>
  <header class="hero">
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
      class="hero-subtitle"
    >
      {{ subtitle }}
    </p>
    <slot />
  </header>
</template>
