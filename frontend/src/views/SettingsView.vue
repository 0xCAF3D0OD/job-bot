<script setup lang="ts">
import { nextTick, onMounted, ref } from "vue";

import { api, type SettingsModel } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import PageHero from "../components/PageHero.vue";
import NewsSourcesPanel from "../components/NewsSourcesPanel.vue";
import ProfilesPanel from "../components/ProfilesPanel.vue";
import SessionPanel from "../components/SessionPanel.vue";
import SitesPanel from "../components/SitesPanel.vue";
import StatusPanel from "../components/StatusPanel.vue";

const form = ref<SettingsModel>({
  orp_monthly_target: null,
  notify_score_threshold: 70,
  llm_monthly_budget_chf: 10,
  orp_due_day: 5,
  employer_search_threshold: 70,
});
const loaded = ref(false);
const saving = ref(false);
const message = ref("");
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
  // Arrivée par /etat (ancienne page) : la section est plus bas, sous le formulaire.
  if (window.location.hash === "#etat") {
    await nextTick();
    document.getElementById("etat")?.scrollIntoView();
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
// Sommaire (docs/19 §4) : les sections dans l'ordre de la page.
const SECTIONS = [
  { id: "recherche", label: "Recherche d'emploi" },
  { id: "actualites", label: "Actualités" },
  { id: "notifications", label: "Notifications" },
  { id: "ia", label: "IA" },
  { id: "profils", label: "Profils d'essai" },
  { id: "connexion", label: "Connexion" },
  { id: "etat", label: "État technique" },
];
</script>

<template>
  <PageHero
    eyebrow="Réglages"
    title="Tes réglages"
    subtitle="Ce que tu peux régler."
  />
  <section class="band">
    <div class="settings-layout">
      <nav
        class="settings-toc"
        aria-label="Sections des réglages"
      >
        <a
          v-for="section in SECTIONS"
          :key="section.id"
          :href="`#${section.id}`"
        >{{ section.label }}</a>
      </nav>
      <div class="settings-sections">
        <h2
          id="recherche"
          class="section-title"
        >
          Recherche d'emploi
        </h2>
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
            <legend><label for="due-day">Date limite de remise des preuves</label></legend>
            <p class="hint">
              Jour du mois suivant où ton conseiller attend les preuves (souvent le 5).
            </p>
            <div class="inline-field">
              <span>le</span>
              <input
                id="due-day"
                v-model.number="form.orp_due_day"
                type="number"
                min="2"
                max="28"
                required
                data-test="due-day"
              >
              <span>du mois suivant</span>
            </div>
          </fieldset>
          <fieldset>
            <legend><label for="threshold">Seuil de notification des offres</label></legend>
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
          <fieldset>
            <legend><label for="employer-threshold">Recherche de l'annonce chez l'employeur</label></legend>
            <p class="hint">
              Dès cette note, l'annonce est cherchée automatiquement chez l'employeur (≈ 0,02 $ si l'IA est nécessaire).
            </p>
            <div class="inline-field">
              <input
                id="employer-threshold"
                v-model.number="form.employer_search_threshold"
                type="number"
                min="0"
                max="100"
                required
              >
              <span>/ 100</span>
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
        <SitesPanel class="settings-status" />

        <h2
          id="actualites"
          class="section-title"
        >
          Actualités
        </h2>
        <NewsSourcesPanel />

        <h2
          id="notifications"
          class="section-title"
        >
          Notifications
        </h2>
        <div
          v-if="loaded"
          class="form-card"
        >
          <fieldset data-test="notifications">
            <legend>Notifications</legend>
            <template v-if="notifications?.configured">
              <p class="hint">
                Sur ton téléphone ({{ notifications.server }}) : offres bien notées, et IA à 80 % du plafond.
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
              Impossible de vérifier pour l'instant : la plateforme ne répond pas. Réessaie dans un moment.
            </p>
            <p
              v-else
              class="hint"
            >
              Non configurées (application ntfy sur ton téléphone ; réglage d'installation, voir le README).
            </p>
          </fieldset>
        </div>

        <h2
          id="ia"
          class="section-title"
        >
          IA
        </h2>
        <form
          v-if="loaded"
          class="form-card"
          data-test="budget-form"
          @submit.prevent="save"
        >
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
              data-test="save-budget"
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

        <h2
          id="profils"
          class="section-title"
        >
          Profils d'essai
        </h2>
        <ProfilesPanel />

        <h2
          id="connexion"
          class="section-title"
        >
          Connexion
        </h2>
        <SessionPanel />

        <h2
          id="etat"
          class="section-title"
        >
          État technique
        </h2>
        <StatusPanel />
      </div>
    </div>
  </section>
</template>
