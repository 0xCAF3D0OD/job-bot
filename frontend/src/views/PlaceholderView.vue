<script setup lang="ts">
import PageHero from "../components/PageHero.vue";
import type { NavEntry } from "../router";

defineProps<{ entry: NavEntry }>();
</script>

<template>
  <PageHero
    :eyebrow="entry.label"
    :title="entry.label"
    :subtitle="entry.description"
  />
  <section class="band">
    <div class="container">
      <div class="placeholder-card">
        <span class="eyebrow">Version {{ entry.since }}</span>
        <span class="muted">Cette page arrive avec la version {{ entry.since }}.</span>
      </div>
    </div>
  </section>
</template>
