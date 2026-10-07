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
import ApplicationCard from "../components/ApplicationCard.vue";
import ApplicationForm, { type ApplicationFormValue } from "../components/ApplicationForm.vue";
import ApplicationsTable from "../components/ApplicationsTable.vue";
import InterviewForm from "../components/InterviewForm.vue";
import OrpSheet from "../components/OrpSheet.vue";
import SuiviCalendar from "../components/SuiviCalendar.vue";
import { applicationBody, applicationUpdateBody } from "../applicationBody";
import { formatMonth, shiftMonth } from "../format";

// Onglet Suivi (docs/22) : candidatures et preuves ORP du mois, en calendrier ou en liste.
const REMIND_AFTER_DAYS = 10;
const VIEW_KEY = "jobbot-suivi-vue";

const route = useRoute();
const router = useRouter();
const orp = ref<OrpMonth | null>(null);
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
const firstIncomplete = computed(() => monthItems.value.find((a) => incomplete.value.has(a.id)) ?? null);
const progress = computed(() => (orp.value?.target ? Math.min(1, orp.value.count / orp.value.target) : null));
const longDate = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "long", year: "numeric" });
const dayTitle = new Intl.DateTimeFormat("fr-CH", { weekday: "long", day: "numeric", month: "long" });
const stateLabel = computed(() => {
  const d = orp.value;
  if (!d) return "";
  if (d.state === "remis" && d.submitted_at) return `Preuves remises le ${longDate.format(new Date(d.submitted_at))}`;
  if (d.state === "a_remettre") return `Preuves à remettre avant le ${longDate.format(new Date(d.due_date))}`;
  return `En cours · remise avant le ${longDate.format(new Date(d.due_date))}`;
});
const toFollowUp = computed(() => {
  const limit = new Date();
  limit.setDate(limit.getDate() - REMIND_AFTER_DAYS);
  const day = limit.toISOString().slice(0, 10);
  return all.value.filter((a) => a.status === "en_attente" && a.sent_at <= day);
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

// Hauteur du panneau = hauteur du calendrier (écran large) ; estompage selon le défilement.
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
// Nouvelles cartes (jour choisi, mois) : retour en haut, estompage recalculé.
watch(panelCards, async () => {
  await nextTick();
  if (panelScroll.value) panelScroll.value.scrollTop = 0;
  onPanelScroll();
});
onUnmounted(() => observer?.disconnect());

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

function editById(id: number): void {
  const application = all.value.find((a) => a.id === id);
  if (application) edit(application);
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
  await load();
}

async function remove(application: Application): Promise<void> {
  if (!window.confirm(`Supprimer la candidature chez ${application.company} ? L'offre revient « en préparation ».`)) {
    return;
  }
  await api.DELETE("/api/applications/{application_id}", {
    params: { path: { application_id: application.id } },
  });
  await load();
}

// Retour d'entretien (docs/23) : formulaire ouvert depuis une carte.
const interviewing = ref<{ application: Application; interview: Interview | null } | null>(null);
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

async function removeInterview(): Promise<void> {
  const current = interviewing.value;
  if (!current?.interview || !window.confirm("Supprimer ce retour d'entretien ?")) return;
  await api.DELETE("/api/interviews/{interview_id}", { params: { path: { interview_id: current.interview.id } } });
  interviewing.value = null;
  await load();
}

async function submit(done: boolean): Promise<void> {
  if (!orp.value || (!done && !window.confirm("Annuler la remise de ce mois ?"))) return;
  busy.value = true;
  try {
    const params = { params: { path: { month: orp.value.month } } };
    if (done) await api.PUT("/api/orp/{month}/submission", params);
    else await api.DELETE("/api/orp/{month}/submission", params);
    await load();
  } finally {
    busy.value = false;
  }
}

watch(
  () => route.query.mois,
  () => void load(),
);
onMounted(() => void load());
</script>

<template>
  <section class="jobs-body">
    <template v-if="orp">
      <div class="applications-head">
        <div class="month-nav">
          <button
            type="button"
            class="secondary small"
            aria-label="Mois précédent"
            data-test="prev-month"
            @click="go(-1)"
          >
            ←
          </button>
          <strong data-test="month">{{ formatMonth(orp.month) }}</strong>
          <button
            type="button"
            class="secondary small"
            aria-label="Mois suivant"
            data-test="next-month"
            @click="go(1)"
          >
            →
          </button>
        </div>
        <div
          class="month-goal"
          data-test="goal"
        >
          <span><strong>{{ orp.count }}</strong>{{ orp.target ? ` / ${orp.target}` : "" }} candidature(s)</span>
          <div
            v-if="progress !== null"
            class="budget-bar"
            role="progressbar"
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
        <span
          :class="['badge', orp.state === 'remis' ? 'new' : '']"
          data-test="state"
        >{{ stateLabel }}</span>
        <!-- Une action ORP à la fois (docs/22 §2). -->
        <template v-if="orp.count">
          <button
            v-if="orp.state === 'remis'"
            type="button"
            class="link"
            :disabled="busy"
            data-test="cancel-submit"
            @click="submit(false)"
          >
            Annuler la remise
          </button>
          <button
            v-else-if="firstIncomplete"
            type="button"
            class="primary small"
            data-test="complete-next"
            @click="edit(firstIncomplete)"
          >
            Compléter {{ orp.incomplete }} ligne(s) <AppIcon name="chevron" />
          </button>
          <button
            v-else
            type="button"
            class="primary small"
            :disabled="busy"
            data-test="submit"
            @click="submit(true)"
          >
            Marquer comme remis <AppIcon name="chevron" />
          </button>
        </template>
        <button
          type="button"
          class="secondary small"
          data-test="add-application"
          @click="addManual"
        >
          Ajouter une candidature
        </button>
      </div>

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
          Calendrier
        </button>
        <button
          type="button"
          role="radio"
          :aria-checked="layout === 'list'"
          data-test="layout-list"
          @click="setLayout('list')"
        >
          Liste
        </button>
      </div>

      <div
        v-if="layout === 'calendar'"
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
        <!-- Panneau à la hauteur du calendrier, liste défilante estompée en haut et en bas
             tant qu'il reste des cartes de ce côté (retour d'usage du 2026-10-07). -->
        <aside
          class="suivi-panel"
          :style="panelHeight ? { height: `${panelHeight}px` } : undefined"
          data-test="day-panel"
        >
          <h3>{{ selectedDay ? dayTitle.format(new Date(`${selectedDay}T12:00:00`)) : "À relancer" }}</h3>
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
              Rien à relancer. Clique sur un jour pour voir ses candidatures.
            </template>
          </p>
          <div
            v-else
            ref="panelScroll"
            :class="['panel-scroll', { 'fade-top': !atTop, 'fade-bottom': !atBottom }]"
            data-test="panel-scroll"
            @scroll="onPanelScroll"
          >
            <ApplicationCard
              v-for="application in panelCards"
              :key="application.id"
              :application="application"
              :orp-row="rowsById.get(application.id) ?? null"
              @status="setStatus"
              @edit="edit"
              @remove="remove"
              @interview="openInterview"
            />
          </div>
        </aside>
      </div>

      <template v-else>
        <label class="check all-months">
          <input
            v-model="allMonths"
            type="checkbox"
            data-test="all-months"
          > Tous les mois
        </label>
        <p
          v-if="loaded && !items.length"
          class="muted empty"
        >
          Aucune candidature en {{ formatMonth(orp.month) }}. Depuis une offre, « Marquer comme envoyée » l'ajoute ici.
        </p>
        <ApplicationsTable
          v-else
          :items="items"
          :show-month="allMonths"
          @edit="edit"
          @status="setStatus"
          @remove="remove"
        />
      </template>

      <details
        class="orp-details"
        data-test="orp-details"
      >
        <summary>Formulaire ORP du mois : tableau, PDF, CSV, saisie Job-Room</summary>
        <OrpSheet
          :data="orp"
          embedded
          @reload="load"
          @edit="editById"
        />
      </details>
    </template>
  </section>

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
