<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "../api/client";
import AuthSplit from "../components/AuthSplit.vue";
import { useAuth } from "../composables/useAuth";
import { formatDate } from "../format";

// Lien reçu de l'exploitant (docs/65 §2) : une invitation (choisir son identifiant et son
// mot de passe) ou une réinitialisation (un nouveau mot de passe). Il ne sert qu'une fois.
const route = useRoute();
const router = useRouter();
const { load } = useAuth();
const token = computed(() => String(route.params.token ?? ""));
const link = ref<{ kind: "invite" | "reset"; username: string | null; expires_at: string } | null>(null);
const problem = ref("");
const username = ref("");
const password = ref("");
const again = ref("");
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
  const { data, error: failed } = await api.GET("/api/auth/links/{token}", {
    params: { path: { token: token.value } },
  });
  if (data) link.value = data;
  else problem.value = sentence(detail(failed, "lien inconnu : demande-en un nouveau"));
});

async function submit(): Promise<void> {
  error.value = "";
  if (password.value !== again.value) {
    error.value = "Les deux mots de passe diffèrent.";
    return;
  }
  busy.value = true;
  try {
    const { error: failed, response } = await api.POST("/api/auth/links/{token}", {
      params: { path: { token: token.value } },
      body: { username: link.value?.kind === "invite" ? username.value.trim() : null, password: password.value },
    });
    if (response.ok) {
      await load(true);
      await router.replace("/aujourdhui");
      return;
    }
    error.value = sentence(detail(failed, "enregistrement impossible"));
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <AuthSplit :title="link?.kind === 'reset' ? 'Nouveau mot de passe' : 'Bienvenue sur jobA1'">
    <div
      v-if="problem"
      class="auth-setup"
      data-test="access-problem"
    >
      <p>{{ problem }}</p>
      <p class="hint">
        Demande un nouveau lien à la personne qui t'a invité.
      </p>
    </div>
    <form
      v-else-if="link"
      class="login-form"
      data-test="access-form"
      @submit.prevent="submit"
    >
      <p
        v-if="link.kind === 'reset'"
        class="hint"
      >
        Pour le compte <strong>{{ link.username }}</strong>. Tes autres sessions seront fermées.
      </p>
      <p
        v-else
        class="hint"
      >
        Choisis ton identifiant et ton mot de passe. Lien valable jusqu'au {{ formatDate(link.expires_at) }}.
        Avant : <RouterLink
          to="/tes-donnees"
          target="_blank"
        >ce que la plateforme garde sur toi</RouterLink>.
      </p>
      <label v-if="link.kind === 'invite'">Identifiant
        <input
          v-model="username"
          type="text"
          autocomplete="username"
          autocapitalize="none"
          spellcheck="false"
          maxlength="40"
          required
          data-test="access-username"
        >
      </label>
      <label>Mot de passe (12 caractères au moins)
        <input
          v-model="password"
          type="password"
          autocomplete="new-password"
          minlength="12"
          required
          data-test="access-password"
        >
      </label>
      <label>Encore une fois
        <input
          v-model="again"
          type="password"
          autocomplete="new-password"
          required
          data-test="access-again"
        >
      </label>
      <p
        v-if="error"
        class="notice"
        role="alert"
        data-test="access-error"
      >
        {{ error }}
      </p>
      <div class="form-actions">
        <button
          type="submit"
          class="primary"
          :disabled="busy"
          data-test="access-submit"
        >
          {{ link.kind === "reset" ? "Changer mon mot de passe" : "Créer mon compte" }}
        </button>
      </div>
    </form>
  </AuthSplit>
</template>
