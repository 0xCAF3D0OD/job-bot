<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch, watchEffect } from "vue";
import { useRoute, useRouter } from "vue-router";

import { api, type Practice, type PracticeDefaults } from "../api/client";
import AiWriting from "../components/AiWriting.vue";
import AppIcon from "../components/AppIcon.vue";
import InlineConfirm from "../components/InlineConfirm.vue";
import MoreMenu, { type MoreMenuItem } from "../components/MoreMenu.vue";
import { useFocusMode } from "../composables/useFocusMode";
import { usePhone } from "../composables/usePhone";
import { usePlan } from "../composables/usePlan";
import { offerUndo } from "../composables/useUndo";
import { meetingChip } from "../dates";
import { FLAGS } from "../flags";

// S'entraîner pour l'entretien (docs/75 ; récapitulatif du 11 novembre, PR 42 ; maquettes Entrainement et
// EntrainementOrdinateur) : une page, plus une fenêtre. Les réglages (avec qui, le ton, la langue), puis une question
// à la fois en mode concentration (sans la navigation), puis le retour. Un entraînement n'est jamais compté comme
// un vrai entretien.
const route = useRoute();
const router = useRouter();
const { phone } = usePhone();
const { focus } = useFocusMode();
const { refresh: refreshPlan } = usePlan();

type Kind = Practice["kind"];
type Tone = Practice["tone"];
type Language = Practice["language"];
// La phrase d'aide dit ce que ce recruteur demande.
const KINDS: { value: Kind; label: string; help: string }[] = [
  { value: "rh", label: "RH", help: "Questions sur ton parcours, ta motivation et tes attentes." },
  { value: "manager", label: "Manager", help: "Questions sur ta façon de travailler, seul et en équipe." },
  { value: "technique", label: "Technique", help: "Questions sur tes projets et tes outils." },
];
const TONES: { value: Tone; label: string }[] = [
  { value: "bienveillant", label: "Bienveillant" },
  { value: "exigeant", label: "Exigeant" },
];
const LANGUAGES: { value: Language; label: string }[] = [
  { value: "fr", label: "Français" },
  { value: "en", label: "Anglais" },
  { value: "de", label: "Allemand" },
];
const LEVELS: Record<string, string> = {
  solide: "Solide",
  a_preciser: "À préciser",
  a_retravailler: "À retravailler",
};
const RENDEZ_VOUS = "/candidatures/rendez-vous-orp";

const applicationId = computed(() => Number(route.params.candidatureId) || null);
const practiceId = computed(() => Number(route.query.seance) || null);

const defaults = ref<PracticeDefaults | null>(null);
const kind = ref<Kind>("rh");
const tone = ref<Tone>("bienveillant");
const language = ref<Language>("fr");
const practice = ref<Practice | null>(null);
const loaded = ref(false);
const draft = ref("");
const busy = ref<"" | "start" | "turn" | "feedback">("");
const message = ref("");
const added = ref<string[]>([]);
const leaving = ref(false);
const field = ref<HTMLTextAreaElement | null>(null);

const finished = computed(() => practice.value?.status === "termine");
const answered = computed(() => (practice.value?.turns ?? []).some((t) => t.role === "candidat" && !t.skipped));
const lastIsRecruiter = computed(() => practice.value?.turns.at(-1)?.role === "recruteur");
// La question à l'écran : la dernière parole du recruteur (une relance la remplace).
const current = computed(() => (practice.value?.turns ?? []).filter((t) => t.role === "recruteur").at(-1) ?? null);
const number = computed(() => Math.max(practice.value?.question ?? 1, 1));
const company = computed(() => practice.value?.company ?? defaults.value?.company ?? "");
// « Internship, Software Engineer · Lombard Odier · jeudi 19 nov., 14 h »
const subtitle = computed(() => {
  const d = defaults.value;
  if (!d?.company) return "Un entretien type, sans candidature.";
  const when = d.interview_at ? meetingChip(d.interview_at).replace(/^./, (c) => c.toLowerCase()) : "";
  return [d.job_title, d.company, when].filter(Boolean).join(" · ");
});
const kindHelp = computed(() => KINDS.find((k) => k.value === kind.value)?.help ?? "");
function languageName(value: Language): string {
  return (LANGUAGES.find((l) => l.value === value)?.label ?? "").toLowerCase();
}
// « Technique · anglais »
const meta = computed(() =>
  practice.value ? `${KINDS.find((k) => k.value === practice.value!.kind)?.label ?? ""} · ${languageName(practice.value.language)}` : "",
);
const words = computed(() => {
  const count = draft.value.trim() ? draft.value.trim().split(/\s+/).length : 0;
  return `${count} ${count > 1 ? "mots" : "mot"}`;
});
const moreItems = computed<MoreMenuItem[]>(() => {
  if (!practice.value) return [];
  const items: MoreMenuItem[] = [];
  if (!finished.value && answered.value && !busy.value) {
    items.push({ label: "Terminer et voir le retour", test: "practice-finish", run: () => void finish() });
  }
  items.push({ label: "Supprimer cet entraînement", test: "practice-delete", danger: true, run: () => void remove() });
  return items;
});

// Sur téléphone, toute la page est sans navigation (le bouton est fixé en bas) ; sur ordinateur, dès la première question.
watchEffect(() => {
  focus.value = phone.value || !!practice.value;
});
onUnmounted(() => {
  focus.value = false;
});

function detail(error: unknown): string {
  const text = (error as { detail?: unknown } | undefined)?.detail;
  if (typeof text !== "string") return "Impossible pour l’instant, réessaie.";
  // Une phrase entière (la limite de la formule, docs/125) se dit telle quelle.
  return /[.!?]$/.test(text) ? text : `Impossible : ${text}.`;
}

async function focusAnswer(): Promise<void> {
  await nextTick();
  field.value?.focus();
}

async function run(wait: "start" | "turn" | "feedback", call: () => Promise<{ data?: Practice; error?: unknown }>): Promise<void> {
  busy.value = wait;
  message.value = "";
  try {
    const { data, error } = await call();
    if (data) practice.value = data;
    else message.value = detail(error);
  } finally {
    busy.value = "";
    void focusAnswer();
  }
}

async function start(): Promise<void> {
  await run("start", () =>
    api.POST("/api/interview-practices", {
      body: { application_id: applicationId.value, kind: kind.value, tone: tone.value, language: language.value },
    }),
  );
  // L'adresse garde la séance : recharger la page la reprend. « Retour » mène toujours d'où l'on vient.
  if (practice.value) {
    void refreshPlan();
    await router.replace({ params: route.params, query: { ...route.query, seance: String(practice.value.id) } });
  }
}

async function send(): Promise<void> {
  const text = draft.value.trim();
  if (!practice.value || busy.value) return;
  // Le bouton reste plein, comme sur la maquette : une réponse vide se dit.
  if (!text) {
    message.value = "Écris ta réponse, ou passe la question.";
    void focusAnswer();
    return;
  }
  const id = practice.value.id;
  practice.value = {
    ...practice.value,
    turns: [...practice.value.turns, { role: "candidat", text, question: practice.value.question, relance: false, skipped: false }],
  };
  draft.value = "";
  const last = practice.value.question >= practice.value.questions;
  await run(last ? "feedback" : "turn", () =>
    api.POST("/api/interview-practices/{practice_id}/answer", { params: { path: { practice_id: id } }, body: { text } }),
  );
  if (message.value) draft.value = text;
}

function skip(): Promise<void> {
  const id = practice.value!.id;
  const last = practice.value!.question >= practice.value!.questions;
  return run(last ? "feedback" : "turn", () => api.POST("/api/interview-practices/{practice_id}/skip", { params: { path: { practice_id: id } } }));
}

function retry(): Promise<void> {
  const id = practice.value!.id;
  // Après la dernière question, « Réessayer » redemande le retour (docs/76 §3).
  const last = practice.value!.question >= practice.value!.questions;
  return run(last ? "feedback" : "turn", () => api.POST("/api/interview-practices/{practice_id}/retry", { params: { path: { practice_id: id } } }));
}

function finish(): Promise<void> {
  const id = practice.value!.id;
  return run("feedback", () => api.POST("/api/interview-practices/{practice_id}/finish", { params: { path: { practice_id: id } } }));
}

// D'où l'on vient ; sinon les Rendez-vous (ou le Bilan pour un entretien type).
function leave(): void {
  if (window.history.state?.back) router.back();
  else void router.push(applicationId.value ? RENDEZ_VOUS : "/bilan");
}
// « Quitter » : une réponse en cours se confirme, pour ne pas la perdre.
function quit(): void {
  if (draft.value.trim() && !finished.value) leaving.value = true;
  else leave();
}

// Quitté tout de suite, supprimé au bout de 6 s, « Annuler » d'ici là (docs/108 §1).
async function remove(): Promise<void> {
  const id = practice.value?.id;
  if (!id) return;
  leave();
  await offerUndo({
    message: "Entraînement supprimé",
    commit: async (keepalive) => {
      const { error } = await api.DELETE("/api/interview-practices/{practice_id}", { params: { path: { practice_id: id } }, keepalive });
      if (error !== undefined) return false;
    },
    restore: () => undefined,
  });
}

async function addToPrepare(text: string): Promise<void> {
  const { data } = await api.POST("/api/interviews/insights/to-prepare", { body: { text, done: false } });
  if (data) added.value = [...added.value, text];
}

// Entrée envoie sur ordinateur ; sur téléphone, elle va à la ligne (on répond « comme à l'oral », souvent en dictant).
function onKey(event: KeyboardEvent): void {
  if (!phone.value && event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    void send();
  }
}

function answerOf(question: number): string {
  const turns = (practice.value?.turns ?? []).filter((t) => t.role === "candidat" && t.question === question);
  return turns.map((t) => (t.skipped ? "(question passée)" : t.text)).join("\n\n");
}
function questionOf(question: number): string {
  return (practice.value?.turns ?? []).find((t) => t.role === "recruteur" && t.question === question && !t.relance)?.text ?? "";
}

async function load(): Promise<void> {
  if (practiceId.value) {
    if (practice.value?.id !== practiceId.value) {
      practice.value =
        (await api.GET("/api/interview-practices/{practice_id}", { params: { path: { practice_id: practiceId.value } } })).data ?? null;
    }
    loaded.value = true;
    if (practice.value) {
      void focusAnswer();
      return;
    }
  }
  const query = applicationId.value ? { application_id: applicationId.value } : {};
  defaults.value = (await api.GET("/api/interview-practices/defaults", { params: { query } })).data ?? null;
  if (defaults.value) {
    kind.value = defaults.value.kind;
    language.value = defaults.value.language;
  }
  loaded.value = true;
}
onMounted(load);
// Le bouton Retour du navigateur, d'une séance vers les réglages ou l'inverse.
watch(practiceId, (id) => {
  if (id === (practice.value?.id ?? null)) return;
  practice.value = null;
  void load();
});
</script>

<template>
  <!-- 1. Les réglages -->
  <section
    v-if="!practice"
    class="pv pv-setup"
    data-test="practice"
  >
    <button
      type="button"
      class="pv-back"
      data-test="practice-back"
      @click="leave"
    >
      <AppIcon name="chevron-left" />{{ applicationId ? "Rendez-vous" : "Retour" }}
    </button>
    <h1>S’entraîner pour l’entretien</h1>
    <p
      v-if="loaded"
      class="pv-sub"
      data-test="practice-subtitle"
    >
      {{ subtitle }}
    </p>
    <p
      v-if="defaults && !defaults.can_practice"
      class="notice"
    >
      L’entraînement demande l’IA, qui n’est pas configurée sur cette installation.
    </p>
    <template v-else>
      <div class="pv-groups">
        <fieldset>
          <legend>Avec qui ?</legend>
          <div
            class="pv-choices"
            role="radiogroup"
            aria-label="Avec qui ?"
          >
            <button
              v-for="option in KINDS"
              :key="option.value"
              type="button"
              role="radio"
              :aria-checked="kind === option.value"
              :data-test="`practice-kind-${option.value}`"
              @click="kind = option.value"
            >
              <AppIcon
                v-if="kind === option.value"
                name="tick"
              />{{ option.label }}
            </button>
          </div>
          <p
            class="pv-help"
            data-test="practice-kind-help"
          >
            {{ kindHelp }}
          </p>
        </fieldset>
        <fieldset>
          <legend>Ton du recruteur</legend>
          <div
            class="pv-choices"
            role="radiogroup"
            aria-label="Ton du recruteur"
          >
            <button
              v-for="option in TONES"
              :key="option.value"
              type="button"
              role="radio"
              :aria-checked="tone === option.value"
              :data-test="`practice-tone-${option.value}`"
              @click="tone = option.value"
            >
              <AppIcon
                v-if="tone === option.value"
                name="tick"
              />{{ option.label }}
            </button>
          </div>
        </fieldset>
        <fieldset>
          <legend>Langue</legend>
          <div
            class="pv-choices"
            role="radiogroup"
            aria-label="Langue"
          >
            <button
              v-for="option in LANGUAGES"
              :key="option.value"
              type="button"
              role="radio"
              :aria-checked="language === option.value"
              :data-test="`practice-language-${option.value}`"
              @click="language = option.value"
            >
              <AppIcon
                v-if="language === option.value"
                name="tick"
              />{{ option.label }}
            </button>
          </div>
          <p
            v-if="defaults?.language_from_offer"
            class="pv-help"
            data-test="practice-language-note"
          >
            L’annonce est en {{ languageName(defaults.language) }}.
          </p>
        </fieldset>
      </div>
      <p class="pv-facts">
        5 questions · environ 10 minutes · tu peux en passer une.
      </p>
      <p
        v-if="message"
        class="notice error"
        role="alert"
      >
        {{ message }}
      </p>
      <div class="pv-start">
        <button
          type="button"
          class="primary pv-main"
          :disabled="!!busy || !defaults"
          data-test="practice-start"
          @click="start"
        >
          {{ busy === "start" ? "Le recruteur arrive…" : "Commencer l’entraînement" }}
        </button>
      </div>
    </template>
  </section>

  <!-- 2. La question, puis 3. le retour : mode concentration -->
  <section
    v-else
    :class="['pv', 'pv-run', { 'pv-done': finished }]"
    data-test="practice"
  >
    <header class="pv-bar">
      <button
        type="button"
        class="pv-quit"
        data-test="practice-quit"
        @click="quit"
      >
        <AppIcon name="close" />Quitter
      </button>
      <div class="pv-progress">
        <template v-if="!finished">
          <span data-test="practice-progress">Question {{ number }} sur {{ practice.questions }}</span>
          <div
            class="pv-segments"
            role="progressbar"
            :aria-valuenow="number"
            aria-valuemin="0"
            :aria-valuemax="practice.questions"
            :aria-label="`Question ${number} sur ${practice.questions}`"
          >
            <span
              v-for="n in practice.questions"
              :key="n"
              :class="{ on: n <= number }"
            />
          </div>
        </template>
        <span
          v-else
          data-test="practice-progress"
        >Le retour</span>
      </div>
      <div class="pv-meta">
        <span data-test="practice-meta">{{ meta }}</span>
        <MoreMenu
          v-if="moreItems.length"
          :items="moreItems"
          label="Actions sur l’entraînement"
          test-id="practice-more"
        />
      </div>
    </header>

    <div class="pv-column">
      <InlineConfirm
        v-if="leaving"
        message="Quitter l’entraînement ? Ta réponse en cours ne sera pas envoyée."
        confirm-label="Quitter"
        cancel-label="Rester"
        @confirm="leave"
        @cancel="leaving = false"
      />

      <template v-if="!finished">
        <p class="pv-who">
          <span aria-hidden="true">R</span>Le recruteur<template v-if="company">
            · {{ company }}
          </template>
        </p>
        <p
          v-if="current"
          class="pv-question"
          :lang="practice.language"
          aria-live="polite"
          data-test="practice-question-text"
        >
          {{ current.text }}
        </p>
        <details
          v-if="current?.tip"
          class="pv-tip"
          open
          data-test="practice-tip"
        >
          <summary>Conseil<AppIcon name="chevron-up" /></summary>
          <p>{{ current.tip }}</p>
        </details>

        <p
          v-if="busy === 'turn'"
          class="pv-thinking"
          role="status"
        >
          Le recruteur réfléchit…
        </p>
        <AiWriting
          v-if="busy === 'feedback'"
          kind="feedback"
        />
        <p
          v-if="message"
          class="notice error"
          role="alert"
        >
          {{ message }}
        </p>
        <div
          v-if="practice.waiting && !busy"
          class="pv-actions"
        >
          <button
            type="button"
            class="secondary"
            data-test="practice-retry"
            @click="retry"
          >
            <span class="with-icon"><AppIcon name="refresh" />Réessayer</span>
          </button>
        </div>
        <form
          v-else-if="lastIsRecruiter && !busy"
          class="pv-answer"
          @submit.prevent="send"
        >
          <div class="pv-field">
            <textarea
              id="practice-answer"
              ref="field"
              v-model="draft"
              maxlength="4000"
              aria-describedby="practice-answer-help"
              data-test="practice-input"
              @keydown="onKey"
              @input="message = ''"
            />
            <label for="practice-answer">Ta réponse</label>
          </div>
          <p class="pv-under">
            <span id="practice-answer-help">{{ phone ? "Réponds comme à l’oral" : "Entrée pour envoyer · Maj+Entrée pour aller à la ligne" }}</span>
            <span data-test="practice-words">{{ words }}</span>
          </p>
          <div class="pv-actions">
            <button
              type="button"
              class="pv-skip"
              data-test="practice-skip"
              @click="skip"
            >
              Passer<span class="pv-wide"> la question</span>
            </button>
            <button
              type="submit"
              class="primary pv-main"
              data-test="practice-send"
            >
              Envoyer la réponse
            </button>
          </div>
        </form>
      </template>

      <div
        v-else-if="practice.feedback"
        class="practice-feedback"
        data-test="practice-feedback"
      >
        <section class="practice-summary">
          <div>
            <h2>Points forts</h2>
            <ul>
              <li
                v-for="item in practice.feedback.strengths"
                :key="item"
              >
                {{ item }}
              </li>
            </ul>
          </div>
          <div>
            <h2>À travailler</h2>
            <ul class="practice-work">
              <li
                v-for="item in practice.feedback.work_on"
                :key="item"
              >
                <span>{{ item }}</span>
                <span
                  v-if="added.includes(item)"
                  class="hint with-icon"
                  data-test="practice-added"
                >Ajouté à « À préparer »<AppIcon name="done" /></span>
                <button
                  v-else
                  type="button"
                  class="link"
                  data-test="practice-add-prepare"
                  @click="addToPrepare(item)"
                >
                  Ajouter à « À préparer »
                </button>
              </li>
            </ul>
          </div>
        </section>
        <section
          v-for="item in practice.feedback.questions"
          :key="item.question"
          class="practice-question"
          data-test="practice-question"
        >
          <p class="practice-question-head">
            <strong :lang="practice.language">{{ item.question }}. {{ questionOf(item.question) }}</strong>
            <span
              :class="['practice-level', item.level]"
              data-test="practice-level"
            >{{ LEVELS[item.level] }}</span>
          </p>
          <p v-if="item.good">
            <span class="muted">Ce qui marche :</span> {{ item.good }}
          </p>
          <p v-if="item.missing">
            <span class="muted">Ce qui manque :</span> {{ item.missing }}
          </p>
          <details
            v-if="item.better"
            class="practice-better"
          >
            <summary>Une meilleure réponse, tirée de ton profil</summary>
            <p>{{ item.better }}</p>
          </details>
          <details class="practice-mine">
            <summary>Ta réponse</summary>
            <p>{{ answerOf(item.question) }}</p>
          </details>
        </section>
        <!-- L'emplacement du lien vers Get'emAll, éteint tant que le drapeau VITE_GETEMALL_LINK ne vaut pas 1. -->
        <p
          v-if="FLAGS.getemallLink"
          class="pv-getemall"
          data-test="practice-getemall"
        >
          <a
            href="https://getthemall.ch"
            target="_blank"
            rel="noopener"
          >Continuer à l’oral sur Get’emAll<AppIcon name="external" /><span class="visually-hidden"> (nouvel onglet)</span></a>
        </p>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* Les valeurs des maquettes Entrainement et EntrainementOrdinateur (récapitulatif du 11 novembre, PR 42), écrites
   avec les échelles ; les tailles hors échelle sont nommées ici. */
.pv {
  --pv-setup: 640px; --pv-col: 720px; --pv-bar: 76px; --pv-h: 48px; --pv-main: 52px; --pv-radius: 12px;
  --pv-15: 0.9375rem; --pv-seg: 6px; --pv-area: 168px; --pv-28: 1.75rem; --pv-avatar: 40px; --pv-track: 400px; --pv-side: 200px;
  --pv-h1: 2rem; --pv-h1-lh: 2.5rem; --pv-gutter: 5rem; --pv-q: 1.5rem; --pv-q-lh: 2.125rem; --pv-22: 1.375rem; --pv-pad-x: 14.5px; --pv-pad-x-focus: 14px; --pv-half: 0.5px; --pv-36: 2.25rem;
  color: var(--text);
}
.pv-setup { width: min(var(--pv-setup), 100%); margin: 0 auto; padding: var(--space-6) 0 var(--space-12); }
.pv-back {
  display: inline-flex; align-items: center; gap: var(--space-1); min-height: 2.75rem; margin-left: calc(-1 * var(--space-2)); padding: 0 var(--space-2) 0 0;
  border: 0; background: none; font: inherit; font-size: var(--pv-15); font-weight: var(--weight-bold); color: var(--primary-text); cursor: pointer;
}
.pv-back :deep(svg) { width: var(--space-5); height: var(--space-5); }
.pv-setup h1 { margin: var(--space-2) 0 0; font-size: var(--pv-h1); line-height: var(--pv-h1-lh); font-weight: var(--weight-heavy); }
.pv-sub { margin: var(--space-2) 0 0; font-size: var(--font-body); line-height: var(--space-6); color: var(--text-secondary); }
.pv-groups { display: flex; flex-direction: column; gap: var(--pv-28); margin-top: var(--space-8); }
.pv-groups fieldset { margin: 0; padding: 0; border: 0; min-width: 0; }
.pv-groups legend { padding: 0; margin-bottom: var(--space-2); font-size: var(--pv-15); font-weight: var(--weight-bold); }
.pv-choices { display: flex; gap: var(--space-2); }
/* Le choix : une coche et une bordure plus épaisse, pas seulement la couleur (WCAG 1.4.1). */
.pv-choices button {
  flex: 1; min-width: 0; height: var(--pv-h); display: flex; align-items: center; justify-content: center; gap: var(--space-2);
  border: 1.5px solid var(--card-line); border-radius: var(--space-6); background: var(--surface); color: var(--text);
  font: inherit; font-size: var(--font-body); font-weight: var(--weight-semibold); cursor: pointer; padding: 0 var(--space-2);
}
.pv-choices button[aria-checked="true"] { border: 2px solid var(--primary-graphic); background: var(--primary-soft); color: var(--primary-text); font-weight: var(--weight-bold); }
.pv-choices button :deep(svg) { flex: none; width: 1.125rem; height: 1.125rem; }
.pv-help { margin: var(--space-2) 0 0; font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.pv-facts { margin: var(--space-8) 0 0; font-size: var(--pv-15); color: var(--text-lead); }
.pv-start { margin-top: var(--space-4); }
.pv-main { height: var(--pv-main); padding: 0 var(--pv-28); border-radius: var(--pv-main); font-size: var(--font-body); font-weight: var(--weight-bold); }
.pv .notice { margin: var(--space-4) 0 0; }

.pv-run { display: flex; flex-direction: column; min-height: 100dvh; }
.pv-bar { flex: none; display: flex; align-items: center; gap: var(--space-6); height: var(--pv-bar); padding: 0 var(--pv-gutter); border-bottom: 1px solid var(--surface-muted); }
.pv-quit {
  flex: none; display: flex; align-items: center; gap: var(--space-2); width: var(--pv-side); height: 2.75rem; padding: 0 var(--space-4) 0 var(--space-2);
  border: 0; background: none; font: inherit; font-size: var(--pv-15); font-weight: var(--weight-bold); color: var(--text); cursor: pointer;
}
.pv-quit :deep(svg) { width: 1.375rem; height: 1.375rem; }
.pv-progress { flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: center; font-size: var(--pv-15); font-weight: var(--weight-bold); }
.pv-segments { display: flex; gap: var(--space-1); width: min(var(--pv-track), 100%); margin-top: var(--space-2); }
.pv-segments span { flex: 1; height: var(--pv-seg); border-radius: var(--pv-seg); background: var(--line-strong); }
.pv-segments span.on { background: var(--primary-graphic); }
.pv-meta { flex: none; width: var(--pv-side); display: flex; align-items: center; justify-content: flex-end; gap: var(--space-2); font-size: var(--font-small); color: var(--text-secondary); }
.pv-column { width: min(var(--pv-col), 100%); margin: 0 auto; padding: var(--space-8) 0 var(--space-12); box-sizing: border-box; }
.pv-column > .inline-confirm { margin-bottom: var(--space-6); }
.pv-who { display: flex; align-items: center; gap: var(--space-3); margin: var(--space-2) 0 0; font-size: var(--font-small); font-weight: var(--weight-bold); color: var(--text-secondary); }
.pv-who span { flex: none; width: var(--pv-avatar); height: var(--pv-avatar); border-radius: 50%; display: flex; align-items: center; justify-content: center; background: var(--primary-soft); color: var(--primary-text); font-size: var(--font-body); font-weight: var(--weight-heavy); }
.pv-question { margin: var(--space-4) 0 0; font-size: var(--pv-q); line-height: var(--pv-q-lh); font-weight: var(--weight-bold); white-space: pre-wrap; }
.pv-tip { margin-top: var(--space-5); border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.pv-tip summary { min-height: var(--pv-h); display: flex; align-items: center; gap: var(--space-2); font-size: var(--pv-15); font-weight: var(--weight-bold); color: var(--primary-text); cursor: pointer; list-style: none; }
.pv-tip summary::-webkit-details-marker { display: none; }
.pv-tip summary :deep(svg) { width: var(--space-4); height: var(--space-4); transform: rotate(180deg); transition: transform var(--t-state); }
.pv-tip[open] summary :deep(svg) { transform: none; }
.pv-tip p { margin: 0 0 var(--space-4); font-size: var(--pv-15); line-height: var(--pv-22); color: var(--text-lead); }
.pv-thinking { margin: var(--space-8) 0 0; color: var(--text-secondary); }
.pv-answer { margin-top: var(--space-8); }
.pv-field { position: relative; }
.pv-field textarea {
  display: block; width: 100%; height: var(--pv-area); box-sizing: border-box; padding: var(--space-4) var(--pv-pad-x); resize: vertical;
  border: 1.5px solid var(--field-border); border-radius: var(--pv-radius); background: var(--surface); color: var(--text);
  font: inherit; font-size: var(--font-body); line-height: var(--space-6);
}
.pv-field textarea:focus { outline: none; border: 2px solid var(--primary-graphic); padding: calc(var(--space-4) - var(--pv-half)) var(--pv-pad-x-focus); }
.pv-field label {
  position: absolute; left: var(--space-3); top: calc(-1 * var(--space-2)); padding: 0 var(--space-1);
  background: linear-gradient(to bottom, var(--bg) 50%, var(--surface) 50%);
  font-size: var(--font-caption); line-height: var(--space-4); font-weight: var(--weight-bold); color: var(--text-lead);
}
.pv-field:focus-within label { color: var(--primary-text); }
.pv-under { display: flex; justify-content: space-between; gap: var(--space-3); margin: var(--space-2) 0 0; font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.pv-under span:last-child { flex: none; }
.pv-actions { display: flex; justify-content: space-between; align-items: center; margin-top: var(--space-6); }
.pv-skip { height: var(--pv-h); padding: 0 var(--space-1); border: 0; background: none; font: inherit; font-size: var(--pv-15); font-weight: var(--weight-bold); color: var(--primary-text); cursor: pointer; }
.pv-getemall { margin: var(--space-6) 0 0; }
.practice-feedback h2 { margin: 0 0 var(--space-2); font-size: var(--font-small); }
@media (prefers-reduced-motion: reduce) { .pv-tip summary :deep(svg) { transition: none; } }

@media (max-width: 820px) {
  .pv { --pv-area: 148px; }
  .pv-setup { padding: var(--space-2) var(--space-5) calc(var(--pv-main) + var(--space-12)); box-sizing: border-box; }
  .pv-setup h1 { font-size: var(--pv-28); line-height: var(--pv-36); }
  .pv-sub { font-size: var(--pv-15); line-height: var(--pv-22); }
  .pv-groups { gap: var(--space-5); margin-top: var(--space-6); }
  .pv-choices button { font-size: var(--pv-15); }
  .pv-facts { margin-top: var(--space-6); }
  /* Le bouton, fixé en bas de l'écran. */
  .pv-start, .pv-answer .pv-actions {
    position: fixed; left: 0; right: 0; bottom: 0; z-index: 5; margin: 0; padding: var(--space-3) var(--space-5) calc(var(--space-5) + env(safe-area-inset-bottom));
    background: var(--bg); border-top: 1px solid var(--line);
  }
  .pv-start .pv-main { width: 100%; }
  .pv-bar { height: auto; flex-wrap: wrap; gap: 0; padding: var(--space-2) var(--space-5) var(--space-3); }
  .pv-quit { width: auto; order: 1; margin-left: calc(-1 * var(--space-2)); }
  .pv-meta { width: auto; order: 2; margin-left: auto; }
  .pv-progress { order: 3; flex: none; width: 100%; align-items: flex-start; }
  .pv-segments { width: 100%; }
  .pv-column { padding: var(--space-4) var(--space-5) calc(var(--pv-main) + var(--space-12)); }
  .pv-question { font-size: var(--space-5); line-height: var(--pv-28); }
  .pv-wide { display: none; }
}
</style>
