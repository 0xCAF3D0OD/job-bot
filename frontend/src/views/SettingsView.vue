<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api, type SettingsModel } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import PageHero from "../components/PageHero.vue";

const form = ref<SettingsModel>({
  orp_monthly_target: null,
  notify_score_threshold: 70,
  llm_monthly_budget_chf: 10,
});
const loaded = ref(false);
const saving = ref(false);
const message = ref("");
const identity = ref<{ name: string; address: string; phone: string; email: string }>({
  name: "",
  address: "",
  phone: "",
  email: "",
});
const identityMessage = ref("");

async function saveIdentity(): Promise<void> {
  const { data } = await api.PUT("/api/identity", {
    body: {
      name: identity.value.name || null,
      address: identity.value.address || null,
      phone: identity.value.phone || null,
      email: identity.value.email || null,
    },
  });
  identityMessage.value = data ? "Coordonnées enregistrées." : "Enregistrement refusé : vérifie les champs.";
}
const notifications = ref<{ configured: boolean; server: string } | null>(null);
// Vrai si l'API n'a pas répondu (arrêtée, ou plus ancienne que l'interface).
const notificationsUnknown = ref(false);
const testMessage = ref("");
const testing = ref(false);

async function sendTest(): Promise<void> {
  testing.value = true;
  try {
    const { error, response } = await api.POST("/api/notifications/test");
    if (response.status === 204) {
      testMessage.value = "Notification envoyée : vérifie ton téléphone.";
    } else {
      const detail = (error as { detail?: unknown } | undefined)?.detail;
      testMessage.value = typeof detail === "string" ? `Échec : ${detail}.` : `Échec (HTTP ${response.status}).`;
    }
  } catch {
    testMessage.value = "API injoignable.";
  } finally {
    testing.value = false;
  }
}

onMounted(async () => {
  const { data } = await api.GET("/api/settings");
  if (data) form.value = data;
  loaded.value = true;
  const who = await api.GET("/api/identity");
  if (who.data) {
    identity.value = {
      name: who.data.name ?? "",
      address: who.data.address ?? "",
      phone: who.data.phone ?? "",
      email: who.data.email ?? "",
    };
  }
  try {
    const status = await api.GET("/api/notifications");
    notifications.value = status.data ?? null;
    notificationsUnknown.value = !status.data;
  } catch {
    notificationsUnknown.value = true;
  }
});

async function save(): Promise<void> {
  saving.value = true;
  try {
    const body = { ...form.value, orp_monthly_target: form.value.orp_monthly_target || null };
    const { data } = await api.PUT("/api/settings", { body });
    message.value = data ? "Réglages enregistrés." : "L'enregistrement a échoué : vérifie les valeurs.";
    if (data) form.value = data;
  } catch {
    message.value = "API injoignable.";
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <PageHero
    eyebrow="Réglages"
    title="Tes réglages"
    subtitle="Objectif de l'ORP, notifications et budget de l'IA."
  />
  <section class="band">
    <div class="container narrow">
      <form
        v-if="loaded"
        class="form-card"
        data-test="settings-form"
        @submit.prevent="save"
      >
        <fieldset>
          <legend><label for="orp">Objectif mensuel de l'ORP</label></legend>
          <p class="hint">
            Nombre de candidatures demandé par ton conseiller. Vide si tu ne le connais pas encore.
          </p>
          <div class="inline-field">
            <input
              id="orp"
              v-model.number="form.orp_monthly_target"
              type="number"
              min="1"
              max="100"
            >
            <span>candidatures par mois</span>
          </div>
        </fieldset>
        <fieldset>
          <legend><label for="threshold">Seuil de notification</label></legend>
          <p class="hint">
            Tu es prévenu des nouvelles offres notées au moins à ce score.
          </p>
          <div class="inline-field">
            <input
              id="threshold"
              v-model.number="form.notify_score_threshold"
              type="number"
              min="0"
              max="100"
              required
            >
            <span>/ 100</span>
          </div>
        </fieldset>
        <fieldset data-test="notifications">
          <legend>Notifications</legend>
          <template v-if="notifications?.configured">
            <p class="hint">
              Envoyées par {{ notifications.server }} pour les nouvelles offres notées au moins au seuil ci-dessus,
              et quand la dépense de l'IA atteint 80 % du plafond.
            </p>
            <div class="inline-field">
              <button
                type="button"
                class="secondary small"
                :disabled="testing"
                data-test="test-notification"
                @click="sendTest"
              >
                Envoyer une notification de test
              </button>
              <span
                v-if="testMessage"
                role="status"
              >{{ testMessage }}</span>
            </div>
          </template>
          <p
            v-else-if="notificationsUnknown"
            class="notice error"
            data-test="notifications-unknown"
          >
            Impossible de vérifier : l'API ne répond pas à cette question. Elle est peut-être arrêtée, ou plus
            ancienne que l'interface. Relance <code>make dev</code>.
          </p>
          <p
            v-else
            class="hint"
          >
            Non configurées. Installe l'application ntfy sur ton téléphone, abonne-toi à un sujet difficile à
            deviner, puis renseigne <code>JOBBOT_NTFY_TOPIC</code> dans <code>.env</code> et relance
            <code>make dev</code>.
          </p>
        </fieldset>
        <fieldset>
          <legend><label for="budget">Plafond mensuel du coût de l'IA</label></legend>
          <p class="hint">
            Au-delà, les offres ne sont plus notées jusqu'au mois suivant.
          </p>
          <div class="inline-field">
            <input
              id="budget"
              v-model.number="form.llm_monthly_budget_chf"
              type="number"
              min="0"
              max="1000"
              step="0.5"
              required
            >
            <span>CHF</span>
          </div>
        </fieldset>
        <div class="form-actions">
          <button
            type="submit"
            class="primary"
            :disabled="saving"
            data-test="save-settings"
          >
            Enregistrer <AppIcon name="chevron" />
          </button>
          <span
            v-if="message"
            role="status"
            class="muted"
          >{{ message }}</span>
        </div>
      </form>
      <form
        v-if="loaded"
        class="form-card identity-card"
        data-test="identity-form"
        @submit.prevent="saveIdentity"
      >
        <fieldset>
          <legend>Mes coordonnées</legend>
          <p class="hint">
            Pour l'en-tête de tes lettres et de ton CV (0.5). Gardées dans ta base locale, jamais envoyées à l'IA.
          </p>
          <div class="form-grid">
            <label class="wide">Nom et prénom
              <input
                v-model="identity.name"
                type="text"
                autocomplete="name"
                data-test="identity-name"
              >
            </label>
            <label class="wide">Adresse
              <textarea
                v-model="identity.address"
                rows="2"
                autocomplete="street-address"
                placeholder="Rue et numéro&#10;NPA localité"
              />
            </label>
            <label>Téléphone
              <input
                v-model="identity.phone"
                type="tel"
                autocomplete="tel"
              >
            </label>
            <label>E-mail
              <input
                v-model="identity.email"
                type="email"
                autocomplete="email"
              >
            </label>
          </div>
        </fieldset>
        <div class="form-actions">
          <button
            type="submit"
            class="primary"
            data-test="save-identity"
          >
            Enregistrer mes coordonnées <AppIcon name="chevron" />
          </button>
          <span
            v-if="identityMessage"
            role="status"
            class="muted"
          >{{ identityMessage }}</span>
        </div>
      </form>
    </div>
  </section>
</template>
