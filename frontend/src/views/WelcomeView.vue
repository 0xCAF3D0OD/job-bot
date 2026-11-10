<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import sparkles from "../assets/accessoires/accessoire-etincelles.webp";
import { api, QUIET, type CriteriaIn, type Offer, type SettingsModel } from "../api/client";
import type { components } from "../api/schema";
import AppIcon from "../components/AppIcon.vue";
import BrandMark from "../components/BrandMark.vue";
import CompanyLogo from "../components/CompanyLogo.vue";
import IconButton from "../components/IconButton.vue";
import SceneIllustration, { type SceneName } from "../components/SceneIllustration.vue";
import TroupeScene from "../components/TroupeScene.vue";
import ScoreRing from "../components/ScoreRing.vue";
import SidePanel from "../components/SidePanel.vue";
import TagInput from "../components/TagInput.vue";
import { useAssistant } from "../composables/useAssistant";
import { useAuth } from "../composables/useAuth";
import { usePhone } from "../composables/usePhone";
import { UNDO_MS } from "../composables/useUndo";
import { companyPlace, rateText, remoteText, scoreWord } from "../format";
import { whyLine } from "../whyLine";

// Les premiers pas (maquette OnboardingC, docs/139 étape 11b ; O1 à O10, Kevin, 2026-11-05) : quatre étapes, une
// barre en quatre segments et « Passer » en haut.
// 1. La page bleue : « Moins chercher plus vivre. ».
// 2. Le CV : lu par l'IA quand elle est branchée (sans les coordonnées, llm/redact.py) ; ses compétences.
// 3. Les critères : postes en puces (pré-remplis par le CV), lieux en puces, l'ORP et ses recherches par mois.
// 4. Le tri : jusqu'à 3 offres déjà notées, à garder ou écarter ; sinon, directement « Tout est prêt. ».
// Ce qui n'est plus demandé prend une valeur par défaut (O1), rappelée en une ligne à la fin, modifiable dans
// Compte : taux peu importe, langues du CV (sinon le français), télétravail accepté, remise le 5, téléphone
// désactivé.
type Understanding = components["schemas"]["Understanding"];
type Step = 0 | 1 | 2 | 3;
const OTHER_LANGUAGES = ["allemand", "italien", "anglais"] as const;
const LANGUAGE_NAMES: Record<string, string> = { allemand: "allemand", italien: "italien", anglais: "anglais" };
const MAX_ROLES = 3;
const DUE_DAY = 5;
// Le gribouillis qui barre le premier mot de chaque titre : le tracé de la maquette (comme « C'est fait ! »).
const SCRIBBLE =
  "M2 22 10.3 3.9 14.3 34.2 18.8 6 25.4 31.4 32 8 37.6 34.8 43 5.4 46.3 36.2 51.3 3.7 58.9 32.1 65.3 5.2 69.4 31.4 76.8 5.6 83.5 33.7 91 7.2 97.9 34.2 104 4.7 107.5 33.5 111.6 5.9 119.2 35.6 126.6 4.9 132.6 34.5 140 8.7 146.7 31.4 152.9 9 157.4 33.3 161.2 5.8 166.3 31.4 170.3 4.5 178 31.5 184.3 8.3 191.1 32.7 196.7 8.3 198 32.1M196 14C150 30 90 6 40 26S8 18 4 30";
// Chaque titre : un début, le mot barré, la fin manuscrite (Caveat Brush, réduite à ces seuls caractères).
const TITLES: { lead: string; struck: string; hand: string }[] = [
  { lead: "Moins", struck: "chercher", hand: "plus vivre." },
  { lead: "", struck: "Tout réécrire", hand: "Ton CV suffit." },
  { lead: "", struck: "Toutes les offres", hand: "Juste les tiennes." },
  { lead: "Lire", struck: "312 offres", hand: "En trier 3." },
];

// Ordinateur dès 1 024 px (MODIFICATIONS_9 §5, maquettes OnboardingOrdinateur… du 9 novembre) : trois étapes sur la
// grille commune (1 080 px, 640 + 80 + 360), une scène par étape à droite, plus de « Passer » ; la lecture du CV ne
// bloque pas l'écran.
const { phone } = usePhone();
const { phone: wideQuery } = usePhone("(min-width: 1024px)");
const desk = computed(() => wideQuery.value && !phone.value);

const router = useRouter();
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
const cvError = ref("");
const understanding = ref<Understanding | null>(null);
const skills = computed(() =>
  (understanding.value?.chunks ?? []).filter((c) => c.kind === "competence").map((c) => c.title).slice(0, 8),
);

// Étape 3, les critères.
const roles = ref<string[]>([]);
const picked = ref<string[]>([]);
const newRole = ref("");
// « + Ajouter » (maquette Onboarding) : le champ d'un poste s'ouvre sur demande quand le CV en a déjà proposé.
const adding = ref(false);
const places = ref<string[]>([]);
const orp = ref(true);
const target = ref(10);
// Le taux minimum (OnboardingOrdinateurEtape2, carte « Taux d'activité ») : celui du CV s'il le dit, sinon peu importe.
const rate = ref<number | null>(null);
const RATES = [null, 50, 60, 70, 80, 90, 100] as const;
const rateLabel = (value: number | null): string => (value ? `${value} à 100\u202F%` : "Peu importe");
// Le panneau ouvert par une carte de critère (Postes, Lieux, Taux d'activité).
const editing = ref<"" | "roles" | "places" | "rate">("");
const EDIT_TITLES = { roles: "Postes", places: "Lieux", rate: "Taux d’activité" } as const;
const rolesFromCv = computed(() => !!understanding.value?.roles.length);
// « Repris de ton CV » seulement si la lecture a vraiment repris quelque chose (test du 10 novembre : le CV
// enregistré mais pas lu affichait quand même « Pré-rempli depuis ton CV »).
const fromCv = computed(() => !!understanding.value && (understanding.value.roles.length > 0 || !!understanding.value.min_rate));
const cvUnread = computed(() => !!cvName.value && !reading.value && !paused.value && !understanding.value);
const rateFromCv = computed(() => !!understanding.value?.min_rate && rate.value === understanding.value.min_rate);

// Étape 4, le tri.
const offers = ref<Offer[]>([]);
const position = ref(0);
const kept = ref(0);
const dismissed = ref(0);
const deciding = ref(false);
const sorting = computed(() => step.value === 3 && position.value < offers.value.length);
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
    if (state.data.goal === "job") orp.value = false;
    // Reprendre là où on s'était arrêté, sans revenir au tri (il se recharge à l'étape 3).
    if (state.data.status !== "done") step.value = Math.max(0, Math.min(state.data.step - 1, 2)) as Step;
  }
  // Sur ordinateur, la page bleue n'existe pas : on commence au CV.
  if (desk.value && step.value === 0) step.value = 1;
  loaded.value = true;
});

function go(next: Step): void {
  step.value = next;
  void remember({ step: next + 1 });
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
    const { data } = await api.POST("/api/documents/{document_id}/understand", { params: { path: { document_id: documentId } }, ...QUIET });
    if (!data || (!data.chunks.length && !data.roles.length)) return;
    understanding.value = data;
    const known = new Set(roles.value.map((r) => r.toLowerCase()));
    const found = data.roles.filter((r) => !known.has(r.toLowerCase()));
    roles.value = [...roles.value, ...found];
    picked.value = [...picked.value, ...found].slice(0, MAX_ROLES);
    if (data.min_rate && rate.value === null) rate.value = data.min_rate;
    saveChunks();
  } catch {
    // La connexion est tombée : le CV est enregistré, la lecture reprend seule (OnboardingOrdinateurCoupure).
    understanding.value = null;
    if (cvId.value === documentId) pause(documentId);
  } finally {
    reading.value = false;
  }
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
  if (step.value === 3) return "reussite";
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
  cvConfirmed.value = true;
  go(2);
  saveChunks();
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

function toggleRole(role: string): void {
  if (picked.value.includes(role)) picked.value = picked.value.filter((r) => r !== role);
  else if (picked.value.length < MAX_ROLES) picked.value = [...picked.value, role];
}

function openAdd(): void {
  adding.value = true;
  void nextTick(() => document.getElementById("welcome-role")?.focus());
}

function addRole(): void {
  const role = newRole.value.trim().slice(0, 80);
  newRole.value = "";
  if (!role) return;
  if (!roles.value.some((r) => r.toLowerCase() === role.toLowerCase())) roles.value = [...roles.value, role];
  const same = roles.value.find((r) => r.toLowerCase() === role.toLowerCase())!;
  if (!picked.value.includes(same) && picked.value.length < MAX_ROLES) picked.value = [...picked.value, same];
}

// Les langues : celles que le CV mentionne, sinon le français seul.
const spoken = computed(() => (understanding.value?.languages ?? []).filter((l) => (OTHER_LANGUAGES as readonly string[]).includes(l)));

// « Voir mes offres » : les critères, les réglages et les postes partent ensemble, avec les valeurs par défaut.
// Un poste tapé sans le « + » compte aussi : le bouton bleu est celui qu'on presse (2026-11-05, Kevin).
async function confirmCriteria(): Promise<void> {
  if (newRole.value.trim()) addRole();
  if (criteria.value) {
    criteria.value = {
      ...criteria.value,
      locations: places.value,
      // Sur ordinateur, le taux se choisit dans sa carte ; sur téléphone, peu importe (O1).
      min_rate: desk.value ? rate.value : null,
      remote_policy: "from_switzerland",
      unspoken_languages: OTHER_LANGUAGES.filter((l) => !spoken.value.includes(l)),
    };
    void api.PUT("/api/criteria", { body: criteria.value });
  }
  if (settings.value) {
    settings.value = { ...settings.value, orp_monthly_target: orp.value ? target.value : null, orp_due_day: DUE_DAY };
    void api.PUT("/api/settings", { body: settings.value });
  }
  step.value = 3;
  void remember({ step: 4, goal: orp.value ? "orp" : "job", roles: picked.value, ...(picked.value[0] ? { trade: picked.value[0] } : {}) });
  const { data } = await api.GET("/api/offers", { params: { query: { view: "to_review", sort: "score", limit: 3 } } });
  offers.value = (data?.items ?? []).filter((o) => o.score !== null && o.score !== undefined).slice(0, 3);
}

// « Garder » et « Écarter » : comme dans Candidatures.
// « Garder » et « Écarter » : comme dans Candidatures. « Écarter » laisse « Annuler » 6 s, comme
// OffersView : l'offre reprend son statut d'avant et le tri revient sur elle.
const notice = ref("");
type Restorable = "to_review" | "later";
const undo = ref<{ id: number; status: Restorable } | null>(null);
let undoTimer: ReturnType<typeof setTimeout> | undefined;

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
    clearTimeout(undoTimer);
    undo.value = choice === "dismiss" ? { id: offer.id, status: offer.status === "later" ? "later" : "to_review" } : null;
    notice.value = undo.value ? "Offre écartée." : "";
    if (undo.value) {
      const shown = undo.value;
      undoTimer = setTimeout(() => {
        if (undo.value !== shown) return;
        undo.value = null;
        notice.value = "";
      }, UNDO_MS);
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
const DESK_EYEBROWS: Record<number, string> = { 1: "Premiers pas", 2: "Ce que tu cherches", 3: "Tes premières offres" };

async function undoDismiss(): Promise<void> {
  const last = undo.value;
  if (!last) return;
  clearTimeout(undoTimer);
  undo.value = null;
  notice.value = "";
  const { response } = await api.PATCH("/api/offers/{offer_id}/status", {
    params: { path: { offer_id: last.id } },
    body: { status: last.status },
  });
  if (!response.ok) return;
  position.value = Math.max(0, position.value - 1);
  dismissed.value = Math.max(0, dismissed.value - 1);
}
onBeforeUnmount(() => {
  clearTimeout(undoTimer);
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
// Les valeurs par défaut (O1), en une ligne.
const defaults = computed(() =>
  [
    "Taux : peu importe",
    `Langues : ${["français", ...spoken.value.map((l) => LANGUAGE_NAMES[l])].join(", ")}`,
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
  <section
    v-if="loaded && desk"
    class="welcome wdk"
    data-test="welcome"
  >
    <header class="wdk-top">
      <span class="welcome-brand"><BrandMark :size="30" />jobA1</span>
      <span
        class="wdk-step"
        data-test="welcome-eyebrow"
      >Étape {{ step }} sur 3</span>
      <span
        class="wdk-bars"
        role="progressbar"
        :aria-label="`Étape ${step} sur 3`"
        aria-valuemin="1"
        aria-valuemax="3"
        :aria-valuenow="step"
        data-test="welcome-dots"
      >
        <span
          v-for="i in 3"
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
            Tes critères
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
                <div
                  class="wdk-bar"
                  role="progressbar"
                  aria-label="Lecture du CV"
                >
                  <span />
                </div>
                <p class="wdk-file-note">
                  {{ readState === "paused" ? "Ton CV est bien enregistré. La lecture reprend toute seule dès que la connexion revient." : "On repère tes postes, tes compétences et tes lieux. Tu peux continuer, on termine pendant ce temps." }}
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
              <span>Ton CV reste privé&#8239;: il sert à noter les offres et à préparer tes lettres. L’IA n’en reçoit que les parties utiles,
                sans tes coordonnées. <RouterLink to="/tes-donnees#ia">En savoir plus</RouterLink></span>
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
              {{ fromCv ? "Repris de ton CV. Vérifie-les, tu pourras les changer à tout moment dans Profil." : cvUnread ? "Ton CV n’a pas pu être lu : indique-les ici, tu pourras les changer à tout moment dans Profil." : "Tu pourras les changer à tout moment dans Profil." }}
            </p>
            <ul class="wdk-rows">
              <li>
                <button
                  type="button"
                  class="wdk-row"
                  aria-haspopup="dialog"
                  data-test="criteria-roles"
                  @click="editing = 'roles'"
                >
                  <span class="wdk-row-text">
                    <span class="wdk-row-key">Postes</span>
                    <span class="wdk-row-value">{{ reading && !picked.length ? "Lecture du CV…" : picked.join(", ") || "À choisir" }}</span>
                    <span
                      v-if="rolesFromCv"
                      class="wdk-tag"
                    ><AppIcon name="tick" />Trouvé dans ton CV</span>
                  </span>
                  <span
                    class="arrow-circle small"
                    aria-hidden="true"
                  ><AppIcon name="arrow-right" /></span>
                </button>
              </li>
              <li>
                <button
                  type="button"
                  class="wdk-row"
                  aria-haspopup="dialog"
                  data-test="criteria-places"
                  @click="editing = 'places'"
                >
                  <span class="wdk-row-text">
                    <span class="wdk-row-key">Lieux</span>
                    <span class="wdk-row-value">{{ places.join(", ") || "Toute la Suisse" }}</span>
                  </span>
                  <span
                    class="arrow-circle small"
                    aria-hidden="true"
                  ><AppIcon name="arrow-right" /></span>
                </button>
              </li>
              <li>
                <button
                  type="button"
                  class="wdk-row"
                  aria-haspopup="dialog"
                  data-test="criteria-rate"
                  @click="editing = 'rate'"
                >
                  <span class="wdk-row-text">
                    <span class="wdk-row-key">Taux d’activité</span>
                    <span class="wdk-row-value">{{ reading && rate === null ? "Lecture du CV…" : rateLabel(rate) }}</span>
                    <span
                      v-if="rateFromCv"
                      class="wdk-tag"
                    ><AppIcon name="tick" />Trouvé dans ton CV</span>
                  </span>
                  <span
                    class="arrow-circle small"
                    aria-hidden="true"
                  ><AppIcon name="arrow-right" /></span>
                </button>
              </li>
            </ul>
            <div class="wdk-card wdk-orp">
              <label class="wdk-orp-row">
                <span><b>Je suis inscrit à l’ORP</b><span>jobA1 tient le suivi de tes recherches</span></span>
                <input
                  v-model="orp"
                  type="checkbox"
                  role="switch"
                  data-test="orp-switch"
                >
              </label>
              <div
                v-if="orp"
                class="wdk-orp-row"
              >
                <span id="welcome-target"><b>Recherches par mois</b><span>Objectif fixé avec ta conseillère</span></span>
                <button
                  type="button"
                  class="wdk-stepper"
                  aria-label="Une de moins"
                  :disabled="target <= 1"
                  data-test="target-minus"
                  @click="target = Math.max(1, target - 1)"
                >
                  −
                </button>
                <output
                  class="wdk-target"
                  aria-live="polite"
                  aria-labelledby="welcome-target"
                  data-test="target"
                >{{ target }}</output>
                <button
                  type="button"
                  class="wdk-stepper"
                  aria-label="Une de plus"
                  :disabled="target >= 99"
                  data-test="target-plus"
                  @click="target = Math.min(99, target + 1)"
                >
                  +
                </button>
              </div>
            </div>
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
            <SidePanel
              :open="editing !== ''"
              :title="editing ? EDIT_TITLES[editing] : ''"
              @close="editing = ''"
            >
              <div
                v-if="editing === 'roles'"
                class="wdk-panel"
              >
                <p class="wdk-panel-note">
                  Trois postes au plus.
                </p>
                <div
                  class="welcome-roles"
                  data-test="roles"
                >
                  <button
                    v-for="role in roles"
                    :key="role"
                    type="button"
                    :class="['chip', 'welcome-role', { on: picked.includes(role) }]"
                    :aria-pressed="picked.includes(role)"
                    :aria-disabled="!picked.includes(role) && picked.length >= MAX_ROLES ? 'true' : undefined"
                    @click="toggleRole(role)"
                  >
                    <AppIcon
                      v-if="picked.includes(role)"
                      name="check"
                    />{{ role }}
                  </button>
                </div>
                <div class="tag-add">
                  <input
                    id="welcome-role"
                    v-model="newRole"
                    type="text"
                    maxlength="80"
                    placeholder="Ajouter un poste"
                    aria-label="Ajouter un poste"
                    data-test="role-input"
                    @keydown.enter.prevent="addRole"
                  >
                  <IconButton
                    icon="plus"
                    label="Ajouter"
                    data-test="role-add"
                    @click="addRole"
                  />
                </div>
              </div>
              <div
                v-else-if="editing === 'places'"
                class="wdk-panel"
              >
                <label
                  for="welcome-place"
                  class="wdk-panel-note"
                >Une ville ou un canton, autant que tu veux.</label>
                <TagInput
                  id="welcome-place"
                  v-model="places"
                  placeholder="Une ville ou un canton"
                />
              </div>
              <fieldset
                v-else-if="editing === 'rate'"
                class="wdk-panel wdk-rates"
              >
                <legend class="visually-hidden">
                  Taux d’activité minimum
                </legend>
                <label
                  v-for="value in RATES"
                  :key="String(value)"
                  class="wdk-rate"
                >
                  <input
                    v-model="rate"
                    type="radio"
                    name="welcome-rate"
                    :value="value"
                  >
                  {{ rateLabel(value) }}
                </label>
              </fieldset>
              <template #footer>
                <button
                  type="button"
                  class="primary wdk-panel-done"
                  data-test="criteria-done"
                  @click="editing = ''"
                >
                  OK
                </button>
              </template>
            </SidePanel>
          </template>

          <template v-else>
            <p class="wdk-lead">
              {{ offers.length ? "jobA1 a lu les offres publiées cette semaine. Celles-ci te correspondent le mieux. Garde ou écarte : jobA1 apprend de tes choix." : "jobA1 lit les offres chaque nuit. Les premières qui te correspondent t’attendront dans Candidatures." }}
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
                  <b>{{ offer.title }}</b>
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
                    :aria-label="`Écarter ${offer.title}`"
                    data-test="welcome-dismiss"
                    @click="decideOffer(offer, 'dismiss')"
                  >
                    Écarter
                  </button>
                  <button
                    type="button"
                    class="secondary wdk-small"
                    :aria-label="`Garder ${offer.title}`"
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
                @click="go(2)"
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
        <SceneIllustration
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
          @click="go((step - 1) as Step)"
        />
        <span class="welcome-brand"><BrandMark :size="30" />jobA1</span>
        <button
          v-if="!(step === 3 && !sorting)"
          type="button"
          class="link welcome-later"
          data-test="welcome-later"
          @click="later"
        >
          Passer
        </button>
      </header>
      <div
        class="welcome-progress"
        role="progressbar"
        :aria-label="`Étape ${step + 1} sur 4`"
        aria-valuemin="1"
        aria-valuemax="4"
        :aria-valuenow="step + 1"
      >
        <span
          v-for="i in 4"
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
          class="welcome-screen"
          :data-test="`welcome-step-${step + 1}`"
        >
          <h1
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
                  <small data-test="cv-reading">{{ reading ? "Lecture de ton CV…" : understanding ? "Importé et analysé" : "Importé, mais pas pu être lu : tu compléteras à l’étape suivante" }}</small>
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
              <span>Ton CV reste privé : il sert à noter les offres et à préparer tes lettres. L’IA n’en reçoit que les parties utiles,
                sans tes coordonnées. <RouterLink to="/tes-donnees#ia">En savoir plus</RouterLink></span>
            </p>
          </template>

          <template v-else-if="step === 2">
            <p class="welcome-lead">
              {{ fromCv ? "Pré-rempli depuis ton CV. Modifiable à tout moment dans Compte." : cvUnread ? "Ton CV n’a pas pu être lu : indique tes postes et tes lieux. Modifiable à tout moment dans Compte." : "Modifiable à tout moment dans Compte." }}
            </p>
            <fieldset class="welcome-field">
              <legend>Postes</legend>
              <div
                class="welcome-roles"
                data-test="roles"
              >
                <button
                  v-for="role in roles"
                  :key="role"
                  type="button"
                  :class="['chip', 'welcome-role', { on: picked.includes(role) }]"
                  :aria-pressed="picked.includes(role)"
                  :aria-disabled="!picked.includes(role) && picked.length >= MAX_ROLES ? 'true' : undefined"
                  @click="toggleRole(role)"
                >
                  <AppIcon
                    v-if="picked.includes(role)"
                    name="check"
                  />{{ role }}
                </button>
                <button
                  v-if="roles.length && !adding"
                  type="button"
                  class="chip welcome-role welcome-role-add"
                  data-test="role-open"
                  @click="openAdd"
                >
                  <AppIcon name="plus" />Ajouter
                </button>
              </div>
              <div
                v-if="!roles.length || adding"
                class="tag-add"
              >
                <input
                  id="welcome-role"
                  v-model="newRole"
                  type="text"
                  maxlength="80"
                  placeholder="Ajouter un poste"
                  aria-label="Ajouter un poste"
                  data-test="role-input"
                  @keydown.enter.prevent="addRole"
                >
                <IconButton
                  icon="plus"
                  label="Ajouter"
                  data-test="role-add"
                  @click="addRole"
                />
              </div>
              <p
                v-if="picked.length >= MAX_ROLES"
                class="welcome-note"
              >
                Trois postes au plus.
              </p>
            </fieldset>
            <div class="welcome-field">
              <label
                for="welcome-place"
                class="welcome-label"
              >Lieux</label>
              <TagInput
                id="welcome-place"
                v-model="places"
                placeholder="Une ville ou un canton"
              />
            </div>
            <div class="welcome-orp">
              <label class="welcome-orp-row">
                <span><strong>Je suis inscrit à l’ORP</strong><small>Active le suivi de tes recherches</small></span>
                <input
                  v-model="orp"
                  type="checkbox"
                  role="switch"
                  data-test="orp-switch"
                >
              </label>
              <div
                v-if="orp"
                class="welcome-orp-row"
              >
                <span id="welcome-target"><strong>Recherches par mois</strong></span>
                <button
                  type="button"
                  class="icon-button welcome-stepper"
                  aria-label="Moins"
                  data-test="target-minus"
                  @click="target = Math.max(1, target - 1)"
                >
                  −
                </button>
                <output
                  aria-live="polite"
                  aria-labelledby="welcome-target"
                  data-test="target"
                >{{ target }}</output>
                <button
                  type="button"
                  class="icon-button welcome-stepper"
                  aria-label="Plus"
                  data-test="target-plus"
                  @click="target = Math.min(30, target + 1)"
                >
                  +
                </button>
              </div>
            </div>
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
          <p
            v-if="notice"
            class="notice"
            role="status"
            data-test="welcome-notice"
          >
            {{ notice }}
            <button
              v-if="undo"
              type="button"
              class="link"
              data-test="undo-status"
              @click="undoDismiss"
            >
              Annuler
            </button>
          </p>
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
          class="primary welcome-cta"
          data-test="welcome-continue"
          @click="confirmCriteria"
        >
          Voir mes offres<AppIcon name="arrow-right" />
        </button>
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
.welcome-progress { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--space-1); padding-top: var(--space-2); }
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
.welcome-skills p, .welcome-label, .welcome-field legend { margin: 0; padding: 0; font-weight: var(--weight-bold); }
.welcome-skills p { font-size: var(--font-small); color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.6px; }
.welcome-skills ul { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: var(--space-2); }
.welcome-skills li { padding: var(--space-1) var(--space-3); border-radius: var(--radius-sm); background: var(--primary-soft); color: var(--primary-text); font-size: var(--font-small); font-weight: var(--weight-semibold); }
.welcome-privacy { display: flex; gap: var(--space-2); margin: auto 0 0; font-size: var(--font-small); line-height: var(--leading-normal); color: var(--text-secondary); }
.welcome-privacy .icon { flex: none; width: 16px; height: 16px; margin-top: calc(var(--space-1) / 2); }
.welcome-field { display: grid; gap: var(--space-3); margin: 0; padding: 0; border: 0; min-width: 0; }
.welcome-field legend { margin-bottom: var(--space-3); }
.welcome-roles { display: flex; flex-wrap: wrap; gap: var(--space-2); }
.welcome-role.chip { min-height: var(--btn-compact); padding: 0 var(--space-3); font-size: var(--font-small); font-weight: var(--weight-semibold); }
.welcome-role .icon { width: 16px; height: 16px; }
.welcome-role-add.chip { border: 1.5px dashed var(--field-border); background: transparent; color: var(--primary-text); }
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
.welcome-note { margin: 0; font-size: var(--font-small); color: var(--text-secondary); }
.welcome-orp { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-card); }
.welcome-orp-row { display: flex; align-items: center; gap: var(--space-3); min-height: 60px; padding: var(--space-2) var(--space-3); }
.welcome-orp-row + .welcome-orp-row { border-top: 1px solid var(--line-soft); }
.welcome-orp-row > span { flex: 1; display: grid; gap: calc(var(--space-1) / 2); }
.welcome-orp-row small { font-size: var(--font-small); color: var(--text-secondary); }
.welcome-orp-row output { min-width: 28px; text-align: center; font-size: var(--title-sub); font-weight: var(--weight-bold); }
.welcome-stepper { width: var(--target-min); height: var(--target-min); border: 1.5px solid var(--field-border); border-radius: var(--radius-pill); font-size: var(--title-sub); font-weight: var(--weight-semibold); }
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
.wdk-file-note { margin: var(--space-2) 0 0; font-size: var(--font-small); line-height: var(--wdk-20); color: var(--text-secondary); }
.wdk-found { display: flex; align-items: center; gap: var(--space-1); margin: var(--space-3) 0 0; font-size: var(--wdk-13); line-height: var(--wdk-16); font-weight: var(--weight-bold); color: var(--success); }
.wdk-found .icon, .wdk-tag .icon { width: var(--space-4); height: var(--space-4); }
.wdk-note { display: flex; gap: var(--space-3); margin: var(--space-5) 0 0; font-size: var(--font-small); line-height: var(--wdk-20); color: var(--text-secondary); }
.wdk-note .icon { flex: none; width: var(--wdk-18); height: var(--wdk-18); }
.wdk-note a { padding: var(--space-1) 0; color: var(--primary-text); font-weight: var(--weight-bold); }
.wdk-foot { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); margin-top: var(--space-8); padding: var(--space-6) 0 var(--wdk-40); }
.wdk-link { display: inline-flex; align-items: center; gap: var(--space-1); min-height: var(--wdk-44); padding: 0; border: 0; background: none; color: var(--primary-text); font: inherit; font-size: var(--font-label); font-weight: var(--weight-bold); cursor: pointer; }
.wdk-link .icon { width: var(--wdk-18); height: var(--wdk-18); }
.wdk-back { height: var(--wdk-52); min-height: var(--wdk-52); padding: 0 var(--space-6); border-radius: var(--radius-pill); font-size: var(--font-body); }
.wdk-rows { display: flex; flex-direction: column; gap: var(--space-2); margin: var(--wdk-28) 0 0; padding: 0; list-style: none; }
.wdk-row { box-sizing: border-box; display: flex; align-items: center; gap: var(--space-4); width: 100%; min-height: var(--wdk-72); padding: var(--wdk-row-pad) var(--wdk-pad); background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--radius-card); color: var(--text); font: inherit; text-align: left; cursor: pointer; }
.wdk-row:hover { border-color: var(--primary-graphic); }
.wdk-row-text { flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: flex-start; }
.wdk-row-key { font-size: var(--wdk-13); line-height: var(--wdk-16); color: var(--text-secondary); }
.wdk-row-value { margin-top: var(--space-1); font-size: var(--font-body); line-height: var(--wdk-22); font-weight: var(--weight-bold); }
.wdk-tag { display: inline-flex; align-items: center; gap: var(--space-1); margin-top: var(--space-1); font-size: var(--wdk-13); line-height: var(--wdk-16); font-weight: var(--weight-bold); color: var(--success); }
.wdk-orp { margin-top: var(--space-4); padding-top: var(--wdk-orp-pad); padding-bottom: var(--wdk-orp-pad); }
.wdk-orp-row { display: flex; align-items: center; gap: var(--space-4); min-height: var(--wdk-56); }
.wdk-orp-row + .wdk-orp-row { border-top: 1px solid var(--line); }
.wdk-orp-row > span:first-child { flex: 1; }
.wdk-orp-row b { display: block; font-size: var(--font-body); line-height: var(--wdk-22); }
.wdk-orp-row b + span { display: block; margin-top: var(--space-1); font-size: var(--font-small); line-height: var(--wdk-20); color: var(--text-secondary); }
.wdk-stepper { flex: none; display: grid; place-items: center; width: var(--wdk-40); height: var(--wdk-40); min-height: var(--wdk-40); padding: 0; border: 1.5px solid var(--field-border); border-radius: var(--radius-pill); background: var(--surface); color: var(--text); font: inherit; font-size: var(--font-title); }
.wdk-target { min-width: var(--space-8); text-align: center; font-size: var(--font-title); font-weight: var(--weight-heavy); }
.wdk-panel { display: flex; flex-direction: column; gap: var(--space-4); margin: 0; padding: 0; border: 0; }
.wdk-panel-note { margin: 0; font-size: var(--font-small); color: var(--text-secondary); }
.wdk-rate { display: flex; align-items: center; gap: var(--space-3); min-height: var(--wdk-44); font-size: var(--font-body); cursor: pointer; }
.wdk-rate input { width: var(--wdk-20); height: var(--wdk-20); margin: 0; accent-color: var(--primary-graphic); }
.wdk-panel-done { width: 100%; }
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
.wdk-scene { display: flex; justify-content: center; align-items: flex-start; padding-top: var(--wdk-48); }
.wdk-scene .illu { width: var(--wdk-scene); }
.wdk-scene .illu img { width: 100%; height: auto; }
.wdk-toast { position: fixed; left: 50%; bottom: var(--space-8); z-index: 20; display: flex; align-items: center; gap: var(--space-4); min-height: var(--wdk-56); padding: 0 var(--space-2) 0 var(--space-5); transform: translateX(-50%); background: var(--snackbar-bg); color: var(--snackbar-text); border-radius: var(--space-4); box-shadow: var(--shadow-band-card); font-size: var(--font-label); font-weight: var(--weight-semibold); }
.wdk-toast button { min-height: var(--wdk-44); padding: 0 var(--space-3); border: 0; background: none; color: var(--snackbar-action); font: inherit; font-weight: var(--weight-heavy); }
</style>
