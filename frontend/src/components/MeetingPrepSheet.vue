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
    <div class="sheet-sum">
      <CalendarDate
        v-bind="cal(at)"
        tone="orp"
      />
      <div class="sheet-sum-text">
        <b>Rendez-vous ORP</b>
        <span>{{ dateText(at) }}, {{ timeAndPlace(at, place) }}</span>
      </div>
    </div>
    <section
      v-if="lines.length"
      class="sheet-group"
      :aria-labelledby="whereId"
      data-test="rdv-prep-lines"
    >
      <h3
        :id="whereId"
        class="sheet-group-title"
      >
        Où tu en es
      </h3>
      <ul class="sheet-items">
        <li
          v-for="line in lines"
          :key="line.label"
          class="sheet-item"
        >
          <div>
            <div class="sheet-key">
              {{ line.label }}
            </div>
            <div class="sheet-text">
              {{ line.text }}
            </div>
          </div>
        </li>
      </ul>
    </section>
    <section
      v-if="questions.length"
      class="sheet-group"
      :aria-labelledby="askId"
      data-test="rdv-prep-questions"
    >
      <h3
        :id="askId"
        class="sheet-group-title"
      >
        Tes questions au conseiller · {{ checkedCount(checked) }}
      </h3>
      <ul class="sheet-items">
        <li
          v-for="question in questions"
          :key="question.key"
        >
          <label class="sheet-item sheet-check">
            <input
              type="checkbox"
              :checked="question.checked"
              :data-test="`rdv-question-${question.key}`"
              @change="emit('toggle', question, ($event.target as HTMLInputElement).checked)"
            >
            <span class="sheet-text">{{ question.text }}</span>
          </label>
        </li>
      </ul>
    </section>
    <a
      class="sheet-link"
      :href="pdf"
      download
      data-test="rdv-pdf"
    >Imprimer ou télécharger en PDF<AppIcon name="chevron" /></a>
  </BottomSheet>
</template>
