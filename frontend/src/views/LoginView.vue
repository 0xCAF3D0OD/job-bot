<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import AppIcon from "../components/AppIcon.vue";
import PageHero from "../components/PageHero.vue";
import { useAuth } from "../composables/useAuth";

// Page de connexion (docs/18 §1) : un seul compte, créé en ligne de commande.
const route = useRoute();
const router = useRouter();
const { me, load, login } = useAuth();
const username = ref("");
const password = ref("");
const error = ref("");
const busy = ref(false);

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
    await router.replace(next());
  } finally {
    busy.value = false;
  }
}

onMounted(() => void load());
</script>

<template>
  <PageHero
    eyebrow="Connexion"
    title="Se connecter"
    subtitle="Les Actualités sont ouvertes ; le reste demande ta connexion."
  />
  <section class="band">
    <div class="container narrow">
      <div
        v-if="me?.setup_needed"
        class="form-card"
        data-test="setup-needed"
      >
        <p>
          Aucun compte n'existe encore. Crée-le une fois, dans un terminal, depuis le dossier du projet :
        </p>
        <pre class="command"><code>cd backend && uv run jobbot set-password</code></pre>
        <p class="hint">
          L'identifiant et le mot de passe (12 caractères au moins) sont demandés au clavier, sans s'afficher.
          Le mot de passe est enregistré haché, jamais en clair ; ne le transmets à personne.
        </p>
      </div>
      <form
        v-else
        class="form-card login-form"
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
        <div class="form-actions">
          <button
            type="submit"
            class="primary"
            :disabled="busy"
            data-test="login-submit"
          >
            {{ busy ? "Connexion…" : "Se connecter" }} <AppIcon name="chevron" />
          </button>
        </div>
      </form>
    </div>
  </section>
</template>
