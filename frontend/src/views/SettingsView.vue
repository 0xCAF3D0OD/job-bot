<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api, type SettingsModel } from "../api/client";
import { plural } from "../format";
import { useAuth } from "../composables/useAuth";
import PageHero from "../components/PageHero.vue";
import AccountDataPanel from "../components/AccountDataPanel.vue";
import AgendaPanel from "../components/AgendaPanel.vue";
import ExtensionPanel from "../components/ExtensionPanel.vue";
import NewsSourcesPanel from "../components/NewsSourcesPanel.vue";
import PlatformPanel from "../components/PlatformPanel.vue";
import ProfilesPanel from "../components/ProfilesPanel.vue";
import SessionPanel from "../components/SessionPanel.vue";
import AppIcon from "../components/AppIcon.vue";
import SettingsSection, { SETTINGS_ICONS } from "../components/SettingsSection.vue";
import SitesPanel from "../components/SitesPanel.vue";

import HoverNote from "../components/HoverNote.vue";
import AiSpend from "../components/AiSpend.vue";
const form = ref<SettingsModel>({
  orp_monthly_target: null,
  notify_score_threshold: 70,
  llm_monthly_budget_chf: 10,
  orp_due_day: 5,
  employer_search_threshold: 70,
  rhythm_days: [0, 1, 2, 3, 4],
  offers_notify_mode: "daily",
  offers_notify_hour: 9,
  rhythm_pause_from: null,
  rhythm_pause_until: null,
});
// Le bon rythme (docs/86) : tes jours de recherche, lundi = 0.
const WEEK = [
  { value: 0, label: "Lundi" },
  { value: 1, label: "Mardi" },
  { value: 2, label: "Mercredi" },
  { value: 3, label: "Jeudi" },
  { value: 4, label: "Vendredi" },
  { value: 5, label: "Samedi" },
  { value: 6, label: "Dimanche" },
];
const HOURS = Array.from({ length: 16 }, (_, i) => i + 6);
const loaded = ref(false);
const saving = ref(false);
const message = ref("");
const notifications = ref<{ configured: boolean; server: string; personal?: boolean; topic?: string | null } | null>(
  null,
);
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

// Compte invité (docs/65 §4) : ses alertes sur son téléphone, avec un sujet ntfy à lui.
async function setPhone(enabled: boolean): Promise<void> {
  const { data } = await api.PUT("/api/notifications/phone", { body: { enabled } });
  if (data) notifications.value = data;
  testMessage.value = "";
}

async function endPause(): Promise<void> {
  form.value.rhythm_pause_from = null;
  form.value.rhythm_pause_until = null;
  await save();
}

async function save(): Promise<void> {
  saving.value = true;
  try {
    const body = {
      ...form.value,
      orp_monthly_target: form.value.orp_monthly_target || null,
      rhythm_pause_from: form.value.rhythm_pause_from || null,
      rhythm_pause_until: form.value.rhythm_pause_until || null,
    };
    const { data } = await api.PUT("/api/settings", { body });
    message.value = data ? "Réglages enregistrés." : "L'enregistrement a échoué : vérifie les valeurs.";
    if (data) form.value = data;
  } catch {
    message.value = "API injoignable.";
  } finally {
    saving.value = false;
  }
}
// Un réglage d'un seul champ s'enregistre au changement (docs/106 §5) : « Enregistré » une
// seconde à côté, ou l'erreur à sa place.
const savedField = ref<string | null>(null);
const fieldError = ref<{ field: string; text: string } | null>(null);
let savedTimer: ReturnType<typeof setTimeout> | null = null;
async function autosave(field: string): Promise<void> {
  await save();
  const ok = message.value === "Réglages enregistrés.";
  fieldError.value = ok ? null : { field, text: message.value };
  message.value = "";
  if (savedTimer) clearTimeout(savedTimer);
  savedField.value = ok ? field : null;
  if (ok) savedTimer = setTimeout(() => (savedField.value = null), 1500);
}
// Le seuil des notifications en cinq pastilles (docs/106, décision 2) ; une valeur d'avant,
// hors des cinq, reste proposée.
const THRESHOLDS = [50, 60, 70, 80, 90];
const thresholdChoices = computed(() => {
  const current = form.value.notify_score_threshold;
  return typeof current === "number" && !THRESHOLDS.includes(current)
    ? [...THRESHOLDS, current].sort((a, b) => a - b)
    : THRESHOLDS;
});
async function setThreshold(value: number): Promise<void> {
  form.value.notify_score_threshold = value;
  await autosave("threshold");
}
const router = useRouter();
const { me } = useAuth();
// L'exploitant (docs/65) : la rubrique Plateforme, son plafond de l'IA, les profils d'essai.
const owner = computed(() => Boolean(me.value?.is_owner));
// Résumés des rubriques, affichés sur téléphone (docs/34 §3).
const summary = computed(() => ({
  recherche: [
    form.value.orp_monthly_target ? `objectif ${form.value.orp_monthly_target} / mois` : "objectif à saisir",
    "sites suivis",
  ].join(" · "),
  rythme: [
    plural(form.value.rhythm_days?.length ?? 5, "jour de recherche", "jours de recherche"),
    form.value.offers_notify_mode === "daily" ? `offres à ${form.value.offers_notify_hour} h` : "offres dès qu'elles arrivent",
    form.value.rhythm_pause_until ? "en pause" : "",
  ]
    .filter(Boolean)
    .join(" · "),
  actualites: "mots-clés et sources",
  notifications: [
    notifications.value ? (notifications.value.configured ? "actives" : "non configurées") : "",
    `dès ${form.value.notify_score_threshold} / 100`,
  ]
    .filter(Boolean)
    .join(" · "),
  ia: `plafond ${form.value.llm_monthly_budget_chf} CHF / mois`,
  compte: [owner.value ? "profils d'essai" : "connexion", me.value?.auth_enabled ? (me.value.username ?? "") : ""]
    .filter(Boolean)
    .join(" · "),
  outils: "agenda, extension",
  plateforme: "comptes et IA de la plateforme",
}));

// Une rubrique à la fois (docs/48 §2) : le sommaire choisit, l'adresse la retient.
const SECTIONS = [
  { id: "recherche", label: "Recherche d'emploi" },
  { id: "rythme", label: "Rythme" },
  { id: "actualites", label: "Actualités" },
  { id: "notifications", label: "Notifications" },
  { id: "ia", label: "IA" },
  { id: "compte", label: "Compte" },
  { id: "outils", label: "Outils" },
  { id: "plateforme", label: "Plateforme" },
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
const sections = computed(() => SECTIONS.filter((s) => s.id !== "plateforme" || owner.value));
const active = computed<SectionId>(() => {
  const wanted = route.query.rubrique;
  return sections.value.find((s) => s.id === wanted)?.id ?? OLD_ANCHORS[route.hash.slice(1)] ?? "recherche";
});
</script>

<template>
  <PageHero
    title="Réglages"
  />
  <section class="band">
    <div class="settings-layout">
      <nav
        class="settings-toc"
        aria-label="Sections des réglages"
      >
        <RouterLink
          v-for="section in sections"
          :key="section.id"
          :to="{ query: { rubrique: section.id } }"
          :class="{ active: active === section.id }"
          :aria-current="active === section.id ? 'page' : undefined"
          :data-test="`toc-${section.id}`"
        >
          <span class="with-icon">
            <AppIcon
              v-if="SETTINGS_ICONS[section.id]"
              :name="SETTINGS_ICONS[section.id]!"
            />{{ section.label }}
          </span>
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
                  inputmode="numeric"
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
                  inputmode="numeric"
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
                  inputmode="numeric"
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
          id="rythme"
          title="Rythme"
          :value="summary.rythme"
          :active="active === 'rythme'"
        >
          <form
            v-if="loaded"
            class="form-card rhythm-form"
            data-test="rhythm-form"
            @submit.prevent="save"
          >
            <fieldset>
              <legend>
                <HoverNote text="Les autres jours, rien n'arrive sur ton téléphone, sauf les rappels avec une date limite.">
                  Jours de recherche
                </HoverNote>
              </legend>
              <div class="rhythm-week">
                <label
                  v-for="day in WEEK"
                  :key="day.value"
                  class="check"
                >
                  <input
                    v-model="form.rhythm_days"
                    type="checkbox"
                    :value="day.value"
                    :disabled="form.rhythm_days?.length === 1 && form.rhythm_days.includes(day.value)"
                    :data-test="`rhythm-day-${day.value}`"
                  >
                  {{ day.label }}
                </label>
              </div>
            </fieldset>
            <fieldset data-test="rhythm-pause">
              <legend>
                <HoverNote text="Vacances, maladie : ni meilleures offres ni message d'offres, et pas de retard au retour.">
                  Une pause
                </HoverNote>
              </legend>
              <div class="rhythm-pause">
                <label>
                  Du
                  <input
                    v-model="form.rhythm_pause_from"
                    type="date"
                    data-test="pause-from"
                  >
                </label>
                <label>
                  Au
                  <input
                    v-model="form.rhythm_pause_until"
                    type="date"
                    :min="form.rhythm_pause_from ?? undefined"
                    data-test="pause-until"
                  >
                </label>
                <button
                  v-if="form.rhythm_pause_from"
                  type="button"
                  class="link"
                  data-test="pause-end"
                  @click="endPause"
                >
                  Terminer la pause
                </button>
              </div>
              <p class="hint">
                Annonce-la à ton conseiller : c'est lui qui décide de ce qu'elle change pour ton objectif.
              </p>
            </fieldset>
            <fieldset>
              <legend>Les offres bien notées</legend>
              <label class="check">
                <input
                  v-model="form.offers_notify_mode"
                  type="radio"
                  value="daily"
                  data-test="rhythm-daily"
                >
                Un message par jour, à
                <select
                  v-model.number="form.offers_notify_hour"
                  aria-label="Heure du message"
                  :disabled="form.offers_notify_mode !== 'daily'"
                  data-test="rhythm-hour"
                >
                  <option
                    v-for="hour in HOURS"
                    :key="hour"
                    :value="hour"
                  >
                    {{ hour }} h
                  </option>
                </select>
              </label>
              <label class="check">
                <input
                  v-model="form.offers_notify_mode"
                  type="radio"
                  value="instant"
                  data-test="rhythm-instant"
                >
                Dès qu'elles arrivent
              </label>
            </fieldset>
            <div class="form-actions">
              <button
                type="submit"
                class="primary"
                :disabled="saving"
                data-test="save-rhythm"
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
          <div
            v-if="loaded"
            class="form-card"
            data-test="notify-form"
          >
            <fieldset>
              <legend id="threshold-label">
                M'avertir d'une offre à partir de
              </legend>
              <div
                class="score-choices"
                role="radiogroup"
                aria-labelledby="threshold-label"
              >
                <button
                  v-for="value in thresholdChoices"
                  :key="value"
                  type="button"
                  role="radio"
                  :aria-checked="form.notify_score_threshold === value"
                  :class="['chip', { on: form.notify_score_threshold === value }]"
                  :data-test="`threshold-${value}`"
                  @click="setThreshold(value)"
                >
                  {{ value }}
                </button>
                <span class="muted">/ 100</span>
                <span
                  v-if="savedField === 'threshold'"
                  class="saved-flash"
                  role="status"
                  data-test="threshold-saved"
                >Enregistré</span>
                <span
                  v-if="fieldError?.field === 'threshold'"
                  class="field-error"
                  role="alert"
                >{{ fieldError.text }}</span>
              </div>
            </fieldset>
          </div>
          <div
            v-if="loaded"
            class="form-card"
          >
            <fieldset data-test="notifications">
              <legend>
                Téléphone
              </legend>
              <template v-if="notifications?.personal">
                <template v-if="notifications.configured">
                  <p data-test="phone-on">
                    Tes alertes arrivent sur ton téléphone. Dans l'application ntfy, abonne-toi au sujet
                    <code>{{ notifications.topic }}</code> sur le serveur {{ notifications.server }}.
                  </p>
                  <div class="settings-line">
                    <strong>Notification de test</strong>
                    <span class="inline-field">
                      <span
                        v-if="testMessage"
                        role="status"
                      >{{ testMessage }}</span>
                      <button
                        type="button"
                        class="link"
                        data-test="phone-off"
                        @click="setPhone(false)"
                      >
                        Arrêter
                      </button>
                      <button
                        type="button"
                        class="secondary small"
                        :disabled="testing"
                        data-test="test-notification"
                        @click="sendTest"
                      >
                        Envoyer
                      </button>
                    </span>
                  </div>
                </template>
                <template v-else>
                  <p class="hint">
                    Les offres bien notées, les relances et le rappel ORP, avec l'application gratuite ntfy.
                  </p>
                  <button
                    type="button"
                    class="secondary small"
                    data-test="phone-on-button"
                    @click="setPhone(true)"
                  >
                    Recevoir sur mon téléphone
                  </button>
                </template>
              </template>
              <template v-else-if="notifications?.configured">
                <div class="settings-line">
                  <strong>Notification de test</strong>
                  <span class="inline-field">
                    <span
                      v-if="testMessage"
                      role="status"
                    >{{ testMessage }}</span>
                    <button
                      type="button"
                      class="secondary small"
                      :disabled="testing"
                      data-test="test-notification"
                      @click="sendTest"
                    >
                      Envoyer
                    </button>
                  </span>
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
                Non configurées : réglage d'installation, voir le README.
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
            <div
              v-if="loaded && !owner"
              class="form-card"
              data-test="budget-fixed"
            >
              <fieldset>
                <legend>Plafond mensuel du coût de l'IA</legend>
                <p>
                  <strong>{{ form.llm_monthly_budget_chf }} CHF</strong> par mois, fixé par l'exploitant de la plateforme.
                </p>
                <p class="hint">
                  Au-delà, les offres ne sont plus notées jusqu'au mois suivant.
                </p>
              </fieldset>
            </div>
            <form
              v-else-if="loaded"
              class="form-card"
              data-test="budget-form"
              @submit.prevent="autosave('budget')"
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
                    inputmode="decimal"
                    required
                    @change="autosave('budget')"
                  >
                  <span>CHF</span>
                  <span
                    v-if="savedField === 'budget'"
                    class="saved-flash"
                    role="status"
                    data-test="budget-saved"
                  >Enregistré</span>
                  <span
                    v-if="fieldError?.field === 'budget'"
                    class="field-error"
                    role="alert"
                  >{{ fieldError.text }}</span>
                </div>
              </fieldset>
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
          <!-- Chaque panneau porte son titre (Profils d'essai, Connexion, Données personnelles) :
               pas de second titre au-dessus (docs/108, 0.77.2). -->
          <ProfilesPanel v-if="owner" />
          <SessionPanel />
          <AccountDataPanel class="settings-next-card" />
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

        <SettingsSection
          v-if="owner"
          id="plateforme"
          title="Plateforme"
          :value="summary.plateforme"
          :active="active === 'plateforme'"
        >
          <PlatformPanel />
        </SettingsSection>

        <!-- Le Diagnostic technique, à l'exploitant seulement (docs/108 §3). -->
        <p
          v-if="owner || me?.auth_enabled === false"
          class="diagnostic-link"
        >
          <RouterLink
            to="/reglages/diagnostic"
            data-test="diagnostic-link"
          >
            <span class="with-icon">Diagnostic technique (collecte, IA, tâches)<AppIcon name="arrow-right" /></span>
          </RouterLink>
        </p>
      </div>
    </div>
  </section>
</template>
