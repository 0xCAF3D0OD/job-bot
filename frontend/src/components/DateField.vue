<script setup lang="ts">
import { nextTick, ref } from "vue";

import DateTimeField from "./DateTimeField.vue";
import DateTimePanel from "./DateTimePanel.vue";
import { usePhone } from "../composables/usePhone";

// Un champ de date seule (lot 10, maquette du 8 novembre, D26) : la pilule de DateTimeField sans l'heure ; un clic
// ouvre DateTimePanel à sa place (plein écran sur téléphone). Remplace les champs de date natifs des formulaires.
// `min` et `max` bornent les jours (`min` absent : à partir d'aujourd'hui ; `null` : sans borne basse). `optional` :
// « Effacer la date » sous la pilule quand une date est choisie. Le curseur revient sur la pilule.
withDefaults(
  defineProps<{
    modelValue: string | null;
    label: string;
    title?: string;
    min?: string | null;
    max?: string;
    optional?: boolean;
    error?: string;
    // Une erreur dite ailleurs (sous le formulaire) : la pilule est seulement marquée.
    invalid?: boolean;
  }>(),
  { title: "", min: undefined, max: "", optional: false, error: "", invalid: false },
);
const emit = defineEmits<{ "update:modelValue": [value: string | null] }>();

const { phone } = usePhone();
const open = ref(false);
const root = ref<HTMLElement | null>(null);

async function back(): Promise<void> {
  open.value = false;
  await nextTick();
  root.value?.querySelector<HTMLElement>("[data-test=dt-date]")?.focus();
}
function picked(value: { date: string }): void {
  emit("update:modelValue", value.date);
  void back();
}
function clear(): void {
  emit("update:modelValue", null);
  void back();
}
function focus(): void {
  root.value?.querySelector<HTMLElement>("[data-test=dt-date]")?.focus();
}
defineExpose({ focus });
</script>

<template>
  <div
    ref="root"
    class="date-field"
  >
    <DateTimePanel
      v-if="open"
      :date="modelValue ?? ''"
      time=""
      :title="title || label"
      :with-time="false"
      :min="min"
      :max="max"
      :full="phone"
      @confirm="picked"
      @cancel="back"
    />
    <template v-else>
      <DateTimeField
        :date="modelValue ?? ''"
        time=""
        :date-label="label"
        :with-time="false"
        :compact="phone"
        :aria-invalid="error || invalid ? 'true' : undefined"
        @open="open = true"
      />
      <button
        v-if="optional && modelValue"
        type="button"
        class="link date-field-clear"
        data-test="date-clear"
        @click="clear"
      >
        Effacer la date
      </button>
      <p
        v-if="error"
        class="field-error"
        role="alert"
        data-test="field-error"
      >
        {{ error }}
      </p>
    </template>
  </div>
</template>
