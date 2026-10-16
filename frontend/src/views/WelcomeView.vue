<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { api, type CriteriaIn, type SettingsModel } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import Illustration, { type IllustrationName } from "../components/Illustration.vue";
import { useAuth } from "../composables/useAuth";

// L'accueil après la première connexion (docs/66) : un écran, une question, des cartes qu'on
// touche ; chaque réponse remplit un vrai réglage. « Passer » partout, « Plus tard » en haut.
type Goal = "job" | "orp" | "news";
type StepKey = "goal" | "trade" | "places" | "rate" | "orp" | "cv" | "phone" | "ready";
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
const cvName = ref("");
const cvError = ref("");
const uploading = ref(false);
const phone = ref<boolean | null>(null);
const topic = ref<string | null>(null);
const criteria = ref<CriteriaIn | null>(null);
const settings = ref<SettingsModel | null>(null);
const index = ref(0);
const direction = ref<"forward" | "back">("forward");
const loaded = ref(false);

const STEPS = computed<StepKey[]>(() => [
  "goal",
  "trade",
  "places",
  "rate",
  ...(goal.value === "orp" ? (["orp"] as const) : []),
  "cv",
  "phone",
  "ready",
]);
const step = computed(() => STEPS.value[Math.min(index.value, STEPS.value.length - 1)]!);
// La progression compte les questions, pas l'écran « C'est prêt ».
const progress = computed(() => Math.round((index.value / (STEPS.value.length - 1)) * 100));

const ART: Record<StepKey, IllustrationName> = {
  goal: "morning-plans",
  trade: "stepping-up",
  places: "mailbox",
  rate: "done",
  orp: "certification",
  cv: "absorbed",
  phone: "message-sent",
  ready: "handshake-deal",
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
    // Reprendre là où on s'était arrêté (docs/66 §4).
    if (state.data.status !== "done") index.value = Math.max(0, Math.min(state.data.step - 1, STEPS.value.length - 1));
  }
  loaded.value = true;
});

// L'écran avance aussitôt ; l'enregistrement suit en arrière-plan (le rythme de Duolingo).
// L'avancement et la réponse de l'écran partent ensemble, pour ne pas se marcher dessus.
function go(next: number, changes: Record<string, unknown> = {}): void {
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
  saveSettings({ orp_monthly_target: target.value ?? null, orp_due_day: dueDay.value });
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
    if (data) cvName.value = data.filename;
    else {
      const detail = (error as { detail?: unknown } | undefined)?.detail;
      cvError.value = typeof detail === "string" ? `Refusé : ${detail}.` : "Ce fichier n'a pas pu être déposé.";
    }
  } finally {
    uploading.value = false;
  }
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
  [
    trade.value.trim(),
    places.value.length
      ? places.value.map((p) => CANTONS.find((c) => c.code === p)?.name ?? p).join(", ")
      : "toute la Suisse",
    rate.value ? `${rate.value} % et plus` : "",
    goal.value === "orp" && target.value ? `${target.value} recherches par mois` : "",
  ].filter(Boolean),
);
</script>

<template>
  <section
    v-if="loaded"
    class="welcome"
    data-test="welcome"
  >
    <header class="welcome-top">
      <button
        v-if="index > 0 && step !== 'ready'"
        type="button"
        class="welcome-back"
        aria-label="Revenir à la question précédente"
        data-test="welcome-back"
        @click="go(index - 1)"
      >
        ←
      </button>
      <span
        v-else
        class="welcome-back"
      />
      <div
        class="welcome-progress"
        role="progressbar"
        :aria-valuenow="progress"
        aria-valuemin="0"
        aria-valuemax="100"
      >
        <span :style="{ width: `${progress}%` }" />
      </div>
      <button
        v-if="step !== 'ready'"
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
    >
      <div
        :key="step"
        class="welcome-screen"
        :data-test="`welcome-${step}`"
      >
        <Illustration
          :name="ART[step]"
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
          <label class="welcome-row">
            <span>Preuves à remettre avant le</span>
            <input
              v-model.number="dueDay"
              class="welcome-input short"
              type="number"
              min="2"
              max="28"
            >
            <span>du mois suivant</span>
          </label>
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
            <AppIcon name="file" />
            <span>
              <strong>{{ cvName ? `✓ ${cvName}` : uploading ? "Dépôt…" : "Déposer mon CV" }}</strong>
              <small>PDF ou Word</small>
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

        <template v-else>
          <h1>C'est prêt !</h1>
          <ul
            v-if="recap.length"
            class="welcome-recap"
            data-test="welcome-recap"
          >
            <li
              v-for="line in recap"
              :key="line"
            >
              <AppIcon name="check" /> {{ line }}
            </li>
          </ul>
          <p class="welcome-hint">
            Prochaine étape : créer tes alertes sur les sites d'emploi. La recherche est déjà remplie.
          </p>
        </template>
      </div>
    </Transition>

    <footer class="welcome-actions">
      <template v-if="step === 'ready'">
        <button
          type="button"
          class="primary welcome-continue"
          data-test="welcome-alerts"
          @click="finish('/candidatures/alertes')"
        >
          Créer mes alertes
        </button>
        <button
          type="button"
          class="link"
          data-test="welcome-today"
          @click="finish('/aujourdhui')"
        >
          Aller à Aujourd'hui
        </button>
      </template>
      <template v-else-if="step !== 'goal' && step !== 'rate'">
        <button
          type="button"
          class="primary welcome-continue"
          :disabled="(step === 'trade' && !trade.trim()) || (step === 'cv' && !cvName) || (step === 'phone' && phone === null)"
          data-test="welcome-continue"
          @click="step === 'trade' ? confirmTrade() : step === 'places' ? confirmPlaces() : step === 'orp' ? confirmOrp() : go(index + 1)"
        >
          Continuer
        </button>
        <button
          type="button"
          class="link"
          data-test="welcome-skip"
          @click="go(index + 1)"
        >
          Passer
        </button>
      </template>
      <button
        v-else
        type="button"
        class="link"
        data-test="welcome-skip"
        @click="go(index + 1)"
      >
        Passer
      </button>
    </footer>
  </section>
</template>
