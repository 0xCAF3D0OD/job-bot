<script setup lang="ts">
import type { NavEntry } from "../router";

defineProps<{ entry: NavEntry }>();
</script>

<template>
  <section>
    <h1>{{ entry.label }}</h1>
    <p class="muted">
      {{ entry.description }}
    </p>
    <div class="card placeholder-card">
      <span class="badge">Version {{ entry.since }}</span>
      <span class="detail">Cette page arrive avec la version {{ entry.since }}.</span>
    </div>
  </section>
</template>
