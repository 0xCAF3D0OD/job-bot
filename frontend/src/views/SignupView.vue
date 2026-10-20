<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import AuthSplit from "../components/AuthSplit.vue";

// Demander un compte (docs/102), sur le modèle du lien d'invitation (docs/65 §2) : le compte
// attend la validation de l'exploitant. Chaque envoi compte dans la limite par adresse (3 par
// heure) : tout ce qui peut se vérifier ici l'est avant d'envoyer.
const MIN_PASSWORD = 12;
const MAX_USERNAME = 40;
const MAX_NOTE = 300;

const state = ref<"loading" | "open" | "closed" | "sent">("loading");
const username = ref("");
const password = ref("");
const again = ref("");
const note = ref("");
const consent = ref(false);
// Le champ piège (docs/102, garde-fous) : invisible, les personnes le laissent vide.
const website = ref("");
const error = ref("");
const busy = ref(false);

function sentence(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1) + ".";
}

function detail(raw: unknown, fallback: string): string {
  const value = (raw as { detail?: unknown } | undefined)?.detail;
  return typeof value === "string" ? value : fallback;
}

onMounted(async () => {
  const { data } = await api.GET("/api/auth/signup");
  state.value = data?.open ? "open" : "closed";
});

function problem(): string {
  const name = username.value.trim();
  if (!name) return "Choisis un identifiant.";
  if (name.length > MAX_USERNAME) return `L'identifiant fait ${MAX_USERNAME} caractères au plus.`;
  if (password.value.length < MIN_PASSWORD) return `Le mot de passe fait ${MIN_PASSWORD} caractères au moins.`;
  if (password.value !== again.value) return "Les deux mots de passe diffèrent.";
  if (note.value.length > MAX_NOTE) return `Le mot pour l'exploitant fait ${MAX_NOTE} caractères au plus.`;
  if (!consent.value) return "Coche la case : lis d'abord ce que deviennent tes données.";
  return "";
}

async function submit(): Promise<void> {
  error.value = problem();
  if (error.value) return;
  busy.value = true;
  try {
    const { error: failed, response } = await api.POST("/api/auth/signup", {
      body: {
        username: username.value.trim(),
        password: password.value,
        note: note.value.trim() || null,
        consent: consent.value,
        website: website.value || null,
      },
    });
    if (response.ok) {
      password.value = "";
      again.value = "";
      state.value = "sent";
      return;
    }
    if (response.status === 403) {
      state.value = "closed";
      return;
    }
    error.value = sentence(detail(failed, "demande refusée : vérifie les champs"));
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <AuthSplit title="Créer un compte">
    <div
      v-if="state === 'closed'"
      class="auth-setup"
      data-test="signup-closed"
    >
      <p>Les demandes de compte sont fermées pour le moment.</p>
      <p class="hint">
        <RouterLink to="/connexion">
          Se connecter
        </RouterLink>
      </p>
    </div>
    <div
      v-else-if="state === 'sent'"
      class="auth-setup"
      role="status"
      data-test="signup-sent"
    >
      <p>Ta demande est envoyée. Tu pourras te connecter dès que l'exploitant l'aura acceptée.</p>
      <p class="hint">
        <RouterLink to="/connexion">
          Se connecter
        </RouterLink>
      </p>
    </div>
    <form
      v-else-if="state === 'open'"
      class="login-form"
      data-test="signup-form"
      novalidate
      @submit.prevent="submit"
    >
      <p class="hint">
        Choisis ton identifiant et ton mot de passe. Ton compte attend ensuite la validation de l'exploitant.
      </p>
      <label>Identifiant
        <input
          v-model="username"
          type="text"
          autocomplete="username"
          autocapitalize="none"
          spellcheck="false"
          :maxlength="MAX_USERNAME"
          required
          data-test="signup-username"
        >
      </label>
      <label>Mot de passe (12 caractères au moins)
        <input
          v-model="password"
          type="password"
          autocomplete="new-password"
          :minlength="MIN_PASSWORD"
          required
          data-test="signup-password"
        >
      </label>
      <label>Confirmer le mot de passe
        <input
          v-model="again"
          type="password"
          autocomplete="new-password"
          required
          data-test="signup-again"
        >
      </label>
      <label>Un mot pour l'exploitant (facultatif)
        <textarea
          v-model="note"
          rows="3"
          :maxlength="MAX_NOTE"
          placeholder="Qui tu es, comment tu as connu jobA1."
          data-test="signup-note"
        />
      </label>
      <div
        class="signup-trap"
        aria-hidden="true"
        data-test="signup-trap"
      >
        <label>Site web
          <input
            v-model="website"
            type="text"
            name="website"
            tabindex="-1"
            autocomplete="off"
            data-test="signup-website"
          >
        </label>
      </div>
      <label class="check signup-consent">
        <input
          v-model="consent"
          type="checkbox"
          data-test="signup-consent"
        >
        <span>J'ai lu <RouterLink
          to="/tes-donnees"
          target="_blank"
        >ce que deviennent mes données</RouterLink></span>
      </label>
      <p
        v-if="error"
        class="notice"
        role="alert"
        data-test="signup-error"
      >
        {{ error }}
      </p>
      <div class="form-actions">
        <button
          type="submit"
          class="primary"
          :disabled="busy"
          data-test="signup-submit"
        >
          <span class="with-icon"><AppIcon name="send" />Envoyer ma demande</span>
        </button>
      </div>
    </form>
  </AuthSplit>
</template>
