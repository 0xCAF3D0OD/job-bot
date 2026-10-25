<script setup lang="ts">
import AppIcon from "../components/AppIcon.vue";
import PageHero from "../components/PageHero.vue";
import StatusPanel from "../components/StatusPanel.vue";

// Diagnostic technique (docs/21 §6) : sorti des Réglages, pour ne pas les charger.
</script>

<template>
  <PageHero
    title="État du service"
  />
  <section class="band">
    <div class="container">
      <RouterLink
        to="/reglages"
        class="back-link"
      >
        <span class="with-icon"><AppIcon name="arrow-left" />Retour aux réglages</span>
      </RouterLink>
      <StatusPanel />
    </div>
  </section>
</template>
