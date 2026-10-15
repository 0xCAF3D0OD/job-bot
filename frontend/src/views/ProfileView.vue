<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import CriteriaForm from "../components/CriteriaForm.vue";
import IdentityForm from "../components/IdentityForm.vue";
import PageHero from "../components/PageHero.vue";
import ProfileParcours from "../components/ProfileParcours.vue";

// Tout ce qui te concerne au même endroit (docs/10 §2 a) ; l'onglet est dans l'URL.
const TABS = [
  // Sur téléphone, un nom court qui tient sur une ligne (docs/36 §5).
  { key: "recherche", label: "Ce que je cherche", short: "Recherche" },
  { key: "parcours", label: "Mon parcours", short: "Parcours" },
  { key: "coordonnees", label: "Mes coordonnées", short: "Coordonnées" },
] as const;
type Tab = (typeof TABS)[number]["key"];

const route = useRoute();
const tab = computed<Tab>(() => {
  const wanted = route.query.onglet;
  return TABS.find((t) => t.key === wanted)?.key ?? "recherche";
});
const SUBTITLES: Record<Tab, string> = {
  recherche:
    "Tes prérequis : une offre qui ne les respecte pas passe dans « Écartées ».",
  parcours: "Ton CV et tes blocs de profil, la base de l'IA pour noter et rédiger.",
  coordonnees: "Pour l'en-tête de tes lettres, de ton CV et des preuves ORP (jamais envoyées à l'IA).",
};
</script>

<template>
  <PageHero
    eyebrow="Profil"
    title="Toi et ta recherche"
    :subtitle="SUBTITLES[tab]"
  />
  <section class="band">
    <div class="container">
      <nav
        class="prep-tabs"
        aria-label="Profil"
      >
        <RouterLink
          v-for="entry in TABS"
          :key="entry.key"
          :to="{ query: entry.key === 'recherche' ? {} : { onglet: entry.key } }"
          :class="{ active: tab === entry.key }"
          :data-test="`tab-${entry.key}`"
        >
          <span class="label-long">{{ entry.label }}</span>
          <span class="label-short">{{ entry.short }}</span>
        </RouterLink>
      </nav>
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
