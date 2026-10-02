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
    <p class="notice">
      Arrive avec la version {{ entry.since }}.
    </p>
  </section>
</template>
