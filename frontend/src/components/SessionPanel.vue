<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import { api } from "../api/client";
import { useAuth } from "../composables/useAuth";
import InlineConfirm from "./InlineConfirm.vue";
import SettingCard from "./SettingCard.vue";
import SettingRow from "./SettingRow.vue";

// Connexion (docs/18 §1) : compte connecté, « Se déconnecter partout » (1.6.67, planche
// « 5. Réglages ») : une carte, une ligne par action, la confirmation sous sa ligne.
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
  <SettingCard
    v-if="me?.auth_enabled && me.authenticated"
    data-test="session-panel"
  >
    <SettingRow
      title="Connexion"
      :description="`Connecté en tant que ${me.username ?? ''}.`"
    >
      <button
        v-if="!confirming"
        type="button"
        class="secondary small"
        data-test="logout-all"
        @click="confirming = true"
      >
        Se déconnecter partout
      </button>
    </SettingRow>
    <div
      v-if="confirming"
      class="setting-row-form"
    >
      <InlineConfirm
        message="Fermer toutes les sessions ouvertes, celle-ci comprise ? Tu devras te reconnecter."
        confirm-label="Se déconnecter partout"
        @confirm="everywhere"
        @cancel="confirming = false"
      />
    </div>
    <SettingRow
      v-if="!me.is_owner"
      title="L'accueil"
      description="Les premières questions, avec tes réponses actuelles."
    >
      <button
        type="button"
        class="secondary small"
        data-test="welcome-again"
        @click="welcomeAgain"
      >
        Refaire l'accueil
      </button>
    </SettingRow>
  </SettingCard>
  <SettingCard v-else-if="me?.demo">
    <SettingRow
      title="Connexion"
      description="Démo : rien de ce que tu fais n'est enregistré."
      data-test="auth-demo"
    />
  </SettingCard>
  <SettingCard v-else-if="me && !me.auth_enabled">
    <SettingRow
      title="Connexion"
      description="Connexion désactivée sur cette installation : toutes les pages sont ouvertes."
      data-test="auth-disabled"
    />
  </SettingCard>
</template>
