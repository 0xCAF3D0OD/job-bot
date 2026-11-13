<script setup lang="ts">
import FormField from "./FormField.vue";
import { computed, nextTick, ref, toRef, watch } from "vue";

import type { components } from "../api/schema";
import { usePhone } from "../composables/usePhone";
import { grow } from "../composables/useAutoGrow";
import { useOrpOutcome } from "../composables/useOrpOutcome";
import { dateText } from "../rendezVous";
import BottomSheet from "./BottomSheet.vue";
import DateTimeField from "./DateTimeField.vue";
import DateTimePanel from "./DateTimePanel.vue";

// Ce qui a été convenu au rendez-vous ORP (docs/83 §1 ; maquettes RendezVous et RendezVousOrdinateur, état
// `noter`, 7.11.2026) : une feuille du bas sur téléphone, un dialogue au centre sur ordinateur. Les recherches
// demandées en compteur, les mesures, le prochain rendez-vous (jobA1 le crée dans « À venir ») et une remarque.
// Les champs et l'enregistrement : useOrpOutcome.
type Page = components["schemas"]["MeetingPage"];
type Meeting = components["schemas"]["MeetingOut"];

const props = defineProps<{ meeting: Meeting | null; target: number | null }>();
const emit = defineEmits<{ saved: [page: Page]; close: [] }>();
const { phone } = usePhone();

const { count, measures, nextDay, nextTime, note, message, busy, before, step, save } = useOrpOutcome(
  toRef(props, "meeting"),
  toRef(props, "target"),
  (page) => emit("saved", page),
);
// Maquette du 8 novembre (D26) : les pilules date et heure ; le sélecteur prend la place du formulaire.
const picking = ref<"" | "date" | "time">("");
watch(
  () => props.meeting,
  () => (picking.value = ""),
);
// « Mesures décidées » : une zone de texte d'une ligne qui grandit avec le texte. Entrée enregistre, comme dans un
// champ d'une ligne. Sans field-sizing (Firefox), la hauteur d'un texte déjà saisi est ajustée à l'ouverture.
const measuresArea = ref<HTMLTextAreaElement | null>(null);
function submitFrom(event: KeyboardEvent): void {
  (event.target as HTMLTextAreaElement).form?.requestSubmit();
}
watch(
  () => [props.meeting, picking.value],
  async () => {
    await nextTick();
    const native = typeof CSS !== "undefined" && typeof CSS.supports === "function" && CSS.supports("field-sizing", "content");
    if (measuresArea.value && !native) grow(measuresArea.value);
  },
);
function focusPill(which: "date" | "time"): void {
  void nextTick(() => document.querySelector<HTMLElement>(`#orp-outcome [data-test=dt-${which}]`)?.focus());
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

const subtitle = computed(() => (props.meeting ? `Rendez-vous ORP du ${dateText(props.meeting.starts_at).toLowerCase()}` : ""));
</script>

<template>
  <BottomSheet
    :open="!!meeting"
    title="Ce qui a été convenu"
    :subtitle="subtitle"
    class="outcome-sheet"
    data-test="outcome-sheet"
    @close="emit('close')"
  >
    <DateTimePanel
      v-if="picking"
      :date="nextDay"
      :time="nextTime || '09:00'"
      title="Prochain rendez-vous"
      :full="phone"
      @confirm="picked"
      @cancel="cancelPick"
    />
    <form
      v-else
      id="orp-outcome"
      class="outcome-form"
      data-test="outcome-form"
      @submit.prevent="save"
    >
      <div
        class="outcome-field"
        role="group"
        aria-labelledby="outcome-count-label"
      >
        <span id="outcome-count-label">Recherches demandées par mois</span>
        <div class="outcome-counter">
          <button
            type="button"
            aria-label="Une de moins"
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
            data-test="outcome-more"
            @click="step(1)"
          >
            +
          </button>
          <small v-if="before">{{ before }}</small>
        </div>
      </div>
      <FormField
        v-slot="f"
        label="Mesures décidées"
        optional
        hint="Ex. : cours, stage, programme"
      >
        <textarea
          :id="f.id"
          ref="measuresArea"
          v-model="measures"
          :aria-describedby="f.describedby"
          rows="1"
          maxlength="1000"
          data-test="outcome-measures"
          @keydown.enter.prevent="submitFrom"
        />
      </FormField>
      <div
        class="outcome-field outcome-next"
        role="group"
        aria-labelledby="outcome-next-label"
        data-test="outcome-next"
      >
        <span id="outcome-next-label">Prochain rendez-vous</span>
        <DateTimeField
          :date="nextDay"
          :time="nextTime"
          :open="picking"
          :compact="phone"
          @open="picking = $event"
        />
        <small>jobA1 le met dans tes Rendez-vous.</small>
      </div>
      <FormField
        v-slot="f"
        label="Autre chose à retenir"
        optional
        hint="Ex. : ce que ton conseiller t’a demandé"
      >
        <textarea
          :id="f.id"
          v-model="note"
          :aria-describedby="f.describedby"
          rows="3"
          maxlength="4000"
          data-test="outcome-note"
        />
      </FormField>
      <p
        v-if="message"
        role="status"
        class="notice error"
      >
        {{ message }}
      </p>
    </form>
    <template
      v-if="!picking"
      #actions
    >
      <button
        v-if="!phone"
        type="button"
        class="secondary"
        @click="emit('close')"
      >
        Annuler
      </button>
      <button
        type="submit"
        form="orp-outcome"
        class="primary"
        :disabled="busy"
        data-test="outcome-save"
      >
        Enregistrer
      </button>
    </template>
  </BottomSheet>
</template>

<style>
/* Valeurs de la maquette : 560 px au centre sur ordinateur ; champs de 48 px aux bords de 1,5 px, coins de 12 ;
   le compteur en ronds de 44 px, le nombre en 24 très gras. */
.outcome-sheet { --out-6: 6px; --out-14: 14px; --out-18: 18px; --out-21: 21px; --out-22: 22px; --out-24: 24px; background: var(--surface); }
/* Le titre de la maquette : 21 px sur téléphone, 22 px sur ordinateur, en gras appuyé. */
.outcome-sheet .sheet-title { font-size: var(--out-21); font-weight: var(--weight-heavy); }
@media (min-width: 1024px) { .outcome-sheet .sheet-title { font-size: var(--out-22); } }
@media (min-width: 821px) { .sheet.outcome-sheet { width: min(560px, calc(100vw - 2 * var(--space-4))); } }
.outcome-form { display: flex; flex-direction: column; gap: var(--out-18); }
.outcome-field { display: flex; flex-direction: column; gap: var(--out-6); min-width: 0; }
.outcome-field > span, #outcome-count-label { font-size: var(--font-small); font-weight: var(--weight-bold); }
.outcome-field em { font-style: normal; font-weight: var(--weight-regular); color: var(--text-secondary); }
.outcome-field :is(input, textarea) {
  box-sizing: border-box; width: 100%; min-width: 0; padding: var(--space-3) var(--out-14); border: 1.5px solid var(--field-border);
  border-radius: var(--radius-sm); background: var(--surface); color: var(--text); font: inherit; font-size: var(--font-body);
}
.outcome-field input { height: var(--btn-secondary); padding-block: 0; }
.outcome-field textarea { resize: none; }
.outcome-counter { display: flex; align-items: center; gap: var(--out-14); }
.outcome-counter button {
  display: inline-flex; align-items: center; justify-content: center; width: var(--target-min); height: var(--target-min); min-height: 0; padding: 0; border: 1.5px solid var(--line); border-radius: 50%;
  background: var(--surface); color: var(--text); font-size: var(--out-22); font-weight: var(--weight-semibold);
}
.outcome-counter > span { min-width: 2.25rem; text-align: center; font-size: var(--out-24); font-weight: var(--weight-heavy); }
.outcome-counter small, .outcome-next small { font-size: var(--font-small); color: var(--text-secondary); }
.outcome-next { display: grid; gap: var(--out-6); }
/* Le pied : sa marge négative ne vaut qu'entre 600 et 820 px, où la feuille a 16 px de marge intérieure. Ailleurs la
   feuille n'en a pas, et le pied dépassait de 16 px du volet de 440 px (défaut du 13 novembre). */
.outcome-sheet .sheet-actions { justify-content: flex-end; border-top: 1px solid var(--line); }
.outcome-sheet .sheet-actions > button { white-space: nowrap; }
@media (min-width: 600px) and (max-width: 820px) { .outcome-sheet .sheet-actions { margin: 0 calc(var(--space-4) * -1); padding: var(--space-3) var(--space-4) 0; } }
/* « Mesures décidées » : une ligne de 56 px au départ (le trait compris, comme le champ commun), le champ grandit avec le
   texte au lieu de le couper. */
.outcome-sheet textarea[data-test="outcome-measures"] { min-height: var(--ff-h); padding-block: calc(var(--space-4) - 1px); }
.outcome-sheet .sheet-actions > button { min-height: var(--btn-secondary); padding: 0 var(--space-6); border-radius: var(--radius-pill); font-weight: var(--weight-bold); }
</style>
