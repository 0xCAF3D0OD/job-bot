<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import AppIcon from "../components/AppIcon.vue";
import CriteriaForm from "../components/CriteriaForm.vue";
import IdentityForm from "../components/IdentityForm.vue";
import PageHero from "../components/PageHero.vue";
import ProfileGauge from "../components/ProfileGauge.vue";
import ProfileParcours from "../components/ProfileParcours.vue";
import SegmentedControl from "../components/SegmentedControl.vue";
import { useNarrow } from "../composables/usePhone";

// Tout ce qui te concerne au même endroit (docs/10 §2 a) ; l'onglet est dans l'URL.
const TABS = [
  // Sur téléphone, un nom court qui tient sur une ligne (docs/36 §5).
  { key: "recherche", label: "Critères", icon: "filter", short: "Critères" },
  { key: "parcours", label: "Parcours", icon: "folder", short: "Parcours" },
  { key: "coordonnees", label: "Coordonnées", icon: "mail", short: "Coordonnées" },
] as const;
type Tab = (typeof TABS)[number]["key"];

const route = useRoute();
const { phone: narrow } = useNarrow();
const segments = TABS.map((entry) => ({
  value: entry.key,
  label: entry.label,
  to: { query: entry.key === "recherche" ? {} : { onglet: entry.key } },
  test: `tab-${entry.key}`,
}));
const tab = computed<Tab>(() => {
  const wanted = route.query.onglet;
  return TABS.find((t) => t.key === wanted)?.key ?? "recherche";
});
// Un sous-titre pour les trois onglets (docs/43 n° 25) : ce que chaque onglet contient est
// dit dans l'onglet lui-même.
</script>

<template>
  <PageHero
    title="Profil"
  >
    <!-- Sous 600 px (planche « Structure téléphone ») : un contrôle segmenté sur toute la largeur. -->
    <SegmentedControl
      v-if="narrow"
      :model-value="tab"
      :options="segments"
      label="Profil"
      full
    />
    <nav
      v-else
      class="prep-tabs"
      aria-label="Profil"
    >
      <RouterLink
        v-for="entry in TABS"
        :key="entry.key"
        :to="{ query: entry.key === 'recherche' ? {} : { onglet: entry.key } }"
        :class="{ active: tab === entry.key }"
        :aria-current="tab === entry.key ? 'page' : undefined"
        :data-test="`tab-${entry.key}`"
      >
        <span class="with-icon">
          <AppIcon :name="entry.icon" />
          <span class="label-long">{{ entry.label }}</span>
          <span class="label-short">{{ entry.short }}</span>
        </span>
      </RouterLink>
    </nav>
  </PageHero>
  <section class="band profile-page">
    <div class="container">
      <!-- La jauge du profil (docs/121 §C.4), seulement ici. -->
      <ProfileGauge />
      <div
        v-if="tab === 'recherche'"
        class="narrow-block"
      >
        <CriteriaForm />
      </div>
      <ProfileParcours v-else-if="tab === 'parcours'" />
      <div
        v-else
        class="narrow-block"
      >
        <IdentityForm />
      </div>
    </div>
  </section>
</template>
