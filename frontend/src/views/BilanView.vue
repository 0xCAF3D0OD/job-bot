<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import PageHero from "../components/PageHero.vue";
import SegmentedControl, { type SegmentOption } from "../components/SegmentedControl.vue";
import { usePhone } from "../composables/usePhone";
import type { BilanTab } from "../router";

// Le Bilan (docs/42, docs/126 §1), une entrée du menu : « Qu'est-ce qui marche, et quoi
// améliorer ? ». Trois sous-onglets en contrôle segmenté, sur téléphone et sur ordinateur (docs/139
// étape 8, maquette Explorer ; B1 et B2, Kevin, 2026-11-04) : ORP, Résultats, Formations.
const route = useRoute();
const { phone } = usePhone();
const tab = computed<BilanTab>(() => (route.meta.tab as BilanTab | undefined) ?? "orp");

const segments = computed<SegmentOption[]>(() => [
  { value: "orp", label: "ORP", to: "/bilan", test: "bilan-tab-orp" },
  // Le mois choisi dans les Résultats suit le lien de l'onglet.
  {
    value: "resultats",
    label: "Résultats",
    to: typeof route.query.mois === "string" ? { path: "/bilan/resultats", query: { mois: route.query.mois } } : "/bilan/resultats",
    test: "bilan-tab-resultats",
  },
  { value: "formations", label: "Formations", to: "/bilan/formations", test: "bilan-tab-formations" },
]);
</script>

<template>
  <PageHero title="Bilan">
    <SegmentedControl
      :model-value="tab"
      :options="segments"
      label="Bilan"
      :full="phone"
      class="bilan-segments"
    />
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
