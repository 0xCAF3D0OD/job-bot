<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api, type InterviewInsights } from "../api/client";
import InterviewCoaching from "./InterviewCoaching.vue";
import InterviewPractice from "./InterviewPractice.vue";
import DisclosureRow from "./DisclosureRow.vue";
import AiWriting from "./AiWriting.vue";
import AppIcon from "./AppIcon.vue";
import HoverNote from "./HoverNote.vue";
import { plural } from "../format";
import { usePlan } from "../composables/usePlan";
import PlanLimit from "./PlanLimit.vue";

const { aiNote, reached, refresh: refreshPlan } = usePlan();

// « Mes enseignements » (docs/23 §3) : tous les retours d'entretien, regroupés, sans IA ;
// les pistes de l'IA seulement à la demande.
const data = ref<InterviewInsights | null>(null);
const busy = ref(false);
const message = ref("");
// Un entretien type, sans candidature (docs/75 §3).
const practicing = ref(false);
const shortDate = new Intl.DateTimeFormat("fr-CH", { day: "numeric", month: "short" });

async function load(): Promise<void> {
  data.value = (await api.GET("/api/interviews/insights")).data ?? null;
}

async function toggle(text: string, done: boolean): Promise<void> {
  const { data: next } = await api.PUT("/api/interviews/insights/prepared", { body: { text, done } });
  if (next) data.value = next;
}

async function coach(): Promise<void> {
  busy.value = true;
  message.value = "";
  try {
    const { data: next, error } = await api.POST("/api/interviews/coach", { body: {} });
    if (next) data.value = next;
    else {
      const detail = (error as { detail?: unknown } | undefined)?.detail;
      message.value = typeof detail === "string" ? `Impossible : ${detail}.` : "Impossible pour l'instant.";
    }
  } finally {
    busy.value = false;
  }
}

defineExpose({ load });
onMounted(() => void load());
</script>

<template>
  <DisclosureRow
    v-if="data"
    class="insights"
    title="Enseignements"
    :value="data.count ? `${plural(data.count, 'entretien', 'entretiens')} · ressenti ${data.average_rating}/5` : 'aucun entretien'"
    data-test="insights"
  >
    <!-- Toujours visible (retour d'usage du 2026-10-07) : dit comment la remplir. -->
    <p
      v-if="!data.count"
      class="hint reading-width"
      data-test="insights-empty"
    >
      Rien pour l'instant. Après un entretien, clique sur « Faire le point sur l'entretien » dans sa candidature.
    </p>
    <div
      v-if="data.count"
      class="insights-grid"
    >
      <section v-if="data.questions.length">
        <h4>Les questions qui reviennent</h4>
        <ul data-test="insight-questions">
          <li
            v-for="question in data.questions.slice(0, 10)"
            :key="question.text"
          >
            {{ question.text }}
            <span class="hint">· {{ question.count }} fois</span>
            <span
              v-if="question.difficult"
              class="badge warn"
            >difficile pour {{ question.difficult }}</span>
          </li>
        </ul>
      </section>
      <section v-if="data.to_prepare.length">
        <h4>À préparer</h4>
        <ul class="prepare-list">
          <li
            v-for="item in data.to_prepare"
            :key="item.text"
          >
            <label class="check">
              <input
                type="checkbox"
                :checked="item.done"
                data-test="prepare-item"
                @change="toggle(item.text, !item.done)"
              > <span :class="{ done: item.done }">{{ item.text }}</span>
            </label>
          </li>
        </ul>
      </section>
      <section v-if="data.went_well.length">
        <h4>Ce qui a marché</h4>
        <ul>
          <li
            v-for="(note, index) in data.went_well.slice(0, 6)"
            :key="index"
          >
            {{ note.text }} <span class="hint">· {{ note.company }}{{ note.held_at ? `, ${shortDate.format(new Date(note.held_at))}` : "" }}</span>
          </li>
        </ul>
      </section>
      <section v-if="data.went_badly.length">
        <h4>Ce qui n'a pas marché</h4>
        <ul>
          <li
            v-for="(note, index) in data.went_badly.slice(0, 6)"
            :key="index"
          >
            {{ note.text }} <span class="hint">· {{ note.company }}{{ note.held_at ? `, ${shortDate.format(new Date(note.held_at))}` : "" }}</span>
          </li>
        </ul>
      </section>
      <section v-if="data.missed_questions.length">
        <h4>Les questions que tu regrettes de ne pas avoir posées</h4>
        <ul>
          <li
            v-for="(note, index) in data.missed_questions.slice(0, 6)"
            :key="index"
          >
            {{ note.text }}
          </li>
        </ul>
      </section>
      <section v-if="data.employer_feedback.length">
        <h4>Retours des employeurs</h4>
        <ul>
          <li
            v-for="(note, index) in data.employer_feedback"
            :key="index"
          >
            {{ note.text }} <span class="hint">· {{ note.company }}</span>
          </li>
        </ul>
      </section>
    </div>
    <div
      v-if="data.count"
      class="insights-ai"
    >
      <InterviewCoaching
        v-if="data.coaching"
        :coaching="data.coaching"
      />
      <AiWriting
        v-if="busy"
        kind="coaching"
      />
      <button
        v-if="data.can_coach"
        type="button"
        class="secondary small"
        :disabled="busy"
        data-test="coach"
        @click="coach"
      >
        <HoverNote :text="busy ? '' : aiNote('Environ 0,03 $.')">
          <span class="with-icon"><AppIcon name="ai" />{{ busy ? "Analyse en cours…" : data.coaching ? "Nouvelles pistes de l'IA" : "Pistes de l'IA" }}</span>
        </HoverNote>
      </button>
      <p
        v-if="message"
        class="notice error"
        role="alert"
      >
        {{ message }}
      </p>
    </div>
    <p
      v-if="data.can_coach"
      class="practice-cta"
    >
      <button
        type="button"
        class="secondary small"
        data-test="insights-practice"
        :disabled="reached('practice')"
        @click="practicing = true"
      >
        <HoverNote :text="aiNote('Environ 0,20 CHF.', 'practice', 'Cinq questions de l\'IA, une à la fois, puis un retour ; tu peux répondre en dictant.')">
          <span class="with-icon"><AppIcon name="ai" />M'entraîner sur un entretien type</span>
        </HoverNote>
      </button>
    </p>
    <PlanLimit usage="practice" />
    <Teleport to="body">
      <InterviewPractice
        v-if="practicing"
        @changed="load"
        @close="practicing = false; refreshPlan()"
      />
    </Teleport>
  </DisclosureRow>
</template>
