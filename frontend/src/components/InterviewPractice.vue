<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";

import { api, type Application, type Practice, type PracticeDefaults } from "../api/client";
import AiWriting from "./AiWriting.vue";
import AppIcon from "./AppIcon.vue";
import IconButton from "./IconButton.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";

// S'entraîner à l'entretien (docs/75) : trois choix, cinq questions du recruteur simulé, une
// relance au plus, puis le retour. Un entraînement n'est jamais compté comme un vrai entretien.
const props = defineProps<{ application?: Application | null; practiceId?: number | null }>();
const emit = defineEmits<{ close: []; changed: [] }>();

type Kind = Practice["kind"];
type Tone = Practice["tone"];
type Language = Practice["language"];
const KINDS: { value: Kind; label: string }[] = [
  { value: "rh", label: "RH" },
  { value: "manager", label: "Manager" },
  { value: "technique", label: "Technique" },
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

const defaults = ref<PracticeDefaults | null>(null);
const kind = ref<Kind>("rh");
const tone = ref<Tone>("bienveillant");
const language = ref<Language>("fr");
const practice = ref<Practice | null>(null);
const draft = ref("");
const busy = ref<"" | "start" | "turn" | "feedback">("");
const message = ref("");
const added = ref<string[]>([]);
const thread = ref<HTMLElement | null>(null);
const dialog = ref<HTMLElement | null>(null);
// Le focus revient où il était à la fermeture (docs/76 §4).
let opener: HTMLElement | null = null;
// Seule la dernière parole du recruteur est annoncée, pas ta propre réponse.
const announced = computed(() => {
  const last = practice.value?.turns.at(-1);
  return last?.role === "recruteur" ? last.text : "";
});
const field = ref<HTMLTextAreaElement | null>(null);

const title = computed(() => practice.value?.company ?? props.application?.company ?? "Entretien type");
const finished = computed(() => practice.value?.status === "termine");
const answered = computed(() =>
  (practice.value?.turns ?? []).some((t) => t.role === "candidat" && !t.skipped),
);
const lastIsRecruiter = computed(() => practice.value?.turns.at(-1)?.role === "recruteur");
const headItems = computed<MoreMenuItem[]>(() =>
  practice.value
    ? [{ label: "Supprimer cet entraînement", test: "practice-delete", danger: true, run: () => void remove() }]
    : [],
);

function detail(error: unknown): string {
  const text = (error as { detail?: unknown } | undefined)?.detail;
  return typeof text === "string" ? `Impossible : ${text}.` : "Impossible pour l'instant, réessaie.";
}

async function scrollDown(): Promise<void> {
  await nextTick();
  const reduced = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  thread.value?.scrollTo?.({ top: thread.value.scrollHeight, behavior: reduced ? "auto" : "smooth" });
  field.value?.focus();
}

async function run(kindOfWait: "start" | "turn" | "feedback", call: () => Promise<{ data?: Practice; error?: unknown }>): Promise<void> {
  busy.value = kindOfWait;
  message.value = "";
  try {
    const { data, error } = await call();
    if (data) {
      practice.value = data;
      emit("changed");
    } else message.value = detail(error);
  } finally {
    busy.value = "";
    void scrollDown();
  }
}

function start(): Promise<void> {
  return run("start", () =>
    api.POST("/api/interview-practices", {
      body: {
        application_id: props.application?.id ?? null,
        kind: kind.value,
        tone: tone.value,
        language: language.value,
      },
    }),
  );
}

async function send(): Promise<void> {
  const text = draft.value.trim();
  if (!text || !practice.value || busy.value) return;
  const id = practice.value.id;
  // La réponse s'affiche tout de suite ; le recruteur suit.
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
  return run(last ? "feedback" : "turn", () =>
    api.POST("/api/interview-practices/{practice_id}/skip", { params: { path: { practice_id: id } } }),
  );
}

function retry(): Promise<void> {
  const id = practice.value!.id;
  // Après la dernière question, « Réessayer » redemande le retour (docs/76 §3).
  const last = practice.value!.question >= practice.value!.questions;
  return run(last ? "feedback" : "turn", () => api.POST("/api/interview-practices/{practice_id}/retry", { params: { path: { practice_id: id } } }));
}

function finish(): Promise<void> {
  const id = practice.value!.id;
  return run("feedback", () =>
    api.POST("/api/interview-practices/{practice_id}/finish", { params: { path: { practice_id: id } } }),
  );
}

async function remove(): Promise<void> {
  if (!practice.value || !window.confirm("Supprimer cet entraînement et son retour ?")) return;
  await api.DELETE("/api/interview-practices/{practice_id}", { params: { path: { practice_id: practice.value.id } } });
  emit("changed");
  emit("close");
}

async function addToPrepare(text: string): Promise<void> {
  const { data } = await api.POST("/api/interviews/insights/to-prepare", { body: { text, done: false } });
  if (data) added.value = [...added.value, text];
}

function onKey(event: KeyboardEvent): void {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
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

watch(
  () => practice.value?.turns.length,
  () => void scrollDown(),
);

// Le focus reste dans la fenêtre ; Échap la ferme d'où qu'il soit.
function focusables(): HTMLElement[] {
  return [
    ...(dialog.value?.querySelectorAll<HTMLElement>(
      "button:not(:disabled), a[href], textarea, summary, [tabindex]:not([tabindex='-1'])",
    ) ?? []),
  ];
}
function onDocumentKey(event: KeyboardEvent): void {
  if (event.key === "Escape" && !event.defaultPrevented) {
    emit("close");
  } else if (event.key === "Tab") {
    const list = focusables();
    const first = list[0];
    const last = list.at(-1);
    if (!first || !last) return;
    const inside = dialog.value?.contains(document.activeElement);
    if (event.shiftKey && (document.activeElement === first || !inside)) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && (document.activeElement === last || !inside)) {
      event.preventDefault();
      first.focus();
    }
  }
}
// À l'ouverture : « Commencer », ou le champ de réponse, sinon la première action.
async function focusFirst(): Promise<void> {
  await nextTick();
  (dialog.value?.querySelector<HTMLElement>("[data-test=practice-start]:not(:disabled), textarea") ?? focusables()[0])?.focus();
}
onUnmounted(() => {
  document.removeEventListener("keydown", onDocumentKey);
  opener?.focus?.();
});

onMounted(async () => {
  opener = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  document.addEventListener("keydown", onDocumentKey);
  if (props.practiceId) {
    practice.value =
      (await api.GET("/api/interview-practices/{practice_id}", { params: { path: { practice_id: props.practiceId } } })).data ??
      null;
    void scrollDown();
    await focusFirst();
    return;
  }
  const query = props.application ? { application_id: props.application.id } : {};
  defaults.value = (await api.GET("/api/interview-practices/defaults", { params: { query } })).data ?? null;
  if (defaults.value) {
    kind.value = defaults.value.kind;
    language.value = defaults.value.language;
  }
  await focusFirst();
});
</script>

<template>
  <div
    class="overlay practice-overlay"
    @click.self="emit('close')"
  >
    <article
      ref="dialog"
      :class="['practice-screen', { running: practice }]"
      role="dialog"
      aria-modal="true"
      :aria-label="`S'entraîner : ${title}`"
      data-test="practice"
    >
      <p
        class="visually-hidden"
        aria-live="polite"
      >
        {{ announced }}
      </p>
      <header class="practice-head">
        <div>
          <h3>{{ title }}</h3>
          <p class="hint">
            S'entraîner<template v-if="practice && !finished">
              · <span data-test="practice-progress">Question {{ Math.max(practice.question, 1) }} sur {{ practice.questions }}</span>
            </template><template v-else-if="finished">
              · le retour
            </template>
          </p>
        </div>
        <div class="practice-head-actions">
          <button
            v-if="practice && !finished && answered"
            type="button"
            class="link"
            :disabled="!!busy"
            data-test="practice-finish"
            @click="finish"
          >
            Terminer<span class="practice-finish-more"> et voir le retour</span>
          </button>
          <MoreMenu
            v-if="headItems.length"
            :items="headItems"
            label="Actions sur l'entraînement"
            test-id="practice-more"
          />
          <IconButton
            icon="close"
            label="Fermer l'entraînement"
            data-test="practice-close"
            @click="emit('close')"
          />
        </div>
      </header>

      <!-- 1. Les trois choix -->
      <div
        v-if="!practice"
        class="practice-setup"
      >
        <p class="practice-intro">
          L'IA joue le recruteur : 5 questions, puis un retour.
        </p>
        <p
          v-if="defaults && !defaults.can_practice"
          class="notice"
        >
          L'entraînement demande l'IA, qui n'est pas configurée sur cette installation.
        </p>
        <template v-else>
          <fieldset class="practice-choice">
            <legend>Le type d'entretien</legend>
            <div
              class="segmented"
              role="radiogroup"
              aria-label="Le type d'entretien"
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
                {{ option.label }}
              </button>
            </div>
          </fieldset>
          <fieldset class="practice-choice">
            <legend>Le ton du recruteur</legend>
            <div
              class="segmented"
              role="radiogroup"
              aria-label="Le ton du recruteur"
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
                {{ option.label }}
              </button>
            </div>
          </fieldset>
          <fieldset class="practice-choice">
            <legend>La langue</legend>
            <div
              class="segmented"
              role="radiogroup"
              aria-label="La langue"
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
                {{ option.label }}
              </button>
            </div>
          </fieldset>
          <p
            v-if="message"
            class="notice error"
            role="alert"
          >
            {{ message }}
          </p>
          <div class="form-actions">
            <button
              type="button"
              class="primary"
              :disabled="!!busy || !defaults"
              data-test="practice-start"
              @click="start"
            >
              <span class="with-icon"><AppIcon name="ai" />{{ busy === "start" ? "Le recruteur arrive…" : "Commencer" }}</span>
            </button>
          </div>
        </template>
      </div>

      <!-- 2. L'entretien -->
      <template v-else-if="!finished">
        <div
          ref="thread"
          class="practice-thread"
        >
          <p
            v-for="(turn, index) in practice.turns"
            :key="index"
            :class="['practice-line', turn.role, { skipped: turn.skipped }]"
            data-test="practice-turn"
          >
            <!-- Sur une ligne : le texte garde ses retours à la ligne (pre-wrap), pas ceux du modèle. -->
            <span class="visually-hidden">{{ turn.role === "recruteur" ? "Recruteur : " : "Toi : " }}</span>{{ turn.skipped ? "Question passée" : turn.text }}
          </p>
          <p
            v-if="busy === 'turn'"
            class="practice-line recruteur thinking"
            role="status"
          >
            Le recruteur réfléchit…
          </p>
          <AiWriting
            v-if="busy === 'feedback'"
            kind="feedback"
          />
        </div>
        <p
          v-if="message"
          class="notice error"
          role="alert"
        >
          {{ message }}
        </p>
        <div
          v-if="practice.waiting && !busy"
          class="form-actions"
        >
          <button
            type="button"
            class="secondary small"
            data-test="practice-retry"
            @click="retry"
          >
            <span class="with-icon"><AppIcon name="refresh" />Réessayer</span>
          </button>
        </div>
        <form
          v-else-if="lastIsRecruiter && busy !== 'feedback'"
          class="practice-answer"
          @submit.prevent="send"
        >
          <textarea
            ref="field"
            v-model="draft"
            rows="3"
            maxlength="4000"
            placeholder="Ta réponse… (Entrée pour envoyer, Maj+Entrée pour aller à la ligne)"
            aria-label="Ta réponse"
            data-test="practice-input"
            @keydown="onKey"
          />
          <div class="practice-answer-actions">
            <button
              type="button"
              class="link"
              :disabled="!!busy"
              data-test="practice-skip"
              @click="skip"
            >
              Passer la question
            </button>
            <button
              type="submit"
              class="primary small"
              :disabled="!!busy || !draft.trim()"
              data-test="practice-send"
            >
              <span class="with-icon"><AppIcon name="send" />Envoyer</span>
            </button>
          </div>
        </form>
      </template>

      <!-- 3. Le retour -->
      <div
        v-else-if="practice.feedback"
        class="practice-feedback"
        data-test="practice-feedback"
      >
        <section class="practice-summary">
          <div>
            <h4>Points forts</h4>
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
            <h4>À travailler</h4>
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
            <strong>{{ item.question }}. {{ questionOf(item.question) }}</strong>
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
      </div>
    </article>
  </div>
</template>
