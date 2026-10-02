<script setup lang="ts">
defineProps<{ eyebrow: string; title: string; subtitle?: string }>();
</script>

<template>
  <header class="hero">
    <span class="eyebrow">{{ eyebrow }}</span>
    <h1>{{ title }}</h1>
    <p
      v-if="subtitle"
      class="hero-subtitle"
    >
      {{ subtitle }}
    </p>
    <slot />
  </header>
</template>
