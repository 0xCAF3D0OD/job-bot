<script setup lang="ts">
import { useRouter } from "vue-router";

import { useAuth } from "../composables/useAuth";
import HelpTip from "./HelpTip.vue";

// Connexion (docs/18 §1) : compte connecté, « Se déconnecter partout ».
const router = useRouter();
const { me, logout } = useAuth();

async function everywhere(): Promise<void> {
  if (!window.confirm("Fermer toutes les sessions ouvertes, celle-ci comprise ?")) return;
  await logout(true);
  await router.push({ name: "login" });
}
</script>

<template>
  <div
    v-if="me?.auth_enabled && me.authenticated"
    class="form-card sites-card"
    data-test="session-panel"
  >
    <fieldset>
      <legend>
        Ton compte
        <HelpTip
          text="La session dure 30 jours. Le mot de passe se change sur l'ordinateur qui fait tourner la plateforme (voir le README) ; toutes les sessions sont alors fermées."
          label="Aide : ton compte"
        />
      </legend>
      <p class="hint">
        Connecté en tant que <strong>{{ me.username }}</strong>.
      </p>
      <div class="form-actions">
        <button
          type="button"
          class="secondary small"
          data-test="logout-all"
          @click="everywhere"
        >
          Se déconnecter partout
        </button>
      </div>
    </fieldset>
  </div>
  <p
    v-else-if="me && !me.auth_enabled"
    class="hint"
    data-test="auth-disabled"
  >
    Connexion désactivée sur cette installation : toutes les pages sont ouvertes.
  </p>
</template>
