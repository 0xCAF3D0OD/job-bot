<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import { api } from "../api/client";
import { useAuth } from "../composables/useAuth";
import InlineConfirm from "./InlineConfirm.vue";

// Connexion (docs/18 §1) : compte connecté, « Se déconnecter partout ».
const router = useRouter();
const { me, logout } = useAuth();

// Refaire l'accueil (docs/66 §4) : les réponses actuelles sont reprises.
async function welcomeAgain(): Promise<void> {
  await api.PUT("/api/welcome", { body: { done: false, postponed: false, step: 1 } });
  if (me.value) me.value = { ...me.value, welcome: "pending" };
  await router.push("/bienvenue");
}

// Confirmé dans la page (docs/108 §1) : on est déconnecté, celle-ci comprise.
const confirming = ref(false);
async function everywhere(): Promise<void> {
  confirming.value = false;
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
        Connexion
      </legend>
      <p class="hint">
        Connecté en tant que <strong>{{ me.username }}</strong>.
      </p>
      <div class="form-actions">
        <!-- Deux liens discrets (docs/108, 0.77.2) : aucune n'est l'action principale de l'écran. -->
        <button
          v-if="!me.is_owner"
          type="button"
          class="link"
          data-test="welcome-again"
          @click="welcomeAgain"
        >
          Refaire l'accueil
        </button>
        <button
          type="button"
          class="link"
          data-test="logout-all"
          @click="confirming = true"
        >
          Se déconnecter partout
        </button>
      </div>
      <InlineConfirm
        v-if="confirming"
        message="Fermer toutes les sessions ouvertes, celle-ci comprise ? Tu devras te reconnecter."
        confirm-label="Se déconnecter partout"
        @confirm="everywhere"
        @cancel="confirming = false"
      />
    </fieldset>
  </div>
  <p
    v-else-if="me?.demo"
    class="hint"
    data-test="auth-demo"
  >
    Démo : pas de connexion, et rien de ce que tu fais n'est enregistré.
  </p>
  <p
    v-else-if="me && !me.auth_enabled"
    class="hint"
    data-test="auth-disabled"
  >
    Connexion désactivée sur cette installation : toutes les pages sont ouvertes.
  </p>
</template>
