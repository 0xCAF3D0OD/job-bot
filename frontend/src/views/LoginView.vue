<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "../api/client";
import AuthSplit from "../components/AuthSplit.vue";
import HoverNote from "../components/HoverNote.vue";
import SocialSignIn from "../components/SocialSignIn.vue";
import { useAuth } from "../composables/useAuth";

// Page de connexion (docs/18 §1) : l'écran coupé en deux, l'illustration à gauche et la
// connexion à droite ; Google, Apple et Microsoft présentés, pas encore branchés (docs/65,
// complément 0.53.1).
const route = useRoute();
const router = useRouter();
const { me, load, login } = useAuth();
const username = ref("");
const password = ref("");
const error = ref("");
const busy = ref(false);
// Les demandes de compte ouvertes (docs/102) : le lien « Créer un compte » ; sinon, l'invitation.
const signupOpen = ref(false);

function next(): string {
  const wanted = typeof route.query.suite === "string" ? route.query.suite : "";
  // Seulement une page de la plateforme (pas d'adresse externe).
  return wanted.startsWith("/") && !wanted.startsWith("//") ? wanted : "/aujourdhui";
}

async function submit(): Promise<void> {
  busy.value = true;
  error.value = "";
  try {
    const problem = await login(username.value.trim(), password.value);
    password.value = "";
    if (problem) {
      error.value = problem.charAt(0).toUpperCase() + problem.slice(1) + ".";
      return;
    }
    // Un compte dont l'accueil n'est pas fini le reprend là où il s'était arrêté (docs/66 §4).
    const welcome = me.value?.welcome;
    await router.replace(welcome === "pending" || welcome === "postponed" ? "/bienvenue" : next());
  } finally {
    busy.value = false;
  }
}

onMounted(async () => {
  void load();
  const { data } = await api.GET("/api/auth/signup");
  signupOpen.value = data?.open === true;
});
</script>

<template>
  <AuthSplit
    title="Se connecter"
    subtitle="Tes offres, tes candidatures et tes preuves ORP, au même endroit."
  >
    <div
      v-if="me?.setup_needed"
      class="auth-setup"
      data-test="setup-needed"
    >
      <p>
        Aucun compte n'existe encore.
        <HoverNote text="L'identifiant et le mot de passe (12 caractères au moins) sont demandés au clavier, sans s'afficher. Le mot de passe est enregistré haché, jamais en clair ; ne le transmets à personne.">
          Crée-le une fois
        </HoverNote>, dans un terminal, depuis le dossier du projet :
      </p>
      <pre class="command"><code>cd backend && uv run jobbot set-password</code></pre>
    </div>
    <template v-else>
      <SocialSignIn />
      <form
        class="login-form"
        data-test="login-form"
        @submit.prevent="submit"
      >
        <label>Identifiant
          <input
            v-model="username"
            type="text"
            autocomplete="username"
            autocapitalize="none"
            spellcheck="false"
            required
            data-test="username"
          >
        </label>
        <label>Mot de passe
          <input
            v-model="password"
            type="password"
            autocomplete="current-password"
            required
            data-test="password"
          >
        </label>
        <p
          v-if="error"
          class="notice"
          role="alert"
          data-test="login-error"
        >
          {{ error }}
        </p>
        <button
          type="submit"
          class="primary auth-submit"
          :disabled="busy"
          data-test="login-submit"
        >
          {{ busy ? "Connexion…" : "Se connecter" }}
        </button>
      </form>
      <!-- Deux lignes : l'inscription, puis les données personnelles (docs/102). -->
      <p class="hint auth-foot">
        <template v-if="signupOpen">
          Pas encore de compte ? <RouterLink
            to="/inscription"
            data-test="signup-link"
          >
            Créer un compte
          </RouterLink>
        </template>
        <template v-else>
          Pas encore de compte ? L'accès se fait sur invitation.
        </template>
      </p>
      <p class="hint auth-foot">
        <RouterLink to="/tes-donnees">
          Données personnelles
        </RouterLink>
      </p>
    </template>
  </AuthSplit>
</template>
