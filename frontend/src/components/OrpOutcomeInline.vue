<script setup lang="ts">
import { computed, nextTick, ref, toRef, watch } from "vue";

import type { components } from "../api/schema";
import { timeOfDay } from "../dates";
import { useOrpOutcome } from "../composables/useOrpOutcome";
import { dateText } from "../rendezVous";
import DateTimeField from "./DateTimeField.vue";
import DateTimePanel from "./DateTimePanel.vue";
import DetailTwoColumns from "./DetailTwoColumns.vue";

// Ce qui a été convenu, dans le détail d'un rendez-vous ORP passé, sur ordinateur (MODIFICATIONS du 8 novembre au
// soir, lot 14 ; capture CandidaturesOrdinateurB--tab-rv) : à gauche un formulaire en trois parties (objectif,
// mesures, prochain rendez-vous) et « Enregistrer » ; à droite « Le rendez-vous ». Le sélecteur de date prend toute
// la place sous l'en-tête, comme avant. La remarque libre n'a pas de champ ici : celle qui est notée est gardée.
type Page = components["schemas"]["MeetingPage"];
type Meeting = components["schemas"]["MeetingOut"];

const props = defineProps<{ meeting: Meeting; target: number | null }>();
const emit = defineEmits<{ saved: [page: Page] }>();

const { count, measures, nextDay, nextTime, message, busy, before, step, save } = useOrpOutcome(
  toRef(props, "meeting"),
  toRef(props, "target"),
  (page) => emit("saved", page),
);

const picking = ref<"" | "date" | "time">("");
watch(
  () => props.meeting.id,
  () => (picking.value = ""),
);
function focusPill(which: "date" | "time"): void {
  void nextTick(() => document.querySelector<HTMLElement>(`[data-test=outcome-inline] [data-test=dt-${which}]`)?.focus());
}
function picked(value: { date: string; time: string }): void {
  nextDay.value = value.date;
  nextTime.value = value.time;
  picking.value = "";
  focusPill("date");
}
function cancelPick(): void {
  const which = picking.value || "date";
  picking.value = "";
  focusPill(which);
}

// « Le rendez-vous » : la date en toutes lettres, l'heure, le lieu, l'objectif jusqu'ici.
const facts = computed(() => [
  { label: "Date", value: dateText(props.meeting.starts_at), test: "fact-date" },
  { label: "Heure", value: timeOfDay(props.meeting.starts_at), test: "fact-time" },
  { label: "Lieu", value: props.meeting.place?.trim() || "Non précisé", test: "fact-place" },
  { label: "Objectif jusqu’ici", value: props.target ? `${props.target} recherches par mois` : "Non précisé", test: "fact-target" },
]);
</script>

<template>
  <div data-test="outcome-inline">
    <DateTimePanel
      v-if="picking"
      :date="nextDay"
      :time="nextTime || '09:00'"
      title="Prochain rendez-vous"
      @confirm="picked"
      @cancel="cancelPick"
    />
    <DetailTwoColumns
      v-else
      aside-label="Le rendez-vous"
      narrow
    >
      <template #main>
        <form
          class="outcome-inline"
          data-test="outcome-inline-form"
          @submit.prevent="save"
        >
          <p class="detail-overline">
            Ce qui a été convenu
          </p>
          <fieldset class="outcome-set">
            <legend>Objectif de recherches</legend>
            <p
              id="outcome-help-target"
              class="outcome-help"
            >
              Le nombre de recherches que l’ORP te demande chaque mois.
            </p>
            <div class="outcome-counter">
              <button
                type="button"
                aria-label="Une de moins"
                aria-describedby="outcome-help-target"
                data-test="outcome-less"
                @click="step(-1)"
              >
                −
              </button>
              <span
                aria-live="polite"
                data-test="outcome-target"
              >{{ count }}</span>
              <button
                type="button"
                aria-label="Une de plus"
                aria-describedby="outcome-help-target"
                data-test="outcome-more"
                @click="step(1)"
              >
                +
              </button>
              <small v-if="before">{{ before }}</small>
            </div>
          </fieldset>
          <fieldset class="outcome-set">
            <legend>Mesures décidées <span class="outcome-optional">(facultatif)</span></legend>
            <p
              id="outcome-help-measures"
              class="outcome-help"
            >
              Un cours, un stage ou un programme proposé par ta conseillère.
            </p>
            <input
              v-model="measures"
              type="text"
              maxlength="1000"
              placeholder="Cours, stage, programme…"
              aria-label="Mesures décidées"
              aria-describedby="outcome-help-measures"
              data-test="outcome-measures"
            >
          </fieldset>
          <fieldset
            class="outcome-set"
            data-test="outcome-next"
          >
            <legend>Prochain rendez-vous <span class="outcome-optional">(facultatif)</span></legend>
            <p class="outcome-help">
              jobA1 prépare ta feuille la veille et te le rappelle le matin.
            </p>
            <DateTimeField
              :date="nextDay"
              :time="nextTime"
              :open="picking"
              @open="picking = $event"
            />
          </fieldset>
          <p
            v-if="message"
            role="status"
            class="notice error"
          >
            {{ message }}
          </p>
          <div class="outcome-inline-actions">
            <button
              type="submit"
              class="primary action-1"
              :disabled="busy"
              data-test="outcome-save"
            >
              Enregistrer
            </button>
          </div>
        </form>
      </template>
      <template #aside>
        <section class="detail-section">
          <h3>Le rendez-vous</h3>
          <dl class="detail-list">
            <div
              v-for="fact in facts"
              :key="fact.test"
              :data-test="fact.test"
            >
              <dt>{{ fact.label }}</dt>
              <dd>{{ fact.value }}</dd>
            </div>
          </dl>
        </section>
      </template>
    </DetailTwoColumns>
  </div>
</template>

<style>
/* Valeurs du lot 14 : sur-titre au-dessus des trois parties ; chaque partie à 28/32 avec un trait au-dessus (sauf la
   première), le titre de 18 en 700, « (facultatif) » en 15 normal, la phrase d'aide en 14 (4 au-dessus, 16
   dessous) ; compteur en ronds de 44 ; « Enregistrer » plein de 52, après un trait. */
.outcome-inline { --out-28: 28px; --out-32: 32px; --out-22: 22px; --out-24: 24px; --out-52: 52px; --out-14: 14px; padding-top: var(--cols-pad-top); }
.outcome-inline > .detail-overline { margin: 0; }
.outcome-set { margin: 0; padding: var(--out-28) 0 var(--out-32); border: 0; border-top: 1px solid var(--line-soft); min-width: 0; }
.outcome-inline > .detail-overline + .outcome-set { border-top: 0; }
.outcome-set legend { float: left; width: 100%; padding: 0; font-size: var(--font-title); line-height: var(--cols-title); font-weight: var(--weight-bold); }
.outcome-set legend + * { clear: both; }
.outcome-optional { font-size: var(--font-label); font-weight: var(--weight-regular); color: var(--text-secondary); }
.outcome-help { margin: var(--space-1) 0 var(--space-4); font-size: var(--font-small); color: var(--text-secondary); }
.outcome-set > input { width: 100%; }
.outcome-inline .outcome-counter { display: flex; align-items: center; gap: var(--out-14); }
.outcome-inline .outcome-counter button {
  display: inline-flex; align-items: center; justify-content: center; width: var(--target-min); height: var(--target-min); min-height: 0; padding: 0;
  border: 1.5px solid var(--line); border-radius: 50%; background: var(--surface); color: var(--text); font-size: var(--out-22); font-weight: var(--weight-semibold);
}
.outcome-inline .outcome-counter > span { min-width: 2.25rem; text-align: center; font-size: var(--out-24); font-weight: var(--weight-heavy); }
.outcome-inline .outcome-counter small { font-size: var(--font-small); color: var(--text-secondary); }
.outcome-inline-actions { padding: var(--space-6) 0 var(--space-2); border-top: 1px solid var(--line-soft); }
.outcome-inline-actions .primary { min-height: var(--out-52); padding: 0 var(--out-28); border-radius: var(--radius-pill); font-weight: var(--weight-bold); }
</style>
