<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, ref } from "vue";

import type { Application } from "../api/client";
import type { components } from "../api/schema";
import {
  agreedLines,
  dateText,
  meetingsToNote,
  notedMeetings,
  pastTitle,
  sheetLines,
  timeAndPlace,
  upcomingAppointments,
  upcomingLabel,
  upcomingWhen,
  upcomingWhere,
  appointmentMatches,
  meetingMatches,
} from "../rendezVous";
import { plural } from "../format";
import { useSheetIdentity } from "../sheetIdentity";
import CalendarDate from "./CalendarDate.vue";
import MeetingPrepSheet from "./MeetingPrepSheet.vue";
import MoreMenu, { type MoreMenuItem } from "./MoreMenu.vue";

// Candidatures › Rendez-vous sur téléphone (planches RendezVous et RendezVousSombre du 18.11). Trois parties, posées
// par OrpMeetingView dans l'ordre de la planche : « À venir » (le prochain rendez-vous ORP et les entretiens, par date),
// « À noter » (un rendez-vous passé à noter), puis « Derniers rendez-vous ORP » (le dernier noté et le Carnet ORP) ;
// « Noter » ouvre la feuille de la vue.
type Page = components["schemas"]["MeetingPage"];
type Question = components["schemas"]["QuestionIO"];
type Meeting = components["schemas"]["MeetingOut"];

const props = defineProps<{
  part: "to-note" | "upcoming" | "past";
  page: Page;
  applications: Application[];
  sheetLink: string;
  // Le « ⋯ » de la carte ORP (C6) : les mêmes actions que celui de la page actuelle.
  meetingItems?: MoreMenuItem[];
  // Les mots de la recherche (maquette du 14 novembre, §6), déjà découpés par OrpMeetingView.
  words?: string[];
  // Enregistre la liste entière des questions (« + Ajouter une question ») ; `false` si le serveur ne l'a pas prise.
  saveQuestions?: (questions: Question[]) => Promise<boolean>;
}>();
const emit = defineEmits<{
  toggle: [question: Question, checked: boolean];
  log: [];
  prepare: [application: Application];
  note: [id: number];
  sheet: [];
}>();

const now = new Date();
const words = computed(() => props.words ?? []);
const items = computed(() => upcomingAppointments(props.page.meeting ?? null, props.applications, now).filter((item) => appointmentMatches(item, words.value)));
const prep = computed(() => props.page.preparation);
const lines = computed(() => sheetLines(prep.value));
const checked = computed(() => prep.value.questions.filter((q) => q.checked).length);
const prepOpen = ref(false);
// Les deux lignes grises de la carte « La feuille » (planche PreparerRendezVous, §71) : le nom et l'office enregistrés,
// chargés avec la page pour qu'ils soient là dès l'ouverture ; puis « 6 recherches, 2 questions ».
const identity = useSheetIdentity();
onMounted(() => {
  if (props.part === "upcoming" && props.page.meeting) void identity.load();
});
const nameLine = computed(() => [identity.values.name, identity.values.office].map((v) => v.trim()).filter(Boolean).join(" · "));
const sheetLine = computed(() => {
  const month = prep.value.months?.at(-1);
  return [month ? plural(month.count, "recherche", "recherches") : "", plural(checked.value, "question", "questions")].filter(Boolean).join(", ");
});
// « Voir la feuille » : la feuille actuelle (?feuille=1) prend la place de la préparation dans l'historique ; Retour
// ramène aux rendez-vous.
function viewSheet(): void {
  emit("sheet");
}
// « Ton nom sur la feuille » (§70, planche FeuilleNom) : une page ouverte depuis « Préparer le rendez-vous », chargée
// à la première ouverture. Elle prend la place de la page de préparation (une seule feuille à la fois, avec son entrée
// d'historique) ; Retour rouvre la préparation, qui reprend la place à son tour.
const FeuilleNomSheet = defineAsyncComponent(() => import("./FeuilleNomSheet.vue"));
const nameShown = ref(false);
const nameOpen = ref(false);
function openName(): void {
  nameShown.value = true;
  nameOpen.value = true;
}
function nameClosed(): void {
  if (!prepOpen.value) prepOpen.value = true;
  else nameOpen.value = false;
}

// À noter, puis le dernier rendez-vous ORP noté.
const toNote = computed(() => meetingsToNote(props.page, now).filter((m) => meetingMatches(m, words.value)));
const last = computed<Meeting | null>(() => notedMeetings(props.page, now).filter((m) => meetingMatches(m, words.value))[0] ?? null);
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
            label="Plus d’actions sur le rendez-vous ORP"
            test-id="rdv-more"
          />
        </div>
        <!-- Deux lignes au plus (demande de Kevin du 16.11, planche RendezVous) : « Rendez-vous ORP » et sa pastille,
             puis « 9 h · dans 3 jours · lieu ». Toute la carte ouvre la feuille de préparation (la planche relie la
             carte à RendezVousPreparer) : le bouton s’étend sur la carte ; son nom dit titre, pastille, date, heure et délai. -->
        <CalendarDate
          class="rdv-date"
          v-bind="cal(item.at)"
          tone="orp"
        />
        <div class="rdv-body">
          <span class="rdv-line">
            <h3
              id="rdv-orp-titre"
              class="rdv-orp-title"
            >
              Rendez-vous ORP
            </h3>
            <!-- « prête » seulement si la feuille a au moins une ligne ; sinon une pastille neutre. -->
            <span
              v-if="lines.length"
              class="rdv-ready"
              data-test="rdv-ready"
            >Feuille prête</span>
            <span
              v-else
              class="rdv-ready rdv-todo"
              data-test="rdv-todo"
            >Feuille à compléter</span>
          </span>
          <span class="rdv-meta rdv-when"><span>{{ upcomingWhen(item, now) }}</span><span v-if="upcomingWhere(item)">&nbsp;· {{ upcomingWhere(item) }}</span></span>
        </div>
        <button
          type="button"
          class="rdv-prepare"
          aria-haspopup="dialog"
          :aria-label="upcomingLabel(item, lines.length ? 'Feuille prête' : 'Feuille à compléter', now)"
          data-test="rdv-prep-open"
          @click="prepOpen = true"
        />
      </article>
      <FeuilleNomSheet
        v-if="item.kind === 'orp' && nameShown"
        :open="nameOpen"
        :identity="identity"
        class="rdv-prep-page"
        @close="nameClosed"
      />
      <MeetingPrepSheet
        v-if="item.kind === 'orp'"
        :open="prepOpen"
        :at="item.at"
        :place="item.meeting.place"
        :lines="lines"
        :questions="prep.questions"
        :checked="checked"
        :pdf="sheetLink"
        :name-line="nameLine"
        :sheet-line="sheetLine"
        :save="saveQuestions"
        @close="prepOpen = false"
        @sheet="viewSheet"
        @toggle="(question, value) => emit('toggle', question, value)"
        @name="openName"
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
          <span class="rdv-line">
            <h3 class="rdv-interview-title">
              {{ item.application.job_title || "Poste non indiqué" }}
            </h3>
            <span class="rdv-ready rdv-peach">À préparer</span>
          </span>
          <span class="rdv-meta rdv-when"><span>{{ upcomingWhen(item, now) }}</span><span v-if="upcomingWhere(item)">&nbsp;· {{ upcomingWhere(item) }}</span></span>
        </div>
        <!-- Toute la carte ouvre la préparation (maquette) : le bouton s’étend sur la carte. -->
        <button
          type="button"
          class="rdv-prepare"
          :aria-label="upcomingLabel(item, 'À préparer', now)"
          :data-test="`rdv-prepare-${item.application.id}`"
          @click="emit('prepare', item.application)"
        />
      </article>
    </template>
  </section>

  <!-- À noter (maquette du 7.11) : un rendez-vous ORP passé dont rien n'est noté ; « Noter » ouvre la feuille. -->
  <section
    v-else-if="part === 'to-note' && toNote.length"
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
            Rendez-vous ORP
          </h3>
          <!-- Plus de « Pas encore noté » (lot 14) : le groupe « À noter » le dit déjà. -->
          <!-- « Vendredi 30 octobre, 11 h · EPFL » : le lieu tel que saisi, sans changer sa casse. -->
          <span
            class="rdv-meta"
            data-test="rdv-to-note-meta"
          >{{ `${dateText(item.starts_at)}, ${timeAndPlace(item.starts_at, item.place)}` }}</span>
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
  <template v-else-if="part === 'past'">
    <!-- Le titre « Derniers rendez-vous ORP » revient avec la planche RendezVous du 18.11 (Kevin, 18.11), sans nombre. -->
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
   entre une icône et son mot. 15 px = --font-small + 1 px. */
.rdv-part { --rdv-14: 14px; --rdv-22: 22px; min-width: 0; display: flex; flex-direction: column; gap: var(--space-2); }
.rdv-title {
  display: flex; align-items: baseline; gap: var(--space-2); margin: var(--space-2) var(--space-1) 0;
  font-size: var(--font-body); font-weight: var(--weight-bold); line-height: var(--leading-tight);
}
.rdv-title span { font-size: var(--label-caps); font-weight: var(--weight-semibold); color: var(--text-secondary); }
.rdv-card {
  display: flex; padding: var(--space-5); background: var(--surface); border: 1px solid var(--line);
  border-radius: var(--radius-card); color: var(--text);
}
/* Cartes « À venir » (planche RendezVous, demande de Kevin du 16.11) : l'icône calendrier, puis deux lignes au plus,
   le titre (16/22) et sa pastille (12, 22 de haut ; marges de 4 pour la grille), puis « 9 h · dans 3 jours · lieu » (14/20), coupées par « … ». */
.rdv-orp, .rdv-interview { position: relative; align-items: center; gap: var(--space-4); }
/* Le « ⋯ » (C6) : 44 px collé au coin en haut à droite, ses points dans la marge ; la 1re ligne lui laisse 16 px. */
.rdv-more { position: absolute; top: 0; right: 0; z-index: 1; }
.rdv-more :deep(.more-button) { width: var(--target-min); height: var(--target-min); }
.rdv-orp .rdv-line { padding-right: var(--space-4); }
.rdv-date { flex: none; }
.rdv-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: var(--space-1); }
.rdv-line { display: flex; align-items: center; gap: var(--space-2); min-width: 0; }
.rdv-orp-title, .rdv-interview-title, .rdv-when > * + * { min-width: 0; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.rdv-orp-title, .rdv-interview-title { margin: 0; font-size: var(--font-body); line-height: var(--rdv-22); font-weight: var(--weight-bold); }
.rdv-meta { font-size: var(--font-small); color: var(--text-secondary); }
.rdv-ready {
  flex: none; padding: var(--space-1) var(--space-2); border-radius: var(--radius-pill); white-space: nowrap;
  background: var(--success-soft); color: var(--success); font-size: var(--font-caption); line-height: var(--rdv-14); font-weight: var(--weight-bold);
}
.rdv-todo { background: var(--neutral-soft); color: var(--text-secondary); }
.rdv-peach { background: var(--peach-soft); color: var(--peach-text); }
/* L'heure et le délai ne sont jamais coupés ; seul ce qui suit l'est (§39, Kevin 16.11). */
.rdv-when { display: flex; min-width: 0; white-space: nowrap; }
/* Hors du flux (aucun écart de plus dans la carte) : le bouton couvre toute la carte. */
.rdv-prepare { position: absolute; inset: 0; padding: 0; border: 0; border-radius: var(--radius-card); background: transparent; cursor: pointer; }
/* La carte entière est la cible (maquette : un lien sur toute la carte) ; le contour de focus suit son rayon. */
.rdv-prepare:focus-visible { outline: 2px solid var(--primary-graphic); outline-offset: 2px; }
.rdv-last { flex-direction: column; gap: var(--space-3); }
.rdv-last-head { display: flex; align-items: center; gap: var(--space-4); }
.rdv-last-title { margin: 0; font-size: var(--font-body); font-weight: var(--weight-bold); line-height: var(--leading-normal); }
.rdv-agreed { display: grid; grid-template-columns: auto 1fr; gap: var(--space-2) var(--space-3); margin: 0; font-size: calc(var(--font-small) + 1px); line-height: 1.4em; }
.rdv-agreed dt { color: var(--text-secondary); }
.rdv-agreed dd { margin: 0; }
/* « Noter ce qui a été convenu » : 48 px, en pilule bleu pâle, texte centré (RendezVousPreparer ; K29 de l'audit). */
.rdv-note { justify-content: center; }
.rdv-note, .rdv-edit-note {
  min-height: var(--btn-tertiary); padding: 0 var(--space-4); border: 0; border-radius: var(--radius-pill); background: var(--primary-soft);
  color: var(--primary-text); font: inherit; font-size: calc(var(--font-small) + 1px); font-weight: var(--weight-bold); cursor: pointer;
}
.rdv-edit-note { align-self: flex-start; min-height: var(--target-min); padding: 0; border-radius: 0; background: transparent; }
.rdv-log {
  align-items: center; justify-content: space-between; width: 100%; min-height: var(--btn-secondary);
  padding: 0 var(--space-4); font: inherit; text-align: left; cursor: pointer;
}
.rdv-log-title { flex: 1; min-width: 0; white-space: normal; font-size: calc(var(--font-small) + 1px); font-weight: var(--weight-bold); }
.rdv-log-count { flex: none; display: flex; align-items: center; gap: var(--space-2); font-size: var(--font-small); color: var(--text-secondary); }
/* « Préparer le rendez-vous » en page entière (RendezVousPreparer, §46 du 17.11 ; planche PreparerRendezVous, §71 du
   18.11), et « Ton nom sur la feuille » : fond de la plateforme ; en haut, une barre de 52 px, la flèche (cible de 44 px,
   sans cercle, 4 px du bord, grille de 4 ; 6 px sur la planche) juste à gauche du titre de 22 px, graisse 800. */
.rdv-prep-page { --rp-nav-h: 52px; --rp-title: 22px; --rp-arrow: 22px; inset: 0; height: auto; max-height: none; border: 0; border-radius: 0; background: var(--bg); }
.rdv-prep-page :deep(.sheet-inner) { padding-top: env(safe-area-inset-top); }
.rdv-prep-page :deep(.sheet-head) { gap: 0; min-height: var(--rp-nav-h); padding: 0 var(--space-1); }
.rdv-prep-page :deep(.sheet-close) { order: -1; width: var(--target-min); height: var(--target-min); border: 0; background: none; }
.rdv-prep-page :deep(.sheet-close .icon) { width: var(--rp-arrow); height: var(--rp-arrow); }
.rdv-prep-page :deep(.sheet-title) { font-size: var(--rp-title); font-weight: var(--weight-heavy); }
</style>
