<script setup lang="ts">
import { computed, defineAsyncComponent, h, nextTick, onBeforeUnmount, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import sparkles from "../assets/accessoires/accessoire-etincelles.webp";
import { api, QUIET, type AlertsPage, type CriteriaIn, type Offer, type SettingsModel } from "../api/client";
import type { components } from "../api/schema";
import AppIcon from "../components/AppIcon.vue";
import BrandMark from "../components/BrandMark.vue";
import CompanyLogo from "../components/CompanyLogo.vue";
import IconButton from "../components/IconButton.vue";
import SceneIllustration, { type SceneName } from "../components/SceneIllustration.vue";
import type WelcomeCriteriaComponent from "../components/WelcomeCriteria.vue";
import type { CriteriaSources } from "../components/WelcomeCriteria.vue";
import LoadingBlocks from "../components/LoadingBlocks.vue";
// Les écrans de chargement (§53) : chargés à la demande, seulement quand un CV se lit.
const LoadingSteps = defineAsyncComponent(() => import("../components/LoadingSteps.vue"));
import TroupeScene from "../components/TroupeScene.vue";
import ScoreRing from "../components/ScoreRing.vue";
import ProfileCompletionForm, { languageLabel, type Level } from "../components/ProfileCompletionForm.vue";
import { useAssistant } from "../composables/useAssistant";
import { useAuth } from "../composables/useAuth";
import { useJobA1Extension } from "../composables/useJobA1Extension";
import { usePhone } from "../composables/usePhone";
import { offerUndo } from "../composables/useUndo";
import { companyPlace, rateText, remoteText, scoreWord } from "../format";
import { whyLine } from "../whyLine";
import { displayTitle } from "../offerTitle";

// Une étape, un fichier chargé à part (allègement (b), issue #797) : seule l'étape affichée pèse sur l'ouverture des
// premiers pas. Les autres sont préchargées quand le navigateur est au repos ; si l'une tarde plus de 300 ms, les blocs
// de chargement (LoadingBlocks attend lui-même 300 ms) remplacent l'écran vide.
const STEP_LOADERS = {
  criteria: () => import("../components/WelcomeCriteria.vue"),
  questions: () => import("../components/WelcomeQuestions.vue"),
  alertSteps: () => import("../components/WelcomeAlertSteps.vue"),
  alertExtension: () => import("../components/WelcomeAlertExtension.vue"),
  profile: () => import("../components/WelcomeProfileStep.vue"),
};
const stepLoads = new Map<keyof typeof STEP_LOADERS, Promise<unknown>>();
function loadStep<K extends keyof typeof STEP_LOADERS>(key: K): ReturnType<(typeof STEP_LOADERS)[K]> {
  if (!stepLoads.has(key)) stepLoads.set(key, STEP_LOADERS[key]());
  return stepLoads.get(key) as ReturnType<(typeof STEP_LOADERS)[K]>;
}
const stepLoading = { render: () => h(LoadingBlocks, { heights: ["4rem", "16rem"] }) };
const WelcomeCriteria = defineAsyncComponent({
  loader: () => loadStep("criteria"),
  loadingComponent: stepLoading,
  delay: 0,
});
const WelcomeQuestions = defineAsyncComponent({
  loader: () => loadStep("questions"),
  loadingComponent: stepLoading,
  delay: 0,
});
const WelcomeAlertSteps = defineAsyncComponent({
  loader: () => loadStep("alertSteps"),
  loadingComponent: stepLoading,
  delay: 0,
});
const WelcomeAlertExtension = defineAsyncComponent({
  loader: () => loadStep("alertExtension"),
  loadingComponent: stepLoading,
  delay: 0,
});
const WelcomeProfileStep = defineAsyncComponent({
  loader: () => loadStep("profile"),
  loadingComponent: stepLoading,
  delay: 0,
});
let idleHandle: number | undefined;
onMounted(() => {
  const idle = window.requestIdleCallback ?? ((run: () => void) => window.setTimeout(run, 1));
  idleHandle = idle(() => {
    // Le téléphone n'ouvre jamais le bloc des critères ni l'extension ; l'ordinateur jamais les questions (§60).
    const skip = desk.value ? ["questions"] : ["criteria", "alertExtension"];
    for (const key of Object.keys(STEP_LOADERS) as (keyof typeof STEP_LOADERS)[]) if (!skip.includes(key)) void loadStep(key);
  });
});
onUnmounted(() => {
  if (idleHandle !== undefined) (window.cancelIdleCallback ?? window.clearTimeout)(idleHandle);
});

// Les premiers pas (maquette OnboardingC, docs/139 étape 11b ; O1 à O10, Kevin, 2026-11-05) : quatre étapes, une
// barre en quatre segments et « Passer » en haut.
// 1. La page bleue : « Moins chercher plus vivre. ».
// 2. Le CV : lu par l'IA quand elle est branchée (sans les coordonnées, llm/redact.py) ; ses compétences.
// 3. Les critères : postes en puces (pré-remplis par le CV), lieux en puces, l'ORP et ses recherches par mois.
// 4. L'alerte (corrections du 13.11 au soir, §1 ; décisions de Kevin du 14.11) : une alerte jobup pour la première
//    recherche enregistrée, en trois étapes ; « J'ai créé l'alerte » la note créée, « Plus tard » passe. Rouverte
//    depuis la carte Premiers pas d'Aujourd'hui (`?etape=alerte`), ses boutons y ramènent.
// 5. Le tri : jusqu'à 3 offres déjà notées, à garder ou écarter ; sinon, directement « Tout est prêt. ».
// Ce qui n'est plus demandé prend une valeur par défaut (O1), rappelée en une ligne à la fin, modifiable dans
// Compte : taux peu importe, langues du CV (sinon le français), télétravail accepté, remise le 5, téléphone
// désactivé.
type Understanding = components["schemas"]["Understanding"];
type Step = 0 | 1 | 2 | 3 | 4;
const MAX_ROLES = 3;
// La lecture du CV (ChargementCV, §53) : quatre étapes, environ 20 secondes en tout.
const CV_STEPS = ["Coordonnées", "Expériences", "Compétences", "Langues"];
const CV_LINES = ["Je lis ton CV,", "environ 20 secondes"];
const DUE_DAY = 5;
// Le gribouillis qui barre le premier mot de chaque titre : le tracé de la maquette (comme « C'est fait ! »).
const SCRIBBLE =
  "M2 22 10.3 3.9 14.3 34.2 18.8 6 25.4 31.4 32 8 37.6 34.8 43 5.4 46.3 36.2 51.3 3.7 58.9 32.1 65.3 5.2 69.4 31.4 76.8 5.6 83.5 33.7 91 7.2 97.9 34.2 104 4.7 107.5 33.5 111.6 5.9 119.2 35.6 126.6 4.9 132.6 34.5 140 8.7 146.7 31.4 152.9 9 157.4 33.3 161.2 5.8 166.3 31.4 170.3 4.5 178 31.5 184.3 8.3 191.1 32.7 196.7 8.3 198 32.1M196 14C150 30 90 6 40 26S8 18 4 30";
// Chaque titre : un début, le mot barré, la fin manuscrite (Caveat Brush, réduite à ces seuls caractères).
const TITLES: { lead: string; struck: string; hand: string }[] = [
  { lead: "Moins", struck: "chercher", hand: "plus vivre." },
  { lead: "", struck: "Tout réécrire", hand: "Ton CV suffit." },
  { lead: "", struck: "Toutes les offres", hand: "Juste les tiennes." },
  { lead: "", struck: "Chercher", hand: "Recevoir." },
  { lead: "Lire", struck: "312 offres", hand: "En trier 3." },
];

// Ordinateur dès 1 024 px (MODIFICATIONS_9 §5, maquettes OnboardingOrdinateur… du 9 novembre ; 4 étapes depuis
// OnboardingOrdinateurAlerte, corrections du 13.11) : les étapes sur la
// grille commune (1 080 px, 640 + 80 + 360), une scène par étape à droite, plus de « Passer » ; la lecture du CV ne
// bloque pas l'écran.
const { phone } = usePhone();
const { phone: wideQuery } = usePhone("(min-width: 1024px)");
const desk = computed(() => wideQuery.value && !phone.value);

const router = useRouter();
const route = useRoute();
const { me } = useAuth();
const assistant = useAssistant();

const step = ref<Step>(0);
const loaded = ref(false);
const criteria = ref<CriteriaIn | null>(null);
const settings = ref<SettingsModel | null>(null);

// Étape 2, le CV.
const cvName = ref("");
const cvId = ref<number | null>(null);
// Sur ordinateur, la carte du fichier : « PDF · 212 Ko ».
const cvMeta = ref("");
// La lecture du CV ne bloque pas l'écran (MODIFICATIONS_9 §5.2) : « Lecture… », « Lu », ou « En pause » quand la
// connexion tombe ; nouvel essai tout seul 5 s plus tard, ou tout de suite par « Réessayer ».
const paused = ref(false);
const retryIn = ref(0);
let retryTimer: ReturnType<typeof setInterval> | undefined;
const RETRY_S = 5;
const uploading = ref(false);
const reading = ref(false);
const readDone = ref(false);
const cvError = ref("");
// « Complétons ton profil » (prompt du 10 novembre, PR 17) : l'étape 1 quand le CV n'a pas pu être lu ou qu'il n'y en a
// pas ; la raison en clair, sous le nom du fichier.
const completing = ref(false);
const cvReason = ref("");
// Les niveaux de langue choisis (formulaire ou étape 2) ; null : on garde ceux déjà enregistrés.
const languageLevels = ref<Record<string, Level> | null>(null);
const levelsForm = ref<InstanceType<typeof ProfileCompletionForm> | null>(null);
const understanding = ref<Understanding | null>(null);
const skills = computed(() =>
  (understanding.value?.chunks ?? []).filter((c) => c.kind === "competence").map((c) => c.title).slice(0, 8),
);

// Étape 3, les critères.
const roles = ref<string[]>([]);
const picked = ref<string[]>([]);
const places = ref<string[]>([]);
const orp = ref(true);
const target = ref(10);
// Le taux minimum (OnboardingOrdinateurEtape2, carte « Taux d'activité ») : celui du CV s'il le dit, sinon peu importe.
const rate = ref<number | null>(null);
// Sur téléphone, l'étape 2 pose une question par écran (§60 du 17.11, WelcomeQuestions) : 1 Postes, 2 Lieu, 3 Taux,
// 4 ORP, 5 Objectif (seulement si inscrit à l'ORP), 6 Langues. La flèche de retour revient à la question précédente.
const question = ref(1);
const questionsBlock = ref<{ flush: () => void } | null>(null);
function nextQuestion(): void {
  questionsBlock.value?.flush();
  if (question.value >= 6) {
    void confirmCriteria();
    return;
  }
  question.value = question.value === 4 && !orp.value ? 6 : question.value + 1;
}
function back(): void {
  if (fromToday && step.value === 3) {
    void router.replace("/aujourdhui");
    return;
  }
  if (step.value === 2 && question.value > 1) {
    question.value = question.value === 6 && !orp.value ? 4 : question.value - 1;
    return;
  }
  if (step.value === 3) question.value = 6;
  go((step.value - 1) as Step);
}
// Le bloc des critères (WelcomeCriteria, section 41) : ses panneaux de modification et le poste tapé sans « + ».
const criteriaBlock = ref<InstanceType<typeof WelcomeCriteriaComponent> | null>(null);
// La provenance des lignes Postes, Lieu et Taux (Kevin, 16.11, #806), gardée dans l'état des premiers pas : « cv » quand
// la valeur vient de la lecture du CV, « user » dès qu'elle est modifiée et validée. Lieu ne vient jamais du CV.
const sources = ref<CriteriaSources>({ roles: "default", places: "default", rate: "default" });
function setSources(changes: Partial<CriteriaSources>): void {
  const next = { ...sources.value, ...changes };
  if (JSON.stringify(next) === JSON.stringify(sources.value)) return;
  sources.value = next;
  void remember({ sources: next });
}
// « Repris de ton CV » seulement si la lecture a vraiment repris quelque chose (test du 10 novembre : le CV
// enregistré mais pas lu affichait quand même « Pré-rempli depuis ton CV »).
const fromCv = computed(() => !!understanding.value && (understanding.value.roles.length > 0 || !!understanding.value.min_rate));
const cvUnread = computed(() => !!cvName.value && !reading.value && !paused.value && !understanding.value);

// Étape 4, l'alerte jobup : la première recherche enregistrée (pas une recherche écrite en dur) et l'adresse jobA1.
const ALERT_SITE = "jobup";
const alerts = ref<AlertsPage | null>(null);
const alertBusy = ref(false);
// Rouverte depuis la carte Premiers pas d'Aujourd'hui : « Retour », « Plus tard » et « J'ai créé l'alerte » y ramènent.
const fromToday = route?.query.etape === "alerte";
const alertSearch = computed(() => alerts.value?.searches.find((s) => s.active) ?? null);
const alertUrl = computed(() => alertSearch.value?.cells.find((c) => c.site === ALERT_SITE)?.url ?? null);
const alertLabel = computed(() => (alertSearch.value ? `${alertSearch.value.terms} · ${alertSearch.value.location || "Toute la Suisse"}` : ""));
// Le code de jobup est arrivé (WelcomeAlertSteps) : « J'ai validé l'alerte » à la place de « J'ai créé l'alerte ».
const codeReceived = ref(false);
// Section 42 du 16.11, ordinateur seulement : créer l'alerte avec l'extension ou à la main. Par défaut l'extension si
// elle est détectée (attribut sur <html> ou message, jamais une requête au serveur), sinon à la main.
const extension = useJobA1Extension(ALERT_SITE);
const VIAS = [
  { key: "extension", label: "Avec l’extension", time: "environ 1 minute" },
  { key: "main", label: "À la main", time: "environ 2 minutes" },
] as const;
type Via = (typeof VIAS)[number]["key"];
const chosenVia = ref<Via | null>(null);
// L'extension n'existe que pour Firefox (Kevin, 16.11, 23 h 29) : le choix ne s'affiche que sur Firefox, ou partout si
// l'extension est détectée ; sinon le parcours à la main seul, comme sur téléphone.
const firefox = /firefox\//i.test(navigator.userAgent);
const viaChoice = computed(() => firefox || !!extension.version.value);
const via = computed<Via>({
  get: () => (viaChoice.value ? chosenVia.value ?? (extension.version.value ? "extension" : "main") : "main"),
  set: (value) => (chosenVia.value = value),
});
function onViaKey(event: KeyboardEvent): void {
  if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)) return;
  event.preventDefault();
  via.value = via.value === "main" ? "extension" : "main";
  const group = event.currentTarget as HTMLElement;
  void nextTick(() => group.querySelector<HTMLElement>("[aria-checked=true]")?.focus());
}
// L'extension a vu l'alerte créée sur jobup (elle l'a notée au serveur) : la page passe à la suite toute seule. En
// secours, une alerte jobup déjà notée créée quand on revient sur l'onglet fait de même.
watch(extension.step, (value) => {
  if (value === "created" && step.value === 3 && desk.value) void afterAlert();
});
async function checkCreated(): Promise<void> {
  if (document.visibilityState !== "visible" || step.value !== 3 || !desk.value || via.value !== "extension" || !extension.version.value) return;
  await loadAlerts();
  if (alertSearch.value?.cells.find((c) => c.site === ALERT_SITE)?.status === "created") void afterAlert();
}
onMounted(() => document.addEventListener("visibilitychange", checkCreated));
onUnmounted(() => document.removeEventListener("visibilitychange", checkCreated));
async function loadAlerts(): Promise<void> {
  const { data } = await api.GET("/api/alert-searches");
  if (data) alerts.value = data;
}

// Étape 5, le tri.
const offers = ref<Offer[]>([]);
const position = ref(0);
const kept = ref(0);
const dismissed = ref(0);
const deciding = ref(false);
const sorting = computed(() => step.value === 4 && position.value < offers.value.length);
const current = computed(() => offers.value[position.value] ?? null);

function focusTitle(el: Element): void {
  const title = el.querySelector<HTMLElement>("h1");
  if (!title) return;
  title.setAttribute("tabindex", "-1");
  title.focus({ preventScroll: true });
}

async function remember(changes: Record<string, unknown>): Promise<void> {
  await api.PUT("/api/welcome", { body: changes });
}

onMounted(async () => {
  const [state, found, saved] = await Promise.all([api.GET("/api/welcome"), api.GET("/api/criteria"), api.GET("/api/settings")]);
  if (found.data) {
    criteria.value = found.data.criteria;
    places.value = [...(found.data.criteria.locations ?? [])];
    rate.value = found.data.criteria.min_rate ?? null;
  }
  if (saved.data) {
    settings.value = saved.data;
    if (saved.data.orp_monthly_target) target.value = saved.data.orp_monthly_target;
  }
  if (state.data) {
    roles.value = [...(state.data.roles ?? [])];
    picked.value = [...roles.value];
    sources.value = { ...sources.value, ...(state.data.sources ?? {}), places: state.data.sources?.places === "user" ? "user" : "default" };
    if (state.data.goal === "job") orp.value = false;
    // Reprendre là où on s'était arrêté, sans revenir au tri (il se recharge à l'étape 3).
    // Une personne arrêtée au tri (étape 4 avant l'alerte, 5 depuis) reprend à l'alerte, qui y mène.
    if (state.data.status !== "done") step.value = Math.max(0, Math.min(state.data.step - 1, 3)) as Step;
  }
  // Sur ordinateur, la page bleue n'existe pas : on commence au CV.
  if (desk.value && step.value === 0) step.value = 1;
  if (fromToday) step.value = 3;
  if (step.value === 3) await loadAlerts();
  loaded.value = true;
});

function go(next: Step): void {
  if (next === 2 && step.value < 2) question.value = 1;
  step.value = next;
  void remember({ step: next + 1 });
  // Retour du tri vers l'alerte : la recherche et l'adresse sont relues si elles manquent.
  if (next === 3 && !alerts.value) void loadAlerts();
}

async function onCv(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (file) await upload(file);
}

// « Glisse ton CV ici » (OnboardingOrdinateur) : le fichier lâché sur la zone suit le même chemin que « Choisir ».
const dragging = ref(false);
async function onDrop(event: DragEvent): Promise<void> {
  dragging.value = false;
  const file = event.dataTransfer?.files?.[0];
  if (file) await upload(file);
}

function sizeText(bytes: number): string {
  return bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))}\u202FKo` : `${(bytes / 1024 / 1024).toFixed(1).replace(".", ",")}\u202FMo`;
}

async function upload(file: File): Promise<void> {
  uploading.value = true;
  cvMeta.value = `${file.name.toLowerCase().endsWith(".pdf") ? "PDF" : "Word"} · ${sizeText(file.size)}`;
  cvError.value = "";
  try {
    const { data, error } = await api.POST("/api/documents", {
      body: { file: "" },
      bodySerializer: () => {
        const form = new FormData();
        form.append("file", file);
        return form;
      },
    });
    if (data) {
      cvName.value = data.filename;
      cvId.value = data.id;
      understanding.value = null;
      cvReason.value = data.text_status === "empty" || data.text_status === "unreadable" ? UNREADABLE : "";
      void understand(data.id);
    } else {
      const detail = (error as { detail?: unknown } | undefined)?.detail;
      cvError.value = typeof detail === "string" ? `Refusé : ${detail}.` : "Ce fichier n’a pas pu être importé.";
    }
  } finally {
    uploading.value = false;
  }
}

// Le CV lu par l'IA (docs/121 §A), sans les coordonnées. Sans IA, plafond atteint ou erreur : pas de
// compétences, et l'étape 3 part de ce qui est déjà enregistré.
async function understand(documentId: number): Promise<void> {
  reading.value = true;
  stopRetry();
  try {
    const { data, response } = await api.POST("/api/documents/{document_id}/understand", { params: { path: { document_id: documentId } }, ...QUIET });
    if (!data || (!data.chunks.length && !data.roles.length)) {
      if (!cvReason.value) cvReason.value = readFailure(response.status, !!data);
      return;
    }
    understanding.value = data;
    const known = new Set(roles.value.map((r) => r.toLowerCase()));
    const found = data.roles.filter((r) => !known.has(r.toLowerCase()));
    roles.value = [...roles.value, ...found];
    picked.value = [...picked.value, ...found].slice(0, MAX_ROLES);
    // Le taux du CV : posé s'il n'y en avait pas, ou identique à celui déjà là (sans modification de la personne).
    const rateFound = !!data.min_rate && (rate.value === null || rate.value === data.min_rate);
    if (rateFound) rate.value = data.min_rate;
    setSources({
      ...(found.length && sources.value.roles !== "user" ? { roles: "cv" as const } : {}),
      ...(rateFound && sources.value.rate !== "user" ? { rate: "cv" as const } : {}),
    });
    saveChunks();
    // §53 (Kevin, 17.11) : la barre et les étapes finissent sous les yeux (0,4 s) avant de laisser la place.
    readDone.value = true;
    await new Promise((done) => setTimeout(done, 400));
    readDone.value = false;
  } catch {
    // La connexion est tombée : le CV est enregistré, la lecture reprend seule (OnboardingOrdinateurCoupure).
    understanding.value = null;
    if (cvId.value === documentId) pause(documentId);
  } finally {
    reading.value = false;
  }
}

// Pourquoi le CV n'a pas été lu, en clair (maquette OnboardingProfil).
const UNREADABLE = "C’est une image scannée : le texte n’est pas lisible.";
function readFailure(status: number, answered: boolean): string {
  if (answered) return "jobA1 n’y a trouvé ni poste ni compétence.";
  if (status === 422) return UNREADABLE;
  if (status === 409) return "La lecture des CV n’est pas disponible pour le moment.";
  return "La lecture a échoué. Tu pourras réessayer depuis Profil.";
}

function stopRetry(): void {
  clearInterval(retryTimer);
  retryTimer = undefined;
  paused.value = false;
  retryIn.value = 0;
}

function pause(documentId: number): void {
  paused.value = true;
  retryIn.value = RETRY_S;
  clearInterval(retryTimer);
  retryTimer = setInterval(() => {
    retryIn.value -= 1;
    if (retryIn.value <= 0) void understand(documentId);
  }, 1000);
}

function retryNow(): void {
  if (cvId.value !== null) void understand(cvId.value);
}

// « Lu : 3 postes, 14 compétences trouvés » (OnboardingOrdinateurCV) : ce que la lecture a trouvé, au bon accord.
const readSummary = computed(() => {
  const found = understanding.value;
  if (!found) return "";
  const competences = found.chunks.filter((c) => c.kind === "competence").length;
  const parts = [
    found.roles.length ? `${found.roles.length} ${found.roles.length > 1 ? "postes" : "poste"}` : "",
    competences ? `${competences} ${competences > 1 ? "compétences" : "compétence"}` : "",
  ].filter(Boolean);
  if (!parts.length) return "Lu, rien de particulier trouvé";
  const plural = found.roles.length + competences > 1;
  return `Lu : ${parts.join(", ")} ${plural ? "trouvés" : "trouvé"}`;
});
const readState = computed<"reading" | "paused" | "done" | "">(() =>
  paused.value ? "paused" : reading.value ? "reading" : cvName.value ? "done" : "",
);
// La scène de la colonne de droite (MODIFICATIONS_9 §6) : une par étape, et par état de la lecture à l'étape 1.
const scene = computed<SceneName>(() => {
  if (step.value === 2) return "lieux-carte";
  if (step.value === 4) return "reussite";
  if (readState.value === "paused") return "connexion-perdue";
  if (readState.value === "reading") return "lecture-calme";
  if (readState.value === "done") return "formations-vide";
  return "offres-profils";
});

// « Continuer » : les blocs lus dans le CV (sauf ceux déjà dans le profil) rejoignent le profil, rattachés au
// CV ; ils restent modifiables dans Profil.
// La lecture peut finir après « Continuer » (elle ne bloque plus l'écran) : les blocs partent alors à son arrivée.
const cvConfirmed = ref(false);
function confirmCv(): void {
  // CV absent ou pas lu : « Complétons ton profil » (la lecture encore en cours, elle, ne bloque pas).
  if (!understanding.value && !reading.value && !paused.value) {
    completing.value = true;
    return;
  }
  cvConfirmed.value = true;
  go(2);
  saveChunks();
}

function profileDone(levels: Record<string, Level>): void {
  languageLevels.value = levels;
  completing.value = false;
  go(2);
}

function profileLater(): void {
  completing.value = false;
  go(2);
}

function profileFile(file: File): void {
  completing.value = false;
  void upload(file);
}

function saveChunks(): void {
  const found = understanding.value;
  if (!found || !cvConfirmed.value) return;
  for (const chunk of found.chunks.filter((c) => c.duplicate_of == null)) {
    void api.POST("/api/profile-chunks", {
      body: { kind: chunk.kind, title: chunk.title, content: chunk.content, tags: chunk.tags, active: true, document_id: cvId.value },
    });
  }
}

// Les langues que le CV mentionne : « Courant » au départ, à corriger à l'étape 2 (PR 17).
const cvLanguages = computed(() => understanding.value?.languages ?? []);

// « Continuer » (« Voir mes offres » avant l'étape de l'alerte) : les critères, les réglages et les postes partent
// ensemble, avec les valeurs par défaut ; puis l'alerte, une fois tout enregistré (les recherches proposées en
// découlent).
// Un poste tapé sans le « + » compte aussi : le bouton bleu est celui qu'on presse (2026-11-05, Kevin).
async function confirmCriteria(): Promise<void> {
  criteriaBlock.value?.flush();
  if (criteria.value) {
    criteria.value = {
      ...criteria.value,
      locations: places.value,
      // Le taux se choisit dans sa ligne, sur ordinateur comme sur téléphone (section 41).
      min_rate: rate.value,
      remote_policy: "from_switzerland",
      // « Non renseigné » n'écarte jamais une offre (PR 17) : plus de langue écartée d'office.
      language_levels: levelsForm.value?.levels ?? languageLevels.value ?? criteria.value.language_levels ?? {},
    };
  }
  const saving: Promise<unknown>[] = [];
  if (criteria.value) saving.push(api.PUT("/api/criteria", { body: criteria.value }));
  if (settings.value) {
    settings.value = { ...settings.value, orp_monthly_target: orp.value ? target.value : null, orp_due_day: DUE_DAY };
    saving.push(api.PUT("/api/settings", { body: settings.value }));
  }
  saving.push(remember({ step: 4, goal: orp.value ? "orp" : "job", roles: picked.value, ...(picked.value[0] ? { trade: picked.value[0] } : {}) }));
  step.value = 3;
  await Promise.all(saving);
  await loadAlerts();
}

// « J'ai créé l'alerte » : jobup noté créé pour la première recherche, comme dans Mes alertes ; « Plus tard » ne note
// rien. Les deux mènent aux premières offres, ou à Aujourd'hui quand l'étape a été rouverte de là.
async function alertDone(): Promise<void> {
  const search = alertSearch.value;
  if (search && !alertBusy.value) {
    alertBusy.value = true;
    try {
      await api.PUT("/api/alert-searches/{search_id}/sites/{site}", { params: { path: { search_id: search.id, site: ALERT_SITE } } });
    } finally {
      alertBusy.value = false;
    }
  }
  await afterAlert();
}
async function afterAlert(): Promise<void> {
  if (fromToday) {
    await router.replace("/aujourdhui");
    return;
  }
  step.value = 4;
  void remember({ step: 5 });
  const { data } = await api.GET("/api/offers", { params: { query: { view: "to_review", sort: "score", limit: 3 } } });
  offers.value = (data?.items ?? []).filter((o) => o.score !== null && o.score !== undefined).slice(0, 3);
}

// « Garder » et « Écarter » : comme dans Candidatures. « Écarter » laisse « Annuler » 6 s dans le bandeau commun à trait
// (§23 du 15.11) : l'offre reprend son statut d'avant et le tri revient sur elle.
type Restorable = "to_review" | "later";

async function decide(choice: "keep" | "dismiss"): Promise<void> {
  const offer = current.value;
  if (!offer || deciding.value) return;
  deciding.value = true;
  try {
    const { response } = await api.PATCH("/api/offers/{offer_id}/status", {
      params: { path: { offer_id: offer.id } },
      body: { status: choice === "keep" ? "preparing" : "ignored" },
    });
    if (!response.ok) return;
    if (choice === "keep") kept.value += 1;
    else dismissed.value += 1;
    position.value += 1;
    if (choice === "dismiss") {
      const status: Restorable = offer.status === "later" ? "later" : "to_review";
      void offerUndo({
        message: "Offre écartée.",
        commit: () => true,
        restore: async () => {
          const { response } = await api.PATCH("/api/offers/{offer_id}/status", { params: { path: { offer_id: offer.id } }, body: { status } });
          if (!response.ok) return;
          position.value = Math.max(0, position.value - 1);
          dismissed.value = Math.max(0, dismissed.value - 1);
        },
      });
    }
  } finally {
    deciding.value = false;
  }
}

// Sur ordinateur, les 3 offres côte à côte (OnboardingOrdinateurEtape3) : « Écarter » ou « Garder » sur chaque carte,
// « Annuler » ensuite sur la carte même.
const decided = ref<Record<number, "keep" | "dismiss">>({});
async function decideOffer(offer: Offer, choice: "keep" | "dismiss"): Promise<void> {
  if (deciding.value) return;
  deciding.value = true;
  try {
    const { response } = await api.PATCH("/api/offers/{offer_id}/status", {
      params: { path: { offer_id: offer.id } },
      body: { status: choice === "keep" ? "preparing" : "ignored" },
    });
    if (response.ok) decided.value = { ...decided.value, [offer.id]: choice };
  } finally {
    deciding.value = false;
  }
}
async function undoOffer(offer: Offer): Promise<void> {
  const { response } = await api.PATCH("/api/offers/{offer_id}/status", {
    params: { path: { offer_id: offer.id } },
    body: { status: offer.status === "later" ? "later" : "to_review" },
  });
  if (!response.ok) return;
  const next = { ...decided.value };
  delete next[offer.id];
  decided.value = next;
}
const initials = (name: string | null | undefined): string =>
  (name || "?").split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]!.toUpperCase()).join("");
const DESK_EYEBROWS: Record<number, string> = { 1: "Premiers pas", 2: "Ce que tu cherches", 3: "Tes prochaines offres", 4: "Tes premières offres" };

onBeforeUnmount(() => {
  clearInterval(retryTimer);
});

const tags = computed(() => {
  const o = current.value;
  if (!o) return [];
  return [rateText(o.rate_min, o.rate_max).replace("–", " à "), o.employment_type ?? "", remoteText(o) ?? ""].filter(Boolean).slice(0, 3);
});

const sortSummary = computed(() => {
  const parts = [
    kept.value ? `${kept.value} ${kept.value === 1 ? "offre gardée" : "offres gardées"}` : "",
    dismissed.value ? `${dismissed.value} ${dismissed.value === 1 ? "écartée" : "écartées"}` : "",
  ].filter(Boolean);
  if (!offers.value.length) return "Tes premières offres arrivent après la prochaine collecte.";
  return parts.length ? `${parts.join(", ")}.` : "";
});
const spokenLanguages = computed(() =>
  Object.entries(levelsForm.value?.levels ?? languageLevels.value ?? criteria.value?.language_levels ?? {})
    .filter(([, level]) => level === "fluent" || level === "native")
    .map(([name]) => languageLabel(name).toLowerCase())
    .join(", "),
);
// Les valeurs par défaut (O1), en une ligne.
const defaults = computed(() =>
  [
    "Taux : peu importe",
    `Langues : ${spokenLanguages.value || "à renseigner dans Profil"}`,
    "Télétravail : accepté depuis la Suisse",
    ...(orp.value ? [`Remise ORP : le ${DUE_DAY}`] : []),
    "Téléphone : désactivé",
  ].join(" · "),
);

async function later(): Promise<void> {
  await remember({ postponed: true });
  if (me.value) me.value = { ...me.value, welcome: "postponed" };
  await router.replace("/aujourdhui");
}

// « Pas de CV à jour ? » (maquette OnboardingC, décision de Kevin du 2026-11-06) : les premiers pas sont mis de
// côté, comme avec « Passer », et l'Assistant reçoit la demande ; on les reprend depuis l'Accueil.
const CV_QUESTION = "Je n’ai pas de CV à jour. Aide-moi à en créer un.";
async function askForCv(): Promise<void> {
  await remember({ postponed: true });
  if (me.value) me.value = { ...me.value, welcome: "postponed" };
  assistant.ask(CV_QUESTION);
  await router.replace({ name: "assistant" });
}

async function finish(to: string): Promise<void> {
  await remember({ done: true, postponed: false });
  if (me.value) me.value = { ...me.value, welcome: "done" };
  await router.replace(to);
}
</script>

<template>
  <!-- Premiers pas sur ordinateur (MODIFICATIONS_9 §5, maquettes OnboardingOrdinateur…) : la grille commune des
       3 étapes, 640 px de contenu, 80 px, la scène de 360 px ; l’en-tête aligné sur la grille. -->
  <WelcomeProfileStep
    v-if="loaded && completing"
    :desk="desk"
    :cv-name="cvName"
    :cv-reason="cvReason"
    :document-id="cvId"
    :roles="picked.length ? picked : roles"
    @back="completing = false"
    @later="profileLater"
    @done="profileDone"
    @file="profileFile"
  />
  <section
    v-else-if="loaded && desk"
    class="welcome wdk"
    data-test="welcome"
  >
    <header class="wdk-top">
      <span class="welcome-brand"><BrandMark :size="30" />jobA1</span>
      <span
        class="wdk-step"
        data-test="welcome-eyebrow"
      >Étape {{ step }} sur 4</span>
      <span
        class="wdk-bars"
        role="progressbar"
        :aria-label="`Étape ${step} sur 4`"
        aria-valuemin="1"
        aria-valuemax="4"
        :aria-valuenow="step"
        data-test="welcome-dots"
      >
        <span
          v-for="i in 4"
          :key="i"
          :class="{ on: i <= step, current: i === step }"
        />
      </span>
    </header>
    <div class="wdk-grid">
      <Transition
        name="welcome-step"
        mode="out-in"
        @after-enter="focusTitle"
      >
        <div
          :key="step"
          class="wdk-col"
          :data-test="`welcome-step-${step + 1}`"
        >
          <p class="wdk-cap">
            {{ DESK_EYEBROWS[step] }}
          </p>
          <h1
            v-if="step === 1"
            class="wdk-title"
          >
            Moins chercher, <span class="welcome-hand">plus vivre.</span>
          </h1>
          <h1
            v-else-if="step === 2"
            class="wdk-title"
          >
            Quel travail cherches-tu ?
          </h1>
          <h1
            v-else-if="step === 3"
            class="wdk-title"
          >
            Crée ton alerte sur jobup
          </h1>
          <h1
            v-else
            class="wdk-title"
            data-test="welcome-offers-title"
          >
            {{ offers.length ? `${offers.length} ${offers.length > 1 ? "offres" : "offre"} pour toi` : "Tes premières offres arrivent demain matin" }}
          </h1>

          <template v-if="step === 1">
            <p class="wdk-lead">
              jobA1 trie les offres, prépare tes lettres et tient ton suivi ORP. Ton CV suffit pour commencer.
            </p>
            <div
              v-if="cvName"
              :class="['wdk-card', 'wdk-file', readState]"
              data-test="cv-done"
            >
              <div class="wdk-file-head">
                <AppIcon
                  name="file"
                  class="wdk-file-icon"
                />
                <span class="wdk-file-name">
                  <b>{{ cvName }}</b>
                  <span>{{ cvMeta }}</span>
                </span>
                <span
                  v-if="readState === 'reading'"
                  class="wdk-file-state"
                  data-test="cv-reading"
                >Lecture…</span>
                <span
                  v-else-if="readState === 'paused'"
                  class="wdk-file-state paused"
                  data-test="cv-reading"
                >En pause</span>
                <label
                  v-else
                  class="link wdk-file-change"
                >
                  Changer
                  <input
                    type="file"
                    accept=".pdf,.docx"
                    class="visually-hidden"
                    @change="onCv"
                  >
                </label>
              </div>
              <template v-if="readState === 'reading' || readState === 'paused'">
                <!-- §53 sur ordinateur (Kevin, 17.11) : la lecture ne bloque pas ; seul le style de ChargementCV entre
                     dans la carte. En pause, la barre orange arrêtée reste. -->
                <LoadingSteps
                  v-if="readState === 'reading'"
                  class="wdk-loading"
                  :lines="CV_LINES"
                  :steps="CV_STEPS"
                  :every-ms="5000"
                  :done="readDone"
                  label="Lecture du CV"
                />
                <div
                  v-else
                  class="wdk-bar"
                  role="progressbar"
                  aria-label="Lecture du CV"
                >
                  <span />
                </div>
                <p class="wdk-file-note">
                  {{ readState === "paused" ? "Ton CV est enregistré. La lecture reprend toute seule." : "Tu peux continuer, on termine en fond." }}
                </p>
              </template>
              <p
                v-else
                class="wdk-found"
                role="status"
                data-test="cv-summary"
              >
                <AppIcon
                  v-if="understanding"
                  name="tick"
                />{{ understanding ? readSummary : "Enregistré. L’IA n’a rien pu lire : tu complètes à l’étape suivante." }}
              </p>
            </div>
            <label
              v-else
              :class="['wdk-drop', { dragging }]"
              data-test="cv-upload"
              @dragover.prevent="dragging = true"
              @dragleave="dragging = false"
              @drop.prevent="onDrop"
            >
              <AppIcon
                name="file"
                class="wdk-drop-icon"
              />
              <b>Glisse ton CV ici</b>
              <span>PDF ou Word, 10&#8239;Mo maximum</span>
              <span class="wdk-drop-button">{{ uploading ? "Import…" : "Choisir un fichier" }}</span>
              <input
                type="file"
                accept=".pdf,.docx"
                class="visually-hidden"
                @change="onCv"
              >
            </label>
            <p
              v-if="cvError"
              class="notice"
              role="alert"
            >
              {{ cvError }}
            </p>
            <p
              class="wdk-note"
              data-test="cv-privacy"
            >
              <AppIcon name="lock" />
              <span>Ton CV reste privé. L’IA ne voit jamais tes coordonnées. <RouterLink to="/tes-donnees#ia">En savoir plus</RouterLink></span>
            </p>
            <div class="wdk-foot">
              <template v-if="!cvName">
                <button
                  v-if="assistant.available.value"
                  type="button"
                  class="wdk-link"
                  data-test="cv-assistant"
                  @click="askForCv"
                >
                  Pas de CV à jour&#8239;? L’Assistant t’aide à en créer un
                </button>
                <span v-else />
                <button
                  type="button"
                  class="wdk-link"
                  data-test="welcome-continue"
                  @click="confirmCv"
                >
                  Continuer sans CV<AppIcon name="chevron" />
                </button>
              </template>
              <template v-else>
                <span />
                <button
                  type="button"
                  class="primary wdk-cta"
                  :disabled="uploading"
                  data-test="welcome-continue"
                  @click="confirmCv"
                >
                  Continuer
                </button>
              </template>
            </div>
          </template>

          <template v-else-if="step === 2">
            <p class="wdk-lead">
              {{ fromCv ? "Repris de ton CV. Modifie-les si besoin." : cvUnread ? "Ton CV n’a pas pu être lu : indique-les ici, tu pourras les changer plus tard dans Profil." : "Tu pourras les changer plus tard dans Profil." }}
            </p>
            <WelcomeCriteria
              ref="criteriaBlock"
              v-model:roles="roles"
              v-model:picked="picked"
              v-model:places="places"
              v-model:rate="rate"
              v-model:orp="orp"
              v-model:target="target"
              :desk="desk"
              :reading="reading"
              :sources="sources"
              :max-roles="MAX_ROLES"
              @edited="(key) => setSources({ [key]: 'user' })"
            />
            <!-- CV lu : les langues quand même, pré-remplies (prompt du 10 novembre, PR 17, point 1). -->
            <ProfileCompletionForm
              v-if="understanding"
              ref="levelsForm"
              class="welcome-langs"
              :sections="['languages']"
              languages-only
              :desk="desk"
              :cv-languages="cvLanguages"
            />
            <div class="wdk-foot">
              <button
                type="button"
                class="secondary wdk-back"
                data-test="welcome-back"
                @click="go(1)"
              >
                Retour
              </button>
              <button
                type="button"
                class="primary wdk-cta"
                data-test="welcome-criteria"
                @click="confirmCriteria"
              >
                Continuer
              </button>
            </div>
          </template>

          <!-- Section 41 du paquet du 16.11 : la phrase sous le titre, puis une carte de 4 étapes ; le code en lecture seule. -->
          <template v-else-if="step === 3">
            <p class="wdk-lead">
              Pour recevoir les nouvelles offres, tu crées une alerte sur jobup. C’est ainsi que jobA1 reçoit tes offres.
            </p>
            <!-- Section 42 du 16.11 : avec l'extension ou à la main, ordinateur seulement, sur Firefox ou extension détectée ;
                 l’avancée de chaque parcours est gardée quand on change (les deux restent montés). -->
            <div
              v-if="viaChoice"
              class="wdk-via"
              role="radiogroup"
              aria-label="Comment créer l’alerte"
              data-test="welcome-alert-via"
              @keydown="onViaKey"
            >
              <button
                v-for="option in VIAS"
                :key="option.key"
                type="button"
                role="radio"
                :aria-checked="via === option.key"
                :tabindex="via === option.key ? 0 : -1"
                :class="['wdk-via-option', { on: via === option.key }]"
                :data-test="`welcome-alert-via-${option.key}`"
                @click="via = option.key"
              >
                <b>{{ option.label }}</b>
                <span>{{ option.key === "extension" && extension.version.value ? "installée · " : "" }}{{ option.time }}</span>
              </button>
            </div>
            <WelcomeAlertExtension
              v-show="via === 'extension'"
              :search-label="alertLabel"
              :url="alertUrl"
              :installed="!!extension.version.value"
              :progress="extension.step.value"
            />
            <WelcomeAlertSteps
              v-if="alerts"
              v-show="via === 'main'"
              v-model:received="codeReceived"
              desk
              :search-label="alertLabel"
              :url="alertUrl"
              :mailbox="alerts.mailbox"
              data-test="welcome-alert"
            />
            <div class="wdk-foot">
              <button
                type="button"
                class="secondary wdk-back"
                data-test="welcome-back"
                @click="fromToday ? router.replace('/aujourdhui') : go(2)"
              >
                Retour
              </button>
              <span class="wdk-foot-end">
                <button
                  type="button"
                  class="wdk-link"
                  data-test="welcome-alert-later"
                  @click="afterAlert"
                >
                  Plus tard
                </button>
                <button
                  v-if="via === 'main'"
                  type="button"
                  class="primary wdk-cta"
                  :disabled="alertBusy"
                  data-test="welcome-alert-done"
                  @click="alertDone"
                >
                  {{ codeReceived ? "J’ai validé l’alerte" : "J’ai créé l’alerte" }}
                </button>
              </span>
            </div>
          </template>

          <template v-else>
            <p class="wdk-lead">
              {{ offers.length ? "Les meilleures offres de la semaine. Garde ou écarte." : "jobA1 lit les offres chaque nuit. Les premières qui te correspondent t’attendront dans Candidatures." }}
            </p>
            <ul
              v-if="offers.length"
              class="wdk-offers"
            >
              <li
                v-for="offer in offers"
                :key="offer.id"
                class="wdk-card wdk-offer"
                data-test="welcome-offer"
              >
                <span
                  class="wdk-offer-logo"
                  aria-hidden="true"
                >{{ initials(offer.company) }}</span>
                <span class="wdk-offer-text">
                  <b>{{ displayTitle(offer.title, offer) }}</b>
                  <span>{{ companyPlace(offer.company || "Entreprise non indiquée", offer.location) }}<template v-if="offer.score != null"> · <b :class="`tone-${scoreWord(offer.score).tone}`">{{ scoreWord(offer.score).word }} · {{ Math.round(offer.score) }}</b></template></span>
                </span>
                <template v-if="decided[offer.id]">
                  <span
                    class="wdk-offer-done"
                    role="status"
                  >{{ decided[offer.id] === "keep" ? "Gardée" : "Écartée" }}</span>
                  <button
                    type="button"
                    class="link"
                    data-test="undo-status"
                    @click="undoOffer(offer)"
                  >
                    Annuler
                  </button>
                </template>
                <template v-else>
                  <button
                    type="button"
                    class="secondary wdk-small"
                    :aria-label="`Écarter ${displayTitle(offer.title, offer)}`"
                    data-test="welcome-dismiss"
                    @click="decideOffer(offer, 'dismiss')"
                  >
                    Écarter
                  </button>
                  <button
                    type="button"
                    class="secondary wdk-small"
                    :aria-label="`Garder ${displayTitle(offer.title, offer)}`"
                    data-test="welcome-keep"
                    @click="decideOffer(offer, 'keep')"
                  >
                    Garder
                  </button>
                </template>
              </li>
            </ul>
            <p
              v-if="offers.length"
              class="wdk-note"
            >
              Les suivantes arrivent chaque matin, triées de la même façon.
            </p>
            <div class="wdk-foot">
              <button
                type="button"
                class="secondary wdk-back"
                data-test="welcome-back"
                @click="go(3)"
              >
                Retour
              </button>
              <button
                type="button"
                class="primary wdk-cta"
                data-test="welcome-finish"
                @click="finish('/candidatures/offres')"
              >
                Voir mes offres
              </button>
            </div>
          </template>
        </div>
      </Transition>
      <div class="wdk-scene">
        <!-- L'alerte (OnboardingOrdinateurAlerte…, section 25 du paquet du 15.11) : la scène de la boîte aux lettres, 420 px,
             40 px sous le haut de la colonne, servie en 840 px (2x). -->
        <img
          v-if="step === 3"
          class="wdk-mailbox"
          src="/illustrations/scene-boite-aux-lettres-840.webp"
          width="420"
          height="299"
          alt=""
          aria-hidden="true"
          data-test="welcome-mailbox"
        >
        <SceneIllustration
          v-else
          :name="scene"
          sizes="360px"
        />
      </div>
    </div>
    <div
      v-if="paused"
      class="wdk-toast"
      role="status"
      data-test="cv-paused"
    >
      <span>Connexion interrompue. Nouvel essai dans {{ retryIn }} {{ retryIn > 1 ? "secondes" : "seconde" }}.</span>
      <button
        type="button"
        data-test="cv-retry"
        @click="retryNow"
      >
        Réessayer
      </button>
    </div>
  </section>
  <!-- Téléphone (§53, planche ChargementCV ; Kevin, 17.11) : la lecture bloquait déjà « Continuer » ; elle prend
       l’écran entier. Coupure ou échec : retour à l’étape, avec ses messages. -->
  <LoadingSteps
    v-else-if="loaded && step === 1 && readState === 'reading'"
    class="loading-steps-full"
    :lines="CV_LINES"
    :steps="CV_STEPS"
    :every-ms="5000"
    :done="readDone"
    label="Lecture du CV"
    data-test="cv-reading-screen"
  >
    <BrandMark :size="64" />
  </LoadingSteps>
  <section
    v-else-if="loaded"
    :class="['welcome', { 'welcome-blue': step === 0 }]"
    data-test="welcome"
  >
    <div class="welcome-column">
      <header class="welcome-top">
        <IconButton
          v-if="step > 0"
          icon="arrow-left"
          label="Étape précédente"
          data-test="welcome-back"
          @click="back"
        />
        <span class="welcome-brand"><BrandMark :size="30" />jobA1</span>
        <button
          v-if="!(step === 4 && !sorting)"
          type="button"
          class="link welcome-later"
          data-test="welcome-later"
          @click="later"
        >
          Passer
        </button>
      </header>
      <div
        v-if="step !== 2"
        class="welcome-progress"
        role="progressbar"
        :aria-label="`Étape ${step + 1} sur 5`"
        aria-valuemin="1"
        aria-valuemax="5"
        :aria-valuenow="step + 1"
      >
        <span
          v-for="i in 5"
          :key="i"
          :class="{ done: i <= step + 1 }"
        />
      </div>

      <Transition
        name="welcome-step"
        mode="out-in"
        @after-enter="focusTitle"
      >
        <div
          :key="step"
          :class="['welcome-screen', { 'welcome-questions': step === 2 }]"
          :data-test="`welcome-step-${step + 1}`"
        >
          <h1
            v-if="step !== 2"
            class="welcome-title"
          >
            <template v-if="TITLES[step]!.lead">
              {{ `${TITLES[step]!.lead} ` }}
            </template>
            <span class="welcome-struck"><s>{{ TITLES[step]!.struck }}</s><svg
              viewBox="0 0 200 40"
              preserveAspectRatio="none"
              aria-hidden="true"
            ><path
              :d="SCRIBBLE"
              pathLength="1"
            /></svg></span>{{ " " }}<br>
            <span class="welcome-hand">{{ TITLES[step]!.hand }}</span>
          </h1>

          <template v-if="step === 0">
            <p class="welcome-lead">
              jobA1 trie les offres, prépare tes lettres et tient ton suivi ORP. En 3 étapes, on règle tout.
            </p>
          </template>

          <template v-else-if="step === 1">
            <p class="welcome-lead">
              jobA1 en tire tes compétences pour noter chaque offre.
            </p>
            <div
              v-if="cvName"
              class="welcome-cv"
              role="status"
              data-test="cv-done"
            >
              <div class="welcome-cv-file">
                <span class="welcome-cv-check"><AppIcon name="check" /></span>
                <span>
                  <strong>{{ cvName }}</strong>
                  <small data-test="cv-reading">{{ understanding ? "Importé et analysé" : "Importé, mais pas pu être lu : tu compléteras à l’étape suivante" }}</small>
                </span>
                <label class="link welcome-cv-change">
                  Changer
                  <input
                    type="file"
                    accept=".pdf,.docx"
                    class="visually-hidden"
                    @change="onCv"
                  >
                </label>
              </div>
              <div
                v-if="skills.length"
                class="welcome-skills"
                data-test="cv-skills"
              >
                <p>Compétences trouvées</p>
                <ul>
                  <li
                    v-for="skill in skills"
                    :key="skill"
                  >
                    {{ skill }}
                  </li>
                </ul>
              </div>
            </div>
            <label
              v-else
              class="welcome-drop"
              data-test="cv-upload"
            >
              <strong>Importer mon CV</strong>
              <small>PDF ou Word, 10 Mo maximum</small>
              <span class="welcome-drop-button">{{ uploading ? "Import…" : "Choisir un fichier" }}</span>
              <input
                type="file"
                accept=".pdf,.docx"
                class="visually-hidden"
                @change="onCv"
              >
            </label>
            <p
              v-if="cvError"
              class="notice"
              role="alert"
            >
              {{ cvError }}
            </p>
            <template v-if="!cvName">
              <button
                v-if="assistant.available.value"
                type="button"
                class="welcome-no-cv"
                data-test="cv-assistant"
                @click="askForCv"
              >
                <span><strong>Pas de CV à jour ?</strong><small>L’Assistant t’aide à en créer un</small></span>
                <AppIcon name="chevron" />
              </button>
              <!-- Le « 1 » seul (§15 du 9 novembre, 100 px), le soleil et la colline (maquette OnboardingC, étape 2). -->
              <div
                class="welcome-cv-scene"
                aria-hidden="true"
                data-test="cv-scene"
              >
                <span class="welcome-cv-sun" />
                <svg
                  class="welcome-cv-hill"
                  viewBox="0 0 300 90"
                  preserveAspectRatio="none"
                ><path d="M0 90 C 40 20, 120 0, 170 10 C 220 20, 270 50, 300 90 Z" /></svg>
                <span class="welcome-cv-ground" />
                <TroupeScene
                  scene="un"
                  :height="100"
                  class="welcome-cv-person"
                  data-test="cv-person"
                />
              </div>
            </template>
            <p
              class="welcome-privacy"
              data-test="cv-privacy"
            >
              <AppIcon name="lock" />
              <span>Ton CV reste privé. L’IA ne voit jamais tes coordonnées. <RouterLink to="/tes-donnees#ia">En savoir plus</RouterLink></span>
            </p>
          </template>

          <!-- §60 du 17.11 : une question par écran (planches PremiersPas1Postes à PremiersPas6Langues). -->
          <WelcomeQuestions
            v-else-if="step === 2"
            ref="questionsBlock"
            v-model:question="question"
            v-model:roles="roles"
            v-model:picked="picked"
            v-model:places="places"
            v-model:rate="rate"
            v-model:orp="orp"
            v-model:target="target"
            v-model:levels="languageLevels"
            :reading="reading"
            :cv-unread="cvUnread"
            :sources="sources"
            :max-roles="MAX_ROLES"
            :cv-languages="cvLanguages"
            :saved-levels="(criteria?.language_levels ?? {}) as Record<string, Level>"
            @edited="(key) => setSources({ [key]: 'user' })"
          />

          <template v-else-if="step === 3">
            <p class="welcome-lead welcome-alert-lead">
              Pour recevoir les nouvelles offres, crée une alerte sur jobup. C’est ainsi que jobA1 reçoit tes offres. Environ 2 minutes.
            </p>
            <WelcomeAlertSteps
              v-if="alerts"
              v-model:received="codeReceived"
              :desk="false"
              :search-label="alertLabel"
              :url="alertUrl"
              :mailbox="alerts.mailbox"
              data-test="welcome-alert"
            />
          </template>
          <template v-else>
            <template v-if="sorting && current">
              <p class="welcome-lead">
                Garde ou écarte. Celles que tu gardes t’attendent dans Candidatures.
              </p>
              <article
                :key="current.id"
                class="welcome-offer"
                data-test="welcome-offer"
              >
                <div class="welcome-offer-head">
                  <CompanyLogo :offer="current" />
                  <ScoreRing
                    :score="current.score ?? null"
                    worded
                  />
                </div>
                <p class="welcome-offer-title">
                  <strong>{{ current.title }}</strong>
                  <span>{{ companyPlace(current.company || "Entreprise non indiquée", current.location) }}</span>
                </p>
                <ul
                  v-if="tags.length"
                  class="pick-tags"
                >
                  <li
                    v-for="tag in tags"
                    :key="tag"
                  >
                    {{ tag }}
                  </li>
                </ul>
                <p
                  v-if="current.why"
                  class="welcome-offer-why"
                >
                  <strong>D’après ton CV :</strong> {{ whyLine(current.why) }}
                </p>
              </article>
              <p
                class="welcome-count"
                aria-live="polite"
              >
                Offre {{ position + 1 }} sur {{ offers.length }}
              </p>
            </template>
            <div
              v-else
              class="welcome-ready"
              role="status"
              data-test="welcome-ready"
            >
              <!-- Le « 1 » seul (§15, 150 px) à la place de la coche (maquette OnboardingC, fin du tri). -->
              <div
                class="welcome-ready-scene"
                aria-hidden="true"
                data-test="welcome-ready-scene"
              >
                <span class="welcome-ready-sun" />
                <img
                  class="welcome-ready-sparkles"
                  :src="sparkles"
                  alt=""
                  width="52"
                  height="52"
                  decoding="async"
                >
                <TroupeScene
                  scene="un"
                  :height="150"
                  full
                  class="welcome-ready-person"
                />
              </div>
              <strong>Tout est prêt.</strong>
              <p
                v-if="sortSummary"
                data-test="welcome-sorted"
              >
                {{ sortSummary }}
              </p>
              <p
                class="welcome-defaults"
                data-test="welcome-defaults"
              >
                {{ defaults }}
              </p>
              <button
                type="button"
                class="link"
                data-test="welcome-account"
                @click="finish('/compte')"
              >
                Modifier dans Compte
              </button>
            </div>
          </template>
        </div>
      </Transition>

      <footer class="welcome-actions">
        <button
          v-if="step === 0"
          type="button"
          class="welcome-cta welcome-start"
          data-test="welcome-start"
          @click="go(1)"
        >
          C’est parti<AppIcon name="arrow-right" />
        </button>
        <button
          v-else-if="step === 1"
          type="button"
          class="primary welcome-cta"
          :disabled="uploading || reading"
          data-test="welcome-continue"
          @click="confirmCv"
        >
          {{ cvName ? "Continuer" : "Continuer sans CV" }}<AppIcon name="arrow-right" />
        </button>
        <button
          v-else-if="step === 2"
          type="button"
          class="welcome-cta welcome-ink"
          data-test="welcome-continue"
          @click="nextQuestion"
        >
          Continuer<span
            class="welcome-guillemet"
            aria-hidden="true"
          >»</span>
        </button>
        <div
          v-else-if="step === 3"
          class="welcome-alert-actions"
        >
          <button
            type="button"
            class="primary welcome-cta"
            :disabled="alertBusy"
            data-test="welcome-alert-done"
            @click="alertDone"
          >
            {{ codeReceived ? "J’ai validé l’alerte" : "J’ai créé l’alerte" }}
          </button>
          <button
            type="button"
            class="link welcome-alert-later"
            data-test="welcome-alert-later"
            @click="afterAlert"
          >
            Plus tard
          </button>
        </div>
        <div
          v-else-if="sorting"
          class="welcome-sort"
        >
          <button
            type="button"
            class="secondary"
            :aria-disabled="deciding ? 'true' : undefined"
            data-test="welcome-dismiss"
            @click="decide('dismiss')"
          >
            <AppIcon name="x-circle" />Écarter
          </button>
          <button
            type="button"
            class="primary"
            :aria-disabled="deciding ? 'true' : undefined"
            data-test="welcome-keep"
            @click="decide('keep')"
          >
            <AppIcon name="done" />Garder
          </button>
        </div>
        <button
          v-else
          type="button"
          class="primary welcome-cta"
          data-test="welcome-finish"
          @click="finish('/aujourdhui')"
        >
          Voir mes offres<AppIcon name="arrow-right" />
        </button>
      </footer>
    </div>
  </section>
</template>

<style>
/* Chargé avec la page seulement, pas avec le premier écran (budget « css-premier », docs/117 §3). */
/* Les premiers pas (OnboardingC, 11b) : une colonne de 30 rem, la barre en 4 segments, le titre barré puis
   manuscrit, l’action en bas. La première étape est toute bleue (O3, O10 : --primary dans les deux thèmes). */
.welcome { min-height: 100dvh; background: var(--bg); color: var(--text); }
.welcome-blue { background: var(--primary); color: var(--on-primary); }
.welcome-column { display: flex; flex-direction: column; min-height: 100dvh; max-width: 30rem; margin: 0 auto; padding: var(--space-2) var(--space-5) var(--space-6); box-sizing: border-box; }
.welcome-top { display: flex; align-items: center; gap: var(--space-1); min-height: var(--target-min); }
.welcome-brand { display: flex; align-items: center; gap: var(--space-2); margin-right: auto; font-size: var(--font-section); font-weight: var(--weight-semibold); }
.welcome-blue .welcome-brand .brand-logo { --logo-line: var(--on-primary); }
.welcome-later { min-height: var(--target-min); padding: 0 var(--space-2); font-size: var(--font-body); color: inherit; }
.welcome-blue .welcome-later { color: var(--on-primary); }
.welcome-progress { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: var(--space-1); padding-top: var(--space-2); }
.welcome-progress span { height: 5px; border-radius: var(--radius-pill); background: var(--line); transition: background-color 0.4s; }
.welcome-progress span.done { background: var(--primary-graphic); }
.welcome-blue .welcome-progress span { background: color-mix(in srgb, var(--on-primary) 32%, transparent); }
.welcome-blue .welcome-progress span.done { background: var(--on-primary); }
.welcome-screen { flex: 1; display: flex; flex-direction: column; gap: var(--space-4); padding-top: var(--space-6); }
.welcome-title { margin: 0; font-size: var(--title-block); line-height: var(--leading-tight); font-weight: var(--weight-bold); letter-spacing: -1px; }
.welcome-title:focus { outline: none; }
.welcome-blue .welcome-title { font-size: var(--title-welcome); line-height: var(--leading-welcome); }
.welcome-struck { position: relative; display: inline-block; white-space: nowrap; }
.welcome-struck s { text-decoration: none; }
.welcome-struck svg { position: absolute; left: -0.1em; top: 50%; width: calc(100% + 0.2em); height: 1.05em; margin-top: -0.48em; overflow: visible; }
.welcome-struck path { fill: none; stroke: var(--scribble); stroke-width: 9px; stroke-linecap: round; stroke-linejoin: round; vector-effect: non-scaling-stroke; stroke-dasharray: 1; animation: goal-strike 1s 0.45s cubic-bezier(.45, 0, .55, 1) both; }
.welcome-hand { display: inline-block; margin-top: var(--space-1); font-family: "Caveat Brush", cursive; font-weight: var(--weight-regular); font-size: var(--title-hand-step); line-height: var(--leading-hand); letter-spacing: 0; color: var(--primary-graphic); transform: rotate(-3deg); animation: goal-write 1s 1.4s steps(22, end) both; }
.welcome-blue .welcome-hand { font-size: var(--title-hand); color: var(--peach); }
.welcome-lead { margin: 0; font-size: var(--font-body); line-height: var(--leading-normal); color: var(--text-secondary); }
.welcome-blue .welcome-lead { font-size: var(--font-title); color: var(--on-primary); }
.welcome-drop { display: grid; justify-items: center; gap: var(--space-2); padding: var(--space-6) var(--space-5); background: var(--surface); border: 2px dashed var(--primary-graphic); border-radius: var(--radius-card); text-align: center; cursor: pointer; }
.welcome-drop small, .welcome-cv small { font-size: var(--font-small); color: var(--text-secondary); }
.welcome-drop-button { display: inline-flex; align-items: center; min-height: 46px; margin-top: var(--space-1); padding: 0 var(--space-5); border-radius: var(--radius-pill); background: var(--primary); color: var(--on-primary); font-weight: var(--weight-bold); }
.welcome-drop:focus-within { outline: 2px solid; }
.welcome-cv { display: grid; gap: var(--space-4); padding: var(--space-4); background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-card); }
.welcome-cv-file { display: flex; align-items: center; gap: var(--space-3); }
.welcome-cv-file > span:nth-child(2) { flex: 1; min-width: 0; display: grid; gap: calc(var(--space-1) / 2); overflow-wrap: anywhere; }
.welcome-cv-check { flex: none; display: grid; place-items: center; width: var(--target-min); height: var(--target-min); border-radius: var(--radius-sm); background: var(--success-soft); color: var(--success); }
.welcome-cv-change { display: inline-flex; align-items: center; min-height: var(--target-min); padding: 0 var(--space-2); cursor: pointer; }
.welcome-skills { display: grid; gap: var(--space-2); padding-top: var(--space-3); border-top: 1px solid var(--line-soft); }
.welcome-skills p { margin: 0; padding: 0; font-weight: var(--weight-bold); }
.welcome-skills p { font-size: var(--font-small); color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.6px; }
.welcome-skills ul { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: var(--space-2); }
.welcome-skills li { padding: var(--space-1) var(--space-3); border-radius: var(--radius-sm); background: var(--primary-soft); color: var(--primary-text); font-size: var(--font-small); font-weight: var(--weight-semibold); }
.welcome-privacy { display: flex; gap: var(--space-2); margin: auto 0 0; font-size: var(--font-small); line-height: var(--leading-normal); color: var(--text-secondary); }
.welcome-privacy .icon { flex: none; width: 16px; height: 16px; margin-top: calc(var(--space-1) / 2); }
/* « Pas de CV à jour ? » et le « 1 » seul (maquette OnboardingC, étape 2). */
.welcome-no-cv { display: flex; align-items: center; gap: var(--space-3); min-height: 60px; padding: var(--space-2) var(--space-4); background: transparent; border: 1.5px solid var(--field-border); border-radius: var(--radius-card); color: var(--text); text-align: left; white-space: normal; }
.welcome-no-cv > span { flex: 1; display: grid; gap: var(--space-1); }
.welcome-no-cv strong { font-size: var(--font-body); }
.welcome-no-cv small { font-size: var(--font-small); color: var(--text-secondary); }
.welcome-no-cv .icon { flex: none; width: 20px; height: 20px; }
.welcome-cv-scene { position: relative; flex: none; height: 150px; overflow: hidden; }
.welcome-cv-sun { position: absolute; right: 40px; top: 10px; width: 76px; height: 76px; border-radius: 50%; background: var(--peach-soft); }
.welcome-cv-hill { position: absolute; left: 0; bottom: 6px; width: 70%; height: 70px; fill: var(--primary-soft); }
.welcome-cv-ground { position: absolute; left: var(--space-6); right: var(--space-2); bottom: 0; height: 10px; border-radius: var(--radius-sm); background: var(--surface-muted); }
.welcome-cv-person { position: absolute; left: 50%; bottom: 6px; transform: translateX(-50%); }
/* Section 41 : Langues 28 px sous le bloc ORP sur ordinateur ; « Retour » 8 px sous « Ajouter une langue ». Le téléphone
   pose les langues à part depuis le §60 (WelcomeQuestions). */
.wdk .welcome-langs { margin-top: var(--wdk-28); }
.welcome-langs + .wdk-foot { margin-top: var(--space-2); }
.welcome-offer { display: grid; gap: var(--space-3); padding: var(--space-5); background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-card); box-shadow: 0 10px 30px rgba(27, 31, 42, 0.10); }
.welcome-offer-head { display: flex; align-items: flex-start; justify-content: space-between; }
.welcome-offer-title { display: grid; gap: var(--space-1); margin: 0; }
.welcome-offer-title strong { font-size: var(--title-sub); line-height: var(--leading-tight); font-weight: var(--weight-bold); }
.welcome-offer-title span { color: var(--text-secondary); }
.welcome-offer-why { margin: 0; padding-top: var(--space-3); border-top: 1px solid var(--line-soft); font-size: var(--font-small); line-height: var(--leading-normal); }
.welcome-count { margin: 0; text-align: center; font-size: var(--font-small); font-weight: var(--weight-semibold); color: var(--text-secondary); }
.welcome-ready { display: grid; justify-items: center; gap: var(--space-3); padding: var(--space-6) var(--space-5); background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-card); text-align: center; }
/* « Tout est prêt. » (maquette OnboardingC) : le rond pêche de 170 px, les étincelles, le « 1 » de 150 px (§15). */
.welcome-ready-scene { position: relative; width: 100%; height: 190px; }
.welcome-ready-sun { position: absolute; left: 50%; top: 6px; width: 170px; height: 170px; border-radius: 50%; background: var(--peach-soft); transform: translateX(-50%); }
.welcome-ready-sparkles { position: absolute; left: 28px; top: 14px; width: auto; height: 52px; }
.welcome-ready-person { position: absolute; left: 50%; bottom: 0; transform: translateX(-50%); }
.welcome-ready > strong { font-size: var(--font-figure); font-weight: var(--weight-bold); }
.welcome-ready p { margin: 0; color: var(--text-secondary); }
.welcome-ready .link { display: inline-flex; align-items: center; min-height: var(--target-min); font-size: var(--font-body); }
.welcome-actions { position: sticky; bottom: 0; padding-top: var(--space-3); background: inherit; }
.welcome-blue .welcome-actions { background: var(--primary); }
.welcome-cta { display: flex; align-items: center; justify-content: space-between; width: 100%; min-height: 58px; padding: 0 var(--space-5) 0 var(--space-6); border-radius: var(--radius-pill); font-size: var(--font-title); font-weight: var(--weight-bold); }
.welcome-start { border: 0; background: var(--on-primary); color: var(--on-brand-surface); cursor: pointer; }
/* L'alerte sur téléphone (OnboardingC, étape 3) : le rappel 16/12 px, les étapes à 14 px ; « Plus tard » de 44 px sous
   le bouton principal. */
/* Section 41 : la phrase 22 px de haut en --text-lead, 16 px au-dessus de la carte (l'écart de l'écran). */
.welcome-alert-lead { font-size: var(--font-label); color: var(--text-lead); }
.welcome-alert-actions { display: flex; flex-direction: column; }
.welcome-alert-later { align-self: center; min-height: var(--target-min); padding: 0 var(--space-4); font-size: var(--font-label); font-weight: var(--weight-bold); color: var(--primary-text); }
.welcome-sort { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-3); }
.welcome-sort button { justify-content: center; min-height: 58px; border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
@media (prefers-reduced-motion: reduce) {
  .welcome-progress span { transition: none; }
  .welcome-struck path, .welcome-hand { animation: none; }
}

/* Premiers pas sur ordinateur (MODIFICATIONS_9 §5.1, maquettes OnboardingOrdinateur…) : en-tête et grille sur 1 080 px,
   640 px de contenu, 80 px, la scène de 360 px à 48 px sous le haut ; boutons 32 px sous le dernier bloc. Valeurs de la
   maquette ramenées sur la grille de 4 (6 → 8 entre les traits, 6 → 4 sous la valeur d’un critère). */
.wdk { --wdk-w: 1080px; --wdk-col: 640px; --wdk-scene: 360px; --wdk-gap: 80px; --wdk-top: 76px; --wdk-bar: 8px; --wdk-bar-on: 28px;
  --wdk-13: 13px; --wdk-16: 16px; --wdk-40: 40px; --wdk-48: 48px; --wdk-18: 18px; --wdk-28: 28px; --wdk-22: 22px; --wdk-20: 20px; --wdk-24: 24px;
  --wdk-52: 52px; --wdk-pad: 18.5px; --wdk-row-pad: 14.5px; --wdk-orp-pad: 10.5px; --wdk-72: 72px; --wdk-56: 56px; --wdk-44: 44px; --wdk-radius-logo: 10px;
  min-height: 100dvh; background: var(--bg); color: var(--text); }
.wdk-top { box-sizing: border-box; display: flex; align-items: center; gap: var(--space-4); width: min(var(--wdk-w), 100% - 2 * var(--space-6)); height: var(--wdk-top); margin: 0 auto; }
.wdk-top .welcome-brand { flex: 1; font-size: var(--font-section); font-weight: var(--weight-heavy); }
.wdk-step { font-size: var(--font-small); font-weight: var(--weight-bold); color: var(--text-secondary); }
.wdk-bars { display: flex; align-items: center; gap: var(--space-2); }
.wdk-bars span { width: var(--wdk-bar); height: var(--wdk-bar); border-radius: var(--radius-pill); background: var(--line-strong); transition: width 0.3s; }
.wdk-bars span.on { background: var(--primary-graphic); }
.wdk-bars span.current { width: var(--wdk-bar-on); }
.wdk-grid { box-sizing: border-box; display: grid; grid-template-columns: minmax(0, var(--wdk-col)) var(--wdk-scene); column-gap: var(--wdk-gap); justify-content: space-between; width: min(var(--wdk-w), 100% - 2 * var(--space-6)); margin: 0 auto; padding-top: var(--wdk-40); }
.wdk-col { display: flex; flex-direction: column; min-width: 0; }
.wdk-cap { margin: 0; font-size: var(--wdk-13); line-height: var(--wdk-16); font-weight: var(--weight-bold); letter-spacing: 0.06em; text-transform: uppercase; color: var(--text-secondary); }
.wdk-title { margin: var(--space-3) 0 0; font-size: var(--wdk-40); line-height: var(--wdk-48); font-weight: var(--weight-heavy); letter-spacing: -0.4px; }
.wdk-title:focus { outline: none; }
.wdk-title .welcome-hand { margin: 0; font-size: 1.45em; line-height: var(--leading-none); color: var(--primary-graphic); transform: none; animation: none; }
.wdk-lead { margin: var(--space-3) 0 0; font-size: var(--wdk-18); line-height: var(--wdk-28); color: var(--text-tertiary); }
.wdk-card { box-sizing: border-box; padding: var(--wdk-pad); background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); }
.wdk-drop { display: flex; flex-direction: column; align-items: center; gap: var(--space-2); margin-top: var(--space-8); padding: var(--space-8) var(--space-6); background: var(--surface); border: 2px dashed var(--field-border); border-radius: var(--radius-card); text-align: center; cursor: pointer; }
.wdk-drop.dragging { border-color: var(--primary-graphic); background: var(--primary-soft); }
.wdk-drop:focus-within { outline: 2px solid var(--primary-graphic); outline-offset: 2px; }
.wdk-drop-icon { width: var(--wdk-28); height: var(--wdk-28); color: var(--primary-graphic); }
.wdk-drop > b { margin-top: var(--space-2); font-size: var(--wdk-18); line-height: var(--wdk-24); }
.wdk-drop > span:not(.wdk-drop-button) { font-size: var(--font-label); line-height: var(--wdk-22); color: var(--text-secondary); }
.wdk-drop-button, .wdk-cta { display: inline-flex; align-items: center; justify-content: center; height: var(--wdk-52); min-height: var(--wdk-52); padding: 0 var(--wdk-28); border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); white-space: nowrap; }
.wdk-drop-button { margin-top: var(--space-3); background: var(--primary); color: var(--on-primary); }
.wdk-file { margin-top: var(--space-8); }
.wdk-file-head { display: flex; align-items: center; gap: var(--space-4); }
.wdk-file-icon { flex: none; width: var(--wdk-28); height: var(--wdk-28); color: var(--primary-graphic); }
.wdk-file-name { flex: 1; min-width: 0; }
.wdk-file-name b { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: var(--font-body); line-height: var(--wdk-22); }
.wdk-file-name span { display: block; margin-top: var(--space-1); font-size: var(--font-small); line-height: var(--wdk-20); color: var(--text-secondary); }
.wdk-file-state { font-size: var(--font-label); font-weight: var(--weight-bold); color: var(--primary-text); }
.wdk-file-state.paused { color: var(--peach-text); }
.wdk-file-change { min-height: var(--wdk-44); display: inline-flex; align-items: center; font-size: var(--font-label); font-weight: var(--weight-bold); color: var(--primary-text); cursor: pointer; }
.wdk-file-change:focus-within { outline: 2px solid var(--primary-graphic); }
.wdk-bar { height: var(--wdk-bar); margin-top: var(--space-4); border-radius: var(--radius-pill); background: var(--surface-muted); overflow: hidden; }
.wdk-bar span { display: block; width: 60%; height: 100%; border-radius: var(--radius-pill); background: var(--primary-graphic); animation: wdk-read 24s cubic-bezier(.1, .7, .3, 1) both; }
.wdk-file.paused .wdk-bar span { background: var(--warning); animation-play-state: paused; }
@keyframes wdk-read { from { width: 8%; } to { width: 92%; } }
@media (prefers-reduced-motion: reduce) { .wdk-bar span { animation: none; } }
.wdk-loading { margin-top: var(--space-5); }
.wdk-file-note { margin: var(--space-2) 0 0; font-size: var(--font-small); line-height: var(--wdk-20); color: var(--text-secondary); }
.wdk-found { display: flex; align-items: center; gap: var(--space-1); margin: var(--space-3) 0 0; font-size: var(--wdk-13); line-height: var(--wdk-16); font-weight: var(--weight-bold); color: var(--success); }
.wdk-found .icon { width: var(--space-4); height: var(--space-4); }
.wdk-note { display: flex; gap: var(--space-3); margin: var(--space-5) 0 0; font-size: var(--font-small); line-height: var(--wdk-20); color: var(--text-secondary); }
.wdk-note .icon { flex: none; width: var(--wdk-18); height: var(--wdk-18); }
.wdk-note a { padding: var(--space-1) 0; color: var(--primary-text); font-weight: var(--weight-bold); }
.wdk-foot { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); margin-top: var(--space-8); padding: var(--space-6) 0 var(--wdk-40); }
.wdk-link { display: inline-flex; align-items: center; gap: var(--space-1); min-height: var(--wdk-44); padding: 0; border: 0; background: none; color: var(--primary-text); font: inherit; font-size: var(--font-label); font-weight: var(--weight-bold); cursor: pointer; }
.wdk-link .icon { width: var(--wdk-18); height: var(--wdk-18); }
.wdk-back { height: var(--wdk-52); min-height: var(--wdk-52); padding: 0 var(--space-6); border-radius: var(--radius-pill); font-size: var(--font-body); }
.wdk-offers { display: flex; flex-direction: column; gap: var(--space-2); margin: var(--wdk-28) 0 0; padding: 0; list-style: none; }
.wdk-offer { display: flex; align-items: center; gap: var(--space-4); padding-top: var(--wdk-row-pad); padding-bottom: var(--wdk-row-pad); }
.wdk-offer-logo { flex: none; display: grid; place-items: center; width: var(--wdk-44); height: var(--wdk-44); border-radius: var(--wdk-radius-logo); background: var(--text); color: var(--surface); font-size: var(--font-label); font-weight: var(--weight-bold); }
.wdk-offer-text { flex: 1; min-width: 0; }
.wdk-offer-text > b { display: block; font-size: var(--font-body); line-height: var(--wdk-22); }
.wdk-offer-text > span { display: block; margin-top: var(--space-1); font-size: var(--font-small); line-height: var(--wdk-20); color: var(--text-secondary); }
.wdk-offer-text .tone-very-close, .wdk-offer-text .tone-close { color: var(--success); }
.wdk-offer-text .tone-dig { color: var(--peach-text); }
.wdk-small { height: var(--wdk-40); min-height: var(--wdk-40); padding: 0 var(--space-4); border-radius: var(--radius-pill); font-size: var(--font-label); }
.wdk-offer-done { font-size: var(--font-label); font-weight: var(--weight-bold); color: var(--text-secondary); }
/* L'alerte sur ordinateur (section 41) : pied à droite « Plus tard » puis « J'ai créé l'alerte », 24 px entre eux. */
.wdk-foot-end { display: flex; align-items: center; gap: var(--space-6); }
.wdk-foot-end .wdk-link { font-size: var(--font-body); }
/* Section 42 du 16.11 : le choix « Avec l'extension / À la main », deux options de 56 px dans un fond gris. */
.wdk-via { --wdk-via-h: 56px; --wdk-via-pad: 4px; --wdk-via-r: 16px; --wdk-via-option-r: 12px; --wdk-via-sub: 13px;
  --wdk-via-shadow: 0 1px 2px rgb(27 31 42 / 12%);
  display: flex; gap: var(--wdk-via-pad); margin-top: var(--space-5); padding: var(--wdk-via-pad); background: var(--surface-muted); border-radius: var(--wdk-via-r); }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .wdk-via { --wdk-via-shadow: 0 1px 2px rgb(0 0 0 / 30%); } }
:root[data-theme="dark"] .wdk-via { --wdk-via-shadow: 0 1px 2px rgb(0 0 0 / 30%); }
.wdk-via-option { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: var(--wdk-via-h); padding: 0 var(--space-3); border: 0; border-radius: var(--wdk-via-option-r); background: transparent; color: var(--text-tertiary); font: inherit; cursor: pointer; }
.wdk-via-option b { font-size: var(--wdk-16); line-height: var(--wdk-22); font-weight: var(--weight-semibold); }
.wdk-via-option span { font-size: var(--wdk-via-sub); line-height: var(--wdk-18); color: var(--text-secondary); }
.wdk-via-option.on { background: var(--surface); box-shadow: var(--wdk-via-shadow); color: var(--text); }
.wdk-via-option.on b { font-weight: var(--weight-heavy); }
.wdk-via ~ .wa-desk { margin-top: var(--space-4); }
.wdk-mailbox { width: 420px; height: auto; margin-top: var(--wdk-40); }
.wdk-scene { display: flex; justify-content: center; align-items: flex-start; padding-top: var(--wdk-48); }
.wdk-scene .illu { width: var(--wdk-scene); }
.wdk-scene .illu img { width: 100%; height: auto; }
.wdk-toast { position: fixed; left: 50%; bottom: var(--space-8); z-index: 20; display: flex; align-items: center; gap: var(--space-4); min-height: var(--wdk-56); padding: 0 var(--space-2) 0 var(--space-5); transform: translateX(-50%); background: var(--snackbar-bg); color: var(--snackbar-text); border-radius: var(--space-4); box-shadow: var(--shadow-band-card); font-size: var(--font-label); font-weight: var(--weight-semibold); }
.wdk-toast button { min-height: var(--wdk-44); padding: 0 var(--space-3); border: 0; background: none; color: var(--snackbar-action); font: inherit; font-weight: var(--weight-heavy); }
</style>
