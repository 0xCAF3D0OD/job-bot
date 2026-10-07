<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api, type InterviewInsights } from "../api/client";
import InterviewCoaching from "./InterviewCoaching.vue";

// « Mes enseignements » (docs/23 §3) : tous les retours d'entretien, regroupés, sans IA ;
// les pistes de l'IA seulement à la demande.
const data = ref<InterviewInsights | null>(null);
const busy = ref(false);
const message = ref("");
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
  <details
    v-if="data && data.count"
    class="insights"
    data-test="insights"
  >
    <summary>
      Mes enseignements · {{ data.count }} entretien(s), ressenti moyen {{ data.average_rating }}/5
    </summary>
    <div class="insights-grid">
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
            >difficile {{ question.difficult }}×</span>
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
    <div class="insights-ai">
      <InterviewCoaching
        v-if="data.coaching"
        :coaching="data.coaching"
      />
      <button
        v-if="data.can_coach"
        type="button"
        class="secondary small"
        :disabled="busy"
        data-test="coach"
        @click="coach"
      >
        {{ busy ? "Analyse en cours…" : data.coaching ? "Nouvelles pistes de l'IA (≈ 0,03 $)" : "Demander des pistes à l'IA (≈ 0,03 $)" }}
      </button>
      <span class="hint">L'IA ne reçoit que tes retours et tes blocs de profil.</span>
      <p
        v-if="message"
        class="notice error"
        role="alert"
      >
        {{ message }}
      </p>
    </div>
  </details>
</template>
