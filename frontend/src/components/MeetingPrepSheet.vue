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
type Question = components["schemas"]["QuestionIO"];

defineProps<{
  open: boolean;
  at: string;
  place: string | null | undefined;
  lines: { label: string; text: string }[];
  questions: Question[];
  checked: number;
  pdf: string;
}>();
const emit = defineEmits<{ close: []; toggle: [question: Question, checked: boolean] }>();

const whereId = useId();
const askId = useId();
function cal(iso: string): { day: number; month: number } {
  const d = new Date(iso);
  return { day: d.getDate(), month: d.getMonth() + 1 };
}
</script>

<template>
  <BottomSheet
    :open="open"
    title="Préparer le rendez-vous"
    data-test="rdv-prep-sheet"
    @close="emit('close')"
  >
    <div class="prep-sum">
      <CalendarDate
        v-bind="cal(at)"
        tone="orp"
      />
      <div class="prep-sum-text">
        <b>Rendez-vous ORP</b>
        <span>{{ dateText(at) }}, {{ timeAndPlace(at, place) }}</span>
      </div>
    </div>
    <section
      v-if="lines.length"
      class="prep-group"
      :aria-labelledby="whereId"
      data-test="rdv-prep-lines"
    >
      <h3
        :id="whereId"
        class="prep-group-title"
      >
        Où tu en es
      </h3>
      <ul class="prep-items">
        <li
          v-for="line in lines"
          :key="line.label"
          class="prep-item"
        >
          <div>
            <div class="prep-key">
              {{ line.label }}
            </div>
            <div class="prep-text">
              {{ line.text }}
            </div>
          </div>
        </li>
      </ul>
    </section>
    <section
      v-if="questions.length"
      class="prep-group"
      :aria-labelledby="askId"
      data-test="rdv-prep-questions"
    >
      <h3
        :id="askId"
        class="prep-group-title"
      >
        Tes questions au conseiller · {{ checkedCount(checked) }}
      </h3>
      <ul class="prep-items">
        <li
          v-for="question in questions"
          :key="question.key"
        >
          <label class="prep-item prep-check">
            <input
              type="checkbox"
              :checked="question.checked"
              :data-test="`rdv-question-${question.key}`"
              @change="emit('toggle', question, ($event.target as HTMLInputElement).checked)"
            >
            <span class="prep-text">{{ question.text }}</span>
          </label>
        </li>
      </ul>
    </section>
    <a
      class="prep-pdf"
      :href="pdf"
      download
      data-test="rdv-pdf"
    >Imprimer ou télécharger en PDF<AppIcon name="chevron" /></a>
  </BottomSheet>
</template>

<style>
/* Valeurs du HTML de RendezVousPreparer : rappel avec 16 px d'écart, 20 px dessous et trait ; familles à 20 px, titre
   13/16 en capitales ; lignes 12 px au-dessus et en dessous, trait --line ; libellé 13/16 juste au-dessus du texte 15/20 ;
   cases de 24 px à 16 px du texte ; lien de bas de 56 px, 8 px au-dessus. */
.prep-sum { display: flex; align-items: center; gap: var(--space-4); padding-bottom: var(--space-5); border-bottom: 1px solid var(--line); }
.prep-sum-text { min-width: 0; }
.prep-sum-text b { display: block; font-size: var(--font-title); line-height: var(--space-6); }
.prep-sum-text span { display: block; margin-top: var(--space-1); font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
.prep-group { padding-top: var(--space-5); }
.prep-group-title { margin: 0 0 var(--space-1); font-size: var(--label-caps); line-height: var(--space-4); font-weight: var(--weight-bold); letter-spacing: .06em; text-transform: uppercase; color: var(--text-secondary); }
.prep-items { margin: 0; padding: 0; list-style: none; }
.prep-item { display: flex; align-items: flex-start; gap: var(--space-4); padding: var(--space-3) 0; border-bottom: 1px solid var(--line); }
.prep-check { align-items: center; min-height: var(--target-min); box-sizing: border-box; cursor: pointer; }
.prep-check input { flex: none; width: var(--space-6); height: var(--space-6); margin: 0; accent-color: var(--primary-graphic); cursor: pointer; }
.prep-key { font-size: var(--label-caps); line-height: var(--space-4); color: var(--text-secondary); }
.prep-text { font-size: var(--font-label); line-height: var(--space-5); overflow-wrap: anywhere; }
.prep-pdf { --prep-pdf-h: 56px; display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); min-height: var(--prep-pdf-h); margin-top: var(--space-2); color: var(--primary-text); font-size: var(--font-label); font-weight: var(--weight-bold); text-decoration: none; }
.prep-pdf > .icon { flex: none; width: var(--space-6); height: var(--space-6); }
</style>
