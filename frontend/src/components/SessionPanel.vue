<script setup lang="ts">
import { useRouter } from "vue-router";

import { useAuth } from "../composables/useAuth";

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
      <legend>Ton compte</legend>
      <p class="hint">
        Connecté en tant que <strong>{{ me.username }}</strong>. Une session dure 30 jours et se prolonge à l'usage.
        Pour changer le mot de passe : <code>cd backend && uv run jobbot set-password</code> (toutes les sessions sont
        alors fermées).
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
    Connexion désactivée (<code>JOBBOT_AUTH_ENABLED=false</code>) : toutes les pages sont ouvertes. À n'utiliser que
    pour un essai sur ta machine.
  </p>
</template>
