<script setup lang="ts">
import { useRouter } from "vue-router";

import { api } from "../api/client";
import { useAuth } from "../composables/useAuth";

// Connexion (docs/18 §1) : compte connecté, « Se déconnecter partout ».
const router = useRouter();
const { me, logout } = useAuth();

// Refaire l'accueil (docs/66 §4) : les réponses actuelles sont reprises.
async function welcomeAgain(): Promise<void> {
  await api.PUT("/api/welcome", { body: { done: false, postponed: false, step: 1 } });
  if (me.value) me.value = { ...me.value, welcome: "pending" };
  await router.push("/bienvenue");
}

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
        <button
          v-if="!me.is_owner"
          type="button"
          class="link"
          data-test="welcome-again"
          @click="welcomeAgain"
        >
          Refaire l'accueil
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
