<script setup lang="ts">
import AuthIllustration from "./AuthIllustration.vue";

// Liens d'accès et demande de compte (docs/65 ; docs/102) : l'écran coupé en deux, l'illustration de la connexion à
// gauche avec la phrase de la plateforme (maquette Connexion, ordinateur), le formulaire à droite. Sur téléphone,
// le bandeau de 150 px au-dessus du formulaire. La page de connexion a sa propre mise en page (LoginView).
defineProps<{ title: string; subtitle?: string }>();
</script>

<template>
  <section class="auth-split">
    <div
      class="auth-art"
      aria-hidden="true"
    >
      <AuthIllustration large />
      <AuthIllustration class="auth-illustration-phone" />
      <p class="auth-pitch">
        Tes alertes triées, tes candidatures préparées, tes justificatifs ORP prêts.
      </p>
    </div>
    <div class="auth-panel">
      <div class="auth-box">
        <h1>{{ title }}</h1>
        <p
          v-if="subtitle"
          class="hint"
        >
          {{ subtitle }}
        </p>
        <slot />
      </div>
    </div>
  </section>
</template>

<style>
/* Sorti de style.css (allègement du 16.11, issue #797) : ces règles ne servent qu'ici, chargées avec ce composant. */
.auth-split { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr); min-height: calc(100dvh - 4.4rem); }
.auth-art { display: flex; flex-direction: column; justify-content: center; align-items: center; gap: calc(var(--space-6) + var(--space-1)); padding: 0 var(--space-6); background: var(--surface); border-right: 1px solid var(--line); }
.auth-pitch { margin: 0; --pitch-24: 1.5rem; --pitch-lh: 1.25; max-width: 520px; text-align: center; font-size: var(--pitch-24); line-height: var(--pitch-lh); font-weight: var(--weight-bold); }
.auth-panel { display: grid; place-items: center; padding: var(--space-12) var(--space-6); background: var(--bg); }
.auth-box { display: grid; gap: var(--space-4); width: min(100%, 24rem); }
@media (max-width: 820px) {
.auth-split { grid-template-columns: minmax(0, 1fr); min-height: 0; }
.auth-art { gap: 0; padding: 0; background: var(--bg); border-right: 0; }
.auth-art .auth-illustration-phone { display: block; }
.auth-panel { padding: var(--space-6) var(--space-4) var(--space-8); place-items: start center; }
}
</style>
