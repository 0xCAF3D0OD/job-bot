<script setup lang="ts">
import AuthScene from "./AuthScene.vue";

// Connexion et liens d'accès (docs/65, complément 0.53.1) : l'écran coupé en deux, la scène qui
// remplit la moitié gauche avec la phrase de la plateforme dessus (docs/67, compléments 0.55.2 et
// 0.55.3 : le jour, ou le soir en sombre), le formulaire à droite. Sur téléphone, la scène en
// bandeau au-dessus du formulaire.
defineProps<{ title: string; subtitle?: string }>();
</script>

<template>
  <section class="auth-split">
    <div
      class="auth-art"
      aria-hidden="true"
    >
      <AuthScene>
        <div class="auth-caption">
          <p class="auth-pitch">
            Tes alertes triées, tes candidatures préparées, tes preuves ORP prêtes.
          </p>
        </div>
      </AuthScene>
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
