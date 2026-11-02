<script setup lang="ts">
import { ref, watch } from "vue";

import BottomSheet from "./BottomSheet.vue";
import BusyButton from "./BusyButton.vue";
import GroupedList from "./GroupedList.vue";
import GroupedRow from "./GroupedRow.vue";

// « Pas vrai » (demande de Kevin du 30.10.2026, repères de Design) : la phrase citée en gris, puis
// deux choix en radios, ligne entière cliquable : la retirer, ou la réécrire d'après le profil.
// « Corriger » applique ; le ✕ ferme, sans « Annuler ». Dans les deux cas, l'affirmation rejoint les
// interdits du profil : jobA1 ne l'écrira plus.
export type FalseClaimMode = "remove" | "rewrite";
const props = withDefaults(
  defineProps<{ open: boolean; sentence: string; busy?: boolean; error?: string; onlySentence?: boolean }>(),
  { busy: false, error: "", onlySentence: false },
);
const emit = defineEmits<{ close: []; confirm: [mode: FalseClaimMode] }>();

const mode = ref<FalseClaimMode>("remove");
watch(
  () => [props.open, props.onlySentence],
  () => {
    // La seule phrase de la lettre ne peut pas être retirée : la réécrire.
    mode.value = props.onlySentence ? "rewrite" : "remove";
  },
);
const CHOICES: { value: FalseClaimMode; label: string; description: string }[] = [
  { value: "remove", label: "Retirer la phrase", description: "Elle disparaît de cette version." },
  { value: "rewrite", label: "La réécrire d'après mon profil", description: "Une nouvelle version, relue." },
];
</script>

<template>
  <BottomSheet
    :open="open"
    title="Pas vrai"
    data-test="false-claim-sheet"
    @close="emit('close')"
  >
    <blockquote
      class="false-claim-quote"
      data-test="false-claim-quote"
    >
      « {{ sentence }} »
    </blockquote>
    <GroupedList :level="3">
      <GroupedRow
        v-for="choice in CHOICES"
        :key="choice.value"
        :title="choice.label"
        :description="choice.description"
        label
        :data-test="`false-claim-${choice.value}`"
      >
        <template #start>
          <input
            v-model="mode"
            type="radio"
            name="false-claim-mode"
            :value="choice.value"
            :disabled="choice.value === 'remove' && onlySentence"
          >
        </template>
      </GroupedRow>
    </GroupedList>
    <p
      v-if="error"
      class="notice error"
      role="alert"
    >
      {{ error }}
    </p>
    <template #actions>
      <BusyButton
        class="primary"
        :busy="busy"
        busy-label="Réécriture…"
        data-test="false-claim-confirm"
        @click="emit('confirm', mode)"
      >
        Corriger
      </BusyButton>
    </template>
  </BottomSheet>
</template>
