<script setup lang="ts">
import type { components } from "../../api/schema";
import { dayShort } from "../../bilanText";
import { KINDS } from "../../interviewLabels";
import InterviewInsights from "../InterviewInsights.vue";

// « Entretiens » déplié (1.6.62) : la liste (date, entreprise, type, état), puis, sans second
// repliable, les enseignements des retours, les pistes de l'IA et l'entraînement (InterviewInsights).
defineProps<{ lines: components["schemas"]["InterviewLineOut"][] }>();

function state(line: components["schemas"]["InterviewLineOut"]): string {
  if (line.state === "upcoming") return "à venir";
  if (line.state === "rejected") return "pas retenu";
  if (line.state === "rated") return `ressenti ${line.rating}/5`;
  return "retour à faire";
}
</script>

<template>
  <div
    class="bilan-interviews"
    data-test="bilan-interviews"
  >
    <ul
      v-if="lines.length"
      class="bilan-interview-list"
    >
      <li
        v-for="line in lines"
        :key="line.application_id"
        :data-test="`interview-${line.application_id}`"
      >
        <span class="bilan-interview-day">{{ dayShort.format(new Date(`${line.day}T12:00:00`)) }}</span>
        <span class="bilan-interview-main">
          <strong>{{ line.company }}</strong>
          <span v-if="line.kind">{{ KINDS[line.kind] ?? line.kind }}</span>
        </span>
        <span :class="['bilan-interview-state', line.state]">{{ state(line) }}</span>
      </li>
    </ul>
    <template v-if="lines.length">
      <h3 class="bilan-subtitle">
        Enseignements
      </h3>
      <InterviewInsights bare />
    </template>
    <p
      v-else
      class="hint"
    >
      Aucun entretien pour l'instant.
    </p>
  </div>
</template>
