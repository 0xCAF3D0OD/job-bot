<script setup lang="ts">
import { useId } from "vue";

import type { components } from "../api/schema";
import { checkedCount, dateText, timeAndPlace } from "../rendezVous";
import AppIcon from "./AppIcon.vue";
import BottomSheet from "./BottomSheet.vue";
import CalendarDate from "./CalendarDate.vue";

// La feuille « Préparer le rendez-vous » (MODIFICATIONS du 8 novembre au soir, §10.7 ; maquettes RendezVousPreparer
// et RendezVousPreparerSombre), ouverte depuis la carte « À venir » du rendez-vous ORP : le rappel (calendrier,
// « Rendez-vous ORP », date · lieu) ; « Où tu en es », le libellé au-dessus de la valeur ; « Tes questions au
// conseiller · n cochées », cases de 24 px sur des lignes de 44 px au moins ; puis « Imprimer ou télécharger en PDF ».
// §46 du 17.11 (décision de Kevin du 17.11) : une page entière sur fond beige, pas une feuille ; la flèche « Retour » à
// gauche du titre à la place de la croix. Retour, Échap et le retour du téléphone la ferment (BottomSheet).
type Question = components["schemas"]["QuestionIO"];

defineProps<{
  open: boolean;
  at: string;
  place: string | null | undefined;
  lines: { label: string; text: string }[];
  questions: Question[];
  checked: number;
  pdf: string;
  // Sous « Ton nom sur la feuille » : le nom et l'office enregistrés ; sous « Voir la feuille » : « 6 recherches,
  // 2 questions ». Vides : la ligne n'a que son titre.
  nameLine?: string;
  sheetLine?: string;
}>();
const emit = defineEmits<{ close: []; toggle: [question: Question, checked: boolean]; name: []; sheet: [] }>();

const whereId = useId();
const askId = useId();
const sheetId = useId();
function cal(iso: string): { day: number; month: number } {
  const d = new Date(iso);
  return { day: d.getDate(), month: d.getMonth() + 1 };
}
</script>

<template>
  <BottomSheet
    :open="open"
    title="Préparer le rendez-vous"
    full
    back
    class="rdv-prep-page prep-page"
    data-test="rdv-prep-sheet"
    @close="emit('close')"
  >
    <div class="prep-card prep-date">
      <CalendarDate
        v-bind="cal(at)"
        tone="orp"
      />
      <div>
        <b class="prep-date-title">Rendez-vous ORP</b>
        <span class="prep-sub">{{ dateText(at) }}, {{ timeAndPlace(at, place) }}</span>
      </div>
    </div>
    <section
      v-if="lines.length"
      :aria-labelledby="whereId"
      data-test="rdv-prep-lines"
    >
      <h3
        :id="whereId"
        class="prep-title"
      >
        Où tu en es
      </h3>
      <ul class="prep-card prep-rows">
        <li
          v-for="line in lines"
          :key="line.label"
          class="prep-line"
        >
          <div class="prep-key">
            {{ line.label }}
          </div>
          <div class="prep-value">
            {{ line.text }}
          </div>
        </li>
      </ul>
    </section>
    <section
      v-if="questions.length"
      :aria-labelledby="askId"
      data-test="rdv-prep-questions"
    >
      <h3
        :id="askId"
        class="prep-title"
      >
        Tes questions au conseiller · {{ checkedCount(checked) }}
      </h3>
      <ul class="prep-card prep-rows">
        <li
          v-for="question in questions"
          :key="question.key"
        >
          <label class="prep-check">
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
    </section>
    <section :aria-labelledby="sheetId">
      <h3
        :id="sheetId"
        class="prep-title"
      >
        La feuille
      </h3>
      <ul class="prep-card prep-rows">
        <li>
          <button
            type="button"
            class="prep-link"
            data-test="rdv-name"
            @click="emit('name')"
          >
            <span><b>Ton nom sur la feuille</b><span
              v-if="nameLine"
              class="prep-sub"
              data-test="rdv-name-line"
            >{{ nameLine }}</span></span><AppIcon name="chevron" />
          </button>
        </li>
        <li>
          <button
            type="button"
            class="prep-link"
            data-test="rdv-view-sheet"
            @click="emit('sheet')"
          >
            <span><b>Voir la feuille</b><span
              v-if="sheetLine"
              class="prep-sub"
            >{{ sheetLine }}</span></span><AppIcon name="chevron" />
          </button>
        </li>
        <li>
          <a
            class="prep-link"
            :href="pdf"
            download
            data-test="rdv-pdf"
          ><span><b>Imprimer ou télécharger en PDF</b></span><AppIcon name="chevron" /></a>
        </li>
      </ul>
    </section>
  </BottomSheet>
</template>

<style scoped>
/* Planche PreparerRendezVous (§71, 18.11) : sur le fond beige, des cartes blanches (trait 1 px, rayon 20 px, 12 px
   entre elles) ; titres de groupe en phrase, 18 px, graisse 800, 24 px au-dessus et 12 px dessous (22 et 10 sur la planche : grille de 4), 4 px plus à
   l'intérieur que les cartes ; lignes séparées d'un trait doux ; libellé 13 px gris au-dessus d'une valeur de 16 px. */
.prep-page { --pp-radius: 20px; --pp-row-h: 56px; --pp-check: 24px; --pp-check-radius: 6px; --pp-chevron: 18px; --pp-lh-sub: 19px; --pp-lh-key: 18px; --pp-lh: 22px; }
.prep-page :deep(.sheet-body) { gap: 0; padding-inline: var(--space-4); }
.prep-card { margin: 0 0 var(--space-3); padding: 0; list-style: none; border: 1px solid var(--line); border-radius: var(--pp-radius); background: var(--surface); }
.prep-rows > li + li { border-top: 1px solid var(--line-soft); }
.prep-date { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-4); }
.prep-date-title { display: block; font-size: var(--font-title); font-weight: var(--weight-bold); line-height: var(--space-6); }
.prep-sub { display: block; margin-top: var(--space-1); font-size: var(--font-small); font-weight: var(--weight-regular); line-height: var(--pp-lh-sub); color: var(--text-secondary); }
.prep-title { margin: var(--space-6) var(--space-1) var(--space-3); font-size: var(--font-title); line-height: var(--space-6); font-weight: var(--weight-heavy); }
.prep-line { padding: var(--space-3) var(--space-4); }
.prep-key { font-size: var(--label-caps); line-height: var(--pp-lh-key); color: var(--text-secondary); }
.prep-value { margin-top: var(--space-1); font-size: var(--font-body); line-height: var(--pp-lh); overflow-wrap: anywhere; }
.prep-check { display: flex; align-items: flex-start; gap: var(--space-3); min-height: var(--target-min); padding: var(--space-3) var(--space-4); font-size: var(--font-body); line-height: var(--pp-lh); cursor: pointer; }
.prep-check input { flex: none; appearance: none; width: var(--pp-check); height: var(--pp-check); margin: 0; border-radius: var(--pp-check-radius); box-shadow: inset 0 0 0 2px var(--field-border); background: var(--surface) center / 16px no-repeat; cursor: pointer; }
.prep-check input:checked { box-shadow: none; background-color: var(--primary-graphic); background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23fff' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m5 12 5 5 9-10'/%3E%3C/svg%3E"); }
.prep-link { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); box-sizing: border-box; width: 100%; min-height: var(--pp-row-h); padding: var(--space-2) var(--space-4); border: 0; background: none; color: var(--text); font: inherit; text-align: left; text-decoration: none; cursor: pointer; }
.prep-link b { display: block; font-size: var(--font-body); font-weight: var(--weight-semibold); line-height: var(--pp-lh); }
.prep-link > .icon { flex: none; width: var(--pp-chevron); height: var(--pp-chevron); color: var(--text-secondary); }
</style>
