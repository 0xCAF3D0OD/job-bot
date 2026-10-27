<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api } from "../api/client";
import { useAuth } from "../composables/useAuth";
import AppIcon from "./AppIcon.vue";
import InlineConfirm from "./InlineConfirm.vue";
import SettingCard from "./SettingCard.vue";
import SettingRow from "./SettingRow.vue";
import { plural } from "../format";

// Tes données (docs/65 §6) : ce qui est gardé, l'export complet, la fermeture du compte. Une carte
// (1.6.67, planche « 5. Réglages ») : une ligne par action, la confirmation sous sa ligne.
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

// Les compteurs en une phrase : « 12 offres · 3 candidatures · … ».
const counts = computed(() => {
  const s = summary.value;
  if (!s) return "Ce que jobA1 garde de toi, et combien de temps.";
  return [
    plural(s.offers, "offre", "offres"),
    plural(s.applications, "candidature", "candidatures"),
    plural(s.documents, "document", "documents"),
    plural(s.profile_blocks, "bloc de profil", "blocs de profil"),
    plural(s.alert_emails, "e-mail d'alerte", "e-mails d'alerte"),
  ].join(" · ");
});

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
  <SettingCard data-test="account-data">
    <SettingRow
      title="Données personnelles"
      :description="counts"
      data-test="account-counts"
    >
      <RouterLink
        to="/tes-donnees"
        class="button-link"
        data-test="data-retention"
      >
        Voir les durées
      </RouterLink>
    </SettingRow>
    <SettingRow
      title="Exporter mes données"
      description="Un fichier ZIP avec tout ce que jobA1 garde de toi."
    >
      <a
        href="/api/account/export"
        download
        class="button-link"
        data-test="export"
      ><span class="with-icon"><AppIcon name="download" />Télécharger</span></a>
    </SettingRow>
    <template v-if="summary?.can_delete">
      <SettingRow
        title="Fermer le compte"
        description="Tout est effacé : offres, candidatures, documents, preuves ORP."
      >
        <button
          v-if="!confirming"
          type="button"
          class="secondary small danger"
          data-test="delete-account"
          @click="confirming = true"
        >
          <span class="with-icon"><AppIcon name="trash" />Fermer mon compte</span>
        </button>
      </SettingRow>
      <!-- La même confirmation que partout (docs/108 §1), le mot de passe dedans : rien ne
           dépasse de l'écran sur téléphone (docs/105, complément 0.77.4). -->
      <form
        v-if="confirming"
        class="account-delete setting-row-form"
        data-test="delete-form"
        @submit.prevent="remove"
      >
        <InlineConfirm
          message="Tout est effacé : offres, candidatures, documents, preuves ORP. Exporte d'abord ce que tu veux garder."
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
  </SettingCard>
</template>
