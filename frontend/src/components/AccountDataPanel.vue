<script setup lang="ts">
import { nextTick, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "../api/client";
import { useAuth } from "../composables/useAuth";
import { plural } from "../format";
import AppIcon from "./AppIcon.vue";
import InlineConfirm from "./InlineConfirm.vue";

// Tes données (docs/65 §6) : ce qui est gardé, l'export complet, la fermeture du compte.
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
const route = useRoute();
const { expired } = useAuth();
const passwordInput = ref<HTMLInputElement | null>(null);

onMounted(async () => {
  const { data } = await api.GET("/api/account/data");
  summary.value = data ?? null;
  // Venu de « Fermer mon compte » dans le menu (docs/105) : la confirmation est ouverte.
  if (route.query.fermer && summary.value?.can_delete) {
    confirming.value = true;
    await nextTick();
    passwordInput.value?.scrollIntoView?.({ block: "center", inline: "nearest" });
    passwordInput.value?.focus({ preventScroll: true });
  }
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
    error.value = typeof detail === "string" ? detail.charAt(0).toUpperCase() + detail.slice(1) + "." : "Fermeture impossible.";
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
          <span class="with-icon"><AppIcon name="trash" />Fermer mon compte</span>
        </button>
        <!-- La même confirmation que partout (docs/108 §1), le mot de passe dedans : rien ne
             dépasse de l'écran sur téléphone (docs/105, complément 0.77.4). -->
        <form
          v-else
          class="account-delete"
          data-test="delete-form"
          @submit.prevent="remove"
        >
          <InlineConfirm
            message="Fermer ton compte efface tout : offres, candidatures, documents, preuves ORP, discussions. Exporte d'abord ce que tu veux garder."
            confirm-label="Fermer définitivement"
            :busy="busy || !password"
            @confirm="remove"
            @cancel="confirming = false"
          >
            <label class="account-delete-password">
              Ton mot de passe pour confirmer
              <input
                ref="passwordInput"
                v-model="password"
                type="password"
                autocomplete="current-password"
                required
                data-test="delete-password"
              >
            </label>
            <p
              v-if="error"
              class="notice"
              role="alert"
              data-test="delete-error"
            >
              {{ error }}
            </p>
          </InlineConfirm>
        </form>
      </template>
    </fieldset>
  </div>
</template>
