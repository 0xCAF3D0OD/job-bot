<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { api } from "../api/client";
import { useAuth } from "../composables/useAuth";
import { plural } from "../format";
import AppIcon from "./AppIcon.vue";

// Tes données (docs/65 §6) : ce qui est gardé, l'export complet, la suppression du compte.
type Summary = {
  offers: number;
  applications: number;
  documents: number;
  profile_blocks: number;
  alert_emails: number;
  conversations: number;
  notifications: number;
  can_delete: boolean;
};
const summary = ref<Summary | null>(null);
const confirming = ref(false);
const password = ref("");
const error = ref("");
const busy = ref(false);
const router = useRouter();
const { expired } = useAuth();

onMounted(async () => {
  const { data } = await api.GET("/api/account/data");
  summary.value = data ?? null;
});

async function remove(): Promise<void> {
  busy.value = true;
  error.value = "";
  try {
    const { error: failed, response } = await api.POST("/api/account/delete", {
      body: { password: password.value },
    });
    password.value = "";
    if (response.ok) {
      expired();
      await router.replace("/connexion");
      return;
    }
    const detail = (failed as { detail?: unknown } | undefined)?.detail;
    error.value = typeof detail === "string" ? detail.charAt(0).toUpperCase() + detail.slice(1) + "." : "Suppression impossible.";
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div
    class="form-card sites-card"
    data-test="account-data"
  >
    <fieldset>
      <legend>Données personnelles</legend>
      <p
        v-if="summary"
        class="hint"
      >
        {{ plural(summary.offers, "offre", "offres") }}, {{ plural(summary.applications, "candidature", "candidatures") }},
        {{ plural(summary.documents, "document", "documents") }}, {{ plural(summary.profile_blocks, "bloc de profil", "blocs de profil") }},
        {{ plural(summary.alert_emails, "e-mail d'alerte", "e-mails d'alerte") }}.
        <RouterLink to="/tes-donnees">
          Ce qui est gardé, et ce qui part à l'IA
        </RouterLink>
      </p>
      <div class="form-actions">
        <a
          href="/api/account/export"
          download
          class="button-link"
          data-test="export"
        ><span class="with-icon"><AppIcon name="download" />Exporter mes données (ZIP)</span></a>
      </div>
      <template v-if="summary?.can_delete">
        <button
          v-if="!confirming"
          type="button"
          class="link danger"
          data-test="delete-account"
          @click="confirming = true"
        >
          <span class="with-icon"><AppIcon name="trash" />Supprimer mon compte</span>
        </button>
        <form
          v-else
          class="account-delete"
          data-test="delete-form"
          @submit.prevent="remove"
        >
          <p>
            Tout sera effacé : offres, candidatures, documents, preuves ORP, discussions. Exporte d'abord ce que tu veux
            garder. Ton mot de passe pour confirmer :
          </p>
          <div class="inline-field">
            <input
              v-model="password"
              type="password"
              autocomplete="current-password"
              required
              data-test="delete-password"
            >
            <button
              type="submit"
              class="secondary small danger"
              :disabled="busy"
              data-test="delete-confirm"
            >
              Supprimer définitivement
            </button>
            <button
              type="button"
              class="link"
              @click="confirming = false"
            >
              Annuler
            </button>
          </div>
          <p
            v-if="error"
            class="notice"
            role="alert"
            data-test="delete-error"
          >
            {{ error }}
          </p>
        </form>
      </template>
    </fieldset>
  </div>
</template>
