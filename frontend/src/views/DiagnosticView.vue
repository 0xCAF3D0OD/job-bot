<script setup lang="ts">
import PageHero from "../components/PageHero.vue";
import StatusPanel from "../components/StatusPanel.vue";

// Diagnostic technique (docs/21 §6) : sorti des Réglages, pour ne pas les charger.
</script>

<template>
  <PageHero
    eyebrow="Réglages"
    title="Diagnostic"
    subtitle="L'état de la collecte, de l'IA et des tâches automatiques."
  />
  <section class="band">
    <div class="container">
      <RouterLink
        to="/reglages"
        class="back-link"
      >
        ← Retour aux réglages
      </RouterLink>
      <StatusPanel />
    </div>
  </section>
</template>
