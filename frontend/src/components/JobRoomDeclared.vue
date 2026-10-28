<script setup lang="ts">
import { ref } from "vue";

import { api } from "../api/client";
import { dateInSentence } from "../dates";
import AppIcon from "./AppIcon.vue";

// Saisie dans Job-Room (docs/70 §6) : « Marquer comme déclarée », ou la date et « Annuler ».
// La même marque que « C'est déclaré » dans l'extension.
const props = defineProps<{ applicationId: number; declaredAt: string | null }>();
const emit = defineEmits<{ changed: [] }>();

const busy = ref(false);

async function set(declared: boolean): Promise<void> {
  busy.value = true;
  try {
    const params = { params: { path: { application_id: props.applicationId } } };
    if (declared) await api.PUT("/api/applications/{application_id}/job-room", params);
    else await api.DELETE("/api/applications/{application_id}/job-room", params);
    emit("changed");
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <p
    class="job-room-declared"
    data-test="job-room-declared"
  >
    <template v-if="declaredAt">
      <span class="done with-icon"><AppIcon name="done" />Déclarée dans Job-Room {{ dateInSentence(`${declaredAt}T12:00:00`) }}</span>
      <button
        type="button"
        class="link"
        :disabled="busy"
        data-test="job-room-undo"
        @click="set(false)"
      >
        Annuler
      </button>
    </template>
    <button
      v-else
      type="button"
      class="link"
      :disabled="busy"
      data-test="job-room-mark"
      @click="set(true)"
    >
      Marquer comme déclarée dans Job-Room
    </button>
  </p>
</template>
