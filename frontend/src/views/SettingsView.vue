<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api, type SettingsModel } from "../api/client";
import { useAuth } from "../composables/useAuth";
import PageHero from "../components/PageHero.vue";
import AgendaPanel from "../components/AgendaPanel.vue";
import ExtensionPanel from "../components/ExtensionPanel.vue";
import NewsSourcesPanel from "../components/NewsSourcesPanel.vue";
import ProfilesPanel from "../components/ProfilesPanel.vue";
import SessionPanel from "../components/SessionPanel.vue";
import SettingsSection from "../components/SettingsSection.vue";
import SitesPanel from "../components/SitesPanel.vue";

import HoverNote from "../components/HoverNote.vue";
import AiSpend from "../components/AiSpend.vue";
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
  // Anciens liens « /reglages#agenda » (docs/48 §5) : la rubrique qui contient la section.
  const old = route.hash.slice(1);
  if (old && OLD_ANCHORS[old] && !route.query.rubrique) {
    await router.replace({ query: { rubrique: OLD_ANCHORS[old] }, hash: route.hash });
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
// Résumés des rubriques, affichés sur téléphone (docs/34 §3).
const summary = computed(() => ({
  recherche: [
    form.value.orp_monthly_target ? `objectif ${form.value.orp_monthly_target} / mois` : "objectif à saisir",
    "sites suivis",
  ].join(" · "),
  actualites: "mots-clés et sources",
  notifications: [
    notifications.value ? (notifications.value.configured ? "actives" : "non configurées") : "",
    `dès ${form.value.notify_score_threshold} / 100`,
  ]
    .filter(Boolean)
    .join(" · "),
  ia: `plafond ${form.value.llm_monthly_budget_chf} CHF / mois`,
  compte: me.value?.auth_enabled ? `profils d'essai · ${me.value.username ?? ""}` : "profils d'essai",
  outils: "agenda, extension",
}));

// Une rubrique à la fois (docs/48 §2) : le sommaire choisit, l'adresse la retient.
const SECTIONS = [
  { id: "recherche", label: "Recherche d'emploi" },
  { id: "actualites", label: "Actualités" },
  { id: "notifications", label: "Notifications" },
  { id: "ia", label: "IA" },
  { id: "compte", label: "Compte" },
  { id: "outils", label: "Outils" },
] as const;
type SectionId = (typeof SECTIONS)[number]["id"];
const OLD_ANCHORS: Record<string, SectionId> = {
  recherche: "recherche",
  actualites: "actualites",
  notifications: "notifications",
  ia: "ia",
  profils: "compte",
  connexion: "compte",
  agenda: "outils",
  extension: "outils",
};
const route = useRoute();
const active = computed<SectionId>(() => {
  const wanted = route.query.rubrique;
  return SECTIONS.find((s) => s.id === wanted)?.id ?? OLD_ANCHORS[route.hash.slice(1)] ?? "recherche";
});
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
        <RouterLink
          v-for="section in SECTIONS"
          :key="section.id"
          :to="{ query: { rubrique: section.id } }"
          :class="{ active: active === section.id }"
          :aria-current="active === section.id ? 'page' : undefined"
          :data-test="`toc-${section.id}`"
        >
          {{ section.label }}
        </RouterLink>
      </nav>
      <div class="settings-sections">
        <SettingsSection
          id="recherche"
          title="Recherche d'emploi"
          :value="summary.recherche"
          :active="active === 'recherche'"
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
            <fieldset class="wide">
              <legend>
                <label for="employer-threshold">
                  <HoverNote text="Dès cette note, l'annonce est cherchée automatiquement chez l'employeur, pour postuler sans passer par un site d'emploi (environ 0,02 $ si l'IA est nécessaire).">
                    Chercher l'annonce chez l'employeur à partir de
                  </HoverNote>
                </label>
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
          :active="active === 'actualites'"
        >
          <NewsSourcesPanel />
        </SettingsSection>

        <SettingsSection
          id="notifications"
          title="Notifications"
          :value="summary.notifications"
          :active="active === 'notifications'"
        >
          <form
            v-if="loaded"
            class="form-card"
            data-test="notify-form"
            @submit.prevent="save"
          >
            <fieldset>
              <legend>
                <label for="threshold">M'avertir d'une offre à partir de</label>
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
            <div class="form-actions">
              <button
                type="submit"
                class="secondary"
                :disabled="saving"
                data-test="save-notify"
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
          <div
            v-if="loaded"
            class="form-card"
          >
            <fieldset data-test="notifications">
              <legend>
                Notifications
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
          :active="active === 'ia'"
        >
          <div class="ai-layout">
            <form
              v-if="loaded"
              class="form-card"
              data-test="budget-form"
              @submit.prevent="save"
            >
              <fieldset>
                <legend>
                  <label for="budget">
                    <HoverNote text="Au-delà, les offres ne sont plus notées jusqu'au mois suivant.">
                      Plafond mensuel du coût de l'IA
                    </HoverNote>
                  </label>
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
            <AiSpend />
          </div>
        </SettingsSection>

        <SettingsSection
          id="compte"
          title="Compte"
          :value="summary.compte"
          :active="active === 'compte'"
        >
          <h3 class="settings-subtitle">
            Profils d'essai
          </h3>
          <ProfilesPanel />
          <h3 class="settings-subtitle">
            Connexion
          </h3>
          <SessionPanel />
        </SettingsSection>

        <SettingsSection
          id="outils"
          title="Outils"
          :value="summary.outils"
          :active="active === 'outils'"
        >
          <!-- Chaque outil a déjà son titre dans sa carte. -->
          <AgendaPanel />
          <ExtensionPanel class="settings-next-card" />
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
