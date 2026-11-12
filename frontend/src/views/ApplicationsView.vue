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
import NetworkError from "../components/NetworkError.vue";
import { isNetworkError } from "../network";
import ApplicationCard from "../components/ApplicationCard.vue";
import OfferLine from "../components/OfferLine.vue";
import ApplicationPanel from "../components/ApplicationPanel.vue";
import SidePanel from "../components/SidePanel.vue";
import ApplicationForm, { type ApplicationFormValue } from "../components/ApplicationForm.vue";
import DisclosureRow from "../components/DisclosureRow.vue";
import InterviewForm from "../components/InterviewForm.vue";
import InterviewPractice from "../components/InterviewPractice.vue";
import InterviewPreparation from "../components/InterviewPreparation.vue";
import MomentScreen from "../components/MomentScreen.vue";
import OrpBlocks from "../components/OrpBlocks.vue";
import OrpProofCard from "../components/OrpProofCard.vue";
import OrpGoalCard from "../components/OrpGoalCard.vue";
import OrpSearchRows from "../components/OrpSearchRows.vue";
import OrpSheet from "../components/OrpSheet.vue";
import SuiviCalendar from "../components/SuiviCalendar.vue";
import CardHead from "../components/CardHead.vue";
import FaceState from "../components/FaceState.vue";
import MoreMenu, { type MoreMenuItem } from "../components/MoreMenu.vue";
import EngagementMoment from "../components/EngagementMoment.vue";
import ShowMore from "../components/ShowMore.vue";
import SuccessCard from "../components/SuccessCard.vue";
import { applicationBody, applicationUpdateBody } from "../applicationBody";
import { useAssistant } from "../composables/useAssistant";
import { dateInList, dateInSentence } from "../dates";
import { formatMonth, ofMonth, orpLeftLine, plural, shiftMonth } from "../format";
import { useDataChanged } from "../composables/useDataChanged";
import { usePageReady } from "../composables/usePageTransition";
import { offerUndo } from "../composables/useUndo";
import InlineConfirm from "../components/InlineConfirm.vue";
import SentCard from "../components/SentCard.vue";
import SentDetail from "../components/SentDetail.vue";
import { usePhone } from "../composables/usePhone";
import { sentSections } from "../sentList";

// Deux pages sur les mêmes données (docs/139 étape 8b ; B7 et B8, Kevin, 2026-11-04) :
// - Candidatures › Envoyées (maquette Envoyees, 7.11.2026) : l'objectif ORP du mois et sa barre, puis les
//   candidatures en rubriques (À relancer, Entretiens, Cette semaine, Plus tôt), avec la carte d'À traiter ;
// - le Suivi ORP (/bilan/orp, maquette Orp) : le mois, l'objectif, le bandeau de la remise quand il est utile,
//   l'export, les recherches du mois, puis « Ajouter », « À déclarer » et le calendrier.
const TODO_ROWS = 3;
const { phone } = usePhone();
// Ordinateur dès 1 024 px (maquette du 8 novembre, CandidaturesOrdinateurB état « Envoyées ») : deux colonnes, la
// liste et la candidature choisie à droite, jamais vide (la première par défaut).
const { phone: wideQuery } = usePhone("(min-width: 1024px)");
const twoColumns = computed(() => wideQuery.value && !phone.value && !orpPage);

const route = useRoute();
const router = useRouter();
const orpPage = route.name === "orp-month";
const orp = ref<OrpMonth | null>(null);
usePageReady(orpPage ? "orp-month" : "applications", () => !!orp.value);
const all = ref<Application[]>([]);
const editing = ref<{ id: number | null; value: ApplicationFormValue } | null>(null);
const error = ref("");
const loaded = ref(false);
const busy = ref(false);
// ?jour=AAAA-MM-JJ (lien du rappel « fais le point », docs/23 §1) : le jour s'ouvre d'emblée.
const selectedDay = ref<string | null>(typeof route.query.jour === "string" ? route.query.jour : null);
const month = computed(() => orp.value?.month ?? "");
const monthItems = computed(() => all.value.filter((a) => a.orp_month === month.value));
// Le filtre par mots (poste, entreprise ; décision de Kevin, 27.10) : dans tous les mois, sans accents ni
// casse ; ?q= dans l'adresse, où mène « Tout voir (N) » de la recherche globale.
const words = ref(typeof route.query.q === "string" ? route.query.q : "");
function plain(text: string): string {
  return text.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}
const wanted = computed(() => plain(words.value).split(/\s+/).filter(Boolean));
function matches(a: Application): boolean {
  const text = plain(`${a.job_title} ${a.company} ${a.location ?? ""}`);
  return wanted.value.every((w) => text.includes(w));
}
// Les rubriques d'Envoyées ; venues de la recherche globale avec des mots, seulement ce qui correspond.
const sections = computed(() => sentSections(wanted.value.length ? all.value.filter(matches) : all.value));
// L'objectif du mois (maquette Envoyees) : « 6 sur 10 », la barre, et ce qui reste d'ici l'échéance ORP (§11).
const goal = computed(() => {
  const data = orp.value;
  if (!data?.target) return null;
  return {
    percent: Math.min(100, Math.round((data.count / data.target) * 100)),
    left: orpLeftLine(data.count, data.target, data.month, data.due_date),
  };
});
let wordsTimer: ReturnType<typeof setTimeout> | undefined;
watch(words, (value) => {
  clearTimeout(wordsTimer);
  wordsTimer = setTimeout(() => {
    const q = value.trim() || undefined;
    if (q !== route.query.q) void router.replace({ query: { ...route.query, q } });
  }, 300);
});
const rowsById = computed(() => new Map((orp.value?.rows ?? []).map((r) => [r.application_id, r])));
const incomplete = computed(() => new Set((orp.value?.rows ?? []).filter((r) => r.missing.length).map((r) => r.application_id)));
// À déclarer dans Job-Room (docs/85) : les candidatures du mois pas encore marquées déclarées,
// date · entreprise · poste ; un clic ouvre le panneau, avec l'offre et les champs à copier.
const toDeclare = computed(() =>
  (orp.value?.rows ?? [])
    .filter((r) => !r.declared_at)
    .map((r) => {
      const application = all.value.find((a) => a.id === r.application_id);
      const day = application ? dateInSentence(`${application.sent_at}T12:00:00`) : `le ${r.date}`;
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
    { label: "Télécharger en CSV (Excel)", test: "csv", icon: "download", href: `/api/orp/${data.month}/csv`, download: true },
  ];
});
const firstIncomplete = computed(() => monthItems.value.find((a) => incomplete.value.has(a.id)) ?? null);
const dayTitle = new Intl.DateTimeFormat("fr-CH", { weekday: "long", day: "numeric", month: "long" });
// Le bandeau des preuves (docs/134) : ce qui reste à faire, et pour quand.
const bannerText = computed(() => {
  const d = orp.value;
  if (!d) return "";
  const month = ofMonth(d.month);
  if (d.state === "remis" && d.submitted_at) return `Justificatifs ${month} remis ${dateInSentence(d.submitted_at)}.`;
  const due = dateInSentence(`${d.due_date}T12:00:00`);
  if (d.incomplete) return `Justificatifs ${month} : ${plural(d.incomplete, "ligne", "lignes")} à compléter, remise avant ${due}.`;
  return `Justificatifs ${month} prêts : à remettre avant ${due}.`;
});
// Les repliables du détail, comme ceux du Bilan (règles §3) : une icône, un titre et l'enseignement
// en une phrase, visible replié.
const calendarLine = computed(() => {
  const missing = monthItems.value.filter((a) => incomplete.value.has(a.id)).length;
  if (missing) return `${plural(missing, "candidature", "candidatures")} à compléter pour l’ORP`;
  const days = new Set(monthItems.value.map((a) => a.sent_at)).size;
  return days ? `${plural(days, "jour", "jours")} avec au moins une candidature` : "Aucune candidature ce mois-ci";
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

// À déclarer dans Job-Room (docs/133 §1) : trois lignes, « Afficher plus » pour le reste.
const showAllDeclare = ref(false);
const declareShown = computed(() => (showAllDeclare.value ? toDeclare.value : toDeclare.value.slice(0, TODO_ROWS)));
// Le calendrier replié s'ouvre de lui-même quand un jour est demandé (lien « fais le point »,
// assistant) : la clé le recrée, ouvert.
const calendarKey = ref(0);

// Une panne de réseau au chargement : l'écran « Pas de connexion » (planche « Illustrations »).
const offline = ref(false);
async function load(): Promise<void> {
  const wanted = typeof route.query.mois === "string" ? route.query.mois : undefined;
  try {
    const [sheet, list] = await Promise.all([
      api.GET("/api/orp", { params: { query: { month: wanted } } }),
      api.GET("/api/applications"),
    ]);
    orp.value = sheet.data ?? null;
    all.value = list.data ?? [];
    offline.value = false;
    loaded.value = true;
  } catch (cause) {
    if (!isNetworkError(cause)) throw cause;
    offline.value = true;
  }
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
// Un entretien proposé : « Entretien décroché », en écran plein, et « Préparer l'entretien » (docs/141, 12).
// Un refus : une réponse qui encourage et propose la suite, jamais triste (docs/141, 13 ; règle des émoticônes).
type Moment = { id: number; company: string };
const celebrating = ref<string | null>(null);
const interviewWon = ref<Moment | null>(null);
const refused = ref<Moment | null>(null);
function celebrateIf(id: number, status: string | undefined, company: string): void {
  const before = all.value.find((a) => a.id === id)?.status;
  if (status === "engagement" && before !== "engagement") celebrating.value = company;
  else if (status === "entretien" && before !== "entretien" && before !== "engagement") interviewWon.value = { id, company };
  else if (status === "refus" && before !== "refus") refused.value = { id, company };
  // L'écran plein prend toute la place : le panneau de la candidature se ferme.
  if (interviewWon.value || refused.value) openId.value = null;
}
// « Préparer l'entretien » ouvre la préparation de cette candidature.
function prepareWon(): void {
  preparing.value = all.value.find((a) => a.id === interviewWon.value?.id) ?? null;
  interviewWon.value = null;
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
  // Les champs obligatoires se vérifient sous chaque champ (règles §4, Formulaire) : il ne reste ici
  // que le refus du serveur, dit tel quel.
  if (!result.data) {
    const detail = (result.error as { detail?: unknown } | undefined)?.detail;
    error.value = typeof detail === "string" ? detail : "Enregistrement impossible pour l’instant : réessaie.";
    return;
  }
  celebrateIf(editing.value.id ?? result.data.id, value.status, value.company);
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
      interview_place: application.interview_place ?? null,
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
const firstSent = computed(() => sections.value.flatMap((section) => section.items)[0] ?? null);
// À droite sur ordinateur : la candidature ouverte, ou la première de la liste.
const shown = computed(() => (twoColumns.value ? (opened.value ?? firstSent.value) : null));
// Sur téléphone, hors du Suivi ORP, la candidature s'ouvre en écran poussé (§8.3) ; « ‹ Envoyées » revient à la liste.
const sentScreen = computed(() => phone.value && !orpPage);
function closeScreen(): void {
  openId.value = null;
  if (!route.query.candidature) return;
  if (window.history.state?.back) router.back();
  else {
    const query = { ...route.query };
    delete query.candidature;
    void router.replace({ query });
  }
}
// Le trait bleu de la carte choisie (§8.1) : au centre vertical de la carte, mesuré dans la section.
const body = ref<HTMLElement | null>(null);
const linkTop = ref<number | null>(null);
function placeLink(): void {
  const root = body.value;
  const card = root?.querySelector<HTMLElement>(".sent-list .list-card[aria-current='true']");
  if (!root || !card || !twoColumns.value) {
    linkTop.value = null;
    return;
  }
  const a = root.getBoundingClientRect();
  const b = card.getBoundingClientRect();
  // Le trait fait 2 px : son bord haut est 1 px au-dessus du centre.
  linkTop.value = Math.round(b.top - a.top + b.height / 2) - 1;
}
const linkObserver = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(() => placeLink());
watch(body, (el, old) => {
  if (old) linkObserver?.unobserve(old);
  if (el) linkObserver?.observe(el);
});
watch([shown, twoColumns], () => void nextTick(placeLink), { flush: "post" });
onUnmounted(() => linkObserver?.disconnect());
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
    message: "Retour d’entretien supprimé",
    commit: async (keepalive) => {
      const { error } = await api.DELETE("/api/interviews/{interview_id}", { params: { path: { interview_id: id } }, keepalive });
      if (error !== undefined) return false;
      await load();
    },
    // Rien n'est parti : le retour est toujours là, dans la candidature.
    restore: () => undefined,
  });
}

// Sur téléphone, la carte en tête du Suivi ORP porte la remise du mois précédent (PR 29) : le bandeau du mois ne la
// répète pas, il ne reste que pour « Compléter ».
const proofCovers = computed(
  () => phone.value && !!orp.value && orp.value.month === shiftMonth(today().slice(0, 7), -1) && (orp.value.state === "remis" || !firstIncomplete.value),
);

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
// « Ajouter une recherche » depuis le Bilan (maquette du 8 novembre) : /bilan/orp?ajouter=1 ouvre le formulaire.
onMounted(() => {
  void load();
  if (route.query.ajouter === "1") {
    addManual();
    const query = { ...route.query };
    delete query.ajouter;
    void router.replace({ query });
  }
});
useDataChanged(load);

// Le mois affiché et le jour choisi : ce dont parle l'assistant (docs/24 §2.2).
const assistant = useAssistant();
watch(
  [month, selectedDay],
  ([m, day]) => {
    if (!m) return;
    const label = day
      ? dateInList(`${day}T12:00:00`)
      : formatMonth(m);
    assistant.setFocus({ month: m, day: day ?? undefined, label });
  },
  { immediate: true },
);
// Lien de l'assistant vers un jour, la page étant déjà ouverte : le calendrier s'ouvre.
watch(
  () => route.query.jour,
  (jour) => {
    if (typeof jour !== "string") return;
    selectedDay.value = jour;
    calendarKey.value += 1;
  },
);
onUnmounted(() => assistant.setFocus(null));
</script>

<template>
  <MomentScreen
    v-if="interviewWon"
    scene="objectif"
    :title="`Entretien décroché chez ${interviewWon.company}.`"
    line="Ta candidature a retenu l’attention."
    data-test="interview-moment"
  >
    <template #actions>
      <button
        type="button"
        class="button-link primary-link sent-screen-primary"
        data-test="interview-prepare"
        @click="prepareWon"
      >
        Préparer l’entretien
      </button>
      <button
        type="button"
        class="link sent-screen-next"
        data-test="interview-later"
        @click="interviewWon = null"
      >
        Plus tard
      </button>
    </template>
  </MomentScreen>
  <MomentScreen
    v-else-if="refused"
    icon="mail"
    :title="`Réponse de ${refused.company}.`"
    line="Pas pour cette fois. Chaque candidature envoyée te rapproche d’un oui."
    data-test="refusal-moment"
  >
    <template #actions>
      <RouterLink
        to="/candidatures/offres"
        class="button-link primary-link sent-screen-primary"
        data-test="refusal-next"
      >
        Préparer la prochaine
      </RouterLink>
      <button
        type="button"
        class="link sent-screen-next"
        data-test="refusal-close"
        @click="refused = null"
      >
        Voir mes candidatures
      </button>
    </template>
  </MomentScreen>
  <section
    v-else
    ref="body"
    :class="['jobs-body', { 'orp-page': orpPage, 'sent-columns': twoColumns, 'blocks-page orp-page-blocks': orpPage && phone }]"
  >
    <!-- Trait entre la liste et le détail, et le lien vers la carte choisie (§8.1) : décoratifs, la sélection est
         portée par aria-current. -->
    <span
      v-if="twoColumns"
      class="sent-divider"
      aria-hidden="true"
    />
    <span
      v-if="twoColumns && linkTop !== null"
      class="sent-link"
      :style="{ top: `${linkTop}px` }"
      aria-hidden="true"
      data-test="sent-link"
    />
    <aside
      v-if="shown"
      class="sent-detail"
      :aria-label="shown.company"
      data-test="sent-detail"
    >
      <SentDetail
        :application="shown"
        :orp-row="rowsById.get(shown.id) ?? null"
        @status="setStatus"
        @edit="editFromPanel"
        @remove="removeFromPanel"
        @interview="interviewFromPanel"
        @prepare="prepareFromPanel"
        @practice="practiceFromPanel"
        @changed="load"
      />
    </aside>
    <template v-if="orp">
      <template v-if="orpPage">
        <!-- La tête de la sous-page (maquette Orp) : le retour au Bilan et le titre. -->
        <header class="orp-page-head">
          <RouterLink
            to="/bilan"
            class="icon-button icon-only"
            aria-label="Retour au Bilan"
            data-test="orp-back"
          >
            <AppIcon name="chevron-left" />
          </RouterLink>
          <h1>Suivi ORP</h1>
        </header>
        <!-- Téléphone : le mois précédent à remettre, ou remis, en tête (récapitulatif du 11 novembre, PR 29). -->
        <OrpProofCard
          v-if="phone"
          @changed="load()"
        />
        <!-- Les chevrons ‹ › de la maquette Orp ; pas de mois suivant après le mois en cours. -->
        <div class="month-nav orp-page-month">
          <IconButton
            icon="chevron"
            label="Mois précédent"
            class="orp-month-prev"
            data-test="prev-month"
            @click="go(-1)"
          />
          <strong data-test="month">{{ formatMonth(orp.month) }}</strong>
          <IconButton
            icon="chevron"
            label="Mois suivant"
            :disabled="orp.month >= today().slice(0, 7)"
            data-test="next-month"
            @click="go(1)"
          />
        </div>
        <!-- Téléphone (lot 18, §10.2 ; maquette Orp) : l'objectif, « À déclarer à l'ORP » et « Recherches du mois » en
             blocs, l’export dans le dernier bloc. -->
        <OrpBlocks
          v-if="phone"
          :data="orp"
          @open="openId = $event"
          @export="sheet?.printPdf()"
        />
        <OrpGoalCard
          v-else
          :data="orp"
        />
        <!-- L'état des preuves du mois, juste sous l'objectif (B8) : une phrase, une action ; seulement s'il y
             a à faire ou si elles sont remises (docs/134). -->
        <div
          v-if="orp.count && (orp.state !== 'en_cours' || firstIncomplete) && !proofCovers"
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
          message="Annuler la remise de ce mois ? Les justificatifs repassent « à remettre »."
          confirm-label="Annuler la remise"
          cancel-label="Garder la remise"
          @confirm="submit(false)"
          @cancel="confirmingCancel = false"
        />
        <!-- L'export du formulaire ; le CSV et le PDF avec le journal restent dans le « ⋯ » (docs/85 §3). -->
        <div class="orp-export-row">
          <button
            v-if="!phone"
            type="button"
            class="secondary orp-export"
            data-test="pdf"
            @click="sheet?.printPdf()"
          >
            <AppIcon name="download" />Exporter le formulaire (PDF)
          </button>
          <MoreMenu
            v-if="orp.count"
            :items="monthMenu.slice(1)"
            label="Plus d’actions sur le mois"
            test-id="orp-more"
          />
        </div>
        <OrpSheet
          ref="sheet"
          :data="orp"
          @reload="load"
        />
        <section
          v-if="!phone"
          class="orp-last orp-month-list"
          aria-labelledby="orp-month-title"
        >
          <h2 id="orp-month-title">
            <span>Recherches du mois</span>
            <span>{{ plural(orp.rows.length, "entrée", "entrées") }}</span>
          </h2>
          <OrpSearchRows
            :rows="orp.rows"
            open
            @open="openId = $event"
          />
        </section>
        <button
          type="button"
          class="pill add-application"
          data-test="add-application"
          @click="addManual"
        >
          <span class="with-icon"><AppIcon name="plus" />Ajouter une recherche</span>
        </button>
      </template>
      <template v-else>
        <!-- L'objectif du mois, vers le Suivi ORP (maquette Envoyees) : le nombre, la barre, ce qui reste. -->
        <RouterLink
          :to="goal ? '/bilan/orp' : { path: '/reglages', query: { rubrique: 'recherche' } }"
          class="sent-goal"
          data-test="goal"
        >
          <span class="sent-goal-head">
            <span>Objectif ORP {{ ofMonth(orp.month) }}</span>
            <span
              class="sent-goal-count"
              data-test="goal-count"
            >{{ goal ? `${orp.count} sur ${orp.target}` : "À indiquer" }}<AppIcon
              name="chevron"
              class="sent-goal-chevron"
            /></span>
          </span>
          <span
            v-if="goal"
            role="progressbar"
            :aria-valuenow="orp.count"
            aria-valuemin="0"
            :aria-valuemax="orp.target ?? 0"
            aria-label="Objectif ORP"
            class="sent-goal-bar"
          ><span :style="{ width: `${goal.percent}%` }" /></span>
          <span class="sent-goal-left">{{ goal ? `${goal.left} · voir le bilan` : "Le nombre de recherches que l’ORP te demande chaque mois" }}</span>
        </RouterLink>
      </template>

      <EngagementMoment
        v-if="celebrating"
        :company="celebrating"
        @close="celebrating = null"
      />
      <SuccessCard
        v-if="submitted"
        name="preuves-orp"
        :title="`Justificatifs ${ofMonth(submitted.month)} remis`"
        test-id="submitted-moment"
        @close="submitted = null"
      >
        <p v-if="submitted.nextDue">
          Prochaine remise avant {{ dateInSentence(`${submitted.nextDue}T12:00:00`) }}.
        </p>
      </SuccessCard>

      <!-- Aucune candidature du tout (docs/128 §3) : ce qui remplit le Suivi. -->
      <FaceState
        v-if="!orpPage && loaded && !all.length"
        title="Pas encore de candidature"
        data-test="applications-none-yet"
      >
        <p>Une candidature envoyée s’ajoute ici.</p>
        <div class="face-state-actions">
          <RouterLink
            to="/candidatures/offres"
            class="button-link primary-link"
          >
            <span class="with-icon"><AppIcon name="briefcase" />Voir les offres</span>
          </RouterLink>
        </div>
      </FaceState>
      <template v-else-if="loaded">
        <!-- Envoyées : les rubriques, la carte d'À traiter (maquette Envoyees). -->
        <template v-if="!orpPage">
          <p
            v-if="wanted.length"
            class="sent-words"
            data-test="sent-words"
          >
            {{ sections.length ? `Candidatures « ${words.trim()} »` : `Aucune candidature pour « ${words.trim()} ».` }}
            <button
              type="button"
              class="link"
              data-test="sent-words-clear"
              @click="words = ''"
            >
              Tout afficher
            </button>
          </p>
          <ul
            class="offer-cards sent-list"
            data-test="sent-list"
          >
            <template
              v-for="section in sections"
              :key="section.key"
            >
              <li
                class="offer-day"
                :data-test="`sent-section-${section.key}`"
              >
                <h2 class="offer-day-title">
                  <span class="offer-day-name">{{ section.title }}</span>
                  <span class="offer-day-count">{{ plural(section.items.length, "candidature", "candidatures") }}</span>
                </h2>
              </li>
              <li
                v-for="application in section.items"
                :key="application.id"
              >
                <SentCard
                  :application="application"
                  :section="section.key"
                  :selected="(shown?.id ?? openId) === application.id"
                  @select="openId = application.id"
                />
              </li>
            </template>
          </ul>
        </template>
        <section
          v-if="orpPage && orp.count && !phone"
          class="dash-card suivi-todo suivi-declare"
          aria-label="À déclarer dans Job-Room"
          data-test="declare"
        >
          <CardHead
            title="À déclarer"
            :count="toDeclare.length || undefined"
          />
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
              v-for="item in declareShown"
              :key="item.id"
            >
              <!-- La Ligne d'offre compacte (planche « Ligne d'offre ») : « Déclarer » à droite. -->
              <OfferLine
                :title="item.title"
                :company="item.company"
                :location="all.find((x) => x.id === item.id)?.location ?? null"
                :state="`Envoyée ${item.day}${item.incomplete ? ' · à compléter' : ''}`"
                :urgent="item.incomplete"
                action="Déclarer"
                :action-test="`declare-${item.id}`"
                @select="openId = item.id"
                @action="openId = item.id"
              />
            </li>
          </ul>
          <ShowMore
            v-if="toDeclare.length > TODO_ROWS"
            v-model="showAllDeclare"
            :hidden="toDeclare.length - TODO_ROWS"
            test-id="declare-all"
          />
        </section>

        <!-- Le calendrier replié (règles §3.4), dans le Suivi ORP ; sur téléphone, le Suivi ORP s'arrête à
             « À déclarer » (Kevin, 6.11). -->
        <section
          v-if="orpPage && !phone"
          class="bilan-detail suivi-detail"
          data-test="suivi-detail"
        >
          <DisclosureRow
            :key="calendarKey"
            :title="`Calendrier ${ofMonth(orp.month)}`"
            icon="calendar"
            :description="calendarLine"
            :start-open="!!selectedDay"
            data-test="detail-calendar"
          >
            <SuiviCalendar
              :month="orp.month"
              :applications="all"
              :incomplete="incomplete"
              :selected="selectedDay"
              @select="selectedDay = selectedDay === $event ? null : $event"
            />
            <!-- Le jour choisi : ses candidatures, sous le calendrier. -->
            <section
              v-if="selectedDay"
              class="suivi-day"
              data-test="day-panel"
            >
              <h3 class="suivi-panel-title">
                {{ dayTitle.format(new Date(`${selectedDay}T12:00:00`)) }}
              </h3>
              <p
                v-if="!dayCards.length"
                class="hint"
              >
                Aucune candidature ce jour-là.
                <button
                  type="button"
                  class="link"
                  @click="addManual"
                >
                  En ajouter une
                </button>
              </p>
              <ul
                v-else
                class="today-rows"
              >
                <li
                  v-for="application in dayCards"
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
            </section>
          </DisclosureRow>
        </section>
      </template>
    </template>
    <NetworkError
      v-else-if="offline"
      @retry="load()"
    />
    <LoadingBlocks
      v-else
      :heights="['3rem', '22rem']"
    />
  </section>

  <!-- Téléphone (§8.3, EnvoyeeDetail) : la candidature est un écran poussé, par-dessus la liste et la barre d'onglets. -->
  <div
    v-if="opened && sentScreen"
    class="sent-screen"
    data-test="sent-screen"
  >
    <SentDetail
      phone
      :application="opened"
      :orp-row="rowsById.get(opened.id) ?? null"
      @close="closeScreen"
      @status="setStatus"
      @edit="editFromPanel"
      @remove="removeFromPanel"
      @interview="interviewFromPanel"
      @prepare="prepareFromPanel"
      @practice="practiceFromPanel"
      @changed="load"
    />
  </div>
  <SidePanel
    v-else-if="opened && !twoColumns"
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
