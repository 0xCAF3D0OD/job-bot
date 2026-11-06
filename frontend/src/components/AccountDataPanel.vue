<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api, type OrpMonth } from "../api/client";
import { useAuth } from "../composables/useAuth";
import AppIcon from "./AppIcon.vue";
import InlineConfirm from "./InlineConfirm.vue";
import OrpSheet from "./OrpSheet.vue";
import SettingCard from "./SettingCard.vue";
import SettingRow from "./SettingRow.vue";
import { plural } from "../format";

// Tes données (docs/65 §6) : ce qui est gardé et l'export complet, dans une carte (1.6.67) ; la suppression du
// compte dans la sienne, en dessous (maquette Réglages, docs/139 étape 10b).
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
// L'export demande le mot de passe, comme la fermeture (docs/regles-securite-donnees.md X-1) :
// une session volée ne suffit pas à emporter les données.
const exporting = ref(false);
const exportPassword = ref("");
const exportError = ref("");
const exportBusy = ref(false);

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
  // Venu d'un lien « ?fermer=1 » (docs/105) : la confirmation est ouverte.
  if (route.query.fermer && summary.value?.can_delete) {
    confirming.value = true;
    await nextTick();
    passwordInput.value?.scrollIntoView?.({ block: "center", inline: "nearest" });
    passwordInput.value?.focus({ preventScroll: true });
  }
});

function detailOf(failed: unknown, fallback: string): string {
  const detail = (failed as { detail?: unknown } | undefined)?.detail;
  return typeof detail === "string" ? detail.charAt(0).toUpperCase() + detail.slice(1) + "." : fallback;
}

async function download(): Promise<void> {
  exportBusy.value = true;
  exportError.value = "";
  try {
    const { data, error: failed, response } = await api.POST("/api/account/export", {
      body: { password: exportPassword.value },
      parseAs: "blob",
    });
    exportPassword.value = "";
    if (!response.ok || !(data instanceof Blob)) {
      exportError.value = detailOf(failed, "Export impossible.");
      return;
    }
    const name = /filename="([^"]+)"/.exec(response.headers.get("content-disposition") ?? "")?.[1] ?? "jobA1.zip";
    const url = URL.createObjectURL(data);
    const link = document.createElement("a");
    link.href = url;
    link.download = name;
    link.click();
    URL.revokeObjectURL(url);
    exporting.value = false;
  } finally {
    exportBusy.value = false;
  }
}

// « Exporter ma feuille ORP » (C13) : le PDF du mois en cours, comme au Bilan, sans quitter la confirmation.
const orp = ref<OrpMonth | null>(null);
const orpSheet = ref<InstanceType<typeof OrpSheet> | null>(null);
const orpBusy = ref(false);
const orpError = ref("");
async function exportOrp(): Promise<void> {
  if (orpBusy.value) return;
  orpBusy.value = true;
  orpError.value = "";
  try {
    const { data } = await api.GET("/api/orp");
    if (!data) throw new Error();
    orp.value = data;
    await nextTick();
    await orpSheet.value?.printPdf();
  } catch {
    orpError.value = "La feuille ORP n'a pas pu être préparée. Réessaie depuis le Bilan.";
  } finally {
    orpBusy.value = false;
  }
}

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
      await router.replace("/connexion?au-revoir=1");
      return;
    }
    error.value = detailOf(failed, "Suppression impossible.");
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
      <button
        v-if="!exporting"
        type="button"
        class="button-link"
        data-test="export"
        @click="exporting = true"
      >
        <span class="with-icon"><AppIcon name="download" />Télécharger</span>
      </button>
    </SettingRow>
    <!-- La confirmation de la fermeture, reprise telle quelle (choix du 2026-11-04) : le mot
         de passe dedans, sous sa ligne. -->
    <form
      v-if="exporting"
      class="account-delete setting-row-form"
      data-test="export-form"
      @submit.prevent="download"
    >
      <InlineConfirm
        message="Tes données partent dans un fichier ZIP. Un avis arrive aussi dans la cloche."
        confirm-label="Télécharger"
        cancel-label="Annuler"
        :danger="false"
        :busy="exportBusy || !exportPassword"
        @confirm="download"
        @cancel="exporting = false"
      >
        <label class="account-delete-password">
          Ton mot de passe pour confirmer
          <input
            v-model="exportPassword"
            type="password"
            autocomplete="current-password"
            required
            data-test="export-password"
          >
        </label>
        <p
          v-if="exportError"
          class="notice"
          role="alert"
          data-test="export-error"
        >
          {{ exportError }}
        </p>
      </InlineConfirm>
    </form>
  </SettingCard>
  <!-- Supprimer le compte (maquette Réglages ; décisions de Kevin du 2026-11-05, C13) : seul dans sa carte, en
       rouge. La confirmation garde le mot de passe, propose d'abord d'exporter la feuille ORP, et « Annuler » a le
       focus. Entrée dans le mot de passe ne supprime rien : seul le clic sur « Supprimer définitivement » le fait. -->
  <SettingCard
    v-if="summary?.can_delete"
    class="account-delete-card"
    data-test="account-delete-card"
  >
    <SettingRow
      v-if="!confirming"
      title="Supprimer mon compte"
      description="Ton CV, tes candidatures et ton suivi ORP sont effacés."
    >
      <button
        type="button"
        class="secondary small danger"
        data-test="delete-account"
        @click="confirming = true"
      >
        <span class="with-icon"><AppIcon name="trash" />Supprimer mon compte</span>
      </button>
    </SettingRow>
    <form
      v-else
      class="account-delete setting-row-form"
      data-test="delete-form"
      @submit.prevent
    >
      <InlineConfirm
        message="Supprimer ton compte ?"
        confirm-label="Supprimer définitivement"
        cancel-label="Annuler"
        :busy="busy || !password"
        @confirm="remove"
        @cancel="confirming = false"
      >
        <p class="account-delete-text">
          Ton CV, tes candidatures et ton suivi ORP seront effacés. Cette action est définitive. Pense à exporter ta
          feuille ORP avant.
        </p>
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
        <button
          type="button"
          class="link account-delete-export"
          :aria-busy="orpBusy ? 'true' : undefined"
          data-test="delete-export-orp"
          @click="exportOrp"
        >
          <span class="with-icon"><AppIcon name="download" />Exporter ma feuille ORP</span>
        </button>
        <p
          v-if="orpError"
          class="notice"
          role="alert"
          data-test="delete-export-orp-error"
        >
          {{ orpError }}
        </p>
        <!-- La feuille du mois, cachée : son PDF se fait sur place, la confirmation reste ouverte. -->
        <div
          v-if="orp"
          hidden
        >
          <OrpSheet
            ref="orpSheet"
            :data="orp"
          />
        </div>
      </InlineConfirm>
    </form>
  </SettingCard>
</template>
