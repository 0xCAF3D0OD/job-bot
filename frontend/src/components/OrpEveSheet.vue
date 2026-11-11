<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { api } from "../api/client";
import type { components } from "../api/schema";
import { sheetLines } from "../rendezVous";
import MeetingPrepSheet from "./MeetingPrepSheet.vue";

// La veille de rendez-vous par-dessus Aujourd'hui (lot du 11 novembre au soir, PR 52 ; maquette
// RendezVousFeuilleOrdinateurV2) : la tâche « Préparer le rendez-vous ORP » ouvre l'écran « Rendez-vous ORP » en
// panneau, sans quitter la page. Il charge lui-même le rendez-vous et sa feuille (docs/83) à l'ouverture ; cocher
// une question l'enregistre, comme dans Candidatures › Rendez-vous.
type Page = components["schemas"]["MeetingPage"];
type Question = components["schemas"]["QuestionIO"];

const props = defineProps<{ open: boolean }>();
const emit = defineEmits<{ close: []; failed: [] }>();

const page = ref<Page | null>(null);
const lines = computed(() => (page.value ? sheetLines(page.value.preparation) : []));

watch(
  () => props.open,
  async (open) => {
    if (!open) return;
    const { data } = await api.GET("/api/orp-meeting");
    if (data?.meeting) page.value = data;
    else emit("failed");
  },
  { immediate: true },
);

async function toggle(question: Question, checked: boolean): Promise<void> {
  if (!page.value) return;
  const questions = page.value.preparation.questions.map((q) => (q.key === question.key ? { ...q, checked } : q));
  const { data } = await api.PUT("/api/orp-meeting/questions", { body: { questions } });
  if (data) page.value = data;
}
</script>

<template>
  <MeetingPrepSheet
    v-if="page?.meeting"
    :open="open"
    :at="page.meeting.starts_at"
    :place="page.meeting.place"
    :lines="lines"
    :questions="page.preparation.questions"
    pdf="/api/orp-meeting/feuille.pdf"
    @close="emit('close')"
    @toggle="toggle"
  />
</template>
