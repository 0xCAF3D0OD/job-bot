<script setup lang="ts">
import { computed, nextTick, onMounted, ref, toRef, watch } from "vue";

import type { components } from "../api/schema";
import { grow } from "../composables/useAutoGrow";
import { useOrpOutcome } from "../composables/useOrpOutcome";
import { dateText, timeAndPlace } from "../rendezVous";
import AppIcon from "./AppIcon.vue";
import FormField from "./FormField.vue";

// Ce qui a été convenu, dans le détail d'un rendez-vous ORP passé, sur ordinateur (récapitulatif du 11 novembre,
// PR 31 ; maquette CandidaturesOrdinateurB, onglet Rendez-vous) : « Objectif de recherches » et « Mesures décidées »
// côte à côte, puis « Prochain rendez-vous » sur toute la largeur (une ligne et « Ajouter », plus de formulaire ici),
// et la barre « Enregistrer » collée en bas de la carte. La colonne « Le rendez-vous » est partie : elle répétait
// l'en-tête. La remarque libre n'a pas de champ ici : celle qui est notée est gardée, comme le prochain rendez-vous
// déjà noté.
type Page = components["schemas"]["MeetingPage"];
type Meeting = components["schemas"]["MeetingOut"];

const props = defineProps<{ meeting: Meeting; target: number | null; next?: Meeting | null }>();
const emit = defineEmits<{ saved: [page: Page]; add: [] }>();

const { count, measures, message, busy, before, step, save } = useOrpOutcome(
  toRef(props, "meeting"),
  toRef(props, "target"),
  (page) => emit("saved", page),
);

// « Mesures décidées » : comme dans le volet (décision du 13 novembre), une zone de texte d'une ligne qui grandit
// avec le texte. Entrée enregistre, comme dans un champ d'une ligne. Sans field-sizing (Firefox), la hauteur d'un
// texte déjà noté est ajustée à l'affichage et quand on passe à un autre rendez-vous.
const measuresArea = ref<HTMLTextAreaElement | null>(null);
function submitFrom(event: KeyboardEvent): void {
  (event.target as HTMLTextAreaElement).form?.requestSubmit();
}
async function fit(): Promise<void> {
  await nextTick();
  const native = typeof CSS !== "undefined" && typeof CSS.supports === "function" && CSS.supports("field-sizing", "content");
  if (measuresArea.value && !native) grow(measuresArea.value);
}
onMounted(fit);
watch(() => props.meeting, fit);

// « Vendredi 20 novembre, 10 h · ORP de Lausanne », ou rien de noté.
const nextLine = computed(() => (props.next ? `${dateText(props.next.starts_at)}, ${timeAndPlace(props.next.starts_at, props.next.place)}` : ""));
</script>

<template>
  <form
    class="outcome-inline"
    aria-labelledby="outcome-inline-title"
    data-test="outcome-inline"
    @submit.prevent="save"
  >
    <p
      id="outcome-inline-title"
      class="detail-overline"
    >
      Ce qui a été convenu
    </p>
    <div class="outcome-pair">
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
          Un cours, un stage ou un programme.
        </p>
        <FormField
          v-slot="{ id }"
          label="Cours, stage ou programme"
        >
          <textarea
            :id="id"
            ref="measuresArea"
            v-model="measures"
            rows="1"
            maxlength="1000"
            aria-describedby="outcome-help-measures"
            data-test="outcome-measures"
            @keydown.enter.prevent="submitFrom"
          />
        </FormField>
      </fieldset>
    </div>
    <div
      class="outcome-next"
      data-test="outcome-next"
    >
      <span class="outcome-next-text">
        <strong>Prochain rendez-vous</strong>
        <span>{{ nextLine || "Pas encore noté. jobA1 prépare ta fiche la veille." }}</span>
      </span>
      <button
        v-if="!next"
        type="button"
        class="outcome-next-add"
        data-test="outcome-next-add"
        @click="emit('add')"
      >
        <AppIcon name="plus" />Ajouter
      </button>
    </div>
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
      <span>L’objectif et les mesures se mettent à jour partout.</span>
    </div>
  </form>
</template>

<style>
/* Valeurs de la maquette (CandidaturesOrdinateurB, onglet Rendez-vous, 11 novembre) : un trait puis le sur-titre à
   24 ; les deux parties côte à côte (écart 40), chacune à 20 du sur-titre, le titre de 18 en 700, « (facultatif) »
   en 15 normal, la phrase d’aide en 14 (4 au-dessus, 16 dessous) ; compteur en ronds de 44 ; la ligne « Prochain
   rendez-vous » entre deux traits ; « Enregistrer » plein de 52, collé en bas de la carte. */
.outcome-inline { --out-28: 28px; --out-22: 22px; --out-52: 52px; --out-14: 14px; --out-6: 6px; --out-18: 18px; margin-top: var(--space-3); padding-top: var(--space-6); border-top: 1px solid var(--line-soft); }
.outcome-inline > .detail-overline { margin: 0; font-size: var(--label-caps); font-weight: var(--weight-bold); letter-spacing: 0.06em; text-transform: uppercase; color: var(--text-secondary); }
.outcome-pair { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: calc(var(--space-8) + var(--space-2)); padding-bottom: var(--space-6); }
.outcome-set { margin: 0; padding: var(--space-5) 0 0; border: 0; min-width: 0; }
.outcome-set legend { float: left; width: 100%; padding: 0; font-size: var(--font-title); height: var(--space-6); line-height: var(--space-6); font-weight: var(--weight-bold); }
.outcome-set legend + * { clear: both; }
.outcome-optional { font-size: var(--font-label); font-weight: var(--weight-regular); color: var(--text-secondary); }
.outcome-help { margin: var(--space-1) 0 var(--space-4); font-size: var(--font-small); line-height: var(--space-5); color: var(--text-secondary); }
/* « Mesures décidées » : une ligne de 56 px au départ (le trait compris, comme le champ commun), le champ grandit avec le
   texte au lieu de le couper. */
.outcome-inline textarea[data-test="outcome-measures"] { min-height: var(--ff-h); padding-block: calc(var(--space-4) - 1px); }
.outcome-inline .outcome-counter { display: flex; align-items: center; gap: var(--out-14); }
.outcome-inline .outcome-counter button {
  display: inline-flex; align-items: center; justify-content: center; width: var(--target-min); height: var(--target-min); min-height: 0; padding: 0;
  border: 1.5px solid var(--line); border-radius: 50%; background: var(--surface); color: var(--text); font-size: var(--out-22); font-weight: var(--weight-semibold);
}
.outcome-inline .outcome-counter > span { min-width: var(--space-8); text-align: center; font-size: var(--out-22); font-weight: var(--weight-heavy); }
.outcome-inline .outcome-counter small { font-size: var(--font-small); color: var(--text-secondary); }
.outcome-next { display: flex; align-items: center; gap: var(--space-4); padding: var(--space-5) 0; border-top: 1px solid var(--line-soft); }
.outcome-next-text { flex: 1; min-width: 0; }
.outcome-next-text strong { display: block; font-size: var(--font-title); line-height: var(--space-6); font-weight: var(--weight-bold); }
.outcome-next-text span { display: block; margin-top: calc(var(--space-1) / 2); font-size: var(--font-small); color: var(--text-secondary); }
button.outcome-next-add, button.outcome-next-add:hover:not(:disabled) {
  flex: none; display: inline-flex; align-items: center; gap: var(--out-6); height: var(--target-min); min-height: var(--target-min); padding: 0 var(--out-18);
  border: 1.5px solid var(--line-strong); border-radius: var(--radius-pill); background: var(--surface); color: var(--text); font-size: var(--font-label); font-weight: var(--weight-bold);
}
.outcome-inline-actions { position: sticky; bottom: 0; display: flex; align-items: center; gap: var(--space-4); padding: var(--space-4) 0; background: var(--surface); border-top: 1px solid var(--line-soft); }
.outcome-inline-actions .primary { flex: none; min-height: var(--out-52); padding: 0 var(--out-28); border-radius: var(--radius-pill); font-weight: var(--weight-bold); }
.outcome-inline-actions > span { font-size: var(--font-small); color: var(--text-secondary); }
</style>
