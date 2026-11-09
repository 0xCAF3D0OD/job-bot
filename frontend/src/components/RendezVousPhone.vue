<script setup lang="ts">
import { computed, ref } from "vue";

import type { Application } from "../api/client";
import type { components } from "../api/schema";
import {
  agreedLines,
  countdown,
  dateText,
  interviewPlace,
  meetingsToNote,
  notedMeetings,
  pastTitle,
  sheetLines,
  timeAndPlace,
  upcomingAppointments,
} from "../rendezVous";
import { plural } from "../format";
import CalendarDate from "./CalendarDate.vue";
import MeetingPrepSheet from "./MeetingPrepSheet.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";
import { timeOfDay } from "../dates";

// Candidatures › Rendez-vous sur téléphone (maquettes RendezVous et RendezVousSombre, 6 et 7.11.2026). Deux parties,
// posées par OrpMeetingView autour de l'état « aucun rendez-vous » : « À venir » (le prochain rendez-vous ORP et les
// entretiens, par date), puis « À noter » et « Derniers rendez-vous ORP » ; « Noter » ouvre la feuille de la vue.
type Page = components["schemas"]["MeetingPage"];
type Question = components["schemas"]["QuestionIO"];
type Meeting = components["schemas"]["MeetingOut"];

const props = defineProps<{
  part: "upcoming" | "past";
  page: Page;
  applications: Application[];
  sheetLink: string;
  // Le « ⋯ » de la carte ORP (C6) : les mêmes actions que celui de la page actuelle.
  meetingItems?: MoreMenuItem[];
}>();
const emit = defineEmits<{
  toggle: [question: Question, checked: boolean];
  log: [];
  prepare: [application: Application];
  note: [id: number];
}>();

const now = new Date();
const items = computed(() => upcomingAppointments(props.page.meeting ?? null, props.applications, now));
const prep = computed(() => props.page.preparation);
const lines = computed(() => sheetLines(prep.value));
const checked = computed(() => prep.value.questions.filter((q) => q.checked).length);
const prepOpen = ref(false);

// À noter, puis le dernier rendez-vous ORP noté.
const toNote = computed(() => meetingsToNote(props.page, now));
const last = computed<Meeting | null>(() => notedMeetings(props.page, now)[0] ?? null);
// Maquette du 8 novembre (D26) : la date dans l'icône calendrier de 48 px (CalendarDate), plus de carré coloré.
function cal(iso: string): { day: number; month: number } {
  const d = new Date(iso);
  return { day: d.getDate(), month: d.getMonth() + 1 };
}
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
        <div
          v-if="meetingItems?.length"
          class="rdv-more"
        >
          <MoreMenu
            :items="meetingItems"
            :inline="false"
            label="Plus d'actions sur le rendez-vous ORP"
            test-id="rdv-more"
          />
        </div>
        <div class="rdv-head">
          <CalendarDate
            class="rdv-date"
            v-bind="cal(item.at)"
            tone="orp"
          />
          <div class="rdv-body">
            <span class="rdv-kicker">{{ countdown(item.at, now) }}</span>
            <h3
              id="rdv-orp-titre"
              class="rdv-orp-title"
            >
              Rendez-vous ORP
            </h3>
            <span class="rdv-meta"><span class="visually-hidden">{{ dateText(item.at) }}, </span>{{ timeAndPlace(item.at, item.meeting.place) }}</span>
            <!-- « prête » seulement si la feuille a au moins une ligne ; sinon une pastille neutre. -->
            <span
              v-if="lines.length"
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
            <span
              v-else
              class="rdv-ready rdv-todo"
              data-test="rdv-todo"
            >Feuille à compléter</span>
          </div>
        </div>
        <!-- §10.7 (9 novembre) : ce qui préparait le rendez-vous passe dans une feuille du bas. Prompt du 9 novembre,
             PR 7 (maquettes RendezVous et RendezVousSombre) : une seule action dans la carte, le bouton plein qui ouvre
             la feuille (elle porte « Imprimer ou télécharger en PDF ») ; plus de « Voir ma feuille ». -->
        <button
          type="button"
          class="rdv-prep-open"
          aria-haspopup="dialog"
          data-test="rdv-prep-open"
          @click="prepOpen = true"
        >
          Préparer le rendez-vous
        </button>
      </article>
      <MeetingPrepSheet
        v-if="item.kind === 'orp'"
        :open="prepOpen"
        :at="item.at"
        :place="item.meeting.place"
        :lines="lines"
        :questions="prep.questions"
        :checked="checked"
        :pdf="sheetLink"
        @close="prepOpen = false"
        @toggle="(question, value) => emit('toggle', question, value)"
      />
      <article
        v-else
        class="rdv-card rdv-interview"
        :data-test="`rdv-interview-${item.application.id}`"
      >
        <CalendarDate
          class="rdv-date"
          v-bind="cal(item.at)"
          tone="blue"
        />
        <div class="rdv-body">
          <span class="rdv-kicker">Entretien d’embauche</span>
          <h3 class="rdv-interview-title">
            {{ item.application.job_title || "Poste non indiqué" }}
          </h3>
          <span class="rdv-meta"><span class="visually-hidden">{{ dateText(item.at) }}, </span>{{ [item.application.company, timeOfDay(item.at)].filter(Boolean).join(" · ") }}</span>
          <span
            v-if="interviewPlace(item.application)"
            class="rdv-meta rdv-place"
            data-test="rdv-place"
          >{{ interviewPlace(item.application) }}</span>
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

  <template v-else-if="part === 'past'">
    <!-- À noter (maquette du 7.11) : un rendez-vous ORP passé dont rien n'est noté ; « Noter » ouvre la feuille. -->
    <section
      v-if="toNote.length"
      class="rdv-part"
      aria-labelledby="rdv-a-noter"
      data-test="rdv-to-note"
    >
      <h2
        id="rdv-a-noter"
        class="rdv-title"
      >
        À noter<span>{{ plural(toNote.length, "rendez-vous", "rendez-vous") }}</span>
      </h2>
      <article
        v-for="item in toNote"
        :key="item.id"
        class="rdv-card rdv-last"
        :data-test="`rdv-to-note-${item.id}`"
      >
        <div class="rdv-last-head">
          <CalendarDate
            class="rdv-date"
            v-bind="cal(item.starts_at)"
            tone="orp"
          />
          <div class="rdv-body">
            <h3 class="rdv-last-title">
              {{ pastTitle(item.starts_at, now) }}
            </h3>
            <!-- Plus de « Pas encore noté » (lot 14) : le groupe « À noter » le dit déjà. -->
            <span class="rdv-meta">{{ `${dateText(item.starts_at)}, ${timeAndPlace(item.starts_at, item.place)}` }}</span>
          </div>
        </div>
        <button
          type="button"
          class="rdv-note"
          data-test="rdv-note"
          @click="emit('note', item.id)"
        >
          Noter ce qui a été convenu
        </button>
      </article>
    </section>
    <section
      v-if="last || page.past.length"
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
      <article
        v-if="last"
        class="rdv-card rdv-last"
      >
        <div class="rdv-last-head">
          <CalendarDate
            class="rdv-date"
            v-bind="cal(last.starts_at)"
            tone="past"
          />
          <div class="rdv-body">
            <h3 class="rdv-last-title">
              {{ pastTitle(last.starts_at, now) }}
            </h3>
            <span class="rdv-meta">Ce qui a été convenu</span>
          </div>
        </div>
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
        <button
          type="button"
          class="rdv-edit-note"
          :data-test="`rdv-edit-note-${last.id}`"
          @click="emit('note', last.id)"
        >
          Modifier
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
</template>

<style scoped>
/* Les valeurs de la maquette (RendezVous.dc.html), écrites avec les échelles (scales.test.ts) ; mises sur la grille de 4
   le 9 novembre (§2.9, audit-grille.js) : 14 → 16 entre le calendrier et le texte, 10 → 8 entre deux cartes, 6 → 8
   entre une icône et son mot ; « Préparer l'entretien » a 44 px de haut. 15 px = --font-small + 1 px. */
.rdv-part { min-width: 0; display: flex; flex-direction: column; gap: var(--space-2); }
.rdv-title {
  display: flex; align-items: baseline; gap: var(--space-2); margin: var(--space-2) var(--space-1) 0;
  font-size: var(--font-body); font-weight: var(--weight-bold); line-height: var(--leading-tight);
}
.rdv-title span { font-size: var(--label-caps); font-weight: var(--weight-semibold); color: var(--text-secondary); }
.rdv-card {
  display: flex; padding: var(--space-5); background: var(--surface); border: 1px solid var(--line);
  border-radius: var(--radius-card); color: var(--text);
}
.rdv-orp { position: relative; flex-direction: column; }
/* Le « ⋯ » (C6) : 44 px dans le coin en haut à droite ; le texte de la carte lui laisse la place. */
.rdv-more { position: absolute; top: var(--space-1); right: var(--space-1); z-index: 1; }
.rdv-more :deep(.more-button) { width: var(--target-min); height: var(--target-min); }
.rdv-orp .rdv-kicker, .rdv-orp-title { padding-right: var(--space-6); }
.rdv-head, .rdv-interview { gap: var(--space-4); }
.rdv-head { display: flex; }
.rdv-interview { position: relative; }
.rdv-date { flex: none; }
.rdv-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: var(--space-1); }
.rdv-kicker { font-size: var(--label-caps); font-weight: var(--weight-bold); color: var(--text-secondary); }
.rdv-orp-title { margin: 0; font-size: var(--font-title); line-height: 1.28em; font-weight: var(--weight-heavy); }
.rdv-interview-title { margin: 0; font-size: var(--font-body); line-height: 1.3125em; font-weight: var(--weight-bold); }
.rdv-meta { font-size: var(--font-small); color: var(--text-secondary); }
/* Un lien de visioconférence est un long mot : il passe à la ligne où il faut. */
.rdv-place { overflow-wrap: anywhere; }
.rdv-ready {
  align-self: flex-start; display: inline-flex; align-items: center; gap: var(--space-2);
  margin-top: var(--space-2); padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-pill); background: var(--success-soft); color: var(--success);
  font-size: var(--label-caps); font-weight: var(--weight-bold);
}
.rdv-ready svg { flex: none; }
.rdv-todo { background: var(--neutral-soft); color: var(--text-secondary); }
.rdv-agreed { font-size: calc(var(--font-small) + 1px); line-height: 1.4em; }
/* « Préparer le rendez-vous » (maquette RendezVous du 9 novembre) : le bouton plein de 52 px, 16 px sous l'en-tête. */
.rdv-prep-open {
  --rdv-btn: 52px;
  display: flex; align-items: center; justify-content: center; width: 100%; min-height: var(--rdv-btn);
  margin-top: var(--space-4); padding: 0 var(--space-4); border: 0; border-radius: var(--radius-pill);
  background: var(--primary); color: var(--on-primary); font: inherit; font-size: var(--font-body); font-weight: var(--weight-bold); cursor: pointer;
}
.rdv-prepare {
  display: flex; align-items: center; gap: var(--space-2); align-self: flex-start; min-height: var(--target-min);
  margin-top: 0; padding: 0; border: 0; border-radius: 0; background: transparent;
  color: var(--primary-text); font: inherit; font-size: calc(var(--font-small) + 1px); font-weight: var(--weight-bold); cursor: pointer;
}
/* La carte entière est la cible (maquette : un lien sur toute la carte). */
.rdv-prepare::after { content: ""; position: absolute; inset: 0; border-radius: var(--radius-card); }
.rdv-prepare:focus-visible { outline: none; }
.rdv-prepare:focus-visible::after { outline: 2px solid var(--primary-graphic); outline-offset: 2px; }
.rdv-last { flex-direction: column; gap: var(--space-3); }
.rdv-last-head { display: flex; align-items: center; gap: var(--space-4); }
.rdv-last-title { margin: 0; font-size: var(--font-body); font-weight: var(--weight-bold); line-height: var(--leading-normal); }
.rdv-agreed { display: grid; grid-template-columns: auto 1fr; gap: var(--space-2) var(--space-3); margin: 0; }
.rdv-agreed dt { color: var(--text-secondary); }
.rdv-agreed dd { margin: 0; }
/* « Noter ce qui a été convenu » : 48 px, en pilule bleu pâle (maquette du 7.11). */
.rdv-note {
  min-height: var(--btn-secondary); padding: 0 var(--space-4); border: 0; border-radius: var(--radius-pill); background: var(--primary-soft);
  color: var(--primary-text); font: inherit; font-size: calc(var(--font-small) + 1px); font-weight: var(--weight-bold); cursor: pointer;
}
.rdv-edit-note {
  align-self: flex-start; min-height: var(--target-min); padding: 0; border: 0; border-radius: 0; background: transparent;
  color: var(--primary-text); font: inherit; font-size: calc(var(--font-small) + 1px); font-weight: var(--weight-bold); cursor: pointer;
}
.rdv-log {
  align-items: center; justify-content: space-between; width: 100%; min-height: var(--btn-secondary);
  padding: 0 var(--space-4); font: inherit; text-align: left; cursor: pointer;
}
.rdv-log-title { flex: 1; min-width: 0; white-space: normal; font-size: calc(var(--font-small) + 1px); font-weight: var(--weight-bold); }
.rdv-log-count { flex: none; display: flex; align-items: center; gap: var(--space-2); font-size: var(--font-small); color: var(--text-secondary); }
</style>
