<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import sparkles from "../assets/accessoires/accessoire-etincelles.webp";
import { api, type CriteriaIn, type Offer, type SettingsModel } from "../api/client";
import type { components } from "../api/schema";
import AppIcon from "../components/AppIcon.vue";
import BrandMark from "../components/BrandMark.vue";
import CompanyLogo from "../components/CompanyLogo.vue";
import Illustration from "../components/Illustration.vue";
import IconButton from "../components/IconButton.vue";
import ScoreRing from "../components/ScoreRing.vue";
import TagInput from "../components/TagInput.vue";
import { useAssistant } from "../composables/useAssistant";
import { useAuth } from "../composables/useAuth";
import { usePhone } from "../composables/usePhone";
import { UNDO_MS } from "../composables/useUndo";
import { rateText, remoteText } from "../format";
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

// Ordinateur dès 1 024 px (maquette du 8 novembre, OnboardingOrdinateur, D27) : trois étapes sur le fond clair, sans
// la page bleue ; en haut, le logo, trois points et « Passer » ; « Étape N sur 3 » au-dessus du titre ; la première
// réunit l'accueil et le CV, avec le personnage de 360 px à droite ; « Retour » et « Continuer » en bas.
const { phone } = usePhone();
const { phone: wideQuery } = usePhone("(min-width: 1024px)");
const desk = computed(() => wideQuery.value && !phone.value);
const DESK_TITLES: Record<number, { lead: string; hand: string }> = {
  1: { lead: "Moins chercher,", hand: "plus vivre." },
  2: { lead: "Ce que tu cherches", hand: "" },
  3: { lead: "312 offres lues. En trier 3.", hand: "" },
};

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
  if (!file) return;
  uploading.value = true;
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
      cvError.value = typeof detail === "string" ? `Refusé : ${detail}.` : "Ce fichier n'a pas pu être importé.";
    }
  } finally {
    uploading.value = false;
  }
}

// Le CV lu par l'IA (docs/121 §A), sans les coordonnées. Sans IA, plafond atteint ou erreur : pas de
// compétences, et l'étape 3 part de ce qui est déjà enregistré.
async function understand(documentId: number): Promise<void> {
  reading.value = true;
  try {
    const { data } = await api.POST("/api/documents/{document_id}/understand", { params: { path: { document_id: documentId } } });
    if (!data || (!data.chunks.length && !data.roles.length)) return;
    understanding.value = data;
    const known = new Set(roles.value.map((r) => r.toLowerCase()));
    const found = data.roles.filter((r) => !known.has(r.toLowerCase()));
    roles.value = [...roles.value, ...found];
    picked.value = [...picked.value, ...found].slice(0, MAX_ROLES);
  } catch {
    understanding.value = null;
  } finally {
    reading.value = false;
  }
}

// « Continuer » : les blocs lus dans le CV (sauf ceux déjà dans le profil) rejoignent le profil, rattachés au
// CV ; ils restent modifiables dans Profil.
function confirmCv(): void {
  const found = understanding.value;
  go(2);
  if (!found) return;
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
      min_rate: null,
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
onBeforeUnmount(() => clearTimeout(undoTimer));

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
const CV_QUESTION = "Je n'ai pas de CV à jour. Aide-moi à en créer un.";
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
  <section
    v-if="loaded"
    :class="['welcome', { 'welcome-blue': step === 0 && !desk, 'welcome-desk': desk }]"
    data-test="welcome"
  >
    <div class="welcome-column">
      <header class="welcome-top">
        <IconButton
          v-if="step > 0 && !desk"
          icon="arrow-left"
          label="Étape précédente"
          data-test="welcome-back"
          @click="go((step - 1) as Step)"
        />
        <span class="welcome-brand"><BrandMark :size="30" />jobA1</span>
        <span
          v-if="desk"
          class="welcome-dots"
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
        v-if="!desk"
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
          <p
            v-if="desk"
            class="welcome-eyebrow"
            data-test="welcome-eyebrow"
          >
            Étape {{ step }} sur 3
          </p>
          <h1
            v-if="desk && DESK_TITLES[step]"
            class="welcome-title"
          >
            {{ DESK_TITLES[step]!.lead }}<template v-if="DESK_TITLES[step]!.hand">
              {{ " " }}<span class="welcome-hand">{{ DESK_TITLES[step]!.hand }}</span>
            </template>
          </h1>
          <h1
            v-else
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
              {{ desk ? "jobA1 trie les offres, prépare tes lettres et tient ton suivi ORP. Ton CV suffit pour commencer." : "jobA1 en tire tes compétences pour noter chaque offre." }}
            </p>
            <Illustration
              v-if="desk"
              pose="bonjour"
              :height="280"
              :desktop-height="360"
              full
              class="welcome-desk-person"
              data-test="welcome-desk-person"
            />
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
                  <small data-test="cv-reading">{{ reading ? "Lecture de ton CV…" : understanding ? "Importé et analysé" : "Importé" }}</small>
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
                <span><strong>Pas de CV à jour ?</strong><small>L'Assistant t'aide à en créer un</small></span>
                <AppIcon name="chevron" />
              </button>
              <!-- Le personnage du kit avec son CV, le soleil et la colline (maquette OnboardingC, étape 2). -->
              <div
                v-if="!desk"
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
                <Illustration
                  pose="cv"
                  :height="122"
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
              <span>Ton CV reste privé : il sert à noter les offres et à préparer tes lettres. L'IA n'en reçoit que les parties utiles,
                sans tes coordonnées. <RouterLink to="/tes-donnees#ia">En savoir plus</RouterLink></span>
            </p>
          </template>

          <template v-else-if="step === 2">
            <p class="welcome-lead">
              Pré-rempli depuis ton CV. Modifiable à tout moment dans Compte.
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
                <span><strong>Je suis inscrit à l'ORP</strong><small>Active le suivi de tes recherches</small></span>
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
                Garde ou écarte. Celles que tu gardes t'attendent dans Candidatures.
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
                  <span>{{ [current.company || "Entreprise non indiquée", current.location].filter(Boolean).join(" · ") }}</span>
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
                  <strong>D'après ton CV :</strong> {{ whyLine(current.why) }}
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
              <!-- Le personnage de la révélation à la place de la coche (maquette OnboardingC, fin du tri). -->
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
                <Illustration
                  pose="revelation"
                  :height="186"
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
          v-if="desk && step > 1 && !(step === 3 && !sorting)"
          type="button"
          class="secondary welcome-desk-back"
          data-test="welcome-back"
          @click="go((step - 1) as Step)"
        >
          Retour
        </button>
        <button
          v-if="step === 0"
          type="button"
          class="welcome-cta welcome-start"
          data-test="welcome-start"
          @click="go(1)"
        >
          C'est parti<AppIcon name="arrow-right" />
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
   manuscrit, l'action en bas. La première étape est toute bleue (O3, O10 : --primary dans les deux thèmes). */
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
/* « Pas de CV à jour ? » et le personnage au CV (maquette OnboardingC, étape 2). */
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
/* « Tout est prêt. » (maquette OnboardingC) : le rond pêche de 170 px, les étincelles, le personnage de 186 px. */
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
/* Ordinateur (maquette du 8 novembre, OnboardingOrdinateur, D27) : 880 px sur le fond clair ; le logo à gauche, trois
   points et « Passer » à droite ; « Étape N sur 3 », le titre de 34, la phrase de 17 ; à la première étape, le personnage
   de 360 px à droite ; « Retour » et « Continuer » en bas, de part et d'autre. */
.welcome-desk { --wd-300: 300px; --wd-34: 34px; --wd-40: 40px; --wd-17: 17px; --wd-28: 28px; --wd-360: 360px; --wd-24: 24px; }
.welcome-desk .welcome-column { min-height: 0; max-width: none; padding: 0; }
.welcome-desk .welcome-screen { flex: none; gap: 0; }
.welcome-desk .welcome-screen > * + * { margin-top: var(--space-4); }
.welcome-desk .welcome-screen > .welcome-title { margin-top: 0; }
.welcome-desk .welcome-top { gap: var(--space-4); padding: var(--space-5) max(var(--space-6), calc((100vw - var(--header-max)) / 2 + var(--space-6))) 0; }
.welcome-desk .welcome-brand { flex: 1; }
.welcome-dots { display: inline-flex; align-items: center; gap: var(--space-1); }
.welcome-dots span { width: 8px; height: 8px; border-radius: var(--radius-pill); background: var(--line); transition: width 0.3s; }
.welcome-dots span.on { background: var(--primary-graphic); }
.welcome-dots span.current { width: var(--wd-28); }
.welcome-desk .welcome-later { padding: 0 var(--space-3); color: var(--primary-text); font-weight: var(--weight-bold); }
.welcome-desk .welcome-screen { position: relative; box-sizing: border-box; width: 100%; max-width: 880px; margin: 0 auto; padding: var(--space-8) 0 0; }
.welcome-desk .welcome-screen[data-test="welcome-step-2"] { padding-right: var(--wd-300); }
.welcome-eyebrow { margin: 0 0 var(--space-2); font-size: var(--label-caps); font-weight: var(--weight-bold); letter-spacing: var(--letter-label); text-transform: uppercase; color: var(--text-secondary); }
.welcome-desk .welcome-title { font-size: var(--wd-34); line-height: var(--wd-40); font-weight: var(--weight-heavy); letter-spacing: -0.4px; }
.welcome-desk .welcome-hand { margin-top: 0; font-size: 1.45em; line-height: var(--leading-none); color: var(--primary-graphic); transform: none; }
.welcome-desk .welcome-screen > .welcome-lead { margin-top: var(--space-3); font-size: var(--wd-17); line-height: var(--wd-28); color: var(--text-secondary); }
.welcome-desk-person { position: absolute; top: var(--wd-24); right: 60px; }
.welcome-desk .welcome-actions { position: static; display: flex; justify-content: space-between; gap: var(--space-3); box-sizing: border-box; width: 100%; max-width: 880px; margin: var(--wd-24) auto var(--space-12); padding: 0; background: none; }
.welcome-desk .welcome-actions > .welcome-cta { width: auto; min-height: var(--target-min); margin-left: auto; padding: 0 var(--space-5); border-radius: var(--radius-pill); font-size: var(--font-label); }
.welcome-desk .welcome-actions > .welcome-cta .icon { display: none; }
.welcome-desk .welcome-desk-back { min-height: var(--target-min); padding: 0 var(--space-4); border-radius: var(--radius-pill); font-size: var(--font-label); }
.welcome-desk .welcome-sort { display: flex; gap: var(--space-3); margin-left: auto; }
.welcome-desk .welcome-sort button { min-height: var(--target-min); padding: 0 var(--space-4); border-radius: var(--radius-pill); font-size: var(--font-label); }
.welcome-desk .welcome-sort .icon { display: none; }
@media (prefers-reduced-motion: reduce) {
  .welcome-progress span { transition: none; }
  .welcome-struck path, .welcome-hand { animation: none; }
}
</style>
