<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import AppIcon from "../components/AppIcon.vue";
import PageHero from "../components/PageHero.vue";
import { useNewsCount } from "../composables/useNewsCount";
import type { IconName } from "../icons";
import type { ProgressTab } from "../router";

// Progresser (docs/90) : Actualités et Formations, deux onglets sous un même titre, comme
// Candidatures. Leurs rubriques (Emploi, Économie, Vidéos ; Catalogue, Suivies) sont un
// sélecteur dans chaque onglet : pas d'onglets dans des onglets.
const route = useRoute();
const tab = computed<ProgressTab>(() => (route.meta.tab as ProgressTab | undefined) ?? "actualites");
const { count: newsCount } = useNewsCount();

const TABS: { key: ProgressTab; label: string; icon: IconName; path: string }[] = [
  { key: "actualites", label: "Actualités", icon: "news", path: "/progresser/actualites" },
  { key: "formations", label: "Formations", icon: "book", path: "/progresser/formations" },
];
</script>

<template>
  <PageHero title="Progresser">
    <nav
      class="prep-tabs"
      aria-label="Progresser"
    >
      <RouterLink
        v-for="item in TABS"
        :key="item.key"
        :to="item.path"
        :class="{ active: tab === item.key }"
        :aria-current="tab === item.key ? 'page' : undefined"
        :data-test="`progress-tab-${item.key}`"
      >
        <span class="with-icon"><AppIcon :name="item.icon" />{{ item.label }}</span>{{ " " }}<span
          v-if="item.key === 'actualites' && newsCount"
          class="tab-count"
          :title="`${newsCount} nouveaux`"
        >{{ newsCount }}</span>
      </RouterLink>
    </nav>
  </PageHero>
  <RouterView />
</template>
