<script setup lang="ts">
import { computed, nextTick, ref } from "vue";

import { api, type Application } from "../api/client";
import { todayDay } from "../dates";
import DateTimeField from "./DateTimeField.vue";
import DateTimePanel from "./DateTimePanel.vue";
import FormField from "./FormField.vue";

// « Ajouter un entretien » sur ordinateur, dans le panneau de droite de Rendez-vous (planches AjouterEntretienOrdinateur
// et AjouterEntretienOrdinateurSombre, §72p ; accord de Kevin du 19.11.2026) : le tour (1er, 2e, Final), la date et
// l'heure, le lieu ou le lien visio. Un entretien déjà prévu reste un élément à part (« À noter » jusqu'à son point) ;
// le nouveau va dans « À venir ». Le tour proposé suit le nombre d'entretiens déjà connus.
type Round = "1" | "2" | "final";

const props = defineProps<{ application: Application }>();
const emit = defineEmits<{ added: [] }>();

const ROUNDS: { key: Round; label: string }[] = [
  { key: "1", label: "1er" },
  { key: "2", label: "2e" },
  { key: "final", label: "Final" },
];
// L'entretien prévu de la candidature compte, sauf si son retour est déjà fait (même jour).
const a = props.application;
const atDay = a.interview_at ? todayDay(new Date(a.interview_at)) : "";
const pending = atDay && !a.interviews?.some((i) => i.held_at === atDay) ? 1 : 0;
const known = (a.interviews?.length ?? 0) + (a.planned?.length ?? 0) + pending;
const round = ref<Round>(known === 0 ? "1" : known === 1 ? "2" : "final");
const day = ref("");
const time = ref("");
const place = ref("");
const picking = ref<"" | "date" | "time">("");
const dayError = ref("");
const timeError = ref("");
const message = ref("");
const busy = ref(false);
const form = ref<HTMLElement | null>(null);

const line = computed(() => `${props.application.job_title || "Poste non indiqué"} · ${props.application.company}`);

function picked(value: { date: string; time: string }): void {
  day.value = value.date;
  time.value = value.time;
  const which = picking.value;
  picking.value = "";
  if (day.value) dayError.value = "";
  if (time.value) timeError.value = "";
  void nextTick(() => form.value?.querySelector<HTMLElement>(`[data-test=dt-${which || "date"}]`)?.focus());
}
function cancelPick(): void {
  const which = picking.value;
  picking.value = "";
  void nextTick(() => form.value?.querySelector<HTMLElement>(`[data-test=dt-${which || "date"}]`)?.focus());
}

async function add(): Promise<void> {
  dayError.value = day.value ? "" : "Indique la date de l’entretien.";
  timeError.value = time.value ? "" : "Indique l’heure.";
  if (dayError.value || timeError.value) {
    await nextTick();
    form.value?.querySelector<HTMLElement>(dayError.value ? "[data-test=dt-date]" : "[data-test=dt-time]")?.focus();
    return;
  }
  busy.value = true;
  message.value = "";
  const { response } = await api.POST("/api/applications/{application_id}/interview-plan", {
    params: { path: { application_id: props.application.id } },
    body: { round: round.value, at: new Date(`${day.value}T${time.value}`).toISOString(), place: place.value || null },
  });
  busy.value = false;
  if (!response.ok) {
    message.value = "Entretien non ajouté. Réessaie dans un instant.";
    return;
  }
  emit("added");
}
</script>

<template>
  <DateTimePanel
    v-if="picking"
    :date="day"
    :time="time"
    title="Ajouter un entretien"
    @confirm="picked"
    @cancel="cancelPick"
  />
  <article
    v-else
    ref="form"
    class="rdv-open fpo aje"
    aria-labelledby="aje-title"
    data-test="rdv-detail-add"
  >
    <div class="rdv-open-head">
      <div class="rdv-open-head-text">
        <h2 id="aje-title">
          Ajouter un entretien
        </h2>
        <p data-test="aje-line">
          {{ line }}
        </p>
      </div>
    </div>
    <section aria-labelledby="aje-round">
      <h3
        id="aje-round"
        class="rdv-open-title"
      >
        Quel entretien ?
      </h3>
      <div
        class="fpo-seg"
        role="radiogroup"
        aria-labelledby="aje-round"
      >
        <button
          v-for="item in ROUNDS"
          :key="item.key"
          type="button"
          role="radio"
          :aria-checked="round === item.key"
          :class="{ on: round === item.key }"
          :data-test="`aje-round-${item.key}`"
          @click="round = item.key"
        >
          {{ item.label }}
        </button>
      </div>
    </section>
    <div>
      <DateTimeField
        :date="day"
        :time="time"
        :open="picking"
        outlined
        :aria-invalid="dayError || timeError ? 'true' : undefined"
        @open="picking = $event"
      />
      <p
        v-if="dayError || timeError"
        class="field-error"
        data-test="aje-when-error"
      >
        {{ dayError || timeError }}
      </p>
    </div>
    <FormField
      v-slot="field"
      label="Lieu ou lien visio"
    >
      <input
        :id="field.id"
        v-model="place"
        type="text"
        maxlength="1000"
        autocomplete="off"
        data-test="aje-place"
      >
    </FormField>
    <p
      v-if="message"
      class="fpo-error"
      role="alert"
      data-test="aje-error"
    >
      {{ message }}
    </p>
    <div class="fpo-foot">
      <button
        type="button"
        class="primary fpo-save"
        :disabled="busy"
        data-test="aje-add"
        @click="add"
      >
        Ajouter
      </button>
    </div>
  </article>
</template>

<style>
/* Valeurs du HTML de la planche AjouterEntretienOrdinateur (§72p) : le cadre de Rendez-vous ouvert (.rdv-open), les
   trois boutons du tour comme le ressenti de Faire le point (.fpo-seg), la date et l'heure côte à côte (1fr 160, écart
   16), champs de 56 au trait 1,5, coins de 12, libellé flottant ; « Ajouter » plein de 48, à gauche. */
.aje .dt-field.dt-field-outlined { gap: var(--space-4); }
.aje .dt-field-outlined .dt-field-date { flex: 1 1 0; }
.aje .dt-field-outlined .dt-field-time { flex: 0 0 160px; }
.aje .dt-field-outlined .dt-pill > .icon:last-child { display: none; }
</style>
