<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api, type AlertsPage } from "../api/client";
import AlertsPanel from "../components/AlertsPanel.vue";
import AlertsSummary from "../components/AlertsSummary.vue";
import AlertsWizard from "../components/AlertsWizard.vue";
import JournalPanel from "../components/JournalPanel.vue";

// Onglet Alertes (docs/20 §1, docs/21 §4) : l'assistant tant que rien n'est en place,
// ensuite un résumé ; le tableau complet dans « Gérer mes alertes » ; le journal replié.
const page = ref<AlertsPage | null>(null);
const mode = ref<"auto" | "wizard" | "manage">("auto");
const journalOpen = ref(false);

// Rien de créé ni reçu : on commence par l'assistant.
const nothingYet = computed(
  () => !!page.value && page.value.searches.every((s) => !s.active || s.cells.every((c) => c.status === "todo")),
);
const view = computed(() => (mode.value !== "auto" ? mode.value : nothingYet.value ? "wizard" : "summary"));

async function load(): Promise<void> {
  const { data } = await api.GET("/api/alert-searches");
  if (data) page.value = data;
}

async function closeManage(): Promise<void> {
  mode.value = "auto";
  await load();
}

onMounted(() => void load());
</script>

<template>
  <section class="jobs-body">
    <template v-if="page">
      <AlertsWizard
        v-if="view === 'wizard'"
        :page="page"
        @updated="page = $event"
        @done="mode = 'auto'"
      />
      <template v-else-if="view === 'manage'">
        <button
          type="button"
          class="link"
          data-test="close-manage"
          @click="closeManage"
        >
          ← Retour au résumé
        </button>
        <AlertsPanel />
      </template>
      <AlertsSummary
        v-else
        :page="page"
        @manage="mode = 'manage'"
        @restart="mode = 'wizard'"
      />
    </template>

    <details
      class="journal-toggle"
      data-test="journal-toggle"
      @toggle="journalOpen = ($event.target as HTMLDetailsElement).open"
    >
      <summary>Voir les alertes reçues</summary>
      <JournalPanel v-if="journalOpen" />
    </details>
  </section>
</template>
