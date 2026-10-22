<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import {
  api,
  type Application,
  type ApplicationStatus,
  type Interview,
  type InterviewIn,
  type OrpMonth,
} from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import IconButton from "../components/IconButton.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
import ApplicationCard from "../components/ApplicationCard.vue";
import ApplicationPanel from "../components/ApplicationPanel.vue";
import SidePanel from "../components/SidePanel.vue";
import ApplicationForm, { type ApplicationFormValue } from "../components/ApplicationForm.vue";
import ApplicationsTable from "../components/ApplicationsTable.vue";
import InterviewForm from "../components/InterviewForm.vue";
import InterviewPractice from "../components/InterviewPractice.vue";
import InterviewPreparation from "../components/InterviewPreparation.vue";
import OrpSheet from "../components/OrpSheet.vue";
import SuiviCalendar from "../components/SuiviCalendar.vue";
import FaceState from "../components/FaceState.vue";
import MoreMenu, { type MoreMenuItem } from "../components/MoreMenu.vue";
import EngagementMoment from "../components/EngagementMoment.vue";
import SuccessCard from "../components/SuccessCard.vue";
import { applicationBody, applicationUpdateBody } from "../applicationBody";
import { isoDay } from "../contactLabels";
import { useAssistant } from "../composables/useAssistant";
import { colorIndex, formatMonth, ofMonth, plural, shiftMonth } from "../format";
import { useDataChanged } from "../composables/useDataChanged";
import { usePageReady } from "../composables/usePageTransition";
import { offerUndo } from "../composables/useUndo";
import InlineConfirm from "../components/InlineConfirm.vue";

// Onglet Suivi (docs/22) : candidatures et preuves ORP du mois, en calendrier ou en liste.
const REMIND_AFTER_DAYS = 10;
const NO_ANSWER_DAYS = 14;
const VIEW_KEY = "jobbot-suivi-vue";

const route = useRoute();
const router = useRouter();
const orp = ref<OrpMonth | null>(null);
usePageReady("applications", () => !!orp.value);
const all = ref<Application[]>([]);
const allMonths = ref(false);
const editing = ref<{ id: number | null; value: ApplicationFormValue } | null>(null);
const error = ref("");
const loaded = ref(false);
const busy = ref(false);
// ?jour=AAAA-MM-JJ (lien du rappel « fais le point », docs/23 §1) : le jour s'ouvre d'emblée.
const selectedDay = ref<string | null>(typeof route.query.jour === "string" ? route.query.jour : null);
const layout = ref<"calendar" | "list">(readLayout());

function readLayout(): "calendar" | "list" {
  try {
    return localStorage.getItem(VIEW_KEY) === "list" ? "list" : "calendar";
  } catch {
    return "calendar";
  }
}

function setLayout(value: "calendar" | "list"): void {
  layout.value = value;
  try {
    localStorage.setItem(VIEW_KEY, value);
  } catch {
    // Choix retenu jusqu'au rechargement seulement.
  }
}

const month = computed(() => orp.value?.month ?? "");
const monthItems = computed(() => all.value.filter((a) => a.orp_month === month.value));
const items = computed(() => (allMonths.value ? all.value : monthItems.value));
const rowsById = computed(() => new Map((orp.value?.rows ?? []).map((r) => [r.application_id, r])));
const incomplete = computed(() => new Set((orp.value?.rows ?? []).filter((r) => r.missing.length).map((r) => r.application_id)));
// À déclarer dans Job-Room (docs/85) : les candidatures du mois pas encore marquées déclarées,
// date · entreprise · poste ; un clic ouvre le panneau, avec l'offre et les champs à copier.
const shortDate = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long" });
const toDeclare = computed(() =>
  (orp.value?.rows ?? [])
    .filter((r) => !r.declared_at)
    .map((r) => {
      const application = all.value.find((a) => a.id === r.application_id);
      const day = application ? shortDate.format(new Date(`${application.sent_at}T12:00:00`)) : r.date;
      return { id: r.application_id, day, company: r.company, title: r.job_title, incomplete: r.missing.length > 0 };
    }),
);
// Le PDF et le CSV du mois, dans le « ⋯ » de la barre du mois (docs/85 §3).
const sheet = ref<InstanceType<typeof OrpSheet> | null>(null);
const monthMenu = computed<MoreMenuItem[]>(() => {
  const data = orp.value;
  if (!data) return [];
  return [
    { label: "Télécharger le PDF", test: "pdf", icon: "download", run: () => void sheet.value?.printPdf() },
    ...(data.searches.length
      ? [{ label: "PDF avec le journal des recherches", test: "pdf-with-searches", icon: "download" as const, count: data.searches.length, run: () => void sheet.value?.printPdf(true) }]
      : []),
    { label: "Télécharger en CSV (Excel)", test: "csv", href: `/api/orp/${data.month}/csv`, download: true },
  ];
});
const firstIncomplete = computed(() => monthItems.value.find((a) => incomplete.value.has(a.id)) ?? null);
const progress = computed(() => (orp.value?.target ? Math.min(1, orp.value.count / orp.value.target) : null));
const longDate = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long", year: "numeric" });
const dayTitle = new Intl.DateTimeFormat("fr-CH", { weekday: "long", day: "numeric", month: "long" });
// Le bandeau des preuves (docs/134) : ce qui reste à faire, et pour quand.
const bannerText = computed(() => {
  const d = orp.value;
  if (!d) return "";
  const month = ofMonth(d.month);
  if (d.state === "remis" && d.submitted_at) return `Preuves ${month} remises le ${longDate.format(new Date(d.submitted_at))}.`;
  const due = longDate.format(new Date(d.due_date));
  if (d.incomplete) return `Preuves ${month} : ${plural(d.incomplete, "ligne", "lignes")} à compléter, remise avant le ${due}.`;
  return `Preuves ${month} prêtes : à remettre avant le ${due}.`;
});
// À relancer (docs/38) : en attente depuis 10 jours, ou relancées sans réponse depuis 14 jours ;
// les plus anciennes d'abord.
const toFollowUp = computed(() => {
  const limit = new Date();
  limit.setDate(limit.getDate() - REMIND_AFTER_DAYS);
  // Dates locales, comme sur la carte : en UTC, le soir, la relance tomberait un jour trop tôt.
  const day = isoDay(limit);
  const noAnswer = new Date();
  noAnswer.setDate(noAnswer.getDate() - NO_ANSWER_DAYS);
  const after = isoDay(noAnswer);
  return all.value
    .filter(
      (a) =>
        (a.status === "en_attente" && a.sent_at <= day) ||
        (a.status === "relancee" && !!a.followed_up_at && a.followed_up_at <= after),
    )
    .sort((a, b) => a.sent_at.localeCompare(b.sent_at));
});
// Cartes du jour choisi : envoyées ce jour-là ou entretien ce jour-là.
const dayCards = computed(() => {
  const day = selectedDay.value;
  if (!day) return [];
  return all.value.filter(
    (a) =>
      a.sent_at === day ||
      (a.interview_at && new Date(a.interview_at).toISOString().slice(0, 10) === day) ||
      a.interviews?.some((i) => i.next_step_at === day),
  );
});

// Cartes du panneau : celles du jour choisi, sinon celles à relancer.
const panelCards = computed(() => (selectedDay.value ? dayCards.value : toFollowUp.value));

// La colonne de droite à la hauteur du calendrier (retour du 2026-10-07, rétabli en docs/134) :
// les onglets restent en haut, la liste défile dessous, estompée là où il reste des lignes.
const calendarBox = ref<HTMLElement | null>(null);
const panelScroll = ref<HTMLElement | null>(null);
const panelHeight = ref<number | null>(null);
const atTop = ref(true);
const atBottom = ref(true);
let observer: ResizeObserver | null = null;
function measure(): void {
  const wide = globalThis.matchMedia?.("(min-width: 901px)").matches ?? true;
  panelHeight.value = wide && calendarBox.value ? calendarBox.value.offsetHeight || null : null;
}
function onPanelScroll(): void {
  const el = panelScroll.value;
  if (!el) return;
  atTop.value = el.scrollTop <= 2;
  atBottom.value = el.scrollTop + el.clientHeight >= el.scrollHeight - 2;
}
watch(calendarBox, (el) => {
  observer?.disconnect();
  if (el && typeof ResizeObserver !== "undefined") {
    observer = new ResizeObserver(measure);
    observer.observe(el);
  }
  measure();
});
onUnmounted(() => observer?.disconnect());
// La liste de droite (docs/133 §1) : à relancer ou à déclarer dans Job-Room.
const panelTab = ref<"follow" | "declare">("follow");
// Nouvelle liste (jour, onglet, mois) : retour en haut, estompage recalculé.
watch([panelCards, panelTab], async () => {
  await nextTick();
  if (panelScroll.value) panelScroll.value.scrollTop = 0;
  onPanelScroll();
});

async function load(): Promise<void> {
  const wanted = typeof route.query.mois === "string" ? route.query.mois : undefined;
  const [sheet, list] = await Promise.all([
    api.GET("/api/orp", { params: { query: { month: wanted } } }),
    api.GET("/api/applications"),
  ]);
  orp.value = sheet.data ?? null;
  all.value = list.data ?? [];
  loaded.value = true;
}

function go(delta: number): void {
  selectedDay.value = null;
  void router.push({ query: { ...route.query, mois: shiftMonth(month.value, delta) } });
}

function today(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

function edit(application: Application): void {
  error.value = "";
  editing.value = { id: application.id, value: { ...application } };
}

function addManual(): void {
  error.value = "";
  editing.value = {
    id: null,
    value: {
      sent_at: selectedDay.value ?? today(),
      method: "electronique",
      assigned_by_orp: false,
      company: "",
      job_title: "",
      status: "en_attente",
    },
  };
}

// Une candidature qui passe en Engagement : le moment de fête, par-dessus la page (docs/60).
// Un entretien proposé : une victoire, le visage ravi (docs/123 §2, R).
const celebrating = ref<string | null>(null);
const interviewWon = ref<string | null>(null);
function celebrateIf(id: number | null, status: string | undefined, company: string): void {
  const before = id === null ? undefined : all.value.find((a) => a.id === id)?.status;
  if (status === "engagement" && before !== "engagement") celebrating.value = company;
  else if (status === "entretien" && before !== "entretien" && before !== "engagement") interviewWon.value = company;
}

async function save(value: ApplicationFormValue): Promise<void> {
  if (!editing.value) return;
  const result =
    editing.value.id === null
      ? await api.POST("/api/applications", { body: { ...applicationBody(value), offer_id: null } })
      : await api.PUT("/api/applications/{application_id}", {
          params: { path: { application_id: editing.value.id } },
          body: applicationUpdateBody(value),
        });
  if (!result.data) {
    error.value = "Vérifie les champs obligatoires (date, entreprise, poste).";
    return;
  }
  celebrateIf(editing.value.id, value.status, value.company);
  editing.value = null;
  await load();
}

async function setStatus(application: Application, status: ApplicationStatus): Promise<void> {
  await api.PUT("/api/applications/{application_id}", {
    params: { path: { application_id: application.id } },
    body: {
      ...applicationBody(application),
      status,
      status_reason: application.status_reason ?? null,
      interview_at: application.interview_at ?? null,
    },
  });
  celebrateIf(application.id, status, application.company);
  await load();
}

// Retirée tout de suite, « Annuler » pendant 6 s (docs/108 §1) ; l'offre revient « en préparation ».
async function remove(application: Application): Promise<void> {
  const before = all.value;
  all.value = before.filter((a) => a.id !== application.id);
  if (openId.value === application.id) openId.value = null;
  await offerUndo({
    message: `Candidature chez ${application.company} supprimée`,
    commit: async (keepalive) => {
      const { error } = await api.DELETE("/api/applications/{application_id}", {
        params: { path: { application_id: application.id } },
        keepalive,
      });
      if (error !== undefined) return false;
      await load();
    },
    restore: () => {
      all.value = before;
    },
  });
}

// Panneau d'une candidature (docs/46 §3), depuis une carte ou la liste. Les formulaires
// (Modifier, entretien) s'ouvrent à sa place : ils passeraient sinon dessous.
const openId = ref<number | null>(null);
// Une candidature ouverte depuis Aujourd'hui (docs/95 §3) : `?candidature=ID`, avec son mois.
watch(
  () => route.query.candidature,
  (id) => {
    if (typeof id === "string" && Number(id)) openId.value = Number(id);
  },
  { immediate: true },
);
const opened = computed(() => (openId.value === null ? null : (all.value.find((a) => a.id === openId.value) ?? null)));
function fromPanel<T extends unknown[]>(action: (...args: T) => unknown): (...args: T) => void {
  return (...args: T) => {
    openId.value = null;
    void action(...args);
  };
}
const editFromPanel = fromPanel(edit);
const removeFromPanel = fromPanel(remove);
const interviewFromPanel = fromPanel(openInterview);
const prepareFromPanel = fromPanel((application: Application) => {
  preparing.value = application;
});
// S'entraîner (docs/75), depuis le « ⋯ » des entretiens.
const practicing = ref<Application | null>(null);
const practiceFromPanel = fromPanel((application: Application) => {
  practicing.value = application;
});

// Retour d'entretien (docs/23) : formulaire ouvert depuis une carte.
const interviewing = ref<{ application: Application; interview: Interview | null } | null>(null);
const preparing = ref<Application | null>(null);
const interviewError = ref("");

function openInterview(application: Application, interview: Interview | null): void {
  interviewError.value = "";
  interviewing.value = { application, interview };
}

function interviewDay(application: Application): string | null {
  return application.interview_at ? new Date(application.interview_at).toISOString().slice(0, 10) : null;
}

async function saveInterview(value: InterviewIn): Promise<void> {
  const current = interviewing.value;
  if (!current) return;
  const result = current.interview
    ? await api.PUT("/api/interviews/{interview_id}", { params: { path: { interview_id: current.interview.id } }, body: value })
    : await api.POST("/api/applications/{application_id}/interviews", {
        params: { path: { application_id: current.application.id } },
        body: value,
      });
  if (!result.data) {
    interviewError.value = "Retour non enregistré : indique au moins ton ressenti global.";
    return;
  }
  interviewing.value = null;
  await load();
}

// Fermé tout de suite, supprimé au bout de 6 s, « Annuler » d'ici là (docs/108 §1).
async function removeInterview(): Promise<void> {
  const id = interviewing.value?.interview?.id;
  if (!id) return;
  interviewing.value = null;
  await offerUndo({
    message: "Retour d'entretien supprimé",
    commit: async (keepalive) => {
      const { error } = await api.DELETE("/api/interviews/{interview_id}", { params: { path: { interview_id: id } }, keepalive });
      if (error !== undefined) return false;
      await load();
    },
    // Rien n'est parti : le retour est toujours là, dans la candidature.
    restore: () => undefined,
  });
}

// Le moment « preuves remises » : la carte qui vient devant (docs/61 §1).
const submitted = ref<{ month: string; nextDue: string | null } | null>(null);
// Annuler la remise se confirme dans la page (docs/108 §1).
const confirmingCancel = ref(false);
async function submit(done: boolean): Promise<void> {
  confirmingCancel.value = false;
  if (!orp.value) return;
  busy.value = true;
  try {
    const month = orp.value.month;
    const params = { params: { path: { month } } };
    if (done) await api.PUT("/api/orp/{month}/submission", params);
    else await api.DELETE("/api/orp/{month}/submission", params);
    submitted.value = null;
    await load();
    if (done) {
      submitted.value = { month, nextDue: null };
      const next = await api.GET("/api/orp", { params: { query: { month: shiftMonth(month, 1) } } }).catch(() => null);
      if (submitted.value?.month === month) submitted.value = { month, nextDue: next?.data?.due_date ?? null };
    }
  } finally {
    busy.value = false;
  }
}

watch(
  () => route.query.mois,
  () => void load(),
);
onMounted(() => void load());
useDataChanged(load);

// Le mois affiché et le jour choisi : ce dont parle l'assistant (docs/24 §2.2).
const assistant = useAssistant();
watch(
  [month, selectedDay],
  ([m, day]) => {
    if (!m) return;
    const label = day
      ? new Date(`${day}T12:00:00`).toLocaleDateString("fr-CH", { day: "numeric", month: "long" })
      : formatMonth(m);
    assistant.setFocus({ month: m, day: day ?? undefined, label });
  },
  { immediate: true },
);
// Lien de l'assistant vers un jour, la page étant déjà ouverte.
watch(
  () => route.query.jour,
  (jour) => {
    if (typeof jour === "string") selectedDay.value = jour;
  },
);
onUnmounted(() => assistant.setFocus(null));
</script>

<template>
  <section class="jobs-body">
    <template v-if="orp">
      <!-- Deux lignes (docs/130 §A) : le mois et les outils, puis le compte et l'état ORP. -->
      <div class="applications-head">
        <div class="month-nav">
          <IconButton
            icon="arrow-left"
            label="Mois précédent"
            data-test="prev-month"
            @click="go(-1)"
          />
          <strong data-test="month">{{ formatMonth(orp.month) }}</strong>
          <IconButton
            icon="arrow-right"
            label="Mois suivant"
            data-test="next-month"
            @click="go(1)"
          />
        </div>
        <div class="applications-tools">
          <div
            class="segmented layout-switch"
            role="radiogroup"
            aria-label="Affichage"
          >
            <button
              type="button"
              role="radio"
              :aria-checked="layout === 'calendar'"
              data-test="layout-calendar"
              @click="setLayout('calendar')"
            >
              <span class="with-icon"><AppIcon name="calendar" />Calendrier</span>
            </button>
            <button
              type="button"
              role="radio"
              :aria-checked="layout === 'list'"
              data-test="layout-list"
              @click="setLayout('list')"
            >
              <span class="with-icon"><AppIcon name="list-check" />Liste</span>
            </button>
          </div>
          <button
            type="button"
            class="pill add-application"
            data-test="add-application"
            @click="addManual"
          >
            <span class="with-icon"><AppIcon name="plus" />Ajouter</span>
          </button>
          <MoreMenu
            v-if="orp.count"
            :items="monthMenu"
            label="Actions sur le mois"
            test-id="orp-more"
          />
        </div>
      </div>
      <div class="applications-summary">
        <div
          class="month-goal"
          data-test="goal"
        >
          <span><strong>{{ orp.count }}</strong>{{ orp.target ? ` / ${orp.target}` : "" }}<span :class="{ 'goal-unit': orp.target }">{{ orp.count === 1 ? " candidature" : " candidatures" }}</span></span>
          <div
            v-if="progress !== null"
            class="budget-bar"
            role="progressbar"
            aria-label="Objectif ORP du mois"
            :aria-valuenow="Math.round(progress * 100)"
            aria-valuemin="0"
            aria-valuemax="100"
          >
            <span :style="{ width: `${progress * 100}%` }" />
          </div>
          <span
            v-else
            class="hint"
          >Objectif ORP à saisir dans les Réglages.</span>
        </div>
      </div>
      <!-- L'état des preuves du mois, un bandeau daté comme sur Aujourd'hui (docs/134) : une
           phrase, une action ; seulement s'il y a à faire ou si elles sont remises. -->
      <div
        v-if="orp.count && (orp.state !== 'en_cours' || firstIncomplete)"
        :class="['today-banner', 'applications-banner', { done: orp.state === 'remis' }]"
        data-test="orp-banner"
      >
        <span data-test="state">{{ bannerText }}</span>
        <!-- Une action ORP à la fois (docs/22 §2). -->
        <button
          v-if="orp.state === 'remis'"
          type="button"
          class="link"
          :disabled="busy"
          data-test="cancel-submit"
          @click="confirmingCancel = true"
        >
          Annuler la remise
        </button>
        <button
          v-else-if="firstIncomplete"
          type="button"
          class="link"
          data-test="complete-next"
          @click="edit(firstIncomplete)"
        >
          Compléter
        </button>
        <button
          v-else
          type="button"
          class="link"
          :disabled="busy"
          data-test="submit"
          @click="submit(true)"
        >
          Marquer comme remis
        </button>
      </div>
      <InlineConfirm
        v-if="confirmingCancel && orp.state === 'remis'"
        message="Annuler la remise de ce mois ? Les preuves repassent « à remettre »."
        confirm-label="Annuler la remise"
        cancel-label="Garder la remise"
        @confirm="submit(false)"
        @cancel="confirmingCancel = false"
      />

      <OrpSheet
        ref="sheet"
        :data="orp"
        @reload="load"
      />

      <EngagementMoment
        v-if="celebrating"
        :company="celebrating"
        @close="celebrating = null"
      />
      <SuccessCard
        v-if="interviewWon"
        face
        :title="`Un entretien chez ${interviewWon}`"
        test-id="interview-moment"
        @close="interviewWon = null"
      >
        <p>Ta candidature a retenu l'attention.</p>
      </SuccessCard>
      <SuccessCard
        v-if="submitted"
        name="preuves-orp"
        :title="`Preuves ${ofMonth(submitted.month)} remises`"
        test-id="submitted-moment"
        @close="submitted = null"
      >
        <p v-if="submitted.nextDue">
          Prochaine remise avant le {{ longDate.format(new Date(submitted.nextDue)) }}.
        </p>
      </SuccessCard>

      <!-- Aucune candidature du tout (docs/128 §3) : ce qui remplit le Suivi. -->
      <FaceState
        v-if="loaded && !all.length"
        title="Pas encore de candidature"
        data-test="applications-none-yet"
      >
        <p>Une candidature envoyée s'ajoute ici.</p>
        <div class="face-state-actions">
          <RouterLink
            to="/candidatures/offres"
            class="pill"
          >
            <span class="with-icon"><AppIcon name="briefcase" />Voir les offres</span>
          </RouterLink>
        </div>
      </FaceState>
      <div
        v-else-if="layout === 'calendar'"
        class="suivi-grid"
      >
        <div ref="calendarBox">
          <SuiviCalendar
            :month="orp.month"
            :applications="all"
            :incomplete="incomplete"
            :selected="selectedDay"
            @select="selectedDay = selectedDay === $event ? null : $event"
          />
        </div>
        <!-- À côté du calendrier, à sa hauteur (docs/134) : les onglets en haut, la liste défile
             dessous, estompée là où il reste des lignes. -->
        <section
          class="suivi-panel"
          :style="panelHeight ? { height: `${panelHeight}px` } : undefined"
          data-test="day-panel"
        >
          <h2
            v-if="selectedDay"
            class="suivi-panel-title"
          >
            {{ dayTitle.format(new Date(`${selectedDay}T12:00:00`)) }}
          </h2>
          <!-- Deux onglets (docs/133 §1) : une liste à la fois, plus de page à parcourir. -->
          <div
            v-else
            class="segmented small suivi-panel-tabs"
            role="radiogroup"
            aria-label="Liste affichée"
          >
            <button
              type="button"
              role="radio"
              :aria-checked="panelTab === 'follow'"
              data-test="panel-tab-follow"
              @click="panelTab = 'follow'"
            >
              À relancer{{ toFollowUp.length ? ` · ${toFollowUp.length}` : "" }}
            </button>
            <button
              v-if="orp.count"
              type="button"
              role="radio"
              :aria-checked="panelTab === 'declare'"
              data-test="panel-tab-declare"
              @click="panelTab = 'declare'"
            >
              À déclarer{{ toDeclare.length ? ` · ${toDeclare.length}` : "" }}
            </button>
          </div>
          <div
            ref="panelScroll"
            :class="['panel-scroll', { 'fade-top': !atTop, 'fade-bottom': !atBottom }]"
            data-test="panel-scroll"
            @scroll="onPanelScroll"
          >
            <template v-if="selectedDay || panelTab === 'follow' || !orp.count">
              <p
                v-if="!panelCards.length"
                class="hint"
              >
                <template v-if="selectedDay">
                  Aucune candidature ce jour-là.
                  <button
                    type="button"
                    class="link"
                    @click="addManual"
                  >
                    En ajouter une
                  </button>
                </template>
                <template v-else>
                  Rien à relancer.
                </template>
              </p>
              <template v-else>
                <ul class="today-rows">
                  <li
                    v-for="application in panelCards"
                    :key="application.id"
                  >
                    <ApplicationCard
                      :application="application"
                      :orp-row="rowsById.get(application.id) ?? null"
                      @open="openId = $event.id"
                      @status="setStatus"
                      @edit="edit"
                      @interview="openInterview"
                      @prepare="preparing = $event"
                      @changed="load"
                    />
                  </li>
                </ul>
              </template>
            </template>
            <section
              v-else
              class="suivi-declare"
              data-test="declare"
            >
              <h2 class="visually-hidden">
                À déclarer dans Job-Room
              </h2>
              <p
                v-if="!toDeclare.length"
                class="hint"
                data-test="declare-done"
              >
                Tout est déclaré.
              </p>
              <ul
                v-else
                class="today-rows"
              >
                <li
                  v-for="item in toDeclare"
                  :key="item.id"
                >
                  <button
                    type="button"
                    class="today-row"
                    :data-test="`declare-${item.id}`"
                    :title="`${item.company} · ${item.title}`"
                    @click="openId = item.id"
                  >
                    <span
                      class="logo"
                      :class="`c${colorIndex(item.company)}`"
                      aria-hidden="true"
                    >{{ item.company.trim().charAt(0).toUpperCase() }}</span>
                    <span class="today-row-main">
                      <strong>{{ item.company }}</strong>
                      <span class="today-row-line">{{ item.title }}</span>
                      <span class="today-row-line">envoyée le {{ item.day }}<template v-if="item.incomplete"> · à compléter</template></span>
                    </span>
                    <span class="today-row-action">Déclarer</span>
                  </button>
                </li>
              </ul>
            </section>
          </div>
        </section>
      </div>

      <template v-else>
        <label class="check all-months">
          <input
            v-model="allMonths"
            type="checkbox"
            data-test="all-months"
          > Tous les mois
        </label>
        <FaceState
          v-if="loaded && !items.length"
          :title="`Aucune candidature en ${formatMonth(orp.month)}`"
          data-test="applications-empty"
        />
        <ApplicationsTable
          v-else
          :items="items"
          :show-month="allMonths"
          @open="openId = $event.id"
          @edit="edit"
          @status="setStatus"
          @remove="remove"
        />
      </template>
    </template>
    <LoadingBlocks
      v-else
      :heights="['3rem', '22rem']"
    />
  </section>

  <SidePanel
    v-if="opened"
    open
    :title="opened.company"
    @close="openId = null"
  >
    <ApplicationPanel
      :application="opened"
      :orp-row="rowsById.get(opened.id) ?? null"
      @status="setStatus"
      @edit="editFromPanel"
      @remove="removeFromPanel"
      @interview="interviewFromPanel"
      @prepare="prepareFromPanel"
      @practice="practiceFromPanel"
      @changed="load"
    />
  </SidePanel>
  <InterviewPractice
    v-if="practicing"
    :application="practicing"
    @close="practicing = null"
  />
  <InterviewPreparation
    v-if="preparing"
    :application="preparing"
    @close="preparing = null"
  />
  <InterviewForm
    v-if="interviewing"
    :company="interviewing.application.company"
    :initial="interviewing.interview"
    :held-at="interviewing.interview?.held_at ?? interviewDay(interviewing.application)"
    :with-employer-feedback="['refus', 'engagement'].includes(interviewing.application.status ?? '')"
    :error="interviewError"
    @submit="saveInterview"
    @remove="removeInterview"
    @close="interviewing = null"
  />
  <ApplicationForm
    v-if="editing"
    :title="editing.id === null ? 'Ajouter une candidature' : 'Modifier la candidature'"
    :initial="editing.value"
    :with-status="editing.id !== null"
    :error="error"
    @submit="save"
    @close="editing = null"
  />
</template>
