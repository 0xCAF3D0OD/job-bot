<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed } from "vue";

import { api, type JobRun, type StatusResponse } from "../api/client";
import ScoringCard from "./ScoringCard.vue";
import { indicators, sinceText } from "./status";

const REFRESH_MS = 30_000;

const status = ref<StatusResponse | null>(null);
const runs = ref<JobRun[]>([]);
const loaded = ref(false);
let timer: ReturnType<typeof setInterval> | undefined;

async function refresh(): Promise<void> {
  try {
    const { data } = await api.GET("/api/status");
    status.value = data ?? null;
  } catch {
    status.value = null;
  }
  if (status.value?.database.up_to_date) {
    try {
      const { data } = await api.GET("/api/job-runs", { params: { query: { limit: 10 } } });
      runs.value = data ?? [];
    } catch {
      runs.value = [];
    }
  } else {
    runs.value = [];
  }
  loaded.value = true;
}

const lights = computed(() => indicators(status.value));

const statusLabel: Record<JobRun["status"], string> = {
  running: "en cours",
  success: "réussie",
  failure: "échec",
};

onMounted(() => {
  void refresh();
  timer = setInterval(() => void refresh(), REFRESH_MS);
});
onUnmounted(() => clearInterval(timer));
</script>

<template>
  <div class="panel">
    <ul
      v-if="loaded"
      class="indicators"
    >
      <li
        v-for="light in lights"
        :key="light.label"
        :class="['indicator', light.level]"
        data-test="indicator"
      >
        <span
          class="dot"
          aria-hidden="true"
        />
        <strong>{{ light.label }}</strong>
        <span class="detail">{{ light.detail }}</span>
      </li>
    </ul>

    <ScoringCard />

    <h2 class="section-title">
      Dernières tâches
    </h2>
    <table
      v-if="runs.length"
      class="runs"
    >
      <thead>
        <tr>
          <th>Tâche</th>
          <th>Début</th>
          <th>Statut</th>
          <th>Entrées / sorties</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="run in runs"
          :key="run.id"
          data-test="run"
        >
          <td>{{ run.job }}</td>
          <td :title="run.started_at">
            {{ sinceText(run.started_at) }}
          </td>
          <td :class="['run-status', run.status]">
            {{ statusLabel[run.status] }}
            <span
              v-if="run.error"
              class="detail"
            >{{ run.error }}</span>
          </td>
          <td>{{ run.items_in ?? "–" }} / {{ run.items_out ?? "–" }}</td>
        </tr>
      </tbody>
    </table>
    <p
      v-else-if="loaded"
      class="muted"
    >
      Aucune exécution enregistrée.
    </p>
  </div>
</template>
