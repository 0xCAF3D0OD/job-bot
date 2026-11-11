<script setup lang="ts">
import { useId } from "vue";

import "../sheet-float.css";
import "../sheet-screen.css";

import type { components } from "../api/schema";
import { timeOfDay } from "../dates";
import { countdown } from "../rendezVous";
import BottomSheet from "./BottomSheet.vue";

// La feuille « Préparer le rendez-vous » (MODIFICATIONS du 8 novembre au soir, §10.7 ; maquettes RendezVousPreparer
// et RendezVousPreparerSombre), ouverte depuis la carte « À venir » du rendez-vous ORP : le rappel (calendrier,
// « Rendez-vous ORP », date · lieu) ; « Où tu en es », le libellé au-dessus de la valeur ; « Tes questions au
// conseiller · n cochées », cases de 24 px sur des lignes de 44 px au moins ; puis « Imprimer ou télécharger en PDF ».
// Lot du 11 novembre au soir, PR 52 (maquettes RendezVousFeuilleV2, RendezVousFeuilleV2Sombre et
// RendezVousFeuilleOrdinateurV2) : l'écran « Rendez-vous ORP ». Téléphone : plein écran à flèche retour. Ordinateur :
// le panneau flottant de 440 px, par-dessus Aujourd'hui. La carte pêche (« ta feuille est prête », « Demain, 9 h 30 »,
// le lieu), « Où tu en es » en lignes de 72 px, « Tes questions au conseiller » en lignes de 56 px à case de 24 px,
// puis « Ouvrir la feuille (PDF) » collé en bas.
type Question = components["schemas"]["QuestionIO"];

defineProps<{
  open: boolean;
  at: string;
  place: string | null | undefined;
  lines: { label: string; text: string }[];
  questions: Question[];
  pdf: string;
}>();
const emit = defineEmits<{ close: []; toggle: [question: Question, checked: boolean] }>();

// La première ligne de la maquette met le nombre en gras (« 7 recherches sur 10 ») ; les autres, leur libellé.
function row(line: { label: string; text: string }): { title: string; sub: string } {
  return line.label === "Ton mois" ? { title: line.text, sub: line.label } : { title: line.label, sub: line.text };
}
const whereId = useId();
const askId = useId();
</script>

<template>
  <BottomSheet
    :open="open"
    title="Rendez-vous ORP"
    screen
    data-test="rdv-prep-sheet"
    @close="emit('close')"
  >
    <div class="eve">
      <div class="screen-hero eve-hero">
        <div class="screen-hero-text">
          <span
            class="screen-hand"
            data-test="rdv-prep-hand"
          >{{ lines.length ? "ta feuille est prête" : "ta feuille est à compléter" }}</span>
          <b data-test="rdv-prep-when">{{ countdown(at) }}, {{ timeOfDay(at) }}</b>
          <span
            v-if="place?.trim()"
            class="screen-hero-lead"
          >{{ place.trim() }}</span>
        </div>
        <img
          src="/tri/feuille-prete.webp"
          alt=""
          width="84"
          height="112"
        >
      </div>
      <section
        v-if="lines.length"
        :aria-labelledby="whereId"
        data-test="rdv-prep-lines"
      >
        <h3
          :id="whereId"
          class="eve-title"
        >
          Où tu en es
        </h3>
        <ul class="eve-rows">
          <li
            v-for="line in lines"
            :key="line.label"
            class="eve-row"
          >
            <b>{{ row(line).title }}</b>
            <span>{{ row(line).sub }}</span>
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
          class="eve-title"
        >
          Tes questions au conseiller
        </h3>
        <ul class="eve-rows">
          <li
            v-for="question in questions"
            :key="question.key"
          >
            <label class="eve-check">
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
    </div>
    <template #actions>
      <a
        class="button-link primary-link"
        :href="pdf"
        target="_blank"
        rel="noopener"
        data-test="rdv-pdf"
      >Ouvrir la feuille (PDF)<span class="visually-hidden"> (nouvel onglet)</span></a>
    </template>
  </BottomSheet>
</template>

<style>
/* RendezVousFeuilleV2 : carte pêche à 8 px de l'en-tête (phrase à la main de 26 px, date 17/24 gras à 12 px, lieu
   15/22 à 4 px, personnage de 112 px) ; titres 13 px gras en capitales, à 24 px des bords et 4 px du premier trait ;
   lignes de 72 px (16/22 gras, 14/20 gris à 4 px) et de 56 px (15/22), séparées d'un trait ; 24 px entre rubriques. */
.eve { --eve-16: 16px; --eve-22: 22px; --eve-14: 14px; display: flex; flex-direction: column; padding-bottom: var(--space-6); }
.eve-hero { margin-top: var(--space-2); }
.eve-hero .screen-hand { font-size: var(--screen-26); line-height: var(--screen-26); }
.eve-hero b { margin-top: var(--space-3); font-size: var(--screen-17); line-height: var(--space-6); }
.eve-hero .screen-hero-lead { margin-top: var(--space-1); }
.eve-hero img { height: var(--screen-illu-tall); }
.eve-title { margin: 0 var(--space-6) var(--space-1); font-size: var(--screen-13); line-height: var(--space-5); font-weight: var(--weight-bold); letter-spacing: .05em; text-transform: uppercase; color: var(--text-secondary); }
.eve section + section { margin-top: var(--space-6); }
.eve-rows { margin: 0 var(--space-6); padding: 0; list-style: none; }
.eve-rows > li { border-top: 1px solid var(--row-sep); }
.eve-row { display: flex; flex-direction: column; justify-content: center; box-sizing: border-box; min-height: var(--screen-row); padding: var(--space-3) 0; }
.eve-row b { font-size: var(--eve-16); line-height: var(--eve-22); }
.eve-row span { margin-top: var(--space-1); font-size: var(--eve-14); line-height: var(--space-5); color: var(--text-secondary); }
.eve-check { display: flex; align-items: center; gap: var(--space-3); box-sizing: border-box; min-height: var(--screen-check-row); padding: var(--space-3) 0; font-size: var(--screen-15); line-height: var(--eve-22); cursor: pointer; }
.eve .eve-check input[type=checkbox] { flex: none; appearance: none; display: grid; place-content: center; width: var(--space-6); height: var(--space-6); margin: 0; border: 0; border-radius: var(--screen-check-radius); background: transparent; box-shadow: inset 0 0 0 2px var(--screen-box); }
.eve .eve-check input[type=checkbox]:checked { background: var(--primary-graphic) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23fff' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m5 12 5 5 9-10'/%3E%3C/svg%3E") center / var(--eve-14) no-repeat; box-shadow: none; }
.eve .eve-check input[type=checkbox]:focus-visible { outline: 2px solid var(--primary-graphic); outline-offset: 2px; }
</style>
