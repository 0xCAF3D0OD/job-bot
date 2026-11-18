<script setup lang="ts">
import AppIcon from "../components/AppIcon.vue";
import PageHero from "../components/PageHero.vue";
import StatusPanel from "../components/StatusPanel.vue";
import { usePhone } from "../composables/usePhone";

// Diagnostic technique (docs/21 §6) : sorti des Réglages, pour ne pas les charger. Même en-tête que les autres
// sous-pages de Réglages (consigne de Kevin du 16.11) : le retour au-dessus du titre, sur le bord gauche des cartes ;
// sur téléphone, l'en-tête des Réglages (audit du 17.11, N6).
const { phone } = usePhone();
</script>

<template>
  <header
    v-if="phone"
    class="rg-phone-head"
  >
    <RouterLink
      to="/compte"
      class="rg-back"
      aria-label="Retour au compte"
    >
      <AppIcon name="arrow-left" />
    </RouterLink>
    <h1>État du service</h1>
  </header>
  <PageHero
    v-else
    title="État du service"
    class="settings-head"
  >
    <template #back>
      <!-- Sur ordinateur, plus de page Compte : « Retour au compte » ouvrait le panneau du profil (accord de Kevin du
           17.11, K43). Le retour mène aux Réglages, sur la ligne « État du service ». -->
      <RouterLink
        to="/reglages"
        class="back-link"
        data-test="settings-back"
      >
        <span class="with-icon"><AppIcon name="arrow-left" />Retour aux réglages</span>
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

<style>
/* L'en-tête des Réglages sur téléphone (mêmes règles que SettingsView) : la page est chargée sans les Réglages. */
.rg-phone-head { --rg-22: 22px; --rg-28: 28px; display: flex; align-items: center; gap: var(--space-1); padding: var(--space-3) var(--space-2) var(--space-1); }
.rg-phone-head h1 { margin: 0; font-size: var(--rg-22); line-height: var(--rg-28); font-weight: var(--weight-bold); }
.rg-back { display: inline-grid; place-items: center; width: 48px; height: 48px; border-radius: var(--radius-pill); color: var(--text); }
.rg-back .icon { width: 24px; height: 24px; }
</style>
