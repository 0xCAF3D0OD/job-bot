<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { api, type SettingsModel } from "../api/client";
import { useAuth } from "../composables/useAuth";
import ConnectionsPanel from "../components/ConnectionsPanel.vue";
import GetemallPanel from "../components/GetemallPanel.vue";
import PageHero from "../components/PageHero.vue";
import PlanPanel from "../components/PlanPanel.vue";
import { usePhone } from "../composables/usePhone";
import { usePlan } from "../composables/usePlan";
import { usePageReady } from "../composables/usePageTransition";
import AccountDataPanel from "../components/AccountDataPanel.vue";
import AgendaPanel from "../components/AgendaPanel.vue";
import ExtensionPanel from "../components/ExtensionPanel.vue";
import PlatformPanel from "../components/PlatformPanel.vue";
import ProfilesPanel from "../components/ProfilesPanel.vue";
import SessionPanel from "../components/SessionPanel.vue";
import AppIcon from "../components/AppIcon.vue";
import DateField from "../components/DateField.vue";
import BusyButton from "../components/BusyButton.vue";
import SettingsSection from "../components/SettingsSection.vue";
import SegmentedControl from "../components/SegmentedControl.vue";
import AppearancePanel from "../components/AppearancePanel.vue";
import SettingCard from "../components/SettingCard.vue";
import SettingRow from "../components/SettingRow.vue";
import SitesPanel from "../components/SitesPanel.vue";

import AiSpend from "../components/AiSpend.vue";
import FaceState from "../components/FaceState.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";

const DEFAULTS: SettingsModel = {
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
  notify_offers: true,
  notify_follow_ups: true,
  notify_orp: true,
  notify_news: false,
};
// La saisie (`form`) et la dernière valeur enregistrée (`stored`, 1.6.66) : une valeur refusée reste
// dans le champ pour la corriger, l'ancienne reste enregistrée.
const form = ref<SettingsModel>({ ...DEFAULTS });
const stored = ref<SettingsModel>({ ...DEFAULTS });
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
usePageReady("settings", () => loaded.value);
const notifications = ref<{ configured: boolean; server: string; personal?: boolean; topic?: string | null } | null>(
  null,
);
// Vrai si l'API n'a pas répondu (arrêtée, ou plus ancienne que l'interface).
const notificationsUnknown = ref(false);
const testMessage = ref("");
const testing = ref(false);

async function sendTest(): Promise<void> {
  if (testing.value) return;
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
  if (data) {
    form.value = { ...DEFAULTS, ...data };
    stored.value = { ...data };
  }
  loaded.value = true;
  try {
    const status = await api.GET("/api/notifications");
    notifications.value = status.data ?? null;
    notificationsUnknown.value = !status.data;
  } catch {
    notificationsUnknown.value = true;
  }
});

// Compte invité (docs/65 §4) : ses alertes sur son téléphone, avec un sujet ntfy à lui.
const phoneSavedAt = ref(0);
async function setPhone(enabled: boolean): Promise<void> {
  const { data } = await api.PUT("/api/notifications/phone", { body: { enabled } });
  if (data) {
    notifications.value = data;
    phoneSavedAt.value = Date.now();
  }
  testMessage.value = "";
}

// L'enregistrement réglage par réglage (1.6.66, planche « 5. Réglages ») : un interrupteur ou un choix
// s'applique tout de suite ; un champ chiffré quand on le quitte. « Enregistré » s'affiche sur la ligne
// (message d'état, WCAG 4.1.3) ; une erreur sous le champ (WCAG 3.3.1).
const savedRow = ref<string | null>(null);
const rowErrors = ref<Record<string, string>>({});
let savedTimer: ReturnType<typeof setTimeout> | null = null;

function clearError(row: string): void {
  rowErrors.value = Object.fromEntries(Object.entries(rowErrors.value).filter(([key]) => key !== row));
}

function refusal(error: unknown): string {
  const detail = (error as { detail?: unknown } | undefined)?.detail;
  if (typeof detail === "string") return `${detail.charAt(0).toUpperCase()}${detail.slice(1)}.`;
  return "Refusé : vérifie la valeur.";
}

async function persist(row: string, patch: Partial<SettingsModel>): Promise<boolean> {
  const body = { ...stored.value, ...patch };
  body.orp_monthly_target = body.orp_monthly_target || null;
  body.rhythm_pause_from = body.rhythm_pause_from || null;
  body.rhythm_pause_until = body.rhythm_pause_until || null;
  if (savedTimer) clearTimeout(savedTimer);
  savedRow.value = null;
  try {
    const { data, error } = await api.PUT("/api/settings", { body });
    if (!data) {
      // Dans la démo, la bulle « rien n'est enregistré » le dit déjà : pas d'erreur sous le champ.
      if (!me.value?.demo) rowErrors.value = { ...rowErrors.value, [row]: refusal(error) };
      return false;
    }
    stored.value = { ...data };
    for (const key of Object.keys(patch) as (keyof SettingsModel)[]) (form.value as Record<string, unknown>)[key] = data[key];
    clearError(row);
    savedRow.value = row;
    savedTimer = setTimeout(() => (savedRow.value = null), 3000);
    return true;
  } catch {
    rowErrors.value = { ...rowErrors.value, [row]: "API injoignable." };
    return false;
  }
}

// Les champs chiffrés et leur règle : une valeur impossible n'est pas envoyée, l'ancienne reste.
type NumberKey = "orp_monthly_target" | "orp_due_day" | "employer_search_threshold" | "llm_monthly_budget_chf";
const RULES: Record<NumberKey, { row: string; min: number; max: number; text: string; optional?: boolean; decimal?: boolean }> = {
  orp_monthly_target: { row: "orp", min: 1, max: 100, text: "Entre 1 et 100.", optional: true },
  orp_due_day: { row: "due", min: 2, max: 28, text: "Entre 2 et 28." },
  employer_search_threshold: { row: "employer", min: 0, max: 100, text: "Entre 0 et 100." },
  llm_monthly_budget_chf: { row: "budget", min: 0, max: 1000, text: "Entre 0 et 1000 CHF.", decimal: true },
};
async function saveNumber(key: NumberKey): Promise<void> {
  const rule = RULES[key];
  const value = form.value[key] as number | string | null;
  const empty = value === null || value === "";
  if (empty && rule.optional) {
    if (stored.value[key] !== null) await persist(rule.row, { [key]: null });
    return;
  }
  const fine = typeof value === "number" && value >= rule.min && value <= rule.max && (rule.decimal || Number.isInteger(value));
  if (!fine) {
    const old = stored.value[key];
    savedRow.value = null;
    rowErrors.value = {
      ...rowErrors.value,
      [rule.row]: `${rule.text} ${old === null || old === undefined ? "Rien n'est enregistré." : `Le ${old} reste enregistré.`}`,
    };
    return;
  }
  if (value === stored.value[key]) {
    clearError(rule.row);
    return;
  }
  await persist(rule.row, { [key]: value });
}

async function saveDays(): Promise<void> {
  await persist("days", { rhythm_days: [...(form.value.rhythm_days ?? [])].sort() });
}
async function savePause(): Promise<void> {
  const { rhythm_pause_from: from, rhythm_pause_until: until } = form.value;
  if (from && until && until < from) {
    rowErrors.value = { ...rowErrors.value, pause: "La fin vient après le début." };
    return;
  }
  await persist("pause", { rhythm_pause_from: from, rhythm_pause_until: until });
}
async function endPause(): Promise<void> {
  form.value.rhythm_pause_from = null;
  form.value.rhythm_pause_until = null;
  await persist("pause", { rhythm_pause_from: null, rhythm_pause_until: null });
}
async function saveMode(): Promise<void> {
  await persist("mode", { offers_notify_mode: form.value.offers_notify_mode, offers_notify_hour: form.value.offers_notify_hour });
}
// Toute la ligne choisit le mode, pas seulement le rond de 20 px (audit téléphone) ; le menu de
// l'heure et la radio elle-même gardent leur propre comportement.
function pickMode(event: MouseEvent, mode: "daily" | "instant"): void {
  if ((event.target as HTMLElement).closest("select, input") || form.value.offers_notify_mode === mode) return;
  form.value.offers_notify_mode = mode;
  void saveMode();
}
// Le seuil des notifications en mots (décision de Kevin du 2026-11-05, C11 ; D3) : Très proche, Proche, À creuser,
// soit 85, 75 et 50 (Proche dès 75, 2026-11-05, Kevin). Une valeur d'avant (60, 70, 80, 90…) s'affiche sous le mot
// le plus proche : 70, l'ancien seuil de Proche, reste « Proche ».
const THRESHOLD_OPTIONS = [
  { value: "85", label: "Très proche", test: "threshold-85" },
  { value: "75", label: "Proche", test: "threshold-75" },
  { value: "50", label: "À creuser", test: "threshold-50" },
];
const threshold = computed({
  get: () => {
    const value = form.value.notify_score_threshold ?? 70;
    return value >= 85 ? "85" : value >= 70 ? "75" : "50";
  },
  set: (value: string) => void setThreshold(Number(value)),
});
// Les interrupteurs de la maquette Réglages (décision de Kevin du 6.11), sur téléphone comme sur ordinateur : ce qui
// part sur le téléphone ; la cloche garde tout. « M'avertir dès » se range sous « Nouvelles offres ». « Actualités et
// formations » attend qu'un envoi existe (notify_news reste côté serveur).
type SwitchKey = "notify_offers" | "notify_follow_ups" | "notify_orp";
const SWITCHES: { key: SwitchKey; title: string; description: string }[] = [
  { key: "notify_offers", title: "Nouvelles offres", description: "Quand une offre te correspond, selon le seuil ci-dessous" },
  { key: "notify_follow_ups", title: "Relances", description: "Une candidature attend une réponse depuis 10 jours" },
  { key: "notify_orp", title: "Objectif ORP", description: "Rappel le 25 du mois, si tu es sous l'objectif" },
];
async function setSwitch(key: SwitchKey, value: boolean): Promise<void> {
  form.value[key] = value;
  await persist(key, { [key]: value });
}
async function setThreshold(value: number): Promise<void> {
  form.value.notify_score_threshold = value;
  await persist("threshold", { notify_score_threshold: value });
}
const { me } = useAuth();
// L'exploitant (docs/65) : la rubrique Plateforme, son plafond de l'IA, les profils d'essai.
const owner = computed(() => Boolean(me.value?.is_owner));
// La formule d'une personne invitée (docs/125).
const { plan } = usePlan();
const planName = computed(() => (plan.value?.plan === "plus" ? "Plus" : "Essentiel"));
// L'IA est-elle branchée ? Lu pour l'exploitant seulement (la rubrique IA, planche « Illustrations »).
const aiConfigured = ref<boolean | null>(null);
watch(
  owner,
  async (isOwner) => {
    if (!isOwner || aiConfigured.value !== null) return;
    try {
      const { data } = await api.GET("/api/scoring");
      aiConfigured.value = data ? data.configured : null;
    } catch {
      aiConfigured.value = null;
    }
  },
  { immediate: true },
);
// Les rubriques de la page Compte (étape 10b) : l'ancienne rubrique Compte se partage entre Affichage, Formule
// et Mes données ; les profils d'essai passent dans Administration.
const SECTIONS = [
  { id: "recherche", label: "Objectif ORP et sites" },
  { id: "rythme", label: "Rythme" },
  { id: "notifications", label: "Notifications" },
  { id: "ia", label: "IA" },
  { id: "affichage", label: "Affichage" },
  { id: "formule", label: "Formule" },
  { id: "donnees", label: "Mes données" },
  // Les comptes Apple, Google ou Microsoft liés (docs/65, complément du 2026-11-05).
  { id: "connexions", label: "Connexions" },
  { id: "outils", label: "Agenda" },
  { id: "plateforme", label: "Administration" },
] as const;
type SectionId = (typeof SECTIONS)[number]["id"];
const route = useRoute();
const { phone } = usePhone();
// Une page Réglages unique sur téléphone (maquette Réglages, décision de Kevin du 6.11) : Notifications,
// Affichage et Mes données à la suite ; le lien du Compte mène à sa section.
const GROUPED = new Set<string>(["notifications", "affichage", "donnees"]);
// Sur ordinateur dès 1 024 px (maquette du 8 novembre, ReglagesOrdinateur) : la même page unique, sur 880 px, avec
// Connexions entre Affichage et Mes données ; le titre « Réglages » sans bandeau.
const WIDE_GROUPED = new Set<string>(["notifications", "affichage", "connexions", "donnees"]);
const { phone: wideQuery } = usePhone("(min-width: 1024px)");
const wide = computed(() => wideQuery.value && !phone.value);
const groupSet = computed(() => (wide.value ? WIDE_GROUPED : GROUPED));
const sections = computed(() => SECTIONS.filter((s) => s.id !== "plateforme" || owner.value));
const active = computed<SectionId>(() => {
  const wanted = route.query.rubrique;
  return sections.value.find((s) => s.id === wanted)?.id ?? "recherche";
});

// Une rubrique par page (décision de Kevin du 2026-11-05, C10) : la page Compte ouvre chacune, et chacune
// revient au compte. Sans rubrique, l'adresse mène à la page Compte (router.ts).
const grouped = computed(() => (phone.value || wide.value) && groupSet.value.has(active.value));
const shows = (id: SectionId): boolean => (grouped.value ? groupSet.value.has(id) : active.value === id);
const label = computed(() =>
  grouped.value ? "Réglages" : (sections.value.find((s) => s.id === active.value)?.label ?? "Réglages"),
);
watch(
  [loaded, active],
  async () => {
    if (!grouped.value || !loaded.value || active.value === "notifications") return;
    await nextTick();
    document.getElementById(active.value)?.scrollIntoView?.({ block: "start" });
  },
  { immediate: true },
);
</script>

<template>
  <PageHero
    v-if="!(wide && grouped)"
    :title="label"
  >
    <template #back>
      <RouterLink
        to="/compte"
        class="back-link"
        data-test="settings-back"
      >
        <span class="with-icon"><AppIcon name="arrow-left" />Retour au compte</span>
      </RouterLink>
    </template>
  </PageHero>
  <section class="band">
    <div :class="['settings-layout', grouped ? 'settings-grouped' : 'settings-sub', { 'settings-wide': wide && grouped }]">
      <h1
        v-if="wide && grouped"
        class="settings-wide-title"
        data-test="settings-title"
      >
        Réglages
      </h1>
      <div class="settings-sections">
        <!-- Une carte par réglage (1.6.66, planche « 5. Réglages ») : titre en gras, une phrase, le
             contrôle à droite ; plus de bouton « Enregistrer ». -->
        <SettingsSection
          v-if="active === 'recherche'"
          id="recherche"
          title="Objectif ORP et sites"
          cards
        >
          <template v-if="loaded">
            <SettingCard>
              <SettingRow
                v-slot="c"
                title="Objectif mensuel de l'ORP"
                description="Les candidatures demandées chaque mois."
                :saved="savedRow === 'orp'"
                :error="rowErrors.orp"
                stack
              >
                <input
                  v-model.number="form.orp_monthly_target"
                  class="setting-number"
                  type="number"
                  inputmode="numeric"
                  min="1"
                  max="100"
                  :aria-labelledby="c.labelledby"
                  :aria-describedby="c.describedby"
                  :aria-invalid="c.invalid"
                  data-test="orp-target"
                  @change="saveNumber('orp_monthly_target')"
                >
                <span>par mois</span>
              </SettingRow>
            </SettingCard>
            <SettingCard>
              <SettingRow
                v-slot="c"
                title="Date limite des preuves"
                description="Le jour du mois suivant où les preuves sont dues."
                :saved="savedRow === 'due'"
                :error="rowErrors.due"
                stack
              >
                <span>le</span>
                <input
                  v-model.number="form.orp_due_day"
                  class="setting-number"
                  type="number"
                  inputmode="numeric"
                  min="2"
                  max="28"
                  :aria-labelledby="c.labelledby"
                  :aria-describedby="c.describedby"
                  :aria-invalid="c.invalid"
                  data-test="due-day"
                  @change="saveNumber('orp_due_day')"
                >
                <span>du mois suivant</span>
              </SettingRow>
            </SettingCard>
            <SitesPanel />
            <SettingCard>
              <SettingRow
                v-slot="c"
                title="Chercher l'annonce chez l'employeur"
                description="Dès cette note, l'annonce est aussi cherchée chez l'employeur."
                :saved="savedRow === 'employer'"
                :error="rowErrors.employer"
                stack
              >
                <span>dès</span>
                <input
                  v-model.number="form.employer_search_threshold"
                  class="setting-number"
                  type="number"
                  inputmode="numeric"
                  min="0"
                  max="100"
                  :aria-labelledby="c.labelledby"
                  :aria-describedby="c.describedby"
                  :aria-invalid="c.invalid"
                  data-test="employer-threshold"
                  @change="saveNumber('employer_search_threshold')"
                >
                <span>/ 100</span>
              </SettingRow>
            </SettingCard>
          </template>
          <!-- Le temps du chargement : des blocs gris à la forme des cartes (règles §4). -->
          <LoadingBlocks
            v-else
            :heights="['4.5rem', '4.5rem', '14rem', '4.5rem']"
          />
        </SettingsSection>

        <SettingsSection
          v-if="active === 'rythme'"
          id="rythme"
          title="Rythme"
          cards
        >
          <template v-if="loaded">
            <SettingCard data-test="rhythm-form">
              <SettingRow
                v-slot="c"
                title="Jours de recherche"
                description="Les autres jours, seulement les rappels avec une date limite."
                :saved="savedRow === 'days'"
                :error="rowErrors.days"
                stack
              >
                <!-- Des pastilles Lu à Di (docs/110) : de vraies cases à cocher, présentées en pastilles. -->
                <div
                  class="rhythm-week"
                  role="group"
                  :aria-labelledby="c.labelledby"
                  :aria-describedby="c.describedby"
                >
                  <label
                    v-for="day in WEEK"
                    :key="day.value"
                    class="day-pill"
                  >
                    <input
                      v-model="form.rhythm_days"
                      type="checkbox"
                      :value="day.value"
                      :disabled="form.rhythm_days?.length === 1 && form.rhythm_days.includes(day.value)"
                      :data-test="`rhythm-day-${day.value}`"
                      @change="saveDays"
                    >
                    <span aria-hidden="true">{{ day.label.slice(0, 2) }}</span>
                    <span class="visually-hidden">{{ day.label }}</span>
                  </label>
                </div>
              </SettingRow>
            </SettingCard>
            <SettingCard data-test="rhythm-pause">
              <SettingRow
                v-slot="c"
                title="Une pause"
                description="Vacances, maladie : ni offres ni message pendant la pause."
                :saved="savedRow === 'pause'"
                :error="rowErrors.pause"
                stack
              >
                <div
                  class="rhythm-pause"
                  role="group"
                  :aria-labelledby="c.labelledby"
                  :aria-describedby="c.describedby"
                >
                  <DateField
                    :model-value="form.rhythm_pause_from ?? null"
                    label="Du"
                    title="Pause à partir du"
                    data-test="pause-from"
                    @update:model-value="form.rhythm_pause_from = $event; void savePause()"
                  />
                  <DateField
                    :model-value="form.rhythm_pause_until ?? null"
                    label="Jusqu'au"
                    title="Pause jusqu'au"
                    :min="form.rhythm_pause_from ?? undefined"
                    data-test="pause-until"
                    @update:model-value="form.rhythm_pause_until = $event; void savePause()"
                  />
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
              </SettingRow>
            </SettingCard>
            <!-- Les deux façons de recevoir les offres, liées : une carte, une ligne d'en-tête, une ligne
                 par choix (loi de proximité). -->
            <SettingCard data-test="rhythm-mode">
              <SettingRow
                title="Les offres bien notées"
                description="Comment elles t'arrivent."
                :saved="savedRow === 'mode'"
                :error="rowErrors.mode"
              />
              <SettingRow
                v-slot="c"
                class="radio-row"
                data-test="rhythm-daily-row"
                title="Un message par jour"
                description="Toutes les offres bien notées du jour, en un seul message."
                @click="pickMode($event, 'daily')"
              >
                <select
                  v-model.number="form.offers_notify_hour"
                  aria-label="Heure du message"
                  :disabled="form.offers_notify_mode !== 'daily'"
                  data-test="rhythm-hour"
                  @change="saveMode"
                >
                  <option
                    v-for="hour in HOURS"
                    :key="hour"
                    :value="hour"
                  >
                    {{ hour }} h
                  </option>
                </select>
                <input
                  v-model="form.offers_notify_mode"
                  type="radio"
                  name="offers-mode"
                  value="daily"
                  :aria-labelledby="c.labelledby"
                  :aria-describedby="c.describedby"
                  data-test="rhythm-daily"
                  @change="saveMode"
                >
              </SettingRow>
              <SettingRow
                v-slot="c"
                class="radio-row"
                data-test="rhythm-instant-row"
                title="Dès qu'elles arrivent"
                description="Un message par offre, dès qu'elle est notée."
                @click="pickMode($event, 'instant')"
              >
                <input
                  v-model="form.offers_notify_mode"
                  type="radio"
                  name="offers-mode"
                  value="instant"
                  :aria-labelledby="c.labelledby"
                  :aria-describedby="c.describedby"
                  data-test="rhythm-instant"
                  @change="saveMode"
                >
              </SettingRow>
            </SettingCard>
          </template>
          <!-- Le temps du chargement : des blocs gris à la forme des cartes (règles §4). -->
          <LoadingBlocks
            v-else
            :heights="['4.5rem', '6rem', '10rem']"
          />
        </SettingsSection>

        <SettingsSection
          v-if="shows('notifications')"
          id="notifications"
          title="Notifications"
          cards
        >
          <template v-if="loaded">
            <SettingCard data-test="notify-switches">
              <template
                v-for="item in SWITCHES"
                :key="item.key"
              >
                <SettingRow
                  v-slot="c"
                  :title="item.title"
                  :description="item.description"
                  :saved="savedRow === item.key"
                  :error="rowErrors[item.key]"
                  :data-test="`switch-row-${item.key}`"
                >
                  <input
                    type="checkbox"
                    role="switch"
                    :checked="form[item.key]"
                    :aria-labelledby="c.labelledby"
                    :aria-describedby="c.describedby"
                    :data-test="`switch-${item.key}`"
                    @change="setSwitch(item.key, !form[item.key])"
                  >
                </SettingRow>
                <SettingRow
                  v-if="item.key === 'notify_offers' && form.notify_offers"
                  title="M'avertir dès"
                  :saved="savedRow === 'threshold'"
                  :error="rowErrors.threshold"
                  class="notify-threshold"
                  data-test="threshold-row"
                  stack
                >
                  <SegmentedControl
                    v-model="threshold"
                    :options="THRESHOLD_OPTIONS"
                    label="M'avertir dès"
                    full
                  />
                </SettingRow>
              </template>
            </SettingCard>
            <SettingCard data-test="notifications">
              <template v-if="notifications?.personal">
                <SettingRow
                  v-slot="c"
                  title="Recevoir sur mon téléphone"
                  description="Offres bien notées, relances et rappel ORP, par l'application ntfy."
                >
                  <input
                    type="checkbox"
                    role="switch"
                    :checked="notifications.configured"
                    :aria-labelledby="c.labelledby"
                    :aria-describedby="c.describedby"
                    data-test="phone-switch"
                    @change="setPhone(!notifications.configured)"
                  >
                </SettingRow>
                <SettingRow
                  v-if="notifications.configured"
                  title="Notification de test"
                  :description="`Dans l'application ntfy, abonne-toi au sujet ${notifications.topic ?? ''} sur le serveur ${notifications.server}.`"
                  data-test="phone-on"
                >
                  <span
                    v-if="testMessage"
                    role="status"
                    class="muted"
                  >{{ testMessage }}</span>
                  <BusyButton
                    class="secondary small"
                    :busy="testing"
                    busy-label="Envoi…"
                    data-test="test-notification"
                    @click="sendTest"
                  >
                    Envoyer
                  </BusyButton>
                </SettingRow>
              </template>
              <SettingRow
                v-else-if="notifications?.configured"
                title="Notification de test"
                description="Un message sur ton téléphone, pour vérifier."
              >
                <span
                  v-if="testMessage"
                  role="status"
                  class="muted"
                >{{ testMessage }}</span>
                <BusyButton
                  class="secondary small"
                  :busy="testing"
                  busy-label="Envoi…"
                  data-test="test-notification"
                  @click="sendTest"
                >
                  Envoyer
                </BusyButton>
              </SettingRow>
              <SettingRow
                v-else-if="notificationsUnknown"
                title="Notifications sur le téléphone"
                description="Impossible de vérifier pour l'instant : la plateforme ne répond pas. Réessaie dans un moment."
                data-test="notifications-unknown"
              />
              <SettingRow
                v-else
                title="Notifications sur le téléphone"
                description="Pas encore disponibles sur cette plateforme."
              />
            </SettingCard>
          </template>
          <!-- Le temps du chargement : des blocs gris à la forme des cartes (règles §4). -->
          <LoadingBlocks
            v-else
            :heights="['4.5rem', '8rem']"
          />
        </SettingsSection>

        <SettingsSection
          v-if="active === 'ia'"
          id="ia"
          title="IA"
          cards
        >
          <template v-if="loaded">
            <!-- Une personne invitée : ce que l'IA fait chaque mois dépend de sa formule, en nombres, pas
                 en francs (docs/125 §2). -->
            <SettingCard
              v-if="!owner"
              data-test="budget-fixed"
            >
              <SettingRow
                :title="`Formule ${planName}`"
                description="Ce que l'IA fait chaque mois : les offres notées, les lettres, les CV, l'assistant."
              >
                <RouterLink
                  :to="{ query: { rubrique: 'formule' } }"
                  class="button-link"
                  data-test="see-plan"
                >
                  Voir ce qui reste
                </RouterLink>
              </SettingRow>
            </SettingCard>
            <template v-else>
              <!-- L'IA pas encore branchée (planche « Illustrations ») : pour l'exploitant seulement. C'est un
                   réglage d'installation, sans écran dans l'application : pas de bouton qui ne mènerait nulle part. -->
              <FaceState
                v-if="aiConfigured === false"
                title="L'IA n'est pas encore branchée"
                illustration="ia-vide"
                data-test="ai-not-configured"
              >
                <p>Elle note les offres et t'aide à rédiger.</p>
                <p class="muted">
                  Un réglage d'installation, sur le serveur.
                </p>
              </FaceState>
              <SettingCard data-test="budget-form">
                <SettingRow
                  v-slot="c"
                  title="Plafond mensuel du coût de l'IA"
                  description="Au-delà, les offres ne sont plus notées jusqu'au mois suivant."
                  :saved="savedRow === 'budget'"
                  :error="rowErrors.budget"
                  stack
                >
                  <input
                    v-model.number="form.llm_monthly_budget_chf"
                    class="setting-number"
                    type="number"
                    min="0"
                    max="1000"
                    step="0.5"
                    inputmode="decimal"
                    :aria-labelledby="c.labelledby"
                    :aria-describedby="c.describedby"
                    :aria-invalid="c.invalid"
                    data-test="budget"
                    @change="saveNumber('llm_monthly_budget_chf')"
                  >
                  <span>CHF</span>
                </SettingRow>
              </SettingCard>
              <SettingCard class="setting-card-body">
                <AiSpend />
              </SettingCard>
            </template>
          </template>
          <!-- Le temps du chargement : des blocs gris à la forme des cartes (règles §4). -->
          <LoadingBlocks
            v-else
            :heights="['4.5rem', '4.5rem', '8rem']"
          />
        </SettingsSection>

        <SettingsSection
          v-if="shows('affichage')"
          id="affichage"
          title="Affichage"
          cards
        >
          <AppearancePanel />
        </SettingsSection>

        <SettingsSection
          v-if="active === 'formule'"
          id="formule"
          title="Formule"
          cards
        >
          <PlanPanel />
        </SettingsSection>

        <SettingsSection
          v-if="shows('donnees')"
          id="donnees"
          title="Mes données"
          cards
        >
          <SessionPanel />
          <AccountDataPanel />
          <!-- « Ce qui part à l'IA » (libellé validé par Kevin, 6.11) : la page publique, à sa section IA. -->
          <SettingCard data-test="ai-data">
            <SettingRow
              title="Ce qui part à l'IA"
              description="Ce que jobA1 envoie à l'IA, et ce qui n'y part jamais."
            >
              <RouterLink
                :to="{ path: '/tes-donnees', hash: '#ia' }"
                class="button-link secondary small"
                data-test="ai-data-link"
              >
                Voir
              </RouterLink>
            </SettingRow>
          </SettingCard>
        </SettingsSection>

        <SettingsSection
          v-if="shows('connexions')"
          id="connexions"
          title="Connexions"
          cards
        >
          <ConnectionsPanel />
          <ExtensionPanel />
          <GetemallPanel />
        </SettingsSection>

        <SettingsSection
          v-if="active === 'outils'"
          id="outils"
          title="Agenda"
          cards
        >
          <AgendaPanel />
        </SettingsSection>

        <SettingsSection
          v-if="owner && active === 'plateforme'"
          id="plateforme"
          title="Administration"
          cards
        >
          <PlatformPanel />
          <ProfilesPanel />
        </SettingsSection>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* La page Réglages unique du téléphone (maquette Réglages) : les titres de section en petites capitales grises. */
.settings-grouped :deep(.settings-section > .section-title) {
  margin: 0 var(--space-1) var(--space-2);
  font-size: var(--font-caption);
  font-weight: var(--weight-bold);
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.settings-grouped :deep(.settings-section + .settings-section) { margin-top: var(--space-5); }
/* Ordinateur (maquette du 8 novembre, ReglagesOrdinateur) : les titres de section en 18 gras, une carte par section
   aux lignes séparées d'un filet (D22) ; Connexions avant Mes données. */
.settings-wide .settings-sections { display: flex; flex-direction: column; gap: var(--space-8); }
.settings-wide :deep(.settings-section + .settings-section) { margin-top: 0; }
.settings-wide :deep(#donnees) { order: 1; }
.settings-wide :deep(.settings-section > .section-title) {
  margin: 0 var(--space-1) var(--settings-10);
  font-size: var(--font-title);
  font-weight: var(--weight-bold);
  color: var(--text);
  text-transform: none;
  letter-spacing: normal;
}
.setting-row.notify-threshold { padding-top: 0; border-top: 0; }
</style>
