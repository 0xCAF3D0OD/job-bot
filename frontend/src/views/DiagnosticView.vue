<script setup lang="ts">
import AppIcon from "../components/AppIcon.vue";
import PageHero from "../components/PageHero.vue";
import StatusPanel from "../components/StatusPanel.vue";

// Diagnostic technique (docs/21 §6) : sorti des Réglages, pour ne pas les charger. Même en-tête que les autres
// sous-pages de Réglages (consigne de Kevin du 16.11) : le retour au-dessus du titre, sur le bord gauche des cartes.
</script>

<template>
  <PageHero
    title="État du service"
    class="settings-head"
  >
    <template #back>
      <RouterLink
        to="/compte"
        class="back-link"
      >
        <span class="with-icon"><AppIcon name="arrow-left" />Retour au compte</span>
      </RouterLink>
    </template>
  </PageHero>
  <section class="band">
    <div class="settings-layout">
      <div class="settings-sections">
        <StatusPanel />
      </div>
    </div>
  </section>
</template>
