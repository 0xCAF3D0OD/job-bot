<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import type { Application } from "../api/client";
import type { components } from "../api/schema";
import { timeOfDay } from "../dates";
import { plural } from "../format";
import {
  agreedLines,
  countdown,
  dateText,
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
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";
import OrpMeetingForm from "./OrpMeetingForm.vue";

// Rendez-vous sur ordinateur, dès 1 024 px (maquette du 8 novembre, CandidaturesOrdinateurB, onglet Rendez-vous) :
// la liste de 480 px à gauche (À venir, À noter, Passés, en cartes de 104 px), le détail de ce qui est choisi à
// droite ; les deux colonnes défilent seules. Le choix est dans l'adresse (?rdv=orp, entretien-12, passe-3).
// Les dates sont dans l'icône calendrier (CalendarDate, D26). Sans rendez-vous ORP prévu, une ligne de texte et
// « Ajouter » en tête de liste, sans carte (D22) ; le détail montre le formulaire.
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
  ...noted.value.map(pastKey),
]);
// Sans rendez-vous ORP prévu, « nouveau » (le formulaire) vient d'abord.
const selected = computed(() => {
  const asked = route.query.rdv;
  if (typeof asked === "string" && (keys.value.includes(asked) || asked === "nouveau")) return asked;
  return nextOrp.value ? "orp" : "nouveau";
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
const selectedPast = computed(() => noted.value.find((m) => pastKey(m) === selected.value) ?? null);
const lastNoted = computed(() => noted.value[0] ?? null);
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

// Les deux colonnes défilent seules, sous l'en-tête : la hauteur se mesure à l'arrivée et au redimensionnement.
const grid = ref<HTMLElement | null>(null);
const top = ref(0);
function measure(): void {
  top.value = Math.max(0, Math.round((grid.value?.getBoundingClientRect().top ?? 0) + window.scrollY));
}
onMounted(() => {
  void nextTick(measure);
  window.addEventListener("resize", measure);
});
onUnmounted(() => window.removeEventListener("resize", measure));
watch(() => props.page, () => void nextTick(measure));
</script>

<template>
  <div
    ref="grid"
    class="rdv-grid"
    :style="{ '--rdv-top': `${top}px` }"
    data-test="rdv-desktop"
  >
    <div
      class="rdv-list"
      aria-label="Liste des rendez-vous"
      role="region"
    >
      <div
        v-if="!nextOrp"
        class="rdv-list-empty"
        data-test="rdv-list-empty"
      >
        <div>
          <strong>Aucun rendez-vous à venir</strong>
          <span>Ajoute le prochain : jobA1 prépare ta feuille la veille.</span>
        </div>
        <button
          type="button"
          class="secondary action-2"
          data-test="rdv-add"
          :aria-expanded="selected === 'nouveau'"
          @click="select('nouveau')"
        >
          Ajouter
        </button>
      </div>
      <template v-if="upcoming.length">
        <h2 class="rdv-list-title">
          À venir<span>{{ plural(upcoming.length, "rendez-vous", "rendez-vous") }}</span>
        </h2>
        <button
          v-for="item in upcoming"
          :key="item.key"
          type="button"
          class="rdv-item"
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
            <span class="rdv-item-sub"><span class="visually-hidden">{{ dateText(item.at) }}, </span>{{ item.kind === "orp" ? timeAndPlace(item.at, item.meeting.place) : [item.application.company, timeOfDay(item.at), interviewPlace(item.application)].filter(Boolean).join(" · ") }}</span>
            <span class="list-card-chips">
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
        </button>
      </template>
      <template v-if="toNote.length">
        <h2 class="rdv-list-title">
          À noter<span>{{ plural(toNote.length, "rendez-vous", "rendez-vous") }}</span>
        </h2>
        <div
          v-for="item in toNote"
          :key="item.id"
          class="rdv-item"
          :data-test="`rdv-to-note-${item.id}`"
        >
          <CalendarDate
            v-bind="cal(item.starts_at)"
            tone="orp"
            :size="44"
          />
          <span class="rdv-item-text">
            <span class="rdv-item-title">{{ pastTitle(item.starts_at, now) }}</span>
            <span class="rdv-item-sub">Pas encore noté · 1 minute</span>
          </span>
          <button
            type="button"
            class="rdv-item-note"
            data-test="rdv-note"
            @click="emit('note', item.id)"
          >
            Noter<span class="visually-hidden"> le {{ pastTitle(item.starts_at, now) }}</span>
          </button>
        </div>
      </template>
      <template v-if="noted.length">
        <h2 class="rdv-list-title">
          Passés<span>{{ noted.length }}</span>
        </h2>
        <button
          v-for="item in noted"
          :key="item.id"
          type="button"
          class="rdv-item"
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
            <span class="list-card-chips"><span class="green">Noté</span></span>
          </span>
        </button>
      </template>
    </div>

    <div
      class="rdv-detail"
      data-test="rdv-detail"
    >
      <!-- Le rendez-vous ORP prévu : la feuille, ce que tu apportes, tes questions, ce qui a été convenu la dernière fois. -->
      <article
        v-if="selected === 'orp' && nextOrp?.kind === 'orp' && !editing"
        aria-labelledby="rdv-detail-title"
        class="rdv-detail-body"
        data-test="rdv-detail-orp"
      >
        <div class="rdv-detail-head">
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
            label="Plus d'actions sur le rendez-vous ORP"
            test-id="rdv-more"
          />
        </div>
        <div class="rdv-detail-actions">
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
          class="rdv-detail-section"
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
          class="rdv-questions-box"
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
          class="rdv-detail-section"
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
        <div class="rdv-detail-head">
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
            <p v-if="interviewPlace(selectedInterview.application)">
              {{ interviewPlace(selectedInterview.application) }}
            </p>
          </div>
        </div>
        <div class="rdv-detail-actions">
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

      <!-- Un rendez-vous ORP noté : ce qui a été convenu, modifiable. -->
      <article
        v-else-if="selectedPast"
        aria-labelledby="rdv-detail-title"
        class="rdv-detail-body"
        data-test="rdv-detail-past"
      >
        <div class="rdv-detail-head">
          <CalendarDate
            v-bind="cal(selectedPast.starts_at)"
            tone="past"
            :size="56"
          />
          <div>
            <span class="rdv-detail-kicker">Noté</span>
            <h1 id="rdv-detail-title">
              {{ pastTitle(selectedPast.starts_at, now) }}
            </h1>
            <p v-if="selectedPast.place">
              {{ selectedPast.place }}
            </p>
          </div>
        </div>
        <dl class="rdv-detail-agreed">
          <template
            v-for="line in agreedLines(selectedPast)"
            :key="line.label"
          >
            <dt>{{ line.label }}</dt>
            <dd>{{ line.text }}</dd>
          </template>
          <template v-if="selectedPast.note">
            <dt>À retenir</dt>
            <dd>{{ selectedPast.note }}</dd>
          </template>
        </dl>
        <div class="rdv-detail-actions">
          <button
            type="button"
            class="secondary"
            :data-test="`rdv-edit-note-${selectedPast.id}`"
            @click="emit('note', selectedPast.id)"
          >
            Modifier ce qui a été convenu
          </button>
        </div>
      </article>

      <!-- Modifier le rendez-vous prévu, ou en ajouter un. -->
      <OrpMeetingForm
        v-else-if="editing && page.meeting"
        :meeting="page.meeting"
        inline
        @saved="emit('saved', $event)"
        @cancel="emit('cancel')"
      />
      <OrpMeetingForm
        v-else
        inline
        :can-cancel="keys.length > 0"
        @saved="emit('saved', $event)"
        @cancel="select(keys[0] ?? 'nouveau')"
      />
    </div>
  </div>
</template>

<style>
/* Valeurs de la maquette (CandidaturesOrdinateurB, onglet Rendez-vous) : liste de 480, écart 24 ; cartes de 104 aux
   marges 14/16, écart 14 ; icône calendrier de 44 (56 dans le détail) ; détail blanc aux coins de 24, marges 24/28. */
.rdv-grid {
  --rdv-3: 3px; --rdv-11: 11px; --rdv-14: 14px; --rdv-17: 17px; --rdv-18: 18px; --rdv-22: 22px; --rdv-26: 26px; --rdv-28: 28px; --rdv-15: 15px; --rdv-lh-title: 1.23; --rdv-lh-text: 1.45;
  display: flex; gap: var(--space-6); height: calc(100dvh - var(--rdv-top, 0px) - var(--space-6)); min-height: 20rem;
}
.rdv-list { flex: none; width: 480px; box-sizing: border-box; overflow-y: auto; display: flex; flex-direction: column; gap: var(--space-2); padding: 0 var(--space-2) var(--space-4) 0; }
.rdv-list-title { display: flex; align-items: baseline; gap: var(--space-2); margin: var(--space-2) var(--space-1) var(--space-1); font-size: var(--font-body); font-weight: var(--weight-bold); }
.rdv-list-title span { font-size: var(--label-caps); font-weight: var(--weight-semibold); color: var(--text-secondary); }
.rdv-item {
  flex: none; display: flex; align-items: center; gap: var(--rdv-14); box-sizing: border-box; height: 104px; width: 100%; padding: var(--rdv-14) var(--space-4);
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-card); color: var(--text); font: inherit; text-align: left;
}
button.rdv-item { cursor: pointer; }
button.rdv-item:hover { border-color: var(--field-border); }
.rdv-item[aria-current="true"] {
  padding: calc(var(--rdv-14) - 1px) calc(var(--space-4) - 1px); border: 2px solid var(--primary-graphic);
  background: color-mix(in srgb, var(--primary-soft) 45%, var(--surface));
}
.rdv-item-text { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: var(--rdv-3); }
.rdv-item-kicker { font-size: var(--font-caption); font-weight: var(--weight-bold); color: var(--text-secondary); }
.rdv-item-title, .rdv-item-sub { overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.rdv-item-title { font-size: var(--font-body); font-weight: var(--weight-bold); }
.rdv-item-sub { font-size: var(--font-small); color: var(--text-secondary); }
.rdv-item .list-card-chips { display: flex; gap: var(--space-1); margin-top: var(--rdv-3); overflow: hidden; }
/* Les puces de ListCard (son CSS n'est pas chargé sur cette page). */
.rdv-item .list-card-chips > * {
  flex: none; padding: var(--rdv-3) var(--space-2); border-radius: var(--radius-sm); white-space: nowrap; font-size: var(--font-caption);
  font-weight: var(--weight-semibold); background: color-mix(in srgb, var(--surface-muted) 70%, var(--surface)); color: var(--text-tertiary);
}
.rdv-item .list-card-chips > .peach { background: var(--peach-soft); color: var(--peach-text); }
.rdv-item .list-card-chips > .green { background: var(--success-soft); color: var(--success); }
.rdv-item-note {
  flex: none; min-height: var(--target-min); padding: 0 var(--space-4); border: 0; border-radius: var(--radius-pill);
  background: var(--primary-soft); color: var(--primary-text); font-size: var(--font-small); font-weight: var(--weight-bold);
}
.rdv-detail {
  flex: 1; min-width: 0; overflow-y: auto; box-sizing: border-box; padding: var(--space-6) var(--rdv-28);
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--space-6);
}
.rdv-detail-body { display: flex; flex-direction: column; gap: var(--rdv-22); }
.rdv-detail-head { display: flex; align-items: flex-start; gap: var(--rdv-18); }
.rdv-detail-head > div:not(.more-menu) { flex: 1; min-width: 0; }
.rdv-detail-kicker { font-size: var(--font-small); font-weight: var(--weight-bold); color: var(--text-secondary); }
.rdv-detail-head h1 { margin: var(--space-1) 0 0; font-size: var(--rdv-26); line-height: var(--rdv-lh-title); font-weight: var(--weight-heavy); }
.rdv-detail-head p { margin: var(--space-1) 0 0; font-size: var(--font-body); color: var(--text-secondary); overflow-wrap: anywhere; }
.rdv-detail-actions { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-2); }
.rdv-detail-actions :is(button, a) { min-height: var(--btn-secondary); padding: 0 var(--space-5); border-radius: var(--radius-pill); font-size: var(--font-body); font-weight: var(--weight-bold); }
.rdv-detail-ready { display: inline-flex; align-items: center; gap: var(--space-1); margin-left: var(--space-1); font-size: var(--font-small); font-weight: var(--weight-bold); color: var(--success); }
.rdv-detail-section { display: flex; flex-direction: column; gap: var(--space-3); }
.rdv-detail-section h2, .rdv-questions-box .rdv-questions-title { margin: 0; font-size: var(--rdv-18); font-weight: var(--weight-bold); }
.rdv-detail-section p { margin: 0; font-size: var(--rdv-15); line-height: var(--rdv-lh-text); color: var(--text-tertiary); }
.rdv-brings { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-3); }
.rdv-brings > div { display: flex; flex-direction: column; gap: var(--space-1); padding: var(--space-4); border: 1px solid var(--line); border-radius: var(--space-4); }
.rdv-brings span { font-size: var(--label-caps); font-weight: var(--weight-bold); color: var(--text-secondary); }
.rdv-brings strong { font-size: var(--rdv-17); line-height: var(--leading-tight); }
.rdv-brings small { font-size: var(--font-small); color: var(--text-secondary); }
.rdv-questions-box { display: flex; flex-direction: column; gap: var(--space-1); padding: var(--space-4) var(--space-5); border: 1px solid var(--line); border-radius: var(--space-4); }
.rdv-questions-box > div { display: flex; align-items: baseline; justify-content: space-between; gap: var(--space-3); }
.rdv-questions-box > div > span { font-size: var(--font-small); color: var(--text-secondary); }
.rdv-questions-box ul { margin: 0; padding: 0; list-style: none; }
.rdv-questions-box label { display: flex; align-items: flex-start; gap: var(--space-3); min-height: var(--target-min); padding: var(--space-2) 0; cursor: pointer; font-size: var(--rdv-15); }
.rdv-questions-box input[type="checkbox"] { flex: none; width: 22px; height: 22px; margin: 0; accent-color: var(--primary); }
.rdv-questions-box > .link { align-self: flex-start; min-height: var(--target-min); padding: 0 var(--space-1); font-weight: var(--weight-bold); }
.rdv-question-new { display: flex; gap: var(--space-2); }
.rdv-question-new input { flex: 1; min-width: 0; }
.rdv-detail-agreed { display: grid; grid-template-columns: auto 1fr; gap: var(--space-2) var(--space-4); margin: 0; font-size: var(--rdv-15); }
.rdv-detail-agreed dt { color: var(--text-secondary); }
.rdv-detail-agreed dd { margin: 0; }
.rdv-detail .rdv-form { max-width: 560px; }
/* Aucun rendez-vous à venir : une ligne de texte et « Ajouter » (44 px, en pilule), un trait dessous, sans carte. */
.rdv-list-empty { flex: none; display: flex; align-items: center; gap: var(--rdv-14); padding: var(--space-1) var(--space-1) var(--space-2); border-bottom: 1px solid var(--line); }
.rdv-list-empty > div { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.rdv-list-empty strong { font-size: var(--rdv-15); }
.rdv-list-empty span { font-size: var(--font-caption); color: var(--text-secondary); }
.rdv-list-empty button { flex: none; height: 44px; padding: 0 var(--rdv-18); border-radius: var(--radius-pill); font-size: var(--rdv-15); font-weight: var(--weight-semibold); }
</style>
