<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { api, type SettingsModel } from "../api/client";
import { useAuth } from "../composables/useAuth";
import HelpTip from "../components/HelpTip.vue";
import PageHero from "../components/PageHero.vue";
import AgendaPanel from "../components/AgendaPanel.vue";
import ExtensionPanel from "../components/ExtensionPanel.vue";
import NewsSourcesPanel from "../components/NewsSourcesPanel.vue";
import ProfilesPanel from "../components/ProfilesPanel.vue";
import SessionPanel from "../components/SessionPanel.vue";
import SettingsSection from "../components/SettingsSection.vue";
import SitesPanel from "../components/SitesPanel.vue";

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
  // Ancien lien vers l'état technique : il a maintenant sa page (docs/21 §6).
  if (window.location.hash === "#etat") {
    await router.replace("/reglages/diagnostic");
    return;
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
const router = useRouter();
const { me } = useAuth();
// Résumés des sections, affichés sur téléphone (docs/34 §3).
const summary = computed(() => ({
  recherche: [
    form.value.orp_monthly_target ? `objectif ${form.value.orp_monthly_target} / mois` : "objectif à saisir",
    `alerte dès ${form.value.notify_score_threshold}`,
  ].join(" · "),
  actualites: "mots-clés et sources",
  notifications: notifications.value ? (notifications.value.configured ? "actives" : "non configurées") : "",
  ia: `plafond ${form.value.llm_monthly_budget_chf} CHF / mois`,
  profils: "profils fictifs",
  connexion: me.value?.auth_enabled ? (me.value.username ?? "") : "désactivée",
  extension: "jetons",
  agenda: "abonnement",
}));

// Sommaire (docs/19 §4) : les sections dans l'ordre de la page.
const SECTIONS = [
  { id: "recherche", label: "Recherche d'emploi" },
  { id: "actualites", label: "Actualités" },
  { id: "notifications", label: "Notifications" },
  { id: "ia", label: "IA" },
  { id: "profils", label: "Profils d'essai" },
  { id: "connexion", label: "Connexion" },
  { id: "agenda", label: "Agenda" },
  { id: "extension", label: "Extension" },
];
</script>

<template>
  <PageHero
    title="Tes réglages"
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
        <SettingsSection
          id="recherche"
          title="Recherche d'emploi"
          :value="summary.recherche"
        >
          <form
            v-if="loaded"
            class="form-card settings-numbers"
            data-test="settings-form"
            @submit.prevent="save"
          >
            <fieldset>
              <legend>
                <label for="orp">Objectif mensuel de l'ORP</label>
                <HelpTip
                  text="Le nombre de candidatures demandé par ton conseiller. Laisse vide si tu ne le connais pas encore."
                  label="Aide : objectif de l'ORP"
                />
              </legend>
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
              <legend>
                <label for="due-day">Date limite de remise des preuves</label>
                <HelpTip
                  text="Le jour du mois suivant où ton conseiller attend les preuves, souvent le 5."
                  label="Aide : date limite"
                />
              </legend>
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
              <legend>
                <label for="threshold">Seuil de notification des offres</label>
                <HelpTip
                  text="Tu es prévenu des nouvelles offres notées au moins à ce score."
                  label="Aide : seuil de notification"
                />
              </legend>
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
              <legend>
                <label for="employer-threshold">Recherche de l'annonce chez l'employeur</label>
                <HelpTip
                  text="Dès cette note, l'annonce est cherchée automatiquement chez l'employeur (environ 0,02 $ si l'IA est nécessaire)."
                  label="Aide : recherche chez l'employeur"
                />
              </legend>
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
                class="secondary"
                :disabled="saving"
                data-test="save-settings"
              >
                Enregistrer
              </button>
              <span
                v-if="message"
                role="status"
                class="muted"
              >{{ message }}</span>
            </div>
          </form>
          <SitesPanel class="settings-status" />
        </SettingsSection>

        <SettingsSection
          id="actualites"
          title="Actualités"
          :value="summary.actualites"
        >
          <NewsSourcesPanel />
        </SettingsSection>

        <SettingsSection
          id="notifications"
          title="Notifications"
          :value="summary.notifications"
        >
          <div
            v-if="loaded"
            class="form-card"
          >
            <fieldset data-test="notifications">
              <legend>
                Notifications
                <HelpTip
                  v-if="notifications?.configured"
                  :text="`Envoyées sur ton téléphone (${notifications.server}) : offres bien notées, et IA à 80 % du plafond.`"
                  label="Aide : notifications"
                />
              </legend>
              <template v-if="notifications?.configured">
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
        </SettingsSection>

        <SettingsSection
          id="ia"
          title="IA"
          :value="summary.ia"
        >
          <form
            v-if="loaded"
            class="form-card"
            data-test="budget-form"
            @submit.prevent="save"
          >
            <fieldset>
              <legend>
                <label for="budget">Plafond mensuel du coût de l'IA</label>
                <HelpTip
                  text="Au-delà, les offres ne sont plus notées jusqu'au mois suivant."
                  label="Aide : plafond de l'IA"
                />
              </legend>
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
                class="secondary"
                :disabled="saving"
                data-test="save-budget"
              >
                Enregistrer
              </button>
              <span
                v-if="message"
                role="status"
                class="muted"
              >{{ message }}</span>
            </div>
          </form>
        </SettingsSection>

        <SettingsSection
          id="profils"
          title="Profils d'essai"
          :value="summary.profils"
        >
          <ProfilesPanel />
        </SettingsSection>

        <SettingsSection
          id="connexion"
          title="Connexion"
          :value="summary.connexion"
        >
          <SessionPanel />
        </SettingsSection>

        <SettingsSection
          id="agenda"
          title="Agenda"
          :value="summary.agenda"
        >
          <AgendaPanel />
        </SettingsSection>

        <SettingsSection
          id="extension"
          title="Extension du navigateur"
          :value="summary.extension"
        >
          <ExtensionPanel />
        </SettingsSection>

        <p class="diagnostic-link">
          <RouterLink
            to="/reglages/diagnostic"
            data-test="diagnostic-link"
          >
            Diagnostic technique (collecte, IA, tâches) →
          </RouterLink>
        </p>
      </div>
    </div>
  </section>
</template>
