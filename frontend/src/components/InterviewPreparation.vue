<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type Application, type InterviewInsights, type Offer } from "../api/client";
import InterviewCoaching from "./InterviewCoaching.vue";

// Fiche « Préparer l'entretien » (docs/23 §3) : le poste, les questions difficiles déjà
// rencontrées, ce qui reste à préparer, les questions à poser ; pistes de l'IA à la demande.
const props = defineProps<{ application: Application }>();
const emit = defineEmits<{ close: [] }>();

const insights = ref<InterviewInsights | null>(null);
const offer = ref<Offer | null>(null);
const busy = ref(false);
const message = ref("");
const longDate = new Intl.DateTimeFormat("fr-CH", { weekday: "long", day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" });

const difficult = computed(() => (insights.value?.questions ?? []).filter((q) => q.difficult));
const frequent = computed(() => (insights.value?.questions ?? []).filter((q) => !q.difficult && q.count > 1));
const todo = computed(() => (insights.value?.to_prepare ?? []).filter((t) => !t.done));
const coaching = computed(() =>
  insights.value?.coaching?.application_id === props.application.id ? insights.value.coaching : null,
);

async function coach(): Promise<void> {
  busy.value = true;
  message.value = "";
  try {
    const { data, error } = await api.POST("/api/interviews/coach", { body: { application_id: props.application.id } });
    if (data) insights.value = data;
    else {
      const detail = (error as { detail?: unknown } | undefined)?.detail;
      message.value = typeof detail === "string" ? `Impossible : ${detail}.` : "Impossible pour l'instant.";
    }
  } finally {
    busy.value = false;
  }
}

onMounted(async () => {
  insights.value = (await api.GET("/api/interviews/insights")).data ?? null;
  if (props.application.offer_id) {
    offer.value =
      (await api.GET("/api/offers/{offer_id}", { params: { path: { offer_id: props.application.offer_id } } })).data ??
      null;
  }
});
</script>

<template>
  <div
    class="overlay"
    @click.self="emit('close')"
  >
    <article
      class="form-card editor application-form preparation-sheet"
      data-test="interview-preparation"
    >
      <h3>Préparer l'entretien · {{ application.company }}</h3>
      <p class="hint">
        {{ application.job_title }}<template v-if="application.interview_at">
          · {{ longDate.format(new Date(application.interview_at)) }}
        </template>
      </p>
      <section v-if="offer?.summary_role">
        <h4>Le poste</h4>
        <p>{{ offer.summary_role }}</p>
        <p
          v-if="offer.summary_asks"
          class="muted"
        >
          Demande : {{ offer.summary_asks }}
        </p>
      </section>
      <section v-if="application.interviews?.length">
        <h4>Tes entretiens précédents ici</h4>
        <ul>
          <li
            v-for="item in application.interviews"
            :key="item.id"
          >
            Ressenti {{ item.rating }}/5<template v-if="item.went_badly">
              · à améliorer : {{ item.went_badly }}
            </template>
          </li>
        </ul>
      </section>
      <section v-if="difficult.length">
        <h4>Les questions qui t'ont déjà mis en difficulté</h4>
        <ul data-test="prep-difficult">
          <li
            v-for="question in difficult"
            :key="question.text"
          >
            {{ question.text }}
          </li>
        </ul>
      </section>
      <section v-if="frequent.length">
        <h4>Les questions qui reviennent</h4>
        <ul>
          <li
            v-for="question in frequent"
            :key="question.text"
          >
            {{ question.text }}
          </li>
        </ul>
      </section>
      <section v-if="todo.length">
        <h4>Encore à préparer</h4>
        <ul data-test="prep-todo">
          <li
            v-for="item in todo"
            :key="item.text"
          >
            {{ item.text }}
          </li>
        </ul>
      </section>
      <section v-if="insights?.missed_questions.length">
        <h4>Des questions à poser</h4>
        <ul>
          <li
            v-for="(note, index) in insights.missed_questions.slice(0, 5)"
            :key="index"
          >
            {{ note.text }}
          </li>
        </ul>
      </section>
      <p
        v-if="insights && !insights.count"
        class="hint"
      >
        Après tes premiers entretiens, cette fiche reprendra tes retours (questions difficiles, points à préparer).
      </p>
      <InterviewCoaching
        v-if="coaching"
        :coaching="coaching"
      />
      <p
        v-if="message"
        class="notice error"
        role="alert"
      >
        {{ message }}
      </p>
      <div class="form-actions">
        <button
          v-if="insights?.can_coach && insights.count"
          type="button"
          class="secondary small"
          :disabled="busy"
          data-test="prep-coach"
          @click="coach"
        >
          {{ busy ? "Analyse en cours…" : "Pistes de l'IA pour cet entretien (≈ 0,03 $)" }}
        </button>
        <button
          type="button"
          class="primary small"
          @click="emit('close')"
        >
          Fermer
        </button>
      </div>
    </article>
  </div>
</template>
