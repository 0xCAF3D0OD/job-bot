<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { useJobsMemory } from "../composables/useJobsMemory";
import { useProgressMemory } from "../composables/useProgressMemory";
import type { NavEntry } from "../router";
import SidePanel from "./SidePanel.vue";

// Menu « burger » (docs/33 §2, docs/89, docs/90) : sur un écran étroit, ☰ ferme la capsule à
// droite et ne montre que les trois pages ; le compte, la collecte et Réglages sont sous ton initiale.
const props = defineProps<{ menu: NavEntry[]; newsCount: number }>();

const open = ref(false);
const route = useRoute();
const { last: lastJobsPage } = useJobsMemory();
const { last: lastProgressPage } = useProgressMemory();

const entries = computed(() =>
  props.menu.map((entry) => ({
    ...entry,
    to: entry.name === "jobs" ? lastJobsPage.value : entry.name === "progress" ? lastProgressPage.value : entry.path,
    active: entry.name === "jobs" ? route.path.startsWith("/candidatures") : route.path.startsWith(entry.path),
  })),
);

// Une page choisie ferme le menu.
watch(
  () => route.fullPath,
  () => (open.value = false),
);
</script>

<template>
  <button
    type="button"
    class="icon-button burger"
    :aria-expanded="open"
    aria-label="Menu"
    data-test="burger"
    @click="open = true"
  >
    <span
      class="burger-lines"
      aria-hidden="true"
    />
  </button>
  <SidePanel
    :open="open"
    title="Menu"
    @close="open = false"
  >
    <nav aria-label="Navigation principale (menu)">
      <ul class="mobile-nav">
        <li
          v-for="entry in entries"
          :key="entry.name"
        >
          <RouterLink
            :to="entry.to"
            :class="{ active: entry.active }"
            :aria-current="entry.active ? 'page' : undefined"
            :data-test="`burger-${entry.name}`"
            @click="open = false"
          >
            {{ entry.label }}
            <span
              v-if="entry.name === 'progress' && newsCount"
              class="nav-dot"
              :aria-label="`${newsCount} nouveaux`"
            />
          </RouterLink>
        </li>
      </ul>
    </nav>
  </SidePanel>
</template>
