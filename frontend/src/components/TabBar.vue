<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { api } from "../api/client";
import { useJobsMemory } from "../composables/useJobsMemory";
import AppIcon from "./AppIcon.vue";

// La barre d'onglets du téléphone (docs/92) : les deux pages de travail, en bas de l'écran,
// avec une icône et un nom ; Candidatures porte le nombre d'offres à examiner. Les écrans de
// travail (Préparer, l'accueil) la cachent, comme ils prennent déjà tout l'écran (docs/75).
const HIDDEN = new Set(["preparation", "welcome"]);

const route = useRoute();
const { last: lastJobsPage } = useJobsMemory();
const toReview = ref(0);

const visible = computed(() => !HIDDEN.has(String(route.name)) && !route.meta.bare);
const tabs = computed(() => [
  { name: "today", label: "Aujourd'hui", icon: "calendar" as const, to: "/aujourdhui", active: route.path.startsWith("/aujourdhui") },
  { name: "jobs", label: "Candidatures", icon: "check-circle" as const, to: lastJobsPage.value, active: route.path.startsWith("/candidatures") },
]);

async function refresh(): Promise<void> {
  try {
    const { data } = await api.GET("/api/today");
    toReview.value = data?.to_review ?? 0;
  } catch {
    // Silencieux : le nombre n'est qu'un repère.
  }
}

watch(() => route.name, () => void refresh());
onMounted(() => void refresh());
</script>

<template>
  <nav
    v-if="visible"
    class="tab-bar"
    aria-label="Pages"
    data-test="tab-bar"
  >
    <RouterLink
      v-for="tab in tabs"
      :key="tab.name"
      :to="tab.to"
      :class="{ active: tab.active }"
      :aria-current="tab.active ? 'page' : undefined"
      :data-test="`tab-${tab.name}`"
    >
      <span class="tab-bar-icon">
        <AppIcon :name="tab.icon" />
        <span
          v-if="tab.name === 'jobs' && toReview"
          class="tab-bar-count"
        >{{ toReview > 9 ? "9+" : toReview }}</span>
      </span>
      {{ tab.label }}
    </RouterLink>
  </nav>
</template>
