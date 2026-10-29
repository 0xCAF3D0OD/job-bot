<script setup lang="ts">
import { ref } from "vue";

import type { Interview, InterviewIn } from "../api/client";
import AppIcon from "./AppIcon.vue";
import FormField from "./FormField.vue";
import IconButton from "./IconButton.vue";
import {
  DURATIONS,
  FORMATS,
  INTEREST,
  INTERVIEWERS,
  KINDS,
  NEXT_STEPS,
  OUTLOOK,
  SUGGESTED_QUESTIONS,
  THANKS,
} from "../interviewLabels";

// Retour d'entretien (docs/23 §2) : quelques clics, puis des champs courts ; seul le
// ressenti global est obligatoire.
const props = defineProps<{
  company: string;
  initial: Interview | null;
  heldAt: string | null;
  withEmployerFeedback: boolean;
  error: string;
}>();
const emit = defineEmits<{ submit: [value: InterviewIn]; close: []; remove: [] }>();

const i = props.initial;
const form = ref({
  kind: i?.kind ?? null,
  held_at: i?.held_at ?? props.heldAt,
  format: i?.format ?? null,
  duration: i?.duration ?? null,
  interviewers: [...(i?.interviewers ?? [])],
  people_count: i?.people_count ?? null,
  rating: i?.rating ?? 0,
  stress: i?.stress ?? null,
  interest: i?.interest ?? null,
  outlook: i?.outlook ?? null,
  questions: (i?.questions ?? []).map((q) => ({ text: q.text, difficult: q.difficult ?? false })),
  salary_asked: i?.salary_asked ?? null,
  salary_answer: i?.salary_answer ?? "",
  went_well: i?.went_well ?? "",
  went_badly: i?.went_badly ?? "",
  to_prepare: (i?.to_prepare ?? []).join("\n"),
  my_questions: i?.my_questions ?? "",
  missed_questions: i?.missed_questions ?? "",
  learned: i?.learned ?? "",
  warnings: i?.warnings ?? "",
  next_step: i?.next_step ?? null,
  next_step_at: i?.next_step_at ?? null,
  thanks: i?.thanks ?? null,
  employer_feedback: i?.employer_feedback ?? "",
});
const newQuestion = ref("");

function addQuestion(text: string): void {
  const value = text.trim();
  if (value && !form.value.questions.some((q) => q.text === value)) form.value.questions.push({ text: value, difficult: false });
  newQuestion.value = "";
}

function toggleInterviewer(key: string): void {
  const list = form.value.interviewers as string[];
  form.value.interviewers = (list.includes(key) ? list.filter((k) => k !== key) : [...list, key]) as typeof form.value.interviewers;
}

// Ressenti global obligatoire (docs/23 §1) : le bouton reste actif et le rappelle (docs/29 §3).
const ratingMissing = ref(false);

function submit(): void {
  if (!form.value.rating) {
    ratingMissing.value = true;
    document.querySelector<HTMLElement>("[data-test=rating-1]")?.focus();
    return;
  }
  ratingMissing.value = false;
  const f = form.value;
  emit("submit", {
    ...f,
    rating: f.rating,
    to_prepare: f.to_prepare.split("\n").map((l) => l.trim()).filter(Boolean),
    salary_answer: f.salary_asked ? f.salary_answer || null : null,
    went_well: f.went_well || null,
    went_badly: f.went_badly || null,
    my_questions: f.my_questions || null,
    missed_questions: f.missed_questions || null,
    learned: f.learned || null,
    warnings: f.warnings || null,
    employer_feedback: f.employer_feedback || null,
    next_step_at: f.next_step && f.next_step !== "rien" ? f.next_step_at || null : null,
  } as InterviewIn);
}
</script>

<template>
  <div
    class="overlay"
    @click.self="emit('close')"
  >
    <form
      class="form-card editor application-form interview-form"
      data-test="interview-form"
      @submit.prevent="submit"
    >
      <h3>
        Retour d'entretien · {{ company }}
      </h3>

      <fieldset>
        <legend>Le déroulé</legend>
        <div class="choice-row">
          <span class="choice-label">Entretien</span>
          <button
            v-for="(label, key) in KINDS"
            :key="key"
            type="button"
            :class="['chip', { on: form.kind === key }]"
            :aria-pressed="form.kind === key"
            :data-test="`kind-${key}`"
            @click="form.kind = form.kind === key ? null : (key as typeof form.kind)"
          >
            {{ label }}
          </button>
        </div>
        <div class="form-grid">
          <FormField
            v-slot="{ id, describedby, invalid }"
            label="Date"
            optional
            :width="10"
          >
            <input
              :id="id"
              v-model="form.held_at"
              type="date"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
            >
          </FormField>
          <FormField
            v-slot="{ id, describedby, invalid }"
            label="Format"
            optional
          >
            <select
              :id="id"
              v-model="form.format"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
            >
              <option :value="null">
                —
              </option>
              <option
                v-for="(label, key) in FORMATS"
                :key="key"
                :value="key"
              >
                {{ label }}
              </option>
            </select>
          </FormField>
          <FormField
            v-slot="{ id, describedby, invalid }"
            label="Durée"
            optional
          >
            <select
              :id="id"
              v-model="form.duration"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
            >
              <option :value="null">
                —
              </option>
              <option
                v-for="(label, key) in DURATIONS"
                :key="key"
                :value="key"
              >
                {{ label }}
              </option>
            </select>
          </FormField>
          <FormField
            v-slot="{ id, describedby, invalid }"
            label="Nombre de personnes"
            optional
            :width="5"
          >
            <input
              :id="id"
              v-model.number="form.people_count"
              type="number"
              min="1"
              max="30"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
            >
          </FormField>
        </div>
        <div class="choice-row">
          <span class="choice-label">Avec qui</span>
          <button
            v-for="(label, key) in INTERVIEWERS"
            :key="key"
            type="button"
            :class="['chip', { on: (form.interviewers as string[]).includes(key) }]"
            :aria-pressed="(form.interviewers as string[]).includes(key)"
            @click="toggleInterviewer(key)"
          >
            {{ label }}
          </button>
        </div>
      </fieldset>

      <fieldset>
        <legend>Ressenti</legend>
        <div class="choice-row">
          <span class="choice-label">Globalement</span>
          <span
            v-if="ratingMissing && !form.rating"
            class="field-error"
            role="status"
            data-test="rating-missing"
          >Indique ton ressenti global, de 1 à 5.</span>
          <button
            v-for="n in 5"
            :key="n"
            type="button"
            :class="['chip', 'score-chip', { on: form.rating === n }]"
            :aria-pressed="form.rating === n"
            :data-test="`rating-${n}`"
            @click="form.rating = n"
          >
            {{ n }}
          </button>
          <span class="hint">1 = mal, 5 = très bien</span>
        </div>
        <div class="choice-row">
          <span class="choice-label">Stress</span>
          <button
            v-for="n in 5"
            :key="n"
            type="button"
            :class="['chip', 'score-chip', { on: form.stress === n }]"
            :aria-pressed="form.stress === n"
            @click="form.stress = form.stress === n ? null : n"
          >
            {{ n }}
          </button>
          <span class="hint">1 = calme, 5 = très stressé</span>
        </div>
        <div class="choice-row">
          <span class="choice-label">Intérêt pour le poste</span>
          <button
            v-for="(label, key) in INTEREST"
            :key="key"
            type="button"
            :class="['chip', { on: form.interest === key }]"
            @click="form.interest = form.interest === key ? null : (key as typeof form.interest)"
          >
            {{ label }}
          </button>
        </div>
        <div class="choice-row">
          <span class="choice-label">La suite, selon toi</span>
          <button
            v-for="(label, key) in OUTLOOK"
            :key="key"
            type="button"
            :class="['chip', { on: form.outlook === key }]"
            @click="form.outlook = form.outlook === key ? null : (key as typeof form.outlook)"
          >
            {{ label }}
          </button>
        </div>
      </fieldset>

      <fieldset>
        <legend>Les questions posées</legend>
        <p
          v-if="form.questions.length"
          class="hint"
        >
          Coche celles qui t'ont mis en difficulté.
        </p>
        <ul class="question-list">
          <li
            v-for="(question, index) in form.questions"
            :key="question.text"
            data-test="interview-question"
          >
            <label class="check">
              <input
                v-model="question.difficult"
                type="checkbox"
              > {{ question.text }}
            </label>
            <IconButton
              icon="close"
              :label="`Retirer ${question.text}`"
              danger
              data-test="remove-question"
              @click="form.questions.splice(index, 1)"
            />
          </li>
        </ul>
        <div class="choice-row">
          <button
            v-for="text in SUGGESTED_QUESTIONS.filter((t) => !form.questions.some((q) => q.text === t))"
            :key="text"
            type="button"
            class="chip"
            data-test="suggested-question"
            @click="addQuestion(text)"
          >
            <span class="with-icon"><AppIcon name="plus" />{{ text }}</span>
          </button>
        </div>
        <FormField
          v-slot="{ id, describedby, invalid }"
          label="Une autre question"
          optional
        >
          <div class="inline-form">
            <input
              :id="id"
              v-model="newQuestion"
              type="text"
              maxlength="300"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
              data-test="new-question"
              @keydown.enter.prevent="addQuestion(newQuestion)"
            >
            <IconButton
              icon="plus"
              label="Ajouter la question"
              data-test="add-question"
              @click="addQuestion(newQuestion)"
            />
          </div>
        </FormField>
        <!-- Oui ou non pris en compte à l'envoi : une case à cocher (règles §4, Choisir). -->
        <label class="check">
          <input
            v-model="form.salary_asked"
            type="checkbox"
            data-test="salary-yes"
          >
          On t'a posé la question du salaire
        </label>
        <FormField
          v-if="form.salary_asked"
          v-slot="{ id, describedby, invalid }"
          label="Ce que tu as répondu"
          optional
        >
          <input
            :id="id"
            v-model="form.salary_answer"
            type="text"
            maxlength="300"
            :aria-describedby="describedby"
            :aria-invalid="invalid"
            data-test="salary-answer"
          >
        </FormField>
      </fieldset>

      <fieldset>
        <legend>Ce qui a marché, ce qui n'a pas marché</legend>
        <div class="form-grid">
          <FormField
            v-slot="{ id, describedby, invalid }"
            class="wide"
            label="Ce qui a bien fonctionné"
            optional
          >
            <textarea
              :id="id"
              v-model="form.went_well"
              rows="2"
              maxlength="2000"
              placeholder="Un exemple qui a porté, une réponse bien préparée…"
              data-test="went-well"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
            />
          </FormField>
          <FormField
            v-slot="{ id, describedby, invalid }"
            class="wide"
            label="Ce qui a moins bien fonctionné"
            optional
          >
            <textarea
              :id="id"
              v-model="form.went_badly"
              rows="2"
              maxlength="2000"
              placeholder="Une réponse hésitante, un point du CV mal expliqué…"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
            />
          </FormField>
          <FormField
            v-slot="{ id, describedby, invalid }"
            class="wide"
            label="Ce que tu aurais dû préparer"
            optional
            hint="Une idée par ligne."
          >
            <textarea
              :id="id"
              v-model="form.to_prepare"
              rows="2"
              placeholder="Un exemple chiffré de projet&#10;Les chiffres de l'entreprise"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
            />
          </FormField>
          <FormField
            v-slot="{ id, describedby, invalid }"
            label="Tes questions posées"
            optional
          >
            <textarea
              :id="id"
              v-model="form.my_questions"
              rows="2"
              maxlength="2000"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
            />
          </FormField>
          <FormField
            v-slot="{ id, describedby, invalid }"
            label="Celles que tu regrettes de ne pas avoir posées"
            optional
          >
            <textarea
              :id="id"
              v-model="form.missed_questions"
              rows="2"
              maxlength="2000"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
            />
          </FormField>
        </div>
      </fieldset>

      <fieldset>
        <legend>Ce que tu as appris sur le poste</legend>
        <div class="form-grid">
          <FormField
            v-slot="{ id, describedby, invalid }"
            label="Missions, équipe, outils, télétravail…"
            optional
          >
            <textarea
              :id="id"
              v-model="form.learned"
              rows="2"
              maxlength="2000"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
            />
          </FormField>
          <FormField
            v-slot="{ id, describedby, invalid }"
            label="Points d'attention"
            optional
          >
            <textarea
              :id="id"
              v-model="form.warnings"
              rows="2"
              maxlength="2000"
              placeholder="Charge, ambiance, flou sur le poste…"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
            />
          </FormField>
        </div>
      </fieldset>

      <fieldset>
        <legend>La suite</legend>
        <div class="form-grid">
          <FormField
            v-slot="{ id, describedby, invalid }"
            label="Prochaine étape annoncée"
            optional
          >
            <select
              :id="id"
              v-model="form.next_step"
              data-test="next-step"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
            >
              <option :value="null">
                —
              </option>
              <option
                v-for="(label, key) in NEXT_STEPS"
                :key="key"
                :value="key"
              >
                {{ label }}
              </option>
            </select>
          </FormField>
          <FormField
            v-if="form.next_step && form.next_step !== 'rien'"
            v-slot="{ id, describedby, invalid }"
            label="Avant le"
            optional
            :width="10"
          >
            <input
              :id="id"
              v-model="form.next_step_at"
              type="date"
              data-test="next-step-at"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
            >
          </FormField>
          <FormField
            v-slot="{ id, describedby, invalid }"
            label="Remerciement"
            optional
          >
            <select
              :id="id"
              v-model="form.thanks"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
            >
              <option :value="null">
                —
              </option>
              <option
                v-for="(label, key) in THANKS"
                :key="key"
                :value="key"
              >
                {{ label }}
              </option>
            </select>
          </FormField>
          <FormField
            v-if="withEmployerFeedback"
            v-slot="{ id, describedby, invalid }"
            class="wide"
            label="Le retour de l'employeur (motif, conseils)"
            optional
          >
            <textarea
              :id="id"
              v-model="form.employer_feedback"
              rows="2"
              maxlength="2000"
              :aria-describedby="describedby"
              :aria-invalid="invalid"
            />
          </FormField>
        </div>
      </fieldset>

      <p
        v-if="error"
        class="notice error"
        role="alert"
      >
        {{ error }}
      </p>
      <div class="form-actions">
        <button
          type="submit"
          class="primary"
          data-test="save-interview"
        >
          Enregistrer le retour
        </button>
        <button
          type="button"
          class="secondary"
          @click="emit('close')"
        >
          Annuler
        </button>
        <IconButton
          v-if="initial"
          icon="trash"
          label="Supprimer ce retour"
          danger
          data-test="remove-interview"
          @click="emit('remove')"
        />
      </div>
    </form>
  </div>
</template>
