<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed } from "vue";

import { api, type JobRun, type StatusResponse } from "../api/client";
import ScoringCard from "./ScoringCard.vue";
import SettingCard from "./SettingCard.vue";
import SettingRow from "./SettingRow.vue";
import { indicators, sinceText, type Level } from "./status";

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
  if (status.value?.database?.up_to_date) {
    try {
      const { data } = await api.GET("/api/job-runs", { params: { query: { limit: 10 } } });
      runs.value = Array.isArray(data) ? data : [];
    } catch {
      runs.value = [];
    }
  } else {
    runs.value = [];
  }
  loaded.value = true;
}

const lights = computed(() => indicators(status.value));

// L'état écrit en mots, pas seulement en couleur (WCAG 1.4.1).
const levelLabel: Record<Level, string> = { ok: "Fonctionne", warn: "À vérifier", down: "En panne" };
const statusLabel: Record<JobRun["status"], string> = {
  running: "En cours",
  success: "Réussie",
  failure: "Échec",
};
const statusLevel: Record<JobRun["status"], Level> = { running: "warn", success: "ok", failure: "down" };

// Une tâche en une phrase : quand, ce qui est entré et sorti, l'erreur s'il y en a une.
function runLine(run: JobRun): string {
  const counts = `entrées ${run.items_in ?? "–"}, sorties ${run.items_out ?? "–"}`;
  const line = `${sinceText(run.started_at)} · ${counts}`;
  return run.error ? `${line} · ${run.error}` : line;
}

onMounted(() => {
  void refresh();
  timer = setInterval(() => void refresh(), REFRESH_MS);
});
onUnmounted(() => clearInterval(timer));
</script>

<template>
  <!-- L'état du service (1.6.67, planche « 5. Réglages ») : une colonne de cartes ; chaque voyant est
       une ligne, son état écrit en mots à droite. Les tâches deviennent des lignes aussi : un tableau
       à quatre colonnes ne tient pas sur un téléphone. -->
  <div class="setting-cards status-panel">
    <SettingCard
      v-if="loaded"
      data-test="indicators"
    >
      <SettingRow
        v-for="light in lights"
        :key="light.label"
        :title="light.label"
        :description="light.detail.charAt(0).toUpperCase() + light.detail.slice(1)"
        :class="light.level"
        data-test="indicator"
      >
        <span :class="['state-word', light.level]">{{ levelLabel[light.level] }}</span>
      </SettingRow>
    </SettingCard>

    <ScoringCard />

    <SettingCard
      v-if="loaded"
      data-test="runs"
    >
      <SettingRow
        title="Dernières tâches"
        :description="runs.length ? 'Les plus récentes, mises à jour toutes les 30 secondes.' : 'Aucune exécution enregistrée.'"
      />
      <SettingRow
        v-for="run in runs"
        :key="run.id"
        :title="run.job"
        :description="runLine(run)"
        data-test="run"
      >
        <span :class="['state-word', statusLevel[run.status]]">{{ statusLabel[run.status] }}</span>
      </SettingRow>
    </SettingCard>
  </div>
</template>
