<script setup lang="ts">
import AlertsPanel from "../components/AlertsPanel.vue";
import JournalPanel from "../components/JournalPanel.vue";

// Onglet Alertes (docs/20 §1) : les alertes à créer sur les sites, puis celles reçues.
</script>

<template>
  <section class="jobs-body">
    <AlertsPanel />
    <h2
      id="recues"
      class="section-title"
    >
      Alertes reçues
    </h2>
    <p class="hint">
      Les e-mails d'alerte lus par la plateforme (le journal des recherches, joint au PDF des preuves ORP si tu le
      souhaites).
    </p>
    <JournalPanel />
  </section>
</template>
