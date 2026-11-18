<script setup lang="ts">
import { computed, nextTick, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import LinkedArrow from "./LinkedArrow.vue";
import LinkedPin from "./LinkedPin.vue";
// Les styles des cartes (ListCard) servent aussi à la carte épinglée : chargés avec cet onglet.
import "./ListCard.vue";

import type { Application } from "../api/client";
import type { components } from "../api/schema";
import { dateInSentence, inDays, timeOfDay } from "../dates";
import { plural } from "../format";
import { offerUndo } from "../composables/useUndo";
import {
  checkedCount,
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
  timeAndPlace,
  upcomingAppointments,
  upcomingLabel,
  upcomingWhen,
  upcomingWhere,
} from "../rendezVous";
import AppIcon from "./AppIcon.vue";
import CalendarDate from "./CalendarDate.vue";
import EmptyState from "./EmptyState.vue";
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
  // Enregistre la liste entière des questions (ajout, modification, suppression) ; vrai si le serveur l'a gardée.
  saveQuestions: (questions: Question[]) => Promise<boolean>;
  // Sous « Ton nom sur la feuille » : le nom et l'office enregistrés (vide : la ligne n'a que son titre).
  nameLine?: string;
}>();
const emit = defineEmits<{
  toggle: [question: Question, checked: boolean];
  sheet: [];
  // « Ton nom sur la feuille » : la feuille s'ouvre sur la case du nom (pas de planche FeuilleNom sur ordinateur).
  name: [];
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
// Le rendez-vous de l'adresse (?rdv=). Rien d'ouvert à l'arrivée (§36 du 16 novembre, décision de Kevin du 16.11) :
// « Choisis un rendez-vous » à droite. PR 41 : un nouveau rendez-vous se saisit dans le panneau « Nouveau rendez-vous ».
const selected = computed(() => {
  const asked = route.query.rdv;
  return typeof asked === "string" && keys.value.includes(asked) ? asked : "";
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

// « Tes questions au conseiller » (planches RendezVousOrdinateurOuvert et PreparerRendezVousQuestion, §72 ; décision de
// Kevin du 18.11) : « + Ajouter une question » ouvre un champ dans la carte, Entrée ajoute, Échap annule, un champ vide
// se ferme sans rien ajouter ; « Enregistré » est annoncé. Le ⋯ de chaque question : Modifier (le même champ, sur la
// ligne) ou Supprimer, avec le bandeau « Annuler » (la liste n'est envoyée qu'à la fin du bandeau).
const adding = ref(false);
const custom = ref("");
const newField = ref<HTMLTextAreaElement | null>(null);
const editingKey = ref<string | null>(null);
const draft = ref("");
const hidden = ref<Set<string>>(new Set());
const savedNote = ref("");
const shownQuestions = computed(() => prep.value.questions.filter((q) => !hidden.value.has(q.key)));
const sheetLine = computed(() => {
  const month = prep.value.months?.at(-1);
  return [month ? plural(month.count, "recherche", "recherches") : "", plural(checked.value, "question", "questions")].filter(Boolean).join(", ");
});
function saved(ok: boolean): void {
  savedNote.value = ok ? "Enregistré" : "";
}
async function openField(): Promise<void> {
  editingKey.value = null;
  adding.value = true;
  await nextTick();
  newField.value?.focus();
}
function cancelField(): void {
  adding.value = false;
  custom.value = "";
  editingKey.value = null;
  draft.value = "";
}
async function addQuestion(): Promise<void> {
  const text = custom.value.trim();
  if (!text) {
    cancelField();
    return;
  }
  const ok = await props.saveQuestions([...prep.value.questions, { key: `custom:${Date.now()}`, text, checked: false }]);
  saved(ok);
  if (ok) cancelField();
}
async function saveEdit(question: Question): Promise<void> {
  const text = draft.value.trim();
  if (!text || text === question.text) {
    cancelField();
    return;
  }
  const ok = await props.saveQuestions(prep.value.questions.map((q) => (q.key === question.key ? { ...q, text } : q)));
  saved(ok);
  if (ok) cancelField();
}
function removeQuestion(question: Question): void {
  hidden.value = new Set([...hidden.value, question.key]);
  const unhide = (): void => {
    const next = new Set(hidden.value);
    next.delete(question.key);
    hidden.value = next;
  };
  void offerUndo({
    message: "Question supprimée",
    commit: async () => {
      const ok = await props.saveQuestions(prep.value.questions.filter((q) => q.key !== question.key));
      if (ok) unhide();
      return ok;
    },
    restore: unhide,
  });
}
// Pas de « ? » ni de « » » seul en début de ligne : l'espace qui les précède devient insécable.
function tidy(text: string): string {
  return text.replace(/ ([?!:;»])/g, "\u00a0$1").replace(/« /g, "«\u00a0");
}
function questionItems(question: Question): MoreMenuItem[] {
  return [
    {
      label: "Modifier",
      test: `rdv-question-edit-${question.key}`,
      icon: "pencil",
      run: () => {
        adding.value = false;
        editingKey.value = question.key;
        draft.value = question.text;
        void nextTick(() => document.querySelector<HTMLTextAreaElement>("[data-test=question-edit]")?.focus());
      },
    },
    { label: "Supprimer", test: `rdv-question-delete-${question.key}`, icon: "trash", danger: true, run: () => removeQuestion(question) },
  ];
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
            :aria-label="upcomingLabel(item, item.kind === 'orp' ? (lines.length ? 'Feuille prête' : 'Feuille à compléter') : 'À préparer', now)"
            @click="select(item.kind === 'orp' ? 'orp' : `entretien-${item.application.id}`)"
          >
            <CalendarDate
              v-bind="cal(item.at)"
              :tone="item.kind === 'orp' ? 'orp' : 'blue'"
              :size="44"
            />
            <!-- Deux lignes au plus (demande de Kevin du 16.11, planche RendezVous) : le titre et sa pastille, puis
                 « 9 h · dans 3 jours · lieu ». -->
            <span class="rdv-item-text">
              <span class="rdv-item-line">
                <span class="rdv-item-title">{{ item.kind === "orp" ? "Rendez-vous ORP" : item.application.job_title || "Poste non indiqué" }}</span>
                <span
                  v-if="item.kind === 'orp'"
                  :class="['rdv-chip', lines.length ? 'green' : '']"
                >{{ lines.length ? "Feuille prête" : "Feuille à compléter" }}</span>
                <span
                  v-else
                  class="rdv-chip peach"
                >À préparer</span>
              </span>
              <span class="rdv-item-sub rdv-when"><span>{{ upcomingWhen(item, now) }}</span><span v-if="upcomingWhere(item)">&nbsp;· {{ upcomingWhere(item) }}</span></span>
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
      <!-- Le rendez-vous ORP prévu, refait d'après la planche RendezVousOrdinateurOuvert (§72, 18.11) : la tuile date, le
           titre, « Voir la feuille » ; « Où tu en es » ; « Tes questions au conseiller » (⋯ par question) ; « La feuille ».
           Gardés de main (absents de la planche) : le ⋯ du rendez-vous (Modifier, Supprimer) et « Convenu la dernière fois ». -->
      <article
        v-if="selected === 'orp' && nextOrp?.kind === 'orp' && !editing"
        aria-labelledby="rdv-detail-title"
        class="rdv-open"
        data-test="rdv-detail-orp"
      >
        <div class="rdv-open-head">
          <CalendarDate
            v-bind="cal(nextOrp.at)"
            tone="orp"
            :size="56"
          />
          <div class="rdv-open-head-text">
            <h2 id="rdv-detail-title">
              Rendez-vous ORP
            </h2>
            <p data-test="rdv-open-when">
              {{ [`${dateText(nextOrp.at)}, ${timeOfDay(nextOrp.at)}`, nextOrp.meeting.place, inDays(nextOrp.at, now).replace(/ /g, "\u00a0")].filter(Boolean).join(" · ") }}
            </p>
          </div>
          <button
            type="button"
            class="primary rdv-open-sheet"
            data-test="rdv-sheet"
            @click="emit('sheet')"
          >
            Voir la feuille
          </button>
          <MoreMenu
            v-if="meetingItems.length"
            :items="meetingItems"
            label="Plus d’actions sur le rendez-vous ORP"
            test-id="rdv-more"
          />
        </div>
        <section
          v-if="lines.length"
          aria-labelledby="rdv-brings"
        >
          <h3
            id="rdv-brings"
            class="rdv-open-title"
          >
            Où tu en es
          </h3>
          <ul
            class="rdv-open-card"
            data-test="rdv-open-lines"
          >
            <li
              v-for="line in lines"
              :key="line.label"
              class="rdv-open-line"
            >
              <span class="rdv-open-key">{{ line.label }}</span>
              <span class="rdv-open-value">{{ line.text }}</span>
            </li>
          </ul>
        </section>
        <section
          aria-labelledby="rdv-questions"
          data-test="rdv-questions"
        >
          <h3
            id="rdv-questions"
            class="rdv-open-title"
          >
            Tes questions au conseiller · {{ checkedCount(checked) }}
          </h3>
          <ul class="rdv-open-card">
            <li
              v-for="question in shownQuestions"
              :key="question.key"
              class="rdv-open-question"
            >
              <form
                v-if="editingKey === question.key"
                class="rdv-open-field"
                @submit.prevent="saveEdit(question)"
              >
                <span
                  class="rdv-open-box"
                  :class="{ on: question.checked }"
                  aria-hidden="true"
                />
                <div>
                  <textarea
                    v-model="draft"
                    rows="2"
                    maxlength="300"
                    aria-label="Modifier la question"
                    data-test="question-edit"
                    @keydown.enter.exact.prevent="saveEdit(question)"
                    @keydown.esc.prevent.stop="cancelField"
                  />
                  <p class="rdv-open-help">
                    <span>Entrée pour enregistrer · Échap pour annuler</span>
                  </p>
                </div>
              </form>
              <template v-else>
                <button
                  type="button"
                  role="checkbox"
                  class="rdv-open-check"
                  :aria-checked="question.checked ? 'true' : 'false'"
                  :data-test="`rdv-question-${question.key}`"
                  @click="emit('toggle', question, !question.checked)"
                >
                  <span
                    class="rdv-open-box"
                    :class="{ on: question.checked }"
                    aria-hidden="true"
                  ><AppIcon
                    v-if="question.checked"
                    name="done"
                  /></span>
                  <span class="rdv-open-question-text">{{ tidy(question.text) }}</span>
                </button>
                <MoreMenu
                  :items="questionItems(question)"
                  :inline="false"
                  label="Actions sur la question"
                  :test-id="`rdv-question-more-${question.key}`"
                />
              </template>
            </li>
            <li
              v-if="adding"
              class="rdv-open-question"
            >
              <form
                class="rdv-open-field"
                @submit.prevent="addQuestion"
              >
                <span
                  class="rdv-open-box"
                  aria-hidden="true"
                />
                <div>
                  <textarea
                    ref="newField"
                    v-model="custom"
                    rows="2"
                    maxlength="300"
                    placeholder="Ta question"
                    aria-label="Nouvelle question"
                    data-test="question-new"
                    @keydown.enter.exact.prevent="addQuestion"
                    @keydown.esc.prevent.stop="cancelField"
                  />
                  <p class="rdv-open-help">
                    <span>Entrée pour ajouter · Échap pour annuler</span>
                  </p>
                </div>
              </form>
            </li>
            <li class="rdv-open-add-row">
              <button
                type="button"
                class="rdv-open-add"
                data-test="rdv-question-open"
                @click="openField"
              >
                + Ajouter une question
              </button>
              <span
                class="rdv-open-saved"
                role="status"
                data-test="rdv-question-saved"
              >{{ savedNote }}</span>
            </li>
          </ul>
        </section>
        <section aria-labelledby="rdv-sheet-title">
          <h3
            id="rdv-sheet-title"
            class="rdv-open-title"
          >
            La feuille
          </h3>
          <ul class="rdv-open-card">
            <li>
              <button
                type="button"
                class="rdv-open-link"
                data-test="rdv-name"
                @click="emit('name')"
              >
                <span><b>Ton nom sur la feuille</b><span
                  v-if="nameLine"
                  class="rdv-open-sub"
                  data-test="rdv-name-line"
                >{{ nameLine }}</span></span><AppIcon name="chevron" />
              </button>
            </li>
            <li>
              <button
                type="button"
                class="rdv-open-link"
                data-test="rdv-view-sheet"
                @click="emit('sheet')"
              >
                <span><b>Voir la feuille</b><span
                  v-if="sheetLine"
                  class="rdv-open-sub"
                >{{ sheetLine }}</span></span><AppIcon name="chevron" />
              </button>
            </li>
            <li>
              <a
                class="rdv-open-link"
                :href="sheetLink"
                download
                data-test="rdv-pdf"
              ><span><b>Imprimer ou télécharger en PDF</b></span><AppIcon name="chevron" /></a>
            </li>
          </ul>
        </section>
        <section
          v-if="lastNoted"
          aria-labelledby="rdv-last"
        >
          <h3
            id="rdv-last"
            class="rdv-open-title"
          >
            Convenu la dernière fois
          </h3>
          <p
            class="rdv-open-card rdv-open-line rdv-open-value"
            data-test="rdv-last-agreed"
          >
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
    <LinkedDetail
      v-else-if="keys.length"
      class="rdv-detail"
      :list="list"
    >
      <EmptyState
        class="choose-detail"
        data-test="choose-detail"
        scene="choisis-rendez-vous"
        title="Choisis un rendez-vous"
        pill="Préparation et feuille ORP s’affichent ici"
        pill-icon="arrow-left"
        :width="340"
        :desktop-width="340"
      />
    </LinkedDetail>
  </div>
</template>

<style>
/* Valeurs de la planche CandidaturesOrdinateurB, onglet Rendez-vous (maquette du 15 novembre, §14) : la même liaison
   qu'Offres et Envoyées (LinkedDetail, liste de 504 px, rail et pointe du §18). Cartes de 80 au minimum, marges 14/16, deux lignes au plus (§39 du 16.11), contour de 1,5
   (--card-line), coins de 18, écart 10 ; la carte choisie en 16 avec un contour de 2. Titres de groupe à 14/4/8. Le
   détail : une carte en-tête (24/28/24/32, coins de 24) puis chaque bloc en carte (marge de 32), 16 px entre elles. */
.rdv-grid {
  --rdv-2: 2px; --rdv-3: 3px; --rdv-14: 14px; --rdv-17: 17px; --rdv-18: 18px; --rdv-21: 21px; --rdv-24: 24px; --rdv-28: 28px; --rdv-30: 30px;
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
  flex: none; display: flex; align-items: center; gap: var(--space-2) var(--rdv-14); box-sizing: border-box; min-height: 80px; padding: var(--rdv-14) var(--space-4);
  background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--rdv-18); color: var(--text); font: inherit; text-align: left;
}
button.rdv-item { cursor: pointer; }
button.rdv-item:hover { border-color: var(--field-border); }
.rdv-item[aria-current="true"], button.rdv-item[aria-current="true"]:hover { max-width: none; border-color: var(--primary-graphic); }
.rdv-item-text { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: var(--rdv-3); }
.rdv-item-line { display: flex; align-items: center; gap: var(--space-2); min-width: 0; }
.rdv-item-title, .rdv-item-sub { min-width: 0; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.rdv-item-title { font-size: var(--font-body); line-height: var(--rdv-21); font-weight: var(--weight-bold); }
.rdv-item-sub { font-size: var(--font-small); color: var(--text-secondary); }
/* L'heure et le délai ne sont jamais coupés ; seul ce qui suit l'est (§39, Kevin 16.11). */
.rdv-when { display: flex; }
.rdv-when > * + * { min-width: 0; overflow: hidden; text-overflow: ellipsis; }
.rdv-chip {
  flex: none; padding: var(--rdv-2) var(--space-2); border-radius: var(--radius-pill); white-space: nowrap; font-size: var(--font-caption);
  font-weight: var(--weight-bold); background: color-mix(in srgb, var(--surface-muted) 70%, var(--surface)); color: var(--text-tertiary);
}
.rdv-chip.green { background: var(--success-soft); color: var(--success); }
.rdv-chip.peach { background: var(--peach-soft); color: var(--peach-text); }
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
/* Le rendez-vous ORP ouvert : valeurs du HTML de la planche RendezVousOrdinateurOuvert (§72, 18.11). Contenu de 680 au
   plus (8 px après le début de la zone), 24 entre les blocs ; en tête, la tuile date de 56, le titre 24/30/800, la ligne
   15 grise, « Voir la feuille » plein de 44 ; titres de bloc 18/24/800 à 4 px du bord ; cartes blanches au trait 1,5
   (--card-line), coins de 18 ; lignes 12/18, libellé 13 gris sur une valeur 16/22 ; questions de 56 avec une case de 24
   (coins de 6) et un ⋯ de 44 ; « + Ajouter une question » 15/700 sur 52 ; lignes de « La feuille » de 60, 16/700. Le
   champ d'ajout (planche PreparerRendezVousQuestion) : trait 2 bleu, coins de 14, aide 13 grise, « Enregistré » vert. */
.rdv-open {
  --ro-2: 2px; --ro-6: 6px; --ro-10: 10px; --ro-14: 14px; --ro-15: 15px; --ro-18: 18px; --ro-22: 22px; --ro-24: 24px; --ro-30: 30px;
  --ro-52: 52px; --ro-56: 56px; --ro-60: 60px; --ro-680: 680px;
  flex: none; display: flex; flex-direction: column; gap: var(--space-6); max-width: var(--ro-680); padding: var(--space-6) var(--space-6) var(--space-12) var(--space-2);
}
.rdv-open-head { display: flex; align-items: center; gap: var(--space-4); }
.rdv-open-head-text { flex: 1; min-width: 0; }
.rdv-open-head h2 { margin: 0; font-size: var(--ro-24); line-height: var(--ro-30); font-weight: var(--weight-heavy); color: var(--text); }
.rdv-open-head p { margin: var(--ro-2) 0 0; font-size: var(--ro-15); color: var(--text-secondary); overflow-wrap: anywhere; }
.rdv-open-head .rdv-open-sheet { flex: none; min-height: var(--target-min); height: var(--target-min); padding: 0 var(--space-5); border-radius: var(--ro-22); font-size: var(--ro-15); font-weight: var(--weight-bold); }
.rdv-open-head .more-button { min-width: var(--target-min); min-height: var(--target-min); }
.rdv-open-title { margin: 0 0 var(--ro-10) var(--space-1); font-size: var(--font-title); line-height: var(--ro-24); font-weight: var(--weight-heavy); color: var(--text); }
.rdv-open-card { margin: 0; padding: 0; list-style: none; background: var(--surface); border: 1.5px solid var(--card-line); border-radius: var(--ro-18); overflow: hidden; }
.rdv-open-card > li + li { border-top: 1px solid var(--line); }
.rdv-open-line { display: flex; flex-direction: column; gap: var(--ro-2); padding: var(--space-3) var(--ro-18); }
.rdv-open-key { font-size: var(--label-caps); color: var(--text-secondary); }
.rdv-open-value { font-size: var(--font-body); line-height: var(--ro-22); color: var(--text); overflow-wrap: anywhere; }
.rdv-open-question { display: flex; align-items: center; }
.rdv-open .rdv-open-check { flex: 1; min-width: 0; display: flex; align-items: center; gap: var(--ro-14); min-height: var(--ro-56); padding: var(--ro-10) 0 var(--ro-10) var(--ro-18); border: 0; border-radius: 0; background: transparent; box-shadow: none; color: var(--text); font: inherit; font-size: var(--font-body); font-weight: var(--weight-regular); line-height: var(--ro-22); text-align: left; cursor: pointer; }
.rdv-open-question-text { flex: 1; min-width: 0; white-space: normal; overflow-wrap: anywhere; }
.rdv-open-box { flex: none; display: flex; align-items: center; justify-content: center; box-sizing: border-box; width: var(--ro-24); height: var(--ro-24); border-radius: var(--ro-6); border: var(--ro-2) solid var(--field-border); color: var(--surface); }
.rdv-open-box.on { border: 0; background: var(--primary-graphic); }
.rdv-open-box .icon { width: var(--space-4); height: var(--space-4); stroke-width: 3; }
.rdv-open-question > .more-menu { flex: none; margin-right: var(--space-2); }
.rdv-open-question .more-button { width: var(--target-min); height: var(--target-min); color: var(--text-secondary); }
.rdv-open-field { flex: 1; display: flex; align-items: flex-start; gap: var(--ro-14); padding: var(--space-3) var(--ro-18); }
.rdv-open-field > .rdv-open-box { margin-top: var(--ro-14); }
.rdv-open-field > div { flex: 1; min-width: 0; }
.rdv-open .rdv-open-field textarea { display: block; box-sizing: border-box; width: 100%; min-height: var(--ro-52); padding: var(--space-3) var(--ro-14); border: var(--ro-2) solid var(--primary-graphic); border-radius: var(--ro-14); background: var(--surface); color: var(--text); font: inherit; font-size: var(--font-body); line-height: var(--ro-22); resize: none; outline: 0; }
.rdv-open-help { display: flex; justify-content: space-between; gap: var(--space-2); margin: var(--space-2) 0 0; font-size: var(--label-caps); color: var(--text-secondary); }
.rdv-open-add-row { display: flex; align-items: center; justify-content: space-between; gap: var(--space-2); padding-right: var(--ro-18); }
.rdv-open .rdv-open-add { display: flex; align-items: center; min-height: var(--ro-52); padding: 0 var(--ro-18); border: 0; border-radius: 0; background: transparent; box-shadow: none; color: var(--primary-text); font-size: var(--ro-15); font-weight: var(--weight-bold); cursor: pointer; }
.rdv-open-saved { font-size: var(--label-caps); font-weight: var(--weight-bold); color: var(--success); }
.rdv-open .rdv-open-link { display: flex; align-items: center; gap: var(--space-3); box-sizing: border-box; width: 100%; min-height: var(--ro-60); padding: var(--ro-10) var(--ro-18); border: 0; border-radius: 0; background: transparent; box-shadow: none; color: var(--text); font: inherit; text-align: left; text-decoration: none; cursor: pointer; }
.rdv-open-link > span { flex: 1; min-width: 0; }
.rdv-open-link b { display: block; font-size: var(--font-body); font-weight: var(--weight-bold); }
.rdv-open-sub { display: block; margin-top: var(--ro-2); font-size: var(--font-small); color: var(--text-secondary); }
.rdv-open-link > .icon { flex: none; width: var(--space-5); height: var(--space-5); color: var(--text-secondary); }
/* « Ce qui a été convenu » : la carte de contenu (4/32/0), sans le trait qui l'ouvrait ; « Enregistrer » collé en bas. */
.outcome-inline.rdv-card { flex: none; margin: 0; padding: var(--space-1) var(--space-8) 0; border: 1px solid var(--line); }
.outcome-inline.rdv-card > .detail-overline { padding-top: var(--space-6); }
.outcome-inline.rdv-card .outcome-inline-actions { border-bottom-left-radius: var(--rdv-24); border-bottom-right-radius: var(--rdv-24); }
.rdv-detail .rdv-form { max-width: 560px; margin-top: var(--space-6); }
</style>
