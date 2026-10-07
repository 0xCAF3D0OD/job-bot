<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { api } from "../api/client";
import type { JobsTab } from "../router";

// Rubrique Candidatures (docs/19 §2) : quatre onglets toujours visibles sous le titre.
const route = useRoute();
const tab = computed<JobsTab>(() => (route.meta.tab as JobsTab | undefined) ?? "offres");
const counts = ref({ offres: 0, suivi: 0, preuves: 0 });

const TABS: { key: JobsTab; label: string; path: string; title: string; hint: string }[] = [
  { key: "offres", label: "Offres", path: "/candidatures/offres", title: "Les offres pour toi", hint: "à examiner" },
  { key: "suivi", label: "Suivi", path: "/candidatures/suivi", title: "Tes candidatures", hint: "à relancer" },
  {
    key: "preuves",
    label: "Preuves ORP",
    path: "/candidatures/preuves",
    title: "Preuves de recherches d'emploi",
    hint: "ligne(s) à compléter",
  },
  { key: "journal", label: "Journal des recherches", path: "/candidatures/journal", title: "Journal des recherches", hint: "" },
];
const current = computed(() => TABS.find((t) => t.key === tab.value) ?? TABS[0]!);

// Le mois choisi suit d'un onglet à l'autre (Suivi et Preuves ORP).
function link(path: string) {
  return typeof route.query.mois === "string" ? { path, query: { mois: route.query.mois } } : { path };
}

function badge(key: JobsTab): number {
  return key === "journal" ? 0 : counts.value[key];
}

async function refresh(): Promise<void> {
  const [today, orp] = await Promise.all([api.GET("/api/today"), api.GET("/api/orp")]);
  counts.value = {
    offres: today.data?.to_review ?? 0,
    suivi: today.data?.to_follow_up ?? 0,
    preuves: orp.data?.incomplete ?? 0,
  };
}

// Pastilles relues à chaque changement d'onglet (une offre traitée, une candidature ajoutée…).
watch(
  () => route.name,
  () => void refresh(),
);
onMounted(() => void refresh());
</script>

<template>
  <div class="jobs-head">
    <span class="eyebrow">Candidatures</span>
    <h1>{{ current.title }}</h1>
    <nav
      class="prep-tabs jobs-tabs"
      aria-label="Candidatures"
    >
      <RouterLink
        v-for="item in TABS"
        :key="item.key"
        :to="link(item.path)"
        :class="{ active: tab === item.key }"
        :aria-current="tab === item.key ? 'page' : undefined"
        :data-test="`jobs-tab-${item.key}`"
      >
        {{ item.label }}
        <span
          v-if="badge(item.key)"
          class="tab-count"
          :title="`${badge(item.key)} ${item.hint}`"
        >{{ badge(item.key) }}</span>
      </RouterLink>
    </nav>
  </div>
  <RouterView />
</template>
