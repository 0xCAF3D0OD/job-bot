<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { api, type CriteriaIn, type SettingsModel } from "../api/client";
import type { components } from "../api/schema";
import AppIcon from "../components/AppIcon.vue";
import Illustration, { type IllustrationName } from "../components/Illustration.vue";
import { useAuth } from "../composables/useAuth";

// L'accueil après la première connexion (docs/66) : un écran, une question, des cartes qu'on
// touche ; chaque réponse remplit un vrai réglage. « Retour » et « Passer » en bas de chaque
// écran, « Plus tard » en haut ; le récapitulatif ramène à la question qu'on veut corriger.
// Depuis la 0.91.0 (docs/121 §A) : le CV déposé est lu par l'IA (sans les coordonnées), un
// écran « Voici ce que j'ai compris » propose les blocs de profil et les postes visés ; les
// langues et le télétravail se demandent, préremplis par le CV.
type Goal = "job" | "orp" | "news";
type StepKey =
  | "goal"
  | "trade"
  | "places"
  | "rate"
  | "orp"
  | "due"
  | "cv"
  | "understood"
  | "languages"
  | "remote"
  | "phone"
  | "ready"
  | "next";
type Understanding = components["schemas"]["Understanding"];
type Remote = "refuse" | "from_switzerland";
// Le français va de soi : on demande les autres langues de travail (les critères écartent
// les offres qui exigent une langue que la personne ne parle pas).
const OTHER_LANGUAGES = [
  { id: "allemand", title: "Allemand" },
  { id: "italien", title: "Italien" },
  { id: "anglais", title: "Anglais" },
] as const;
type OtherLanguage = (typeof OTHER_LANGUAGES)[number]["id"];
type Icon = InstanceType<typeof AppIcon>["$props"]["name"];

const router = useRouter();
const { me } = useAuth();

const goal = ref<Goal | null>(null);
const trade = ref("");
const places = ref<string[]>([]);
const city = ref("");
const rate = ref<number | null | undefined>(undefined);
const target = ref<number | null | undefined>(undefined);
const dueDay = ref(5);
const dueChosen = ref(false);
const cvName = ref("");
const cvId = ref<number | null>(null);
// La lecture du CV par l'IA : rien tant qu'elle n'a pas répondu ; sans IA, l'écran est sauté.
const reading = ref(false);
const understanding = ref<Understanding | null>(null);
const keptChunks = ref<number[]>([]);
const keptRoles = ref<string[]>([]);
const chunksAdded = ref(0);
const languages = ref<OtherLanguage[] | null>(null);
const remote = ref<Remote | null>(null);
const cvError = ref("");
const uploading = ref(false);
const phone = ref<boolean | null>(null);
const topic = ref<string | null>(null);
const criteria = ref<CriteriaIn | null>(null);
const settings = ref<SettingsModel | null>(null);
const index = ref(0);
const direction = ref<"forward" | "back">("forward");
// Venu du récapitulatif pour corriger une réponse : « Continuer » y ramène aussitôt.
const fromRecap = ref(false);
const loaded = ref(false);

const STEPS = computed<StepKey[]>(() => [
  "goal",
  "trade",
  "places",
  "rate",
  ...(goal.value === "orp" ? (["orp", "due"] as const) : []),
  "cv",
  ...(understanding.value ? (["understood"] as const) : []),
  "languages",
  "remote",
  "phone",
  "ready",
  "next",
]);
const step = computed(() => STEPS.value[Math.min(index.value, STEPS.value.length - 1)]!);
// Un point par écran : plein quand la question a une réponse, on le touche pour y aller.
const LABELS: Record<StepKey, string> = {
  goal: "Ce qui t'amène",
  trade: "Ton métier",
  places: "Où travailler",
  rate: "Taux d'activité",
  orp: "Objectif ORP",
  due: "Date de remise",
  cv: "Ton CV",
  understood: "Ce que dit ton CV",
  languages: "Langues",
  remote: "Télétravail",
  phone: "Notifications",
  ready: "C'est prêt",
  next: "La suite",
};
function answered(key: StepKey): boolean {
  return {
    goal: goal.value !== null,
    trade: trade.value.trim() !== "",
    places: places.value.length > 0,
    rate: rate.value !== undefined,
    orp: target.value != null,
    due: dueChosen.value,
    cv: cvName.value !== "",
    understood: chunksAdded.value > 0,
    languages: languages.value !== null,
    remote: remote.value !== null,
    phone: phone.value !== null,
    ready: false,
    next: false,
  }[key];
}

function jump(to: number): void {
  if (to === index.value) return;
  fromRecap.value = false;
  direction.value = to > index.value ? "forward" : "back";
  index.value = to;
  void remember({ step: to + 1 });
}

// L'écran de la date a déjà son calendrier : pas d'illustration.
const ART: Partial<Record<StepKey, IllustrationName>> = {
  goal: "accueil-reseau",
  trade: "formations",
  places: "lieux-carte",
  rate: "tableau-de-bord",
  orp: "preuves-orp",
  cv: "offres-profils",
  languages: "accueil-reseau",
  remote: "porte-ouverte",
  phone: "lecture-calme",
  ready: "suivi-envoi",
};

const GOALS: { id: Goal; icon: Icon; title: string; hint: string }[] = [
  { id: "job", icon: "search", title: "Je cherche un emploi", hint: "Trouver les bonnes offres et postuler vite." },
  { id: "orp", icon: "calendar", title: "Je suis inscrit·e à l'ORP", hint: "Et je dois prouver mes recherches chaque mois." },
  { id: "news", icon: "news", title: "Je veux suivre mon métier", hint: "Les actualités et les formations de mon domaine." },
];
const TRADES = ["DevOps", "Informatique", "Infirmier·ère", "Comptable", "Vente", "Logistique", "Enseignement", "Cuisine"];
const CANTONS = [
  { code: "VD", name: "Vaud" },
  { code: "GE", name: "Genève" },
  { code: "FR", name: "Fribourg" },
  { code: "NE", name: "Neuchâtel" },
  { code: "VS", name: "Valais" },
  { code: "JU", name: "Jura" },
  { code: "BE", name: "Berne" },
  { code: "ZH", name: "Zurich" },
];
const RATES: { value: number | null; title: string }[] = [
  { value: 100, title: "100 %" },
  { value: 80, title: "80 à 100 %" },
  { value: 50, title: "50 à 80 %" },
  { value: null, title: "Peu importe" },
];
const TARGETS = [4, 6, 8, 10, 12];
const CHUNK_KIND: Record<string, string> = {
  experience: "Expérience",
  competence: "Compétence",
  formation: "Formation",
  preference: "Préférence",
};

// En changeant d'écran, le bouton qui avait le focus disparaît : le focus va au titre du nouvel
// écran, pour que le clavier et les lecteurs d'écran ne perdent pas leur place (docs/69 §4).
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
  const [state, found, saved, notifications] = await Promise.all([
    api.GET("/api/welcome"),
    api.GET("/api/criteria"),
    api.GET("/api/settings"),
    api.GET("/api/notifications"),
  ]);
  if (found.data) {
    criteria.value = found.data.criteria;
    places.value = [...(found.data.criteria.locations ?? [])];
    rate.value = found.data.criteria.min_rate ?? undefined;
    // Déjà réglés (accueil repris) : les langues et le télétravail gardent leur réponse.
    if (found.data.saved_at) {
      const unspoken = found.data.criteria.unspoken_languages ?? [];
      languages.value = OTHER_LANGUAGES.map((l) => l.id).filter((id) => !unspoken.includes(id));
      remote.value = found.data.criteria.remote_policy === "refuse" ? "refuse" : "from_switzerland";
    }
  }
  if (saved.data) {
    settings.value = saved.data;
    target.value = saved.data.orp_monthly_target ?? undefined;
    dueDay.value = saved.data.orp_due_day ?? 5;
  }
  topic.value = notifications.data?.topic ?? null;
  if (state.data) {
    goal.value = state.data.goal ?? null;
    trade.value = state.data.trade ?? "";
    keptRoles.value = [...(state.data.roles ?? [])];
    // Reprendre là où on s'était arrêté (docs/66 §4).
    if (state.data.status !== "done") index.value = Math.max(0, Math.min(state.data.step - 1, STEPS.value.length - 1));
  }
  loaded.value = true;
});

// L'écran avance aussitôt ; l'enregistrement suit en arrière-plan (le rythme de Duolingo).
// L'avancement et la réponse de l'écran partent ensemble, pour ne pas se marcher dessus.
function go(next: number, changes: Record<string, unknown> = {}): void {
  if (fromRecap.value && next > index.value) {
    next = STEPS.value.indexOf("ready");
    fromRecap.value = false;
  }
  direction.value = next > index.value ? "forward" : "back";
  index.value = Math.max(0, Math.min(next, STEPS.value.length - 1));
  void remember({ step: index.value + 1, ...changes });
}

// Les réponses sont d'abord fusionnées ici : chaque envoi contient toutes celles d'avant.
function saveCriteria(changes: Partial<CriteriaIn>): void {
  if (!criteria.value) return;
  criteria.value = { ...criteria.value, ...changes };
  void api.PUT("/api/criteria", { body: criteria.value });
}

function saveSettings(changes: Partial<SettingsModel>): void {
  if (!settings.value) return;
  settings.value = { ...settings.value, ...changes };
  void api.PUT("/api/settings", { body: settings.value });
}

function chooseGoal(id: Goal): void {
  // Passer à l'ORP ajoute une question : on la pose avant de revenir au récapitulatif.
  if (id === "orp" && goal.value !== "orp") fromRecap.value = false;
  goal.value = id;
  go(index.value + 1, { goal: id });
}

function confirmTrade(): void {
  go(index.value + 1, trade.value.trim() ? { trade: trade.value.trim() } : {});
}

function togglePlace(code: string): void {
  places.value = places.value.includes(code) ? places.value.filter((p) => p !== code) : [...places.value, code];
}

function addCity(): void {
  const name = city.value.trim();
  if (name && !places.value.some((p) => p.toLowerCase() === name.toLowerCase())) places.value = [...places.value, name];
  city.value = "";
}

function confirmPlaces(): void {
  addCity();
  saveCriteria({ locations: places.value });
  go(index.value + 1);
}

function chooseRate(value: number | null): void {
  rate.value = value;
  saveCriteria({ min_rate: value });
  go(index.value + 1);
}

function confirmOrp(): void {
  saveSettings({ orp_monthly_target: target.value ?? null });
  go(index.value + 1);
}

// La date de remise : le calendrier du mois prochain, semaines du lundi au dimanche. L'ORP
// accepte un jour entre le 2 et le 28 ; les autres jours sont grisés.
const DUE_MIN = 2;
const DUE_MAX = 28;
const dueMonth = computed(() => {
  const today = new Date();
  const first = new Date(today.getFullYear(), today.getMonth() + 1, 1);
  const days = new Date(first.getFullYear(), first.getMonth() + 1, 0).getDate();
  return {
    title: first.toLocaleDateString("fr-CH", { month: "long", year: "numeric" }),
    offset: (first.getDay() + 6) % 7,
    days: Array.from({ length: days }, (_, i) => i + 1),
  };
});

function chooseDue(day: number): void {
  dueDay.value = day;
  dueChosen.value = true;
  saveSettings({ orp_due_day: day });
  go(index.value + 1);
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
      void understand(data.id);
    } else {
      const detail = (error as { detail?: unknown } | undefined)?.detail;
      cvError.value = typeof detail === "string" ? `Refusé : ${detail}.` : "Ce fichier n'a pas pu être déposé.";
    }
  } finally {
    uploading.value = false;
  }
}

// Le CV lu par l'IA (docs/121 §A), sans les coordonnées : les blocs et ce qu'il dit de la
// recherche. Sans IA, plafond atteint ou erreur : l'écran « Voici ce que j'ai compris » ne
// vient pas, l'accueil continue comme avant (les blocs se proposeront dans Profil).
async function understand(documentId: number): Promise<void> {
  reading.value = true;
  try {
    const { data } = await api.POST("/api/documents/{document_id}/understand", {
      params: { path: { document_id: documentId } },
    });
    if (!data || (!data.chunks.length && !data.roles.length)) return;
    understanding.value = data;
    keptChunks.value = data.chunks.map((_, i) => i).filter((i) => data.chunks[i]!.duplicate_of == null);
    const known = new Set(keptRoles.value.map((r) => r.toLowerCase()));
    keptRoles.value = [...keptRoles.value, ...data.roles.filter((r) => !known.has(r.toLowerCase()))].slice(0, 3);
    if (languages.value === null && data.languages.length)
      languages.value = OTHER_LANGUAGES.map((l) => l.id).filter((id) => data.languages.includes(id));
    if (remote.value === null && data.remote) remote.value = data.remote === "remote" ? "from_switzerland" : "refuse";
  } catch {
    understanding.value = null;
  } finally {
    reading.value = false;
  }
}

function toggle<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
}

// « C'est bon » : les blocs gardés rejoignent le profil (rattachés au CV), les postes gardés
// sont notés pour les alertes (docs/121 §B).
async function acceptUnderstood(): Promise<void> {
  const found = understanding.value;
  if (!found) return go(index.value + 1);
  const chosen = keptChunks.value.map((i) => found.chunks[i]!).filter(Boolean);
  go(index.value + 1, { roles: keptRoles.value });
  const created = await Promise.all(
    chosen.map((chunk) =>
      api.POST("/api/profile-chunks", {
        body: { kind: chunk.kind, title: chunk.title, content: chunk.content, tags: chunk.tags, active: true, document_id: cvId.value },
      }),
    ),
  );
  chunksAdded.value = created.filter((r) => r.data).length;
}

function confirmLanguages(): void {
  const spoken = languages.value ?? [];
  languages.value = [...spoken];
  saveCriteria({ unspoken_languages: OTHER_LANGUAGES.map((l) => l.id).filter((id) => !spoken.includes(id)) });
  go(index.value + 1);
}

function chooseRemote(value: Remote): void {
  remote.value = value;
  saveCriteria({ remote_policy: value });
  go(index.value + 1);
}

async function choosePhone(enabled: boolean): Promise<void> {
  phone.value = enabled;
  if (!enabled) go(index.value + 1);
  const { data } = await api.PUT("/api/notifications/phone", { body: { enabled } });
  topic.value = data?.topic ?? null;
}

async function later(): Promise<void> {
  await remember({ postponed: true });
  if (me.value) me.value = { ...me.value, welcome: "postponed" };
  await router.replace("/aujourdhui");
}

async function finish(to: string): Promise<void> {
  await remember({ done: true, postponed: false });
  if (me.value) me.value = { ...me.value, welcome: "done" };
  await router.replace(to);
}

const recap = computed(() =>
  (
    [
      { step: "goal", text: GOALS.find((g) => g.id === goal.value)?.title ?? "" },
      { step: "trade", text: trade.value.trim() },
      {
        step: "places",
        text: places.value.length
          ? places.value.map((p) => CANTONS.find((c) => c.code === p)?.name ?? p).join(", ")
          : "Toute la Suisse",
      },
      { step: "rate", text: rate.value ? `${rate.value} % et plus` : rate.value === null ? "Tout taux d'activité" : "" },
      {
        step: "understood",
        text: chunksAdded.value ? `${chunksAdded.value} ${chunksAdded.value === 1 ? "bloc ajouté" : "blocs ajoutés"} au profil` : "",
      },
      {
        step: "languages",
        text:
          languages.value === null
            ? ""
            : ["Français", ...OTHER_LANGUAGES.filter((l) => languages.value!.includes(l.id)).map((l) => l.title)].join(", "),
      },
      {
        step: "remote",
        text: remote.value === "refuse" ? "Sur place ou hybride" : remote.value ? "Aussi à distance" : "",
      },
      { step: "orp", text: goal.value === "orp" && target.value ? `${target.value} recherches par mois` : "" },
      { step: "due", text: goal.value === "orp" ? `Preuves à remettre avant le ${dueDay.value} du mois` : "" },
    ] satisfies { step: StepKey; text: string }[]
  ).filter((line) => line.text),
);

function edit(key: StepKey): void {
  fromRecap.value = true;
  direction.value = "back";
  index.value = STEPS.value.indexOf(key);
  void remember({ step: index.value + 1 });
}
</script>

<template>
  <section
    v-if="loaded"
    class="welcome"
    data-test="welcome"
  >
    <header class="welcome-top">
      <nav
        class="welcome-dots"
        aria-label="Étapes de l'accueil"
      >
        <button
          v-for="(key, i) in STEPS"
          :key="key"
          type="button"
          :class="['welcome-dot', { current: i === index, answered: answered(key) }]"
          :aria-label="`${i + 1}. ${LABELS[key]}`"
          :aria-current="i === index ? 'step' : undefined"
          :title="LABELS[key]"
          :data-test="`dot-${key}`"
          @click="jump(i)"
        />
      </nav>
      <button
        v-if="step !== 'ready' && step !== 'next'"
        type="button"
        class="link"
        data-test="welcome-later"
        @click="later"
      >
        Plus tard
      </button>
    </header>

    <Transition
      :name="`welcome-${direction}`"
      mode="out-in"
      @after-enter="focusTitle"
    >
      <div
        :key="step"
        class="welcome-screen"
        :data-test="`welcome-${step}`"
      >
        <Illustration
          v-if="ART[step]"
          :name="ART[step]!"
          class="welcome-art"
        />

        <template v-if="step === 'goal'">
          <h1>Bienvenue ! Qu'est-ce qui t'amène ?</h1>
          <div class="welcome-cards">
            <button
              v-for="item in GOALS"
              :key="item.id"
              type="button"
              :class="['welcome-card', { chosen: goal === item.id }]"
              :data-test="`goal-${item.id}`"
              @click="chooseGoal(item.id)"
            >
              <AppIcon :name="item.icon" />
              <span><strong>{{ item.title }}</strong><small>{{ item.hint }}</small></span>
            </button>
          </div>
        </template>

        <template v-else-if="step === 'trade'">
          <h1>Quel métier cherches-tu ?</h1>
          <input
            v-model="trade"
            class="welcome-input"
            type="text"
            maxlength="80"
            placeholder="Ton métier, en quelques mots"
            data-test="trade-input"
            @keydown.enter.prevent="confirmTrade"
          >
          <div class="welcome-chips">
            <button
              v-for="name in TRADES"
              :key="name"
              type="button"
              :class="['welcome-chip', { chosen: trade === name }]"
              @click="trade = name"
            >
              {{ name }}
            </button>
          </div>
        </template>

        <template v-else-if="step === 'places'">
          <h1>Où veux-tu travailler ?</h1>
          <p class="welcome-hint">
            Plusieurs choix possibles.
          </p>
          <div class="welcome-chips">
            <button
              v-for="canton in CANTONS"
              :key="canton.code"
              type="button"
              :class="['welcome-chip', { chosen: places.includes(canton.code) }]"
              :data-test="`place-${canton.code}`"
              @click="togglePlace(canton.code)"
            >
              {{ canton.name }}
            </button>
            <button
              type="button"
              :class="['welcome-chip', { chosen: !places.length }]"
              data-test="place-all"
              @click="places = []"
            >
              Toute la Suisse
            </button>
          </div>
          <div class="welcome-row">
            <input
              v-model="city"
              class="welcome-input"
              type="text"
              placeholder="Ou une ville (Lausanne, Sion…)"
              @keydown.enter.prevent="addCity"
            >
          </div>
          <p
            v-if="places.some((p) => !CANTONS.some((c) => c.code === p))"
            class="welcome-hint"
          >
            {{ places.filter((p) => !CANTONS.some((c) => c.code === p)).join(", ") }}
          </p>
        </template>

        <template v-else-if="step === 'rate'">
          <h1>Quel taux d'activité ?</h1>
          <div class="welcome-cards two">
            <button
              v-for="item in RATES"
              :key="String(item.value)"
              type="button"
              :class="['welcome-card', { chosen: rate === item.value }]"
              :data-test="`rate-${item.value ?? 'any'}`"
              @click="chooseRate(item.value)"
            >
              <span><strong>{{ item.title }}</strong></span>
            </button>
          </div>
        </template>

        <template v-else-if="step === 'orp'">
          <h1>Combien de recherches l'ORP te demande-t-il par mois ?</h1>
          <div class="welcome-chips">
            <button
              v-for="value in TARGETS"
              :key="value"
              type="button"
              :class="['welcome-chip big', { chosen: target === value }]"
              :data-test="`target-${value}`"
              @click="target = value"
            >
              {{ value }}
            </button>
            <button
              type="button"
              :class="['welcome-chip', { chosen: target === null }]"
              @click="target = null"
            >
              Je ne sais pas encore
            </button>
          </div>
        </template>

        <template v-else-if="step === 'due'">
          <h1>Avant quel jour remets-tu tes preuves à l'ORP ?</h1>
          <p class="welcome-hint">
            Chaque mois, pour les recherches du mois d'avant. La plateforme te le rappellera.
          </p>
          <div
            class="welcome-calendar"
            data-test="due-calendar"
          >
            <p class="welcome-calendar-title">
              {{ dueMonth.title }}
            </p>
            <span
              v-for="(day, i) in ['L', 'M', 'M', 'J', 'V', 'S', 'D']"
              :key="`h${i}`"
              class="welcome-calendar-head"
              aria-hidden="true"
            >{{ day }}</span>
            <span
              v-for="n in dueMonth.offset"
              :key="`e${n}`"
            />
            <button
              v-for="day in dueMonth.days"
              :key="day"
              type="button"
              :class="['welcome-day', { chosen: dueDay === day }]"
              :disabled="day < DUE_MIN || day > DUE_MAX"
              :aria-pressed="dueDay === day"
              :data-test="`due-${day}`"
              @click="chooseDue(day)"
            >
              {{ day }}
            </button>
          </div>
        </template>

        <template v-else-if="step === 'cv'">
          <h1>Ton CV, pour que la plateforme te connaisse</h1>
          <p class="welcome-hint">
            Il sert à noter les offres et à préparer tes lettres. Jamais tes coordonnées ne partent à l'IA.
          </p>
          <label
            :class="['welcome-card', 'upload', { chosen: !!cvName }]"
            data-test="cv-upload"
          >
            <AppIcon :name="cvName ? 'file' : 'upload'" />
            <span>
              <strong
                v-if="cvName"
                class="with-icon"
              ><AppIcon name="done" />{{ cvName }}</strong>
              <strong v-else>{{ uploading ? "Dépôt…" : "Déposer mon CV" }}</strong>
              <small data-test="cv-reading">{{ reading ? "Lecture de ton CV…" : "PDF ou Word" }}</small>
            </span>
            <input
              type="file"
              accept=".pdf,.docx,.txt,.md"
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
        </template>

        <template v-else-if="step === 'understood' && understanding">
          <h1>Voici ce que j'ai compris</h1>
          <p class="welcome-hint">
            Lu par l'IA, sans tes coordonnées. Décoche ce qui ne va pas.
          </p>
          <div
            v-if="understanding.roles.length || keptRoles.length"
            class="welcome-group"
          >
            <p class="welcome-label">
              Postes visés
            </p>
            <div
              class="welcome-chips"
              data-test="understood-roles"
            >
              <button
                v-for="role in [...new Set([...keptRoles, ...understanding.roles])]"
                :key="role"
                type="button"
                :class="['welcome-chip', { chosen: keptRoles.includes(role) }]"
                :aria-pressed="keptRoles.includes(role)"
                @click="keptRoles = toggle(keptRoles, role)"
              >
                {{ role }}
              </button>
            </div>
          </div>
          <div
            v-if="understanding.chunks.length"
            class="welcome-group"
          >
            <p class="welcome-label">
              Blocs de profil
            </p>
            <ul
              class="welcome-blocks"
              data-test="understood-chunks"
            >
              <li
                v-for="(chunk, i) in understanding.chunks"
                :key="i"
              >
                <label class="welcome-block">
                  <input
                    type="checkbox"
                    :checked="keptChunks.includes(i)"
                    :data-test="`understood-chunk-${i}`"
                    @change="keptChunks = toggle(keptChunks, i)"
                  >
                  <span>
                    <strong>{{ chunk.title }}</strong>
                    <small>{{ chunk.duplicate_of != null ? `${CHUNK_KIND[chunk.kind]} · déjà dans le profil` : CHUNK_KIND[chunk.kind] }}</small>
                  </span>
                </label>
              </li>
            </ul>
          </div>
        </template>

        <template v-else-if="step === 'languages'">
          <h1>En plus du français, quelles langues parles-tu au travail ?</h1>
          <div
            class="welcome-chips"
            data-test="languages"
          >
            <button
              v-for="item in OTHER_LANGUAGES"
              :key="item.id"
              type="button"
              :class="['welcome-chip', { chosen: languages?.includes(item.id) }]"
              :aria-pressed="!!languages?.includes(item.id)"
              :data-test="`language-${item.id}`"
              @click="languages = toggle(languages ?? [], item.id)"
            >
              {{ item.title }}
            </button>
            <button
              type="button"
              :class="['welcome-chip', { chosen: languages?.length === 0 }]"
              :aria-pressed="languages?.length === 0"
              data-test="language-none"
              @click="languages = []"
            >
              Aucune
            </button>
          </div>
        </template>

        <template v-else-if="step === 'remote'">
          <h1>Et le télétravail complet ?</h1>
          <div class="welcome-cards">
            <button
              type="button"
              :class="['welcome-card', { chosen: remote === 'refuse' }]"
              data-test="remote-refuse"
              @click="chooseRemote('refuse')"
            >
              <AppIcon name="building" />
              <span><strong>Sur place ou hybride</strong><small>Les postes tout à distance sont écartés.</small></span>
            </button>
            <button
              type="button"
              :class="['welcome-card', { chosen: remote === 'from_switzerland' }]"
              data-test="remote-yes"
              @click="chooseRemote('from_switzerland')"
            >
              <AppIcon name="home" />
              <span><strong>Aussi à distance</strong><small>Depuis la Suisse.</small></span>
            </button>
          </div>
        </template>

        <template v-else-if="step === 'phone'">
          <h1>Dernière chose : comment veux-tu être prévenu·e ?</h1>
          <div class="welcome-cards">
            <button
              type="button"
              :class="['welcome-card', { chosen: phone === true }]"
              data-test="phone-yes"
              @click="choosePhone(true)"
            >
              <AppIcon name="bell" />
              <span><strong>Sur mon téléphone</strong><small>Les offres bien notées, les relances, le rappel ORP.</small></span>
            </button>
            <button
              type="button"
              :class="['welcome-card', { chosen: phone === false }]"
              data-test="phone-no"
              @click="choosePhone(false)"
            >
              <AppIcon name="inbox" />
              <span><strong>Seulement dans la plateforme</strong><small>Dans la cloche, en haut.</small></span>
            </button>
          </div>
          <p
            v-if="phone && topic"
            class="welcome-hint"
            data-test="phone-topic"
          >
            Installe l'application gratuite ntfy et abonne-toi au sujet <code>{{ topic }}</code>.
          </p>
        </template>

        <template v-else-if="step === 'ready'">
          <h1>C'est prêt !</h1>
          <ul
            v-if="recap.length"
            class="welcome-recap"
            data-test="welcome-recap"
          >
            <li
              v-for="line in recap"
              :key="line.step"
            >
              <button
                type="button"
                :data-test="`recap-${line.step}`"
                :aria-label="`${line.text} — modifier`"
                @click="edit(line.step)"
              >
                <AppIcon name="check" />
                <span>{{ line.text }}</span>
                <AppIcon
                  name="pencil"
                  class="welcome-recap-edit"
                />
              </button>
            </li>
          </ul>
        </template>

        <template v-else-if="step === 'next'">
          <div class="welcome-speaker">
            <!-- La bulle est le titre de l'écran (docs/69 §4). -->
            <h1
              class="welcome-bubble"
              data-test="welcome-bubble"
            >
              Prochaine étape : créer tes alertes sur les sites d'emploi. La recherche est déjà remplie.
            </h1>
            <Illustration
              name="messager"
              class="welcome-character"
            />
          </div>
        </template>
      </div>
    </Transition>

    <footer class="welcome-actions">
      <button
        v-if="step === 'next'"
        type="button"
        class="primary welcome-continue"
        data-test="welcome-alerts"
        @click="finish('/candidatures/alertes')"
      >
        Créer mes alertes
      </button>
      <button
        v-else-if="step !== 'goal' && step !== 'rate' && step !== 'due' && step !== 'remote'"
        type="button"
        class="primary welcome-continue"
        :disabled="
          (step === 'trade' && !trade.trim()) ||
            (step === 'cv' && (!cvName || reading)) ||
            (step === 'languages' && languages === null) ||
            (step === 'phone' && phone === null)
        "
        data-test="welcome-continue"
        @click="
          step === 'trade'
            ? confirmTrade()
            : step === 'places'
              ? confirmPlaces()
              : step === 'orp'
                ? confirmOrp()
                : step === 'understood'
                  ? acceptUnderstood()
                  : step === 'languages'
                    ? confirmLanguages()
                    : go(index + 1)
        "
      >
        {{ fromRecap ? "Enregistrer" : step === "understood" ? "C'est bon" : "Continuer" }}
      </button>
      <div class="welcome-nav">
        <button
          v-if="index > 0"
          type="button"
          class="secondary"
          data-test="welcome-back"
          @click="fromRecap ? go(STEPS.indexOf('ready')) : go(index - 1)"
        >
          <span class="with-icon"><AppIcon name="arrow-left" />{{ fromRecap ? "Revenir au récapitulatif" : "Retour" }}</span>
        </button>
        <button
          v-if="step !== 'ready' && step !== 'next'"
          type="button"
          class="secondary"
          data-test="welcome-skip"
          @click="go(index + 1)"
        >
          <span class="with-icon">Passer<AppIcon name="arrow-right" /></span>
        </button>
      </div>
    </footer>
  </section>
</template>
