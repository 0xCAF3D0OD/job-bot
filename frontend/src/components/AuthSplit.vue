<script setup lang="ts">
import Illustration from "./Illustration.vue";

// Connexion et liens d'accès (docs/65, complément 0.53.1) : l'écran coupé en deux, une
// illustration et la phrase de la plateforme à gauche, le formulaire à droite. Sur téléphone,
// le formulaire seul, l'illustration en petit au-dessus.
defineProps<{ title: string; subtitle?: string }>();
</script>

<template>
  <section class="auth-split">
    <div
      class="auth-art"
      aria-hidden="true"
    >
      <Illustration
        name="emails-tries"
        class="auth-illu"
      />
      <p class="auth-tagline">
        Less searching. More living.
      </p>
      <p class="auth-pitch">
        Tes alertes triées, tes candidatures préparées, tes preuves ORP prêtes.
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
