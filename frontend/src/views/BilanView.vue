<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import PageHero from "../components/PageHero.vue";
import FolderTabs, { type FolderTab } from "../components/FolderTabs.vue";
import { usePhone } from "../composables/usePhone";
import type { BilanTab } from "../router";

// Le Bilan (docs/42, docs/126 §1), une entrée du menu : « Qu'est-ce qui marche, et quoi
// améliorer ? ». Trois sous-onglets, sur téléphone et sur ordinateur (docs/139 étape 8 ; B1 et B2, Kevin,
// 2026-11-04) : ORP, Résultats, Formations, en onglets « dossier » depuis le 17.11 (§47).
const route = useRoute();
const { phone } = usePhone();
const tab = computed<BilanTab>(() => (route.meta.tab as BilanTab | undefined) ?? "orp");

const segments = computed<FolderTab[]>(() => [
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
  <!-- Ordinateur (maquette du 8 novembre, BilanOrdinateur) : le titre à gauche et les onglets à droite, sur 880 px ;
       le contenu dessous, sur la même colonne. Plus de bande bleue (prompt du 9 novembre §1 : seule Aujourd’hui en a
       une ; maquettes BilanOrdinateur et BilanOrdinateurSombre). -->
  <template v-if="!phone">
    <section
      :class="['today-band bilan-band', 'flat']"
      data-test="bilan-band"
    >
      <div class="today-band-inner bilan-band-inner folder-head">
        <h1>Bilan</h1>
        <FolderTabs
          :selected="tab"
          :tabs="segments"
          label="Bilan"
          class="bilan-segments"
        />
      </div>
    </section>
    <!-- Maquette du 9 novembre (BilanOrdinateur) : le fond crème de la page, sans bande grise sous le titre. -->
    <div :class="['bilan-page', `bilan-page-${tab}`]">
      <RouterView />
    </div>
  </template>
  <PageHero
    v-else
    title="Bilan"
  >
    <FolderTabs
      :selected="tab"
      :tabs="segments"
      label="Bilan"
      class="bilan-segments"
    />
  </PageHero>
  <!-- Résultats sur la bande grise, comme Candidatures (1.6.62, planche « 3 et 4. Bilan »). -->
  <template v-if="phone">
    <section
      v-if="tab === 'resultats'"
      class="band jobs-band"
    >
      <RouterView />
    </section>
    <RouterView v-else />
  </template>
</template>

<style>
/* Onglets dossier sur ordinateur (§47, planche BilanOrdinateur) : le titre et les onglets posés sur la ligne. */
.bilan-band-inner.folder-head { align-items: flex-end; border-bottom: 1.5px solid var(--tab-line); }
.bilan-band-inner.folder-head h1 { margin-bottom: var(--space-2); }
.bilan-band-inner .bilan-segments { height: auto; border: 0; }
/* Sorti de style.css (allègement du 16.11, issue #797) : ces règles ne servent qu'ici, chargées avec ce composant. */
.bilan-page { --bilan-17: 17px; --bilan-gap-28: 28px; --bilan-pad: 18.5px; --bilan-pad-y: 14.5px; --bilan-card-h: 72px; --bilan-bar: 10px; --bilan-lh-21: 21px; }
</style>
