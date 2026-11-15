<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import LinkedArrow from "./LinkedArrow.vue";
import LinkedPin from "./LinkedPin.vue";
// Les styles des cartes (ListCard) servent aussi à la carte épinglée : chargés avec cet onglet.
import "./ListCard.vue";

import type { Application } from "../api/client";
import type { components } from "../api/schema";
import { dateInSentence, timeOfDay } from "../dates";
import {
  countdown,
  dateText,
  interviewFormat,
  interviewPlace,
  lastAgreed,
  meetingsToNote,
  notedMeetings,
  notedSummary,
  pastTitle,
  sheetLines,
  splitLine,
  timeAndPlace,
  upcomingAppointments,
} from "../rendezVous";
import AppIcon from "./AppIcon.vue";
import CalendarDate from "./CalendarDate.vue";
import LinkedDetail from "./LinkedDetail.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";
import OrpMeetingForm from "./OrpMeetingForm.vue";
import OrpOutcomeInline from "./OrpOutcomeInline.vue";

// Rendez-vous sur ordinateur, dès 1 024 px (maquette du 8 novembre, CandidaturesOrdinateurB, onglet Rendez-vous) :
// la liste de 480 px à gauche (À venir, À noter, Passés, en cartes de 104 px), le détail de ce qui est choisi à
// droite ; les deux colonnes défilent seules. Le choix est dans l'adresse (?rdv=orp, entretien-12, passe-3).
// Les dates sont dans l'icône calendrier (CalendarDate, D26). En tête de liste, « Aucun rendez-vous à venir » quand
// rien n'est prévu. Maquette du 14 novembre (§6) : plus de « + Nouveau rendez-vous » ici, le seul bouton d'ajout est
// le « + Ajouter » de l'en-tête (et « Prochain rendez-vous › Ajouter » dans une fiche ORP).
type Page = components["schemas"]["MeetingPage"];
type Question = components["schemas"]["QuestionIO"];
type Meeting = components["schemas"]["MeetingOut"];

const props = defineProps<{
  page: Page;
  applications: Application[];
  sheetLink: string;
  meetingItems: MoreMenuItem[];
  editing: boolean;
}>();
const emit = defineEmits<{
  toggle: [question: Question, checked: boolean];
  question: [text: string];
  sheet: [];
  prepare: [application: Application];
  note: [id: number];
  saved: [page: Page];
  cancel: [];
  // « orp » : depuis « Prochain rendez-vous » d'une fiche ORP, le panneau s'ouvre sur l'ORP.
  add: [kind?: "orp"];
}>();

const route = useRoute();
const router = useRouter();
const now = new Date();
const upcoming = computed(() => upcomingAppointments(props.page.meeting ?? null, props.applications, now));
const toNote = computed(() => meetingsToNote(props.page, now));
const noted = computed(() => notedMeetings(props.page, now));
const prep = computed(() => props.page.preparation);
const lines = computed(() => sheetLines(prep.value));
const checked = computed(() => prep.value.questions.filter((q) => q.checked).length);
const nextOrp = computed(() => upcoming.value.find((u) => u.kind === "orp") ?? null);

function pastKey(m: Meeting): string {
  return `passe-${m.id}`;
}
const keys = computed(() => [
  ...upcoming.value.map((u) => (u.kind === "orp" ? "orp" : `entretien-${u.application.id}`)),
  ...toNote.value.map(pastKey),
  ...noted.value.map(pastKey),
]);
// Sans rendez-vous ORP prévu : le premier rendez-vous à noter (lot 14), sinon le premier de la liste. PR 41 : plus de
// formulaire dans le détail, un nouveau rendez-vous se saisit dans le panneau « Nouveau rendez-vous ».
const selected = computed(() => {
  const asked = route.query.rdv;
  if (typeof asked === "string" && keys.value.includes(asked)) return asked;
  if (nextOrp.value) return "orp";
  return toNote.value[0] ? pastKey(toNote.value[0]) : (keys.value[0] ?? "");
});
function select(key: string): void {
  void router.replace({ query: { ...route.query, rdv: key } });
}
const selectedInterview = computed(() => {
  const key = selected.value;
  if (!key.startsWith("entretien-")) return null;
  const found = upcoming.value.find((u) => u.kind === "entretien" && `entretien-${u.application.id}` === key);
  return found?.kind === "entretien" ? found : null;
});
// Un rendez-vous passé, à noter ou noté : son détail est le formulaire de ce qui a été convenu (lot 14).
const selectedPast = computed(() => [...toNote.value, ...noted.value].find((m) => pastKey(m) === selected.value) ?? null);
// « Vendredi 30 octobre, 11 h · EPFL ».
function pastLine(m: Meeting): string {
  return `${dateText(m.starts_at)}, ${timeAndPlace(m.starts_at, m.place)}`;
}
const lastNoted = computed(() => noted.value[0] ?? null);
// La carte compacte épinglée (LinkedPin, §18 du 15 novembre ; Kevin, 15.11) : le titre de la carte choisie,
// « <Entreprise> · Sélection affichée » (l'ORP pour ses rendez-vous), la date dans l'icône calendrier de la liste, à 40 px,
// du même ton que la carte représentée (Kevin, 15.11), et un nom de bouton qui dit la date complète.
const pinned = computed(() => {
  const key = selected.value;
  const interview = selectedInterview.value;
  const past = selectedPast.value;
  const found =
    key === "orp" && nextOrp.value
      ? { title: "Rendez-vous ORP", name: "ORP", at: nextOrp.value.at, tone: "orp" as const }
      : interview
        ? { title: interview.application.job_title || "Poste non indiqué", name: interview.application.company || "Entreprise non indiquée", at: interview.at, tone: "blue" as const }
        : past
          ? { title: pastTitle(past.starts_at, now), name: "ORP", at: past.starts_at, tone: past.outcome_at ? ("past" as const) : ("orp" as const) }
          : null;
  if (!found) return null;
  return { ...found, label: `Revenir au rendez-vous du ${dateInSentence(found.at).slice(3)}, ${found.name}, dans la liste` };
});
// Le jour et le mois de l'icône calendrier.
function cal(iso: string): { day: number; month: number } {
  const d = new Date(iso);
  return { day: d.getDate(), month: d.getMonth() + 1 };
}

// « + Ajouter une question » ouvre un champ sur place.
const adding = ref(false);
const custom = ref("");
function addQuestion(): void {
  const text = custom.value.trim();
  if (!text) return;
  emit("question", text);
  custom.value = "";
}

// La liste reliée au détail (§14 du 15 novembre) : la hauteur des colonnes (--linked-top) et l'encoche sont
// calculées par LinkedDetail (useLinkedNotch).
const list = ref<HTMLElement | null>(null);
</script>

<template>
  <div
    class="rdv-grid"
    data-test="rdv-desktop"
  >
    <div
      ref="list"
      class="rdv-list linked-list"
      aria-label="Liste des rendez-vous"
      role="region"
    >
      <div
        v-if="!upcoming.length"
        class="rdv-list-empty"
        data-linked-tools
        data-test="rdv-list-empty"
      >
        <span class="rdv-empty-pill"><AppIcon name="calendar" />Aucun rendez-vous à venir</span>
      </div>
      <LinkedPin
        v-if="pinned"
        side="top"
        :title="pinned.title"
        :sub="pinned.name"
        :label="pinned.label"
      >
        <template #logo>
          <CalendarDate
            v-bind="cal(pinned.at)"
            :tone="pinned.tone"
            :size="40"
          />
        </template>
      </LinkedPin>
      <div class="linked-cards">
        <template v-if="upcoming.length">
          <h2 class="rdv-list-title">
            À venir<span>{{ upcoming.length }}</span>
          </h2>
          <button
            v-for="item in upcoming"
            :key="item.key"
            type="button"
            class="rdv-item list-card"
            :aria-current="selected === (item.kind === 'orp' ? 'orp' : `entretien-${item.application.id}`) ? 'true' : undefined"
            :data-test="item.kind === 'orp' ? 'rdv-item-orp' : `rdv-item-entretien-${item.application.id}`"
            @click="select(item.kind === 'orp' ? 'orp' : `entretien-${item.application.id}`)"
          >
            <CalendarDate
              v-bind="cal(item.at)"
              :tone="item.kind === 'orp' ? 'orp' : 'blue'"
              :size="44"
            />
            <span class="rdv-item-text">
              <span class="rdv-item-kicker">{{ item.kind === "orp" ? countdown(item.at, now) : "Entretien d’embauche" }}</span>
              <span class="rdv-item-title">{{ item.kind === "orp" ? "Rendez-vous ORP" : item.application.job_title || "Poste non indiqué" }}</span>
              <span class="rdv-item-sub"><span class="visually-hidden">{{ dateText(item.at) }}, </span>{{ item.kind === "orp" ? timeAndPlace(item.at, item.meeting.place) : [item.application.company, timeOfDay(item.at), interviewFormat(item.application), interviewPlace(item.application)].filter(Boolean).join(" · ") }}</span>
              <span class="rdv-chips">
                <span
                  v-if="item.kind === 'orp'"
                  :class="lines.length ? 'green' : ''"
                >{{ lines.length ? "Ta feuille est prête" : "Feuille à compléter" }}</span>
                <span
                  v-else
                  class="peach"
                >À préparer</span>
              </span>
            </span>
            <LinkedArrow v-if="selected === (item.kind === 'orp' ? 'orp' : `entretien-${item.application.id}`)" />
          </button>
        </template>
        <template v-if="toNote.length">
          <h2 class="rdv-list-title">
            À noter<span>{{ toNote.length }}</span>
          </h2>
          <button
            v-for="item in toNote"
            :key="item.id"
            type="button"
            class="rdv-item list-card"
            :aria-current="selected === pastKey(item) ? 'true' : undefined"
            :data-test="`rdv-to-note-${item.id}`"
            @click="select(pastKey(item))"
          >
            <CalendarDate
              v-bind="cal(item.starts_at)"
              tone="orp"
              :size="44"
            />
            <span class="rdv-item-text">
              <span class="rdv-item-title">{{ pastTitle(item.starts_at, now) }}</span>
              <span class="rdv-item-sub">{{ pastLine(item) }}</span>
            </span>
            <LinkedArrow v-if="selected === pastKey(item)" />
          </button>
        </template>
        <template v-if="noted.length">
          <h2 class="rdv-list-title">
            Passés<span>{{ noted.length }}</span>
          </h2>
          <button
            v-for="item in noted"
            :key="item.id"
            type="button"
            class="rdv-item list-card"
            :aria-current="selected === pastKey(item) ? 'true' : undefined"
            :data-test="`rdv-item-passe-${item.id}`"
            @click="select(pastKey(item))"
          >
            <CalendarDate
              v-bind="cal(item.starts_at)"
              tone="past"
              :size="44"
            />
            <span class="rdv-item-text">
              <span class="rdv-item-title">{{ pastTitle(item.starts_at, now) }}</span>
              <span class="rdv-item-sub">{{ notedSummary(item) }}</span>
            </span>
            <LinkedArrow v-if="selected === pastKey(item)" />
          </button>
        </template>
      </div>
      <LinkedPin
        v-if="pinned"
        side="bottom"
        :title="pinned.title"
        :sub="pinned.name"
        :label="pinned.label"
      >
        <template #logo>
          <CalendarDate
            v-bind="cal(pinned.at)"
            :tone="pinned.tone"
            :size="40"
          />
        </template>
      </LinkedPin>
    </div>

    <LinkedDetail
      v-if="selected || (editing && page.meeting)"
      class="rdv-detail"
      :list="list"
      data-test="rdv-detail"
    >
      <!-- Le rendez-vous ORP prévu : la feuille, ce que tu apportes, tes questions, ce qui a été convenu la dernière fois. -->
      <article
        v-if="selected === 'orp' && nextOrp?.kind === 'orp' && !editing"
        aria-labelledby="rdv-detail-title"
        class="rdv-detail-body"
        data-test="rdv-detail-orp"
      >
        <div class="rdv-detail-head rdv-card">
          <CalendarDate
            v-bind="cal(nextOrp.at)"
            tone="orp"
            :size="56"
          />
          <div>
            <span class="rdv-detail-kicker">{{ countdown(nextOrp.at, now) }}</span>
            <h1 id="rdv-detail-title">
              Rendez-vous ORP
            </h1>
            <p>{{ [`${dateText(nextOrp.at)}, ${timeOfDay(nextOrp.at)}`, nextOrp.meeting.place].filter(Boolean).join(" · ") }}</p>
          </div>
          <MoreMenu
            v-if="meetingItems.length"
            :items="meetingItems"
            label="Plus d’actions sur le rendez-vous ORP"
            test-id="rdv-more"
          />
        </div>
        <div class="rdv-detail-actions rdv-card">
          <button
            type="button"
            class="primary"
            data-test="rdv-sheet"
            @click="emit('sheet')"
          >
            Voir ma feuille
          </button>
          <a
            class="button-link secondary"
            :href="sheetLink"
            download
            data-test="rdv-pdf"
          >Télécharger en PDF</a>
          <span
            v-if="lines.length"
            class="rdv-detail-ready"
          ><AppIcon name="done" />Ta feuille est prête</span>
        </div>
        <section
          v-if="lines.length"
          aria-labelledby="rdv-brings"
          class="rdv-detail-section rdv-card"
        >
          <h2 id="rdv-brings">
            Ce que tu apportes
          </h2>
          <div class="rdv-brings">
            <div
              v-for="line in lines"
              :key="line.label"
            >
              <span>{{ line.label }}</span>
              <strong>{{ splitLine(line.text).main }}</strong>
              <small v-if="splitLine(line.text).sub">{{ splitLine(line.text).sub }}</small>
            </div>
          </div>
        </section>
        <section
          aria-labelledby="rdv-questions"
          class="rdv-questions-box rdv-card"
          data-test="rdv-questions"
        >
          <div>
            <span
              id="rdv-questions"
              class="rdv-questions-title"
            >
              Tes questions au conseiller
            </span>
            <span v-if="prep.questions.length">{{ checked }} {{ checked > 1 ? "cochées" : "cochée" }} sur {{ prep.questions.length }}</span>
          </div>
          <ul>
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
          <form
            v-if="adding"
            class="rdv-question-new"
            @submit.prevent="addQuestion"
          >
            <input
              v-model="custom"
              type="text"
              maxlength="300"
              aria-label="Une autre question"
              data-test="question-new"
            >
            <button
              type="submit"
              class="secondary"
              data-test="question-add"
            >
              Ajouter
            </button>
          </form>
          <button
            v-else
            type="button"
            class="link"
            data-test="rdv-question-open"
            @click="adding = true"
          >
            + Ajouter une question
          </button>
        </section>
        <section
          v-if="lastNoted"
          aria-labelledby="rdv-last"
          class="rdv-detail-section rdv-card"
        >
          <h2 id="rdv-last">
            Convenu la dernière fois
          </h2>
          <p data-test="rdv-last-agreed">
            {{ lastAgreed(lastNoted, now) }}
          </p>
        </section>
      </article>

      <!-- Un entretien d'embauche : où, quand, et la préparation. -->
      <article
        v-else-if="selectedInterview"
        aria-labelledby="rdv-detail-title"
        class="rdv-detail-body"
        data-test="rdv-detail-interview"
      >
        <div class="rdv-detail-head rdv-card">
          <CalendarDate
            v-bind="cal(selectedInterview.at)"
            :size="56"
          />
          <div>
            <span class="rdv-detail-kicker">Entretien d’embauche · {{ countdown(selectedInterview.at, now).toLowerCase() }}</span>
            <h1 id="rdv-detail-title">
              {{ selectedInterview.application.job_title || "Poste non indiqué" }}
            </h1>
            <p>{{ [selectedInterview.application.company, `${dateText(selectedInterview.at)}, ${timeOfDay(selectedInterview.at)}`].filter(Boolean).join(" · ") }}</p>
            <p
              v-if="interviewFormat(selectedInterview.application) || interviewPlace(selectedInterview.application)"
              data-test="rdv-interview-where"
            >
              {{ [interviewFormat(selectedInterview.application), interviewPlace(selectedInterview.application)].filter(Boolean).join(" · ") }}
            </p>
          </div>
        </div>
        <div class="rdv-detail-actions rdv-card">
          <button
            type="button"
            class="primary"
            data-test="rdv-prepare"
            @click="emit('prepare', selectedInterview.application)"
          >
            Préparer l’entretien
          </button>
        </div>
      </article>

      <!-- Un rendez-vous ORP passé, à noter ou noté (lot 14) : l'en-tête, puis ce qui a été convenu en deux colonnes. -->
      <article
        v-else-if="selectedPast"
        aria-labelledby="rdv-detail-title"
        class="rdv-detail-body rdv-detail-past"
        data-test="rdv-detail-past"
      >
        <div class="rdv-detail-head rdv-card">
          <CalendarDate
            v-bind="cal(selectedPast.starts_at)"
            :tone="selectedPast.outcome_at ? 'past' : 'orp'"
            :size="56"
          />
          <div>
            <h2 id="rdv-detail-title">
              {{ pastTitle(selectedPast.starts_at, now) }}
            </h2>
            <p>{{ pastLine(selectedPast) }}</p>
          </div>
        </div>
        <OrpOutcomeInline
          :key="selectedPast.id"
          class="rdv-card"
          :meeting="selectedPast"
          :target="page.target"
          :next="nextOrp?.kind === 'orp' ? page.meeting : null"
          @saved="emit('saved', $event)"
          @add="emit('add', 'orp')"
        />
      </article>

      <!-- Modifier le rendez-vous prévu. -->
      <OrpMeetingForm
        v-else-if="editing && page.meeting"
        :meeting="page.meeting"
        inline
        @saved="emit('saved', $event)"
        @cancel="emit('cancel')"
      />
    </LinkedDetail>
  </div>
</template>

<style>
/* Valeurs de la planche CandidaturesOrdinateurB, onglet Rendez-vous (maquette du 15 novembre, §14) : la même liaison
   qu'Offres et Envoyées (LinkedDetail, liste de 504 px, rail et pointe du §18). Cartes de 104 au minimum, marges 14/18,5, contour de 1,5
   (--card-line), coins de 18, écart 10 ; la carte choisie en 16 avec un contour de 2. Titres de groupe à 14/4/8. Le
   détail : une carte en-tête (24/28/24/32, coins de 24) puis chaque bloc en carte (marge de 32), 16 px entre elles. */
.rdv-grid {
  --rdv-2: 2px; --rdv-3: 3px; --rdv-14: 14px; --rdv-18-5: 18.5px; --rdv-17: 17px; --rdv-18: 18px; --rdv-21: 21px; --rdv-24: 24px; --rdv-28: 28px; --rdv-30: 30px;
  --rdv-15: 15px; --rdv-lh-text: 1.45;
  display: flex; align-items: stretch; gap: 0; height: calc(100dvh - var(--linked-top, 0px)); min-height: 20rem; box-sizing: border-box; padding-top: var(--space-1);
}
.rdv-list.linked-list > .linked-cards { display: flex; flex-direction: column; }
/* Carte épinglée : l'icône calendrier de la liste, à 40 px, à la place du logo. */
.linked-pin-card > .calendar-date { flex: none; }
.rdv-list-title { display: flex; align-items: baseline; gap: var(--space-2); margin: 0; padding: var(--rdv-14) var(--space-1) var(--space-2); font-size: var(--font-body); font-weight: var(--weight-bold); }
.rdv-list-title span { font-size: var(--label-caps); font-weight: var(--weight-semibold); color: var(--text-secondary); }
.rdv-item + .rdv-item { margin-top: calc(var(--space-2) + var(--rdv-2)); }
.rdv-item {
  flex: none; display: flex; align-items: center; gap: var(--space-2) var(--rdv-14); box-sizing: border-box; min-height: 104px; padding: var(--rdv-14) var(--rdv-18-5);
  background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--rdv-18); color: var(--text); font: inherit; text-align: left;
}
button.rdv-item { cursor: pointer; }
button.rdv-item:hover { border-color: var(--field-border); }
.rdv-item[aria-current="true"], button.rdv-item[aria-current="true"]:hover { max-width: none; border-color: var(--primary-graphic); }
.rdv-item-text { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: var(--rdv-2); }
.rdv-item-kicker { font-size: var(--font-caption); font-weight: var(--weight-bold); color: var(--text-secondary); }
.rdv-item-title, .rdv-item-sub { overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.rdv-item-title { font-size: var(--font-body); line-height: var(--rdv-21); font-weight: var(--weight-bold); }
.rdv-item-sub { font-size: var(--font-small); color: var(--text-secondary); }
.rdv-chips { display: flex; gap: var(--space-1); margin-top: var(--rdv-3); overflow: hidden; }
.rdv-chips > * {
  flex: none; padding: var(--rdv-3) var(--space-2); border-radius: var(--radius-sm); white-space: nowrap; font-size: var(--font-caption);
  font-weight: var(--weight-semibold); background: color-mix(in srgb, var(--surface-muted) 70%, var(--surface)); color: var(--text-tertiary);
}
.rdv-chips > .peach { background: var(--peach-soft); color: var(--peach-text); }
.rdv-chips > .green { background: var(--success-soft); color: var(--success); }
/* « Aucun rendez-vous à venir » : la pastille en haut de la liste, alignée sur les cartes, un trait dessous (480 px). */
.linked-list > .rdv-list-empty { display: flex; align-items: center; padding: calc(var(--linked-room) + var(--space-1)) calc(var(--linked-gap) + var(--space-1)) calc(var(--space-2) + var(--rdv-2) - var(--linked-room)) calc(var(--linked-bar) + var(--space-1)); }
.rdv-list-empty::after { content: ""; position: absolute; left: var(--linked-bar); right: var(--linked-gap); bottom: calc(-1 * var(--linked-room)); border-bottom: 1px solid var(--line); }
.rdv-list-empty + .rdv-list-title { margin-top: calc(var(--space-1) + var(--rdv-2)); }
.rdv-empty-pill {
  display: inline-flex; align-items: center; gap: var(--space-1); padding: var(--space-1) var(--space-3); border-radius: var(--radius-pill); white-space: nowrap;
  background: var(--primary-soft); color: var(--primary-text); font-size: var(--font-small); line-height: var(--space-5); font-weight: var(--weight-semibold);
}
.rdv-empty-pill svg { width: var(--space-4); height: var(--space-4); }
.rdv-detail-body { flex: none; display: flex; flex-direction: column; gap: var(--space-4); }
.rdv-card { box-sizing: border-box; padding: var(--space-6) var(--space-8); background: var(--surface); border: 1px solid var(--line); border-radius: var(--rdv-24); }
.rdv-detail-head.rdv-card { flex: none; display: flex; align-items: flex-start; gap: var(--space-4); margin-top: var(--space-6); padding: var(--space-6) var(--rdv-28) var(--space-6) var(--space-8); }
.rdv-detail-head > div:not(.more-menu) { flex: 1; min-width: 0; }
.rdv-detail-head .more-button { min-width: var(--target-min); min-height: var(--target-min); }
.rdv-detail-kicker { display: block; margin-bottom: var(--space-1); font-size: var(--font-small); font-weight: var(--weight-bold); color: var(--text-secondary); }
.rdv-detail-head :is(h1, h2) { margin: 0; font-size: var(--rdv-24); line-height: var(--rdv-30); font-weight: var(--weight-heavy); color: var(--text); }
.rdv-detail-head p { margin: var(--space-1) 0 0; font-size: var(--font-label); color: var(--text-secondary); overflow-wrap: anywhere; }
.rdv-detail-actions { flex: none; display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-2); }
.rdv-detail-actions :is(button, a) { min-height: var(--btn-secondary); padding: 0 var(--space-5); border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
.rdv-detail-ready { display: inline-flex; align-items: center; gap: var(--space-1); margin-left: var(--space-1); font-size: var(--font-small); font-weight: var(--weight-bold); color: var(--success); }
.rdv-detail-section { flex: none; display: flex; flex-direction: column; gap: var(--space-3); }
.rdv-detail-section h2, .rdv-questions-box .rdv-questions-title { margin: 0; font-size: var(--rdv-18); font-weight: var(--weight-bold); }
.rdv-detail-section p { margin: 0; font-size: var(--rdv-15); line-height: var(--rdv-lh-text); color: var(--text-tertiary); }
.rdv-brings { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-3); }
.rdv-brings > div { display: flex; flex-direction: column; gap: var(--space-1); padding: var(--space-4); border: 1px solid var(--line); border-radius: var(--space-4); }
.rdv-brings span { font-size: var(--label-caps); font-weight: var(--weight-bold); color: var(--text-secondary); }
.rdv-brings strong { font-size: var(--rdv-17); line-height: var(--leading-tight); }
.rdv-brings small { font-size: var(--font-small); color: var(--text-secondary); }
.rdv-questions-box { flex: none; display: flex; flex-direction: column; gap: var(--space-1); }
.rdv-questions-box > div { display: flex; align-items: baseline; justify-content: space-between; gap: var(--space-3); }
.rdv-questions-box > div > span { font-size: var(--font-small); color: var(--text-secondary); }
.rdv-questions-box ul { margin: 0; padding: 0; list-style: none; }
.rdv-questions-box label { display: flex; align-items: flex-start; gap: var(--space-3); min-height: var(--target-min); padding: var(--space-2) 0; cursor: pointer; font-size: var(--rdv-15); }
.rdv-questions-box input[type="checkbox"] { flex: none; width: 22px; height: 22px; margin: 0; accent-color: var(--primary); }
.rdv-questions-box > .link { align-self: flex-start; min-height: var(--target-min); padding: 0 var(--space-1); font-weight: var(--weight-bold); }
.rdv-question-new { display: flex; gap: var(--space-2); }
.rdv-question-new input { flex: 1; min-width: 0; }
/* « Ce qui a été convenu » : la carte de contenu (4/32/0), sans le trait qui l'ouvrait ; « Enregistrer » collé en bas. */
.outcome-inline.rdv-card { flex: none; margin: 0; padding: var(--space-1) var(--space-8) 0; border: 1px solid var(--line); }
.outcome-inline.rdv-card > .detail-overline { padding-top: var(--space-6); }
.outcome-inline.rdv-card .outcome-inline-actions { border-bottom-left-radius: var(--rdv-24); border-bottom-right-radius: var(--rdv-24); }
.rdv-detail .rdv-form { max-width: 560px; margin-top: var(--space-6); }
</style>
