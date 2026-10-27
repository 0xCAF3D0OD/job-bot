<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api, type SettingsModel } from "../api/client";
import { plural } from "../format";
import { useAuth } from "../composables/useAuth";
import { usePhone } from "../composables/usePhone";
import PageHero from "../components/PageHero.vue";
import PlanPanel from "../components/PlanPanel.vue";
import { usePlan } from "../composables/usePlan";
import { usePageReady } from "../composables/usePageTransition";
import AccountDataPanel from "../components/AccountDataPanel.vue";
import AgendaPanel from "../components/AgendaPanel.vue";
import ExtensionPanel from "../components/ExtensionPanel.vue";
import PlatformPanel from "../components/PlatformPanel.vue";
import ProfilesPanel from "../components/ProfilesPanel.vue";
import SessionPanel from "../components/SessionPanel.vue";
import AppIcon from "../components/AppIcon.vue";
import SettingsSection, { SETTINGS_ICONS } from "../components/SettingsSection.vue";
import SettingCard from "../components/SettingCard.vue";
import SettingRow from "../components/SettingRow.vue";
import SitesPanel from "../components/SitesPanel.vue";

import AiSpend from "../components/AiSpend.vue";

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
    form.value = { ...data };
    stored.value = { ...data };
  }
  loaded.value = true;
  void setupMarkers();
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
  await persist("threshold", { notify_score_threshold: value });
}
const router = useRouter();
const { me } = useAuth();
// L'exploitant (docs/65) : la rubrique Plateforme, son plafond de l'IA, les profils d'essai.
const owner = computed(() => Boolean(me.value?.is_owner));
// La formule d'une personne invitée (docs/125).
const { plan } = usePlan();
const planName = computed(() => (plan.value?.plan === "plus" ? "Plus" : "Essentiel"));
// Le Diagnostic technique, à l'exploitant seulement (docs/108 §3).
// Pas dans la démo : un écran technique, du jargon pour qui découvre jobA1 (audit du 22.10.2026).
const showDiagnostic = computed(() => owner.value || (me.value?.auth_enabled === false && !me.value?.demo));
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
  notifications: [
    notifications.value ? (notifications.value.configured ? "actives" : "non configurées") : "",
    `dès ${form.value.notify_score_threshold} / 100`,
  ]
    .filter(Boolean)
    .join(" · "),
  ia: owner.value ? `plafond ${form.value.llm_monthly_budget_chf} CHF / mois` : `formule ${planName.value}`,
  compte: [owner.value ? "profils d'essai" : `formule ${planName.value}`, me.value?.auth_enabled ? (me.value.username ?? "") : ""]
    .filter(Boolean)
    .join(" · "),
  outils: "abonnement, extension du navigateur",
  plateforme: "comptes et IA de la plateforme",
}));

// Une rubrique à la fois (docs/48 §2) : le sommaire choisit, l'adresse la retient.
const SECTIONS = [
  { id: "recherche", label: "Recherche d'emploi" },
  { id: "rythme", label: "Rythme" },
  { id: "notifications", label: "Notifications" },
  { id: "ia", label: "IA" },
  { id: "compte", label: "Compte" },
  { id: "outils", label: "Agenda et extension" },
  { id: "plateforme", label: "Administration" },
] as const;
type SectionId = (typeof SECTIONS)[number]["id"];
const OLD_ANCHORS: Record<string, SectionId> = {
  recherche: "recherche",
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

// Sur téléphone, une longue page (docs/110) : les marqueurs du haut mènent à chaque rubrique et
// suivent la lecture. Ils se collent sous la barre du haut.
const { phone } = usePhone();
const current = ref<SectionId>("recherche");
const markers = ref<HTMLElement | null>(null);
const markersTop = ref(0);
let spy: IntersectionObserver | undefined;

function goTo(id: SectionId, smooth = true): void {
  current.value = id;
  document.getElementById(id)?.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "start" });
}

function watchSections(): void {
  spy?.disconnect();
  if (!phone.value || typeof IntersectionObserver === "undefined") return;
  const top = markersTop.value + (markers.value?.offsetHeight ?? 0);
  // La rubrique en cours : celle qui passe juste sous les marqueurs.
  spy = new IntersectionObserver(
    (entries) => {
      const seen = entries.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
      const first = seen[0]?.target.id as SectionId | undefined;
      if (first) current.value = first;
    },
    { rootMargin: `-${top + 8}px 0px -55% 0px` },
  );
  for (const section of sections.value) {
    const el = document.getElementById(section.id);
    if (el) spy.observe(el);
  }
}

// Le marqueur en cours reste visible dans la rangée qui défile.
watch(current, async (id) => {
  await nextTick();
  markers.value?.querySelector<HTMLElement>(`[data-test="marker-${id}"]`)?.scrollIntoView?.({ block: "nearest", inline: "nearest" });
});

async function setupMarkers(): Promise<void> {
  if (!phone.value) return;
  await nextTick();
  markersTop.value = Math.round(document.querySelector<HTMLElement>(".topbar")?.getBoundingClientRect().height ?? 0);
  watchSections();
  const wanted = sections.value.find((s) => s.id === route.query.rubrique)?.id;
  if (wanted) goTo(wanted, false);
}
watch(phone, () => void setupMarkers());
onUnmounted(() => spy?.disconnect());
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
        <!-- Sur ordinateur, le Diagnostic est une entrée du sommaire, sous un filet (0.78.4). -->
        <RouterLink
          v-if="showDiagnostic"
          to="/reglages/diagnostic"
          class="toc-diagnostic"
          data-test="diagnostic-link"
        >
          <span class="with-icon"><AppIcon name="activity" />État du service</span>
        </RouterLink>
      </nav>
      <!-- Sur téléphone, les marqueurs pour parcourir la longue page (docs/110). -->
      <nav
        v-if="phone"
        ref="markers"
        class="settings-markers"
        aria-label="Aller à une rubrique"
        :style="{ top: `${markersTop}px` }"
        data-test="settings-markers"
      >
        <a
          v-for="section in sections"
          :key="section.id"
          :href="`#${section.id}`"
          :class="{ active: current === section.id }"
          :aria-current="current === section.id ? 'location' : undefined"
          :data-test="`marker-${section.id}`"
          @click.prevent="goTo(section.id)"
        >{{ section.label }}</a>
      </nav>
      <div class="settings-sections">
        <!-- Une carte par réglage (1.6.66, planche « 5. Réglages ») : titre en gras, une phrase, le
             contrôle à droite ; plus de bouton « Enregistrer ». -->
        <SettingsSection
          id="recherche"
          title="Recherche d'emploi"
          :value="summary.recherche"
          :active="active === 'recherche'"
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
        </SettingsSection>

        <SettingsSection
          id="rythme"
          title="Rythme"
          :value="summary.rythme"
          :active="active === 'rythme'"
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
                  <label>
                    Du
                    <input
                      v-model="form.rhythm_pause_from"
                      type="date"
                      data-test="pause-from"
                      @change="savePause"
                    >
                  </label>
                  <label>
                    Jusqu'au
                    <input
                      v-model="form.rhythm_pause_until"
                      type="date"
                      :min="form.rhythm_pause_from ?? undefined"
                      :aria-invalid="c.invalid"
                      data-test="pause-until"
                      @change="savePause"
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
                title="Un message par jour"
                description="Toutes les offres bien notées du jour, en un seul message."
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
                title="Dès qu'elles arrivent"
                description="Un message par offre, dès qu'elle est notée."
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
        </SettingsSection>

        <SettingsSection
          id="notifications"
          title="Notifications"
          :value="summary.notifications"
          :active="active === 'notifications'"
          cards
        >
          <template v-if="loaded">
            <SettingCard data-test="notify-form">
              <SettingRow
                v-slot="c"
                title="M'avertir d'une offre dès"
                description="Une offre notée sous ce seuil reste dans la liste, sans notification."
                :saved="savedRow === 'threshold'"
                :error="rowErrors.threshold"
                stack
              >
                <div
                  class="score-choices"
                  role="radiogroup"
                  :aria-labelledby="c.labelledby"
                  :aria-describedby="c.describedby"
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
                  <span class="muted score-max">/ 100</span>
                </div>
              </SettingRow>
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
                  <button
                    type="button"
                    class="secondary small"
                    :disabled="testing"
                    data-test="test-notification"
                    @click="sendTest"
                  >
                    Envoyer
                  </button>
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
                <button
                  type="button"
                  class="secondary small"
                  :disabled="testing"
                  data-test="test-notification"
                  @click="sendTest"
                >
                  Envoyer
                </button>
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
        </SettingsSection>

        <SettingsSection
          id="ia"
          title="IA"
          :value="summary.ia"
          :active="active === 'ia'"
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
                  :to="{ query: { rubrique: 'compte' } }"
                  class="button-link"
                  data-test="see-plan"
                >
                  Voir ce qui reste
                </RouterLink>
              </SettingRow>
            </SettingCard>
            <template v-else>
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
        </SettingsSection>

        <SettingsSection
          id="compte"
          title="Compte"
          :value="summary.compte"
          :active="active === 'compte'"
          cards
        >
          <!-- Chaque panneau porte ses cartes (1.6.67) : la formule, les profils d'essai, la connexion,
               les données personnelles. -->
          <PlanPanel />
          <ProfilesPanel v-if="owner" />
          <SessionPanel />
          <AccountDataPanel />
        </SettingsSection>

        <SettingsSection
          id="outils"
          title="Agenda et extension"
          :value="summary.outils"
          :active="active === 'outils'"
          cards
        >
          <AgendaPanel />
          <ExtensionPanel />
        </SettingsSection>

        <SettingsSection
          v-if="owner"
          id="plateforme"
          title="Administration"
          :value="summary.plateforme"
          :active="active === 'plateforme'"
          cards
        >
          <PlatformPanel />
        </SettingsSection>

        <!-- Le Diagnostic technique, à l'exploitant seulement (docs/108 §3) ; sur téléphone, une
             ligne grise en fin de page, comme les autres destinations (0.78.4). -->
        <RouterLink
          v-if="phone && showDiagnostic"
          to="/reglages/diagnostic"
          class="info-card diagnostic-row"
          data-test="diagnostic-row"
        >
          <span>
            <span class="setting-title">État du service</span>
            <span class="setting-desc">La collecte, l'IA et les tâches de la plateforme.</span>
          </span>
          <AppIcon name="chevron" />
        </RouterLink>
      </div>
    </div>
  </section>
</template>
