<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import AppIcon from "../components/AppIcon.vue";
import PageHero from "../components/PageHero.vue";
import type { IconName } from "../icons";
import type { BilanTab } from "../router";

// Le Bilan (docs/42, docs/126 §1), une entrée du menu : « Qu'est-ce qui marche, et quoi
// améliorer ? ». Les résultats d'abord, puis Formations (les manques y mènent), deux onglets
// sous un même titre, comme Candidatures. Remplace Progresser (docs/90). Les Actualités en
// sont retirées (1.6.25).
const route = useRoute();
const tab = computed<BilanTab>(() => (route.meta.tab as BilanTab | undefined) ?? "resultats");

const TABS: { key: BilanTab; label: string; icon: IconName; path: string }[] = [
  { key: "resultats", label: "Résultats", icon: "stats", path: "/bilan" },
  { key: "formations", label: "Formations", icon: "book", path: "/bilan/formations" },
];

// Le mois choisi dans les Résultats suit le lien de l'onglet.
function link(path: string) {
  return path === "/bilan" && typeof route.query.mois === "string" ? { path, query: { mois: route.query.mois } } : { path };
}
</script>

<template>
  <PageHero title="Bilan">
    <!-- Les onglets de Candidatures (sur téléphone : l'icône au-dessus du nom, la pastille sur
         l'icône), par cohérence entre les deux rubriques. -->
    <nav
      class="prep-tabs jobs-tabs"
      aria-label="Bilan"
    >
      <RouterLink
        v-for="item in TABS"
        :key="item.key"
        :to="link(item.path)"
        :class="{ active: tab === item.key }"
        :aria-current="tab === item.key ? 'page' : undefined"
        :data-test="`bilan-tab-${item.key}`"
      >
        <span class="with-icon"><AppIcon :name="item.icon" />{{ item.label }}</span>
      </RouterLink>
    </nav>
  </PageHero>
  <!-- Résultats sur la bande grise, comme Candidatures (1.6.62, planche « 3 et 4. Bilan »). -->
  <section
    v-if="tab === 'resultats'"
    class="band jobs-band"
  >
    <RouterView />
  </section>
  <RouterView v-else />
</template>
