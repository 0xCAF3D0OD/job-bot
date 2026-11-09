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
