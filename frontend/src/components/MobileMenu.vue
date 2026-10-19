<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { useJobsMemory } from "../composables/useJobsMemory";
import type { NavEntry } from "../router";
import SidePanel from "./SidePanel.vue";

// Menu « burger » (docs/33 §2, docs/89) : sur un écran étroit, ☰ ferme la capsule à droite et
// ne montre que les cinq pages ; le compte, la collecte et Réglages sont sous ton initiale.
const props = defineProps<{ menu: NavEntry[]; newsCount: number }>();

const open = ref(false);
const route = useRoute();
const { last: lastJobsPage } = useJobsMemory();

const entries = computed(() =>
  props.menu.map((entry) => ({
    ...entry,
    to: entry.name === "jobs" ? lastJobsPage.value : entry.path,
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
              v-if="entry.name === 'news' && newsCount"
              class="nav-count"
            >{{ newsCount }}</span>
          </RouterLink>
        </li>
      </ul>
    </nav>
  </SidePanel>
</template>
