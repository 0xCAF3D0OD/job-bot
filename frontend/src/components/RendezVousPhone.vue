<script setup lang="ts">
import { computed, ref } from "vue";

import type { Application } from "../api/client";
import type { components } from "../api/schema";
import {
  agreedLines,
  checkedCount,
  countdown,
  dateBlock,
  dateText,
  pastTitle,
  sheetLines,
  timeAndPlace,
  upcomingAppointments,
} from "../rendezVous";
import { plural } from "../format";
import { timeOfDay } from "../dates";

// Candidatures › Rendez-vous sur téléphone (maquettes RendezVous et RendezVousSombre, 6.11.2026). Deux parties,
// posées par OrpMeetingView autour de ses états existants (aucun rendez-vous, noter ce qui a été convenu) :
// « À venir » (le prochain rendez-vous ORP et les entretiens, par date), puis « Derniers rendez-vous ORP ».
type Page = components["schemas"]["MeetingPage"];
type Question = components["schemas"]["QuestionIO"];
type Meeting = components["schemas"]["MeetingOut"];

const props = defineProps<{
  part: "upcoming" | "past";
  page: Page;
  applications: Application[];
  sheetLink: string;
  noting: number | null;
}>();
const emit = defineEmits<{
  toggle: [question: Question, checked: boolean];
  sheet: [];
  log: [];
  prepare: [application: Application];
  note: [id: number];
}>();

const now = new Date();
const items = computed(() => upcomingAppointments(props.page.meeting ?? null, props.applications, now));
const prep = computed(() => props.page.preparation);
const lines = computed(() => sheetLines(prep.value));
const checked = computed(() => prep.value.questions.filter((q) => q.checked).length);
const questionsOpen = ref(false);

// Le dernier rendez-vous ORP : celui qui vient d'avoir lieu, sinon le premier du carnet.
const last = computed<Meeting | null>(() => {
  const meeting = props.page.meeting;
  if (meeting && Date.parse(meeting.starts_at) <= now.getTime()) return meeting;
  return props.page.past[0] ?? null;
});
</script>

<template>
  <section
    v-if="part === 'upcoming' && items.length"
    class="rdv-part"
    aria-labelledby="rdv-a-venir"
    data-test="rdv-upcoming"
  >
    <h2
      id="rdv-a-venir"
      class="rdv-title"
    >
      À venir<span>{{ plural(items.length, "rendez-vous", "rendez-vous") }}</span>
    </h2>
    <template
      v-for="item in items"
      :key="item.key"
    >
      <article
        v-if="item.kind === 'orp'"
        class="rdv-card rdv-orp"
        aria-labelledby="rdv-orp-titre"
        data-test="rdv-orp"
      >
        <div class="rdv-head">
          <span
            class="rdv-date rdv-date-orp"
            aria-hidden="true"
          >
            <span class="rdv-date-day-name">{{ dateBlock(item.at).weekday }}</span>
            <span class="rdv-date-number">{{ dateBlock(item.at).day }}</span>
            <span class="rdv-date-month">{{ dateBlock(item.at).month }}</span>
          </span>
          <div class="rdv-body">
            <span class="rdv-kicker">{{ countdown(item.at, now) }}</span>
            <h3
              id="rdv-orp-titre"
              class="rdv-orp-title"
            >
              Rendez-vous ORP
            </h3>
            <span class="rdv-meta"><span class="visually-hidden">{{ dateText(item.at) }}, </span>{{ timeAndPlace(item.at, item.meeting.place) }}</span>
            <span
              class="rdv-ready"
              data-test="rdv-ready"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2.6"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              ><path d="m5 12.5 4.5 4.5L19 7.5" /></svg>Ta feuille est prête
            </span>
          </div>
        </div>
        <ul
          v-if="lines.length"
          class="rdv-lines"
          data-test="rdv-lines"
        >
          <li
            v-for="line in lines"
            :key="line.label"
          >
            <span
              class="rdv-dot"
              aria-hidden="true"
            />
            <span class="rdv-line">
              <span class="rdv-line-label">{{ line.label }}</span>
              <span class="rdv-line-text">{{ line.text }}</span>
            </span>
          </li>
        </ul>
        <div
          v-if="prep.questions.length"
          class="rdv-questions"
        >
          <button
            type="button"
            class="rdv-questions-toggle"
            :aria-expanded="questionsOpen"
            aria-controls="rdv-questions-list"
            data-test="rdv-questions"
            @click="questionsOpen = !questionsOpen"
          >
            <span class="rdv-questions-title">Tes questions au conseiller</span>
            <span class="rdv-questions-count">{{ checkedCount(checked) }}<svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.4"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
              :class="{ open: questionsOpen }"
            ><path d="m6 9 6 6 6-6" /></svg></span>
          </button>
          <ul
            v-show="questionsOpen"
            id="rdv-questions-list"
            class="rdv-questions-list"
          >
            <li
              v-for="question in prep.questions"
              :key="question.key"
            >
              <label>
                <input
                  type="checkbox"
                  :checked="question.checked"
                  :data-test="`rdv-question-${question.key}`"
                  @change="emit('toggle', question, ($event.target as HTMLInputElement).checked)"
                >
                <span>{{ question.text }}</span>
              </label>
            </li>
          </ul>
        </div>
        <button
          type="button"
          class="rdv-sheet"
          data-test="rdv-sheet"
          @click="emit('sheet')"
        >
          Voir ma feuille
        </button>
        <a
          class="rdv-pdf"
          :href="sheetLink"
          download
          data-test="rdv-pdf"
        >Imprimer ou télécharger en PDF</a>
      </article>
      <article
        v-else
        class="rdv-card rdv-interview"
        :data-test="`rdv-interview-${item.application.id}`"
      >
        <span
          class="rdv-date rdv-date-interview"
          aria-hidden="true"
        >
          <span class="rdv-date-day-name">{{ dateBlock(item.at).weekday }}</span>
          <span class="rdv-date-number">{{ dateBlock(item.at).day }}</span>
          <span class="rdv-date-month">{{ dateBlock(item.at).month }}</span>
        </span>
        <div class="rdv-body">
          <span class="rdv-kicker">Entretien d’embauche</span>
          <h3 class="rdv-interview-title">
            {{ item.application.job_title || "Poste non indiqué" }}
          </h3>
          <span class="rdv-meta"><span class="visually-hidden">{{ dateText(item.at) }}, </span>{{ [item.application.company, timeOfDay(item.at)].filter(Boolean).join(" · ") }}</span>
          <span
            v-if="item.application.company_address"
            class="rdv-meta"
          >{{ item.application.company_address }}</span>
          <!-- Toute la carte ouvre la préparation (maquette) : le bouton s'étend sur la carte. -->
          <button
            type="button"
            class="rdv-prepare"
            :data-test="`rdv-prepare-${item.application.id}`"
            @click="emit('prepare', item.application)"
          >
            Préparer l’entretien<span class="visually-hidden"> {{ item.application.job_title }}, {{ item.application.company }}</span><svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.4"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            ><path d="m9 6 6 6-6 6" /></svg>
          </button>
        </div>
      </article>
    </template>
  </section>

  <section
    v-else-if="part === 'past' && last"
    class="rdv-part"
    aria-labelledby="rdv-derniers"
    data-test="rdv-past"
  >
    <h2
      id="rdv-derniers"
      class="rdv-title"
    >
      Derniers rendez-vous ORP
    </h2>
    <article class="rdv-card rdv-last">
      <div class="rdv-last-head">
        <span
          class="rdv-date rdv-date-past"
          aria-hidden="true"
        >
          <span class="rdv-date-number">{{ dateBlock(last.starts_at).day }}</span>
          <span class="rdv-date-month">{{ dateBlock(last.starts_at).month }}</span>
        </span>
        <div class="rdv-body">
          <h3 class="rdv-last-title">
            {{ pastTitle(last.starts_at, now) }}
          </h3>
          <span class="rdv-meta">Ce qui a été convenu</span>
        </div>
      </div>
      <!-- Ce qui a été convenu, à noter ou à modifier : le formulaire existant (OrpOutcomeForm), posé par la vue. -->
      <slot
        v-if="noting === last.id"
        name="noting"
        :meeting="last"
      />
      <template v-else-if="last.outcome_at">
        <dl
          v-if="agreedLines(last).length"
          class="rdv-agreed"
          data-test="rdv-agreed"
        >
          <template
            v-for="line in agreedLines(last)"
            :key="line.label"
          >
            <dt>{{ line.label }}</dt>
            <dd>{{ line.text }}</dd>
          </template>
        </dl>
      </template>
      <button
        v-else
        type="button"
        class="rdv-note"
        data-test="rdv-note"
        @click="emit('note', last.id)"
      >
        Noter ce qui a été convenu
      </button>
    </article>
    <button
      v-if="page.past.length"
      type="button"
      class="rdv-card rdv-log"
      data-test="rdv-log"
      @click="emit('log')"
    >
      <span class="rdv-log-title">Carnet ORP</span>
      <span class="rdv-log-count">{{ plural(page.past.length, "rendez-vous", "rendez-vous") }}<svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2.4"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      ><path d="m9 6 6 6-6 6" /></svg></span>
    </button>
  </section>
</template>

<style scoped>
/* Les valeurs de la maquette (RendezVous.dc.html), écrites avec les échelles (scales.test.ts) :
   14 px = --space-4 − 2 px, 10 px = --space-2 + 2 px, 15 px = --font-small + 1 px, 58 px = --btn-primary + 4 px. */
.rdv-part { min-width: 0; display: flex; flex-direction: column; gap: calc(var(--space-2) + var(--space-1) / 2); }
.rdv-title {
  display: flex; align-items: baseline; gap: var(--space-2); margin: calc(var(--space-1) * 1.5) var(--space-1) 0;
  font-size: var(--font-body); font-weight: var(--weight-bold); line-height: var(--leading-tight);
}
.rdv-title span { font-size: var(--label-caps); font-weight: var(--weight-semibold); color: var(--text-secondary); }
.rdv-card {
  display: flex; padding: var(--space-4); background: var(--surface); border: 1px solid var(--line);
  border-radius: var(--radius-card); color: var(--text);
}
.rdv-orp { flex-direction: column; }
.rdv-head, .rdv-interview { gap: calc(var(--space-4) - var(--space-1) / 2); }
.rdv-head { display: flex; }
.rdv-interview { position: relative; }
.rdv-date {
  flex: none; display: flex; flex-direction: column; align-items: center; justify-content: center;
  width: var(--btn-secondary); height: calc(var(--btn-primary) + var(--space-1));
  border-radius: calc(var(--radius-card) - var(--space-1)); line-height: var(--leading-none);
}
.rdv-date-orp { background: var(--peach-soft); color: var(--peach-text); }
.rdv-date-interview { background: var(--primary-soft); color: var(--primary-text); }
.rdv-date-past { height: var(--btn-secondary); background: var(--surface-muted); color: var(--text-tertiary); }
.rdv-date-day-name { font-size: var(--font-caption); font-weight: var(--weight-bold); text-transform: uppercase; letter-spacing: 0.4px; }
.rdv-date-number { margin-top: calc(var(--space-1) - 1px); font-size: var(--title-sub); font-weight: var(--weight-heavy); }
.rdv-date-past .rdv-date-number { margin-top: 0; font-size: calc(var(--font-body) * 1.25); }
.rdv-date-month { margin-top: calc(var(--space-1) / 2); font-size: var(--font-caption); font-weight: var(--weight-semibold); }
.rdv-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: var(--space-1); }
.rdv-kicker { font-size: var(--label-caps); font-weight: var(--weight-bold); color: var(--text-secondary); }
.rdv-orp-title { margin: 0; font-size: var(--font-title); line-height: 1.28em; font-weight: var(--weight-heavy); }
.rdv-interview-title { margin: 0; font-size: var(--font-body); line-height: 1.3125em; font-weight: var(--weight-bold); }
.rdv-meta { font-size: var(--font-small); color: var(--text-secondary); }
.rdv-ready {
  align-self: flex-start; display: inline-flex; align-items: center; gap: calc(var(--space-1) * 1.5);
  margin-top: calc(var(--space-1) * 1.5); padding: var(--space-1) calc(var(--space-2) + var(--space-1) / 2);
  border-radius: var(--radius-pill); background: var(--success-soft); color: var(--success);
  font-size: var(--label-caps); font-weight: var(--weight-bold);
}
.rdv-ready svg { flex: none; }
.rdv-lines { margin: calc(var(--space-4) - var(--space-1) / 2) 0 0; padding: 0; list-style: none; }
.rdv-lines li {
  display: flex; gap: calc(var(--space-2) + var(--space-1) / 2); padding: calc(var(--space-2) + var(--space-1) / 2) 0;
  border-top: 1px solid var(--line-soft);
}
.rdv-dot {
  flex: none; width: calc(var(--space-1) * 1.5); height: calc(var(--space-1) * 1.5);
  margin: var(--space-2) calc(var(--space-1) * 1.5) 0 var(--space-1); border-radius: var(--radius-pill); background: var(--text-secondary);
}
.rdv-line { min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.rdv-line-label { font-size: var(--label-caps); font-weight: var(--weight-bold); color: var(--text-secondary); }
.rdv-line-text, .rdv-questions-list span, .rdv-agreed { font-size: calc(var(--font-small) + 1px); line-height: 1.4em; }
.rdv-questions { border-top: 1px solid var(--line-soft); }
.rdv-questions-toggle {
  display: flex; align-items: center; justify-content: space-between; width: 100%; min-height: var(--btn-tertiary);
  padding: 0; border: 0; border-radius: 0; background: transparent; color: var(--text); font: inherit; cursor: pointer;
}
.rdv-questions-title { flex: 1; min-width: 0; text-align: left; font-size: calc(var(--font-small) + 1px); font-weight: var(--weight-bold); }
.rdv-questions-count { flex: none; display: flex; align-items: center; gap: calc(var(--space-1) * 1.5); font-size: var(--font-small); font-weight: var(--weight-regular); color: var(--text-secondary); }
.rdv-questions-count svg { transition: transform 200ms; }
.rdv-questions-count svg.open { transform: rotate(180deg); }
.rdv-questions-list { margin: 0 0 calc(var(--space-1) * 1.5); padding: 0; list-style: none; }
.rdv-questions-list label {
  display: flex; align-items: flex-start; gap: var(--space-3); min-height: var(--target-min); padding: var(--space-2) 0; cursor: pointer;
}
.rdv-questions-list input { flex: none; width: calc(var(--space-5) + 2px); height: calc(var(--space-5) + 2px); margin: 1px 0 0; accent-color: var(--primary); cursor: pointer; }
.rdv-sheet {
  display: flex; align-items: center; justify-content: center; margin-top: calc(var(--space-2) + var(--space-1) / 2); min-height: var(--btn-secondary); padding: 0 var(--space-4);
  border: 0; border-radius: var(--radius-pill); background: var(--primary); color: var(--on-primary);
  font: inherit; font-size: var(--font-body); font-weight: var(--weight-bold); cursor: pointer;
}
.rdv-pdf {
  display: flex; align-items: center; justify-content: center; margin-top: var(--space-1); min-height: var(--target-min);
  color: var(--primary-text); font-size: calc(var(--font-small) + 1px); font-weight: var(--weight-bold); text-decoration: none;
}
.rdv-pdf:hover { text-decoration: underline; }
.rdv-prepare {
  display: flex; align-items: center; gap: calc(var(--space-1) * 1.5); align-self: flex-start;
  margin-top: calc(var(--space-1) * 1.5); padding: 0; border: 0; border-radius: 0; background: transparent;
  color: var(--primary-text); font: inherit; font-size: calc(var(--font-small) + 1px); font-weight: var(--weight-bold); cursor: pointer;
}
/* La carte entière est la cible (maquette : un lien sur toute la carte). */
.rdv-prepare::after { content: ""; position: absolute; inset: 0; border-radius: var(--radius-card); }
.rdv-prepare:focus-visible { outline: none; }
.rdv-prepare:focus-visible::after { outline: 2px solid var(--primary-graphic); outline-offset: 2px; }
.rdv-last { flex-direction: column; gap: var(--space-3); }
.rdv-last-head { display: flex; align-items: center; gap: calc(var(--space-4) - var(--space-1) / 2); }
.rdv-last-title { margin: 0; font-size: var(--font-body); font-weight: var(--weight-bold); line-height: var(--leading-normal); }
.rdv-agreed { display: grid; grid-template-columns: auto 1fr; gap: calc(var(--space-1) * 1.5) var(--space-3); margin: 0; }
.rdv-agreed dt { color: var(--text-secondary); }
.rdv-agreed dd { margin: 0; }
.rdv-note {
  align-self: flex-start; min-height: var(--target-min); padding: 0; border: 0; border-radius: 0; background: transparent;
  color: var(--primary-text); font: inherit; font-size: calc(var(--font-small) + 1px); font-weight: var(--weight-bold); cursor: pointer;
}
.rdv-log {
  align-items: center; justify-content: space-between; width: 100%; min-height: var(--btn-secondary);
  padding: 0 var(--space-4); font: inherit; text-align: left; cursor: pointer;
}
.rdv-log-title { flex: 1; min-width: 0; font-size: calc(var(--font-small) + 1px); font-weight: var(--weight-bold); }
.rdv-log-count { flex: none; display: flex; align-items: center; gap: calc(var(--space-1) * 1.5); font-size: var(--font-small); color: var(--text-secondary); }
</style>
