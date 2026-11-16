<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { api, type SettingsModel } from "../api/client";
import { useAuth } from "../composables/useAuth";
import { SCORE_HELP } from "../composables/useOfferFilters";
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
import SettingsMore from "../components/SettingsMore.vue";
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
      testMessage.value = "Notification envoyée : vérifie ton téléphone.";
    } else {
      const detail = (error as { detail?: unknown } | undefined)?.detail;
      testMessage.value = typeof detail === "string" ? `Échec : ${detail}.` : `Échec (HTTP ${response.status}).`;
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
  return "Refusé : vérifie la valeur.";
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
      [rule.row]: `${rule.text} ${old === null || old === undefined ? "Rien n’est enregistré." : `Le ${old} reste enregistré.`}`,
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
// « M'avertir dès » en chiffres, comme « Note minimale » des filtres (Kevin, 16.11) : mêmes seuils, même aide.
const THRESHOLD_OPTIONS = [85, 75, 50].map((n) => ({ value: String(n), label: `${n} et +`, test: `threshold-${n}` }));
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
  { key: "notify_orp", title: "Objectif ORP", description: "Rappel 5 jours avant la fin du mois" },
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
// revient au compte. Sans rubrique, l'adresse mène à la page Compte sur téléphone, aux notifications sur ordinateur
// (router.ts).
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
  <!-- Téléphone, page Réglages (planche Reglages du 14.11, §6) : la flèche de 24 px dans un bouton de 48 px, puis
       le titre ; plus de « Retour au compte » ni de bandeau. -->
  <header
    v-if="phone && grouped"
    class="rg-phone-head"
  >
    <RouterLink
      to="/compte"
      class="rg-back"
      aria-label="Retour au compte"
      data-test="settings-back"
    >
      <AppIcon name="arrow-left" />
    </RouterLink>
    <h1 data-test="settings-title">
      Réglages
    </h1>
  </header>
  <!-- Sous-pages (consigne de Kevin du 16.11, point 1) : le retour au-dessus du titre, et le lien, le titre et les
       cartes sur le même bord gauche (.settings-head, même colonne que .settings-sections). -->
  <PageHero
    v-else-if="!(wide && grouped)"
    :title="label"
    :class="{ 'settings-head': !grouped }"
  >
    <template #back>
      <!-- Sur ordinateur, plus de page Compte (PR 20) : chaque rubrique revient aux Réglages. -->
      <RouterLink
        v-if="phone || active !== 'notifications'"
        :to="phone ? '/compte' : '/reglages'"
        class="back-link"
        data-test="settings-back"
      >
        <span class="with-icon"><AppIcon name="arrow-left" />{{ phone ? "Retour au compte" : "Retour aux réglages" }}</span>
      </RouterLink>
    </template>
  </PageHero>
  <section class="band">
    <div :class="['settings-layout', grouped ? 'settings-grouped' : 'settings-sub', { 'settings-wide': wide && grouped, 'settings-phone': phone && grouped }]">
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
                title="Objectif mensuel de l’ORP"
                description="Les candidatures demandées chaque mois."
                :saved="savedRow === 'orp'"
                :error="rowErrors.orp"
                class="num-row"
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
                title="Date limite des justificatifs"
                description="À rendre chaque mois avant ce jour."
                :saved="savedRow === 'due'"
                :error="rowErrors.due"
                class="num-row"
                stack
              >
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
                title="Chercher l’annonce chez l’employeur"
                description="Dès cette note, l’annonce est aussi cherchée chez l’employeur."
                :saved="savedRow === 'employer'"
                :error="rowErrors.employer"
                class="num-row"
                stack
              >
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
                description="Vacances, maladie : ni offres ni message pendant la pause."
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
                    label="Jusqu’au"
                    title="Pause jusqu’au"
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
                description="Comment elles t’arrivent."
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
                title="Dès qu’elles arrivent"
                description="Un message par offre, dès qu’elle est notée."
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
                  v-slot="c"
                  title="M’avertir dès"
                  :description="SCORE_HELP"
                  :saved="savedRow === 'threshold'"
                  :error="rowErrors.threshold"
                  class="notify-threshold"
                  data-test="threshold-row"
                  stack
                >
                  <SegmentedControl
                    v-model="threshold"
                    :options="THRESHOLD_OPTIONS"
                    label="M’avertir dès"
                    :aria-labelledby="c.labelledby"
                    :aria-describedby="c.describedby"
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
                  description="Offres bien notées, relances et rappel ORP, par l’application ntfy."
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
                  :description="`Dans l’application ntfy, abonne-toi au sujet ${notifications.topic ?? ''} sur le serveur ${notifications.server}.`"
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
                description="Impossible de vérifier pour l’instant : la plateforme ne répond pas. Réessaie dans un moment."
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
                description="Ce que l’IA fait chaque mois : les offres notées, les lettres, les CV, l’assistant."
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
                   réglage d’installation, sans écran dans l’application : pas de bouton qui ne mènerait nulle part. -->
              <FaceState
                v-if="aiConfigured === false"
                title="L’IA n’est pas encore branchée"
                illustration="ia-vide"
                data-test="ai-not-configured"
              >
                <p>Elle note les offres et t’aide à rédiger.</p>
                <p class="muted">
                  Un réglage d’installation, sur le serveur.
                </p>
              </FaceState>
              <SettingCard data-test="budget-form">
                <SettingRow
                  v-slot="c"
                  title="Plafond mensuel du coût de l’IA"
                  description="Au-delà, les offres ne sont plus notées jusqu’au mois suivant."
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
          <AppearancePanel
            :detailed="grouped"
            :phone="phone"
          />
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
          <!-- Mes données (planches Reglages et ReglagesOrdinateur du 14.11) : une liste, Exporter puis « L’IA et tes
               données », puis Supprimer mon compte ; la connexion (fonction de main absente des planches) reste dessous. -->
          <AccountDataPanel :phone="phone" />
          <SessionPanel />
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

        <!-- Ordinateur (PR 20, point 1) : ce qui était sur la page Compte, sous les notifications. -->
        <SettingsMore v-if="!phone && shows('notifications')" />

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

<style>
/* Réglages, refaits d'après les planches du 14 novembre (Reglages pour le téléphone, ReglagesOrdinateur dès 1 024 px).
   Sans `scoped` (classes propres à la page, rg-* et settings-grouped/-phone/-wide) : le CSS reste sous la limite de
   poids. Téléphone : listes bordées de 1 px, rayon 18, lignes de 64 px (16/600, aide 13/18). Ordinateur : une carte
   par section bordée de 1,5 px, lignes à 18,5 px du bord (15/600, aide 14). Valeurs hors grille arrondies à 4 px. */
.rg-phone-head, .settings-layout { --rg-6: 6px; --rg-10: 10px; --rg-12: 12px; --rg-13: 13px; --rg-14: 14px; --rg-15: 15px; --rg-16: 16px; --rg-18: 18px; --rg-185: 18.5px; --rg-19: 19px; --rg-20: 20px; --rg-21: 21px; --rg-22: 22px; --rg-28: 28px; }
.rg-phone-head { display: flex; align-items: center; gap: var(--space-1); padding: var(--space-3) var(--space-2) var(--space-1); }
.rg-phone-head h1 { margin: 0; font-size: var(--rg-22); line-height: var(--rg-28); font-weight: var(--weight-bold); }
.rg-back { display: inline-grid; place-items: center; width: 48px; height: 48px; border-radius: var(--radius-pill); color: var(--text); }
.rg-back .icon { width: 24px; height: 24px; }
.settings-phone { padding: var(--rg-10) var(--space-5) var(--rg-28); }
.settings-grouped .settings-sections { gap: 0; }
.settings-grouped .settings-section > .section-title { margin: 0 var(--space-1) var(--space-2); font-size: var(--rg-13); font-weight: var(--weight-bold); color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.6px; }
.settings-grouped .settings-section + .settings-section { margin-top: var(--rg-22); }
.settings-grouped :is(.setting-cards, .appearance, .account-data) { display: grid; gap: var(--space-3); }
.settings-grouped :is(.setting-card, .rg-list) { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-card); overflow: hidden; }
.settings-grouped .setting-row { flex-wrap: nowrap; gap: var(--space-3); min-height: 64px; padding: var(--rg-10) var(--rg-14); }
.settings-grouped :is(.setting-row + .setting-row, .rg-list > * + *) { border-top: 1px solid var(--line-soft); }
.settings-grouped .setting-row.stack { flex-wrap: wrap; }
.settings-grouped .setting-row-text { flex: 1 1 auto; }
.settings-grouped :is(.setting-row-title, .rg-label) { font-size: var(--font-body); font-weight: var(--weight-semibold); color: var(--text); }
.settings-grouped :is(.setting-row-description, .rg-sub) { font-size: var(--rg-13); line-height: var(--rg-18); font-weight: var(--weight-regular); color: var(--text-secondary); }
.settings-phone input[type="checkbox"][role="switch"] { width: 52px; height: 32px; }
.settings-phone input[type="checkbox"][role="switch"]::after { top: 3px; left: 3px; width: 26px; height: 26px; }
.settings-phone input[type="checkbox"][role="switch"]:checked::after { transform: translateX(20px); }
.settings-grouped .appearance-row { display: flex; align-items: center; gap: var(--space-4); min-height: 64px; padding: var(--rg-12) var(--rg-14); }
.settings-phone .appearance-row { flex-direction: column; align-items: stretch; gap: var(--space-3); padding: var(--rg-14); }
.settings-phone .appearance-row .segmented { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-radius: var(--rg-14); }
.settings-phone .appearance-row .segmented > button { min-height: 44px; border: 0; border-radius: var(--rg-10); font-size: var(--rg-14); }
.settings-grouped :is(.rg-link-row, .rg-danger-row) { display: flex; align-items: center; gap: var(--space-3); width: 100%; min-height: 56px; margin: 0; padding: 0 var(--rg-14); border: 0; border-radius: 0; background: transparent; color: var(--text); font: inherit; text-align: left; text-decoration: none; white-space: normal; cursor: pointer; }
.settings-grouped .rg-label { flex: 1; min-width: 0; }
.settings-grouped .rg-value { min-width: 0; font-size: var(--rg-15); color: var(--text-secondary); text-align: right; }
.settings-grouped .rg-link-row > .icon:last-child { width: 18px; height: 18px; color: var(--text-secondary); }
.settings-grouped .rg-lead { width: 20px; height: 20px; color: var(--primary-graphic); }
.settings-grouped .rg-link-two { padding-block: var(--rg-12); }
.settings-grouped .rg-sub { display: block; margin-top: var(--space-1); }
.settings-grouped [data-test=delete-form] .inline-confirm > p:first-child { font-weight: var(--weight-bold); }
.settings-grouped .rg-list > .setting-row-form { padding: var(--space-4) var(--rg-14); }
.settings-phone .rg-danger-button { min-height: 52px; margin-top: var(--rg-6); justify-content: center; border: 1.5px solid var(--danger-line); border-radius: var(--rg-16); background: var(--surface); color: var(--danger); font: inherit; font-weight: var(--weight-bold); cursor: pointer; }
/* Ordinateur : la carte par section vient de style.css (.settings-wide .setting-cards). */
.settings-wide .settings-sections { display: flex; flex-direction: column; gap: var(--space-8); }
.settings-wide .settings-section + .settings-section { margin-top: 0; }
.settings-wide #donnees { order: 1; }
.settings-wide .settings-section > .section-title { margin: 0 var(--space-1) var(--space-3); font-size: var(--font-title); color: var(--text); text-transform: none; letter-spacing: normal; }
.settings-wide .setting-cards { border-radius: var(--radius-card); }
.settings-wide :is(.setting-card, .rg-list) { border: 0; border-radius: 0; }
.settings-wide :is(.setting-cards > * + *, .setting-row + .setting-row, .rg-list > * + *) { border-top: 1px solid var(--surface-muted); }
.settings-wide :is(.account-data, .appearance) { gap: 0; }
.settings-wide :is(.setting-row, .appearance-row, .rg-link-row) { gap: var(--space-4); padding: var(--rg-12) var(--rg-185); }
.settings-wide .rg-link-row { min-height: 64px; }
.settings-wide :is(.setting-row-title, .rg-label, .rg-danger-row) { font-size: var(--rg-15); }
.settings-wide :is(.setting-row-description, .account-data .rg-sub) { font-size: var(--font-small); line-height: var(--rg-20); }
.settings-wide .appearance-row .segmented { padding: var(--space-1); gap: 0; border-radius: var(--rg-19); }
.settings-wide .appearance-row .segmented > button { min-height: 32px; padding: 0 var(--space-4); border: 0; border-radius: var(--rg-16); color: var(--text); font-size: var(--rg-14); }
.settings-wide .rg-link-row > .icon:last-child { width: 20px; height: 20px; }
.settings-wide .account-data .rg-link-row { min-height: 56px; }
.settings-wide .account-data .rg-label { font-weight: var(--weight-regular); line-height: var(--rg-21); }
.settings-wide .account-data .arrow-circle { border-width: 2px; }
.settings-wide .rg-danger-row { min-height: 56px; padding: 0 var(--rg-20); color: var(--danger); font-weight: var(--weight-bold); }
.settings-wide .rg-list > .setting-row-form { padding: var(--space-4) var(--rg-185); }
.settings-wide #connexions .setting-row-control :is(button, a):not(.link) { min-height: 44px; padding: 0 var(--space-4); border-radius: var(--rg-22); font-size: var(--rg-15); }
.settings-grouped .setting-row.notify-threshold { padding-top: 0; border-top: 0; min-height: 0; }
/* Objectif ORP et sites (consigne de Kevin du 16.11, points 2 et 3). Champs chiffrés : une colonne fixe
   d'une carte à l'autre (texte 1fr, champ 72 px, unité 120 px, assez pour « du mois suivant », écart 12 px), rayon des
   champs de saisie (--ff-radius), 44 px de haut, chiffre centré. Sur téléphone, le champ et l'unité sous le texte. */
.setting-row.num-row { --num-unit: 120px; display: grid; grid-template-columns: minmax(0, 1fr) 72px var(--num-unit); align-items: center; gap: var(--space-2) var(--space-3); }
.num-row > .setting-row-control { display: contents; }
.num-row .setting-number { grid-column: 2; grid-row: 1; width: 72px; height: 44px; min-height: 44px; padding: 0; border-radius: var(--ff-radius); text-align: center; }
.num-row .setting-row-control > span:not([role="status"]) { grid-column: 3; grid-row: 1; }
.num-row .setting-row-status { grid-column: 2 / -1; grid-row: 2; }
.num-row > .setting-row-error { grid-column: 1 / -1; text-align: left; }
@media (max-width: 820px) {
  .setting-row.num-row { grid-template-columns: 72px var(--num-unit) minmax(0, 1fr); }
  .num-row > .setting-row-text { grid-column: 1 / -1; }
  .num-row .setting-number { grid-column: 1; grid-row: 2; }
  .num-row .setting-row-control > span:not([role="status"]) { grid-column: 2; grid-row: 2; }
  .num-row .setting-row-status { grid-column: 3; grid-row: 2; }
}
</style>
