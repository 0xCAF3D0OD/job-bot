<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import type { ChunkKind } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import CriteriaForm from "../components/CriteriaForm.vue";
import IdentityForm from "../components/IdentityForm.vue";
import PageHero from "../components/PageHero.vue";
import ProfileDesktop from "../components/ProfileDesktop.vue";
import ProfileGauge from "../components/ProfileGauge.vue";
import ProfileParcours from "../components/ProfileParcours.vue";
import SegmentedControl from "../components/SegmentedControl.vue";
import { useNarrow } from "../composables/usePhone";

// Tout ce qui te concerne au même endroit (docs/10 §2 a) ; l'onglet est dans l'URL.
// Téléphone : trois onglets (Critères, Parcours, Coordonnées). Ordinateur (PR 9b, décision de Kevin du 10 novembre) :
// une page unique (ProfileDesktop) ; chaque ligne de « Mon parcours » ouvre sa page, ?onglet=… avec un retour.
const TABS = [
  { key: "recherche", label: "Critères" },
  { key: "parcours", label: "Parcours" },
  { key: "coordonnees", label: "Coordonnées" },
] as const;
type Tab = (typeof TABS)[number]["key"];

// Les pages de l'ordinateur. `parcours` (documents et tous les blocs) reste pour les anciens liens et la jauge.
type Page = { title: string; part?: "all" | "documents" | "blocks"; kind?: ChunkKind };
const PAGES: Record<string, Page> = {
  formations: { title: "Formations", part: "blocks", kind: "formation" },
  experiences: { title: "Expériences", part: "blocks", kind: "experience" },
  competences: { title: "Compétences", part: "blocks", kind: "competence" },
  documents: { title: "Documents et certificats", part: "documents" },
  parcours: { title: "Mon parcours", part: "all" },
  coordonnees: { title: "Coordonnées" },
};

const route = useRoute();
const { phone: narrow } = useNarrow();
const segments = TABS.map((entry) => ({
  value: entry.key,
  label: entry.label,
  to: { query: entry.key === "recherche" ? {} : { onglet: entry.key } },
  test: `tab-${entry.key}`,
}));
const wanted = computed(() => (typeof route.query.onglet === "string" ? route.query.onglet : ""));
// Sur téléphone, une page de l'ordinateur ouvre l'onglet qui la contient.
const tab = computed<Tab>(() => {
  if (wanted.value === "coordonnees") return "coordonnees";
  return wanted.value && wanted.value in PAGES ? "parcours" : "recherche";
});
const page = computed<Page | null>(() => PAGES[wanted.value] ?? null);
const openChunk = computed(() => (typeof route.query.bloc === "string" ? Number(route.query.bloc) || null : null));
const create = computed(() => (route.query.nouveau ? (page.value?.kind ?? null) : null));
</script>

<template>
  <!-- Lot 18 (§10.5) : sur ordinateur, toute la page sur le fond des blocs. -->
  <div class="page-blocks-wide">
    <template v-if="!narrow">
      <ProfileDesktop v-if="!page" />
      <template v-else>
        <header
          class="jobs-head profile-subhead"
          data-test="profile-subhead"
        >
          <RouterLink
            :to="{ query: {} }"
            class="profile-back"
            data-test="profile-back"
          >
            <AppIcon name="arrow-left" />Profil
          </RouterLink>
          <h1>{{ page.title }}</h1>
        </header>
        <section class="band profile-page">
          <div class="container">
            <!-- La jauge, comme sur chaque onglet d'avant ; elle annonce aussi que la page est prête. -->
            <ProfileGauge />
            <div
              v-if="wanted === 'coordonnees'"
              class="narrow-block"
            >
              <IdentityForm />
            </div>
            <ProfileParcours
              v-else
              :key="wanted"
              :part="page.part"
              :start-kind="page.kind ?? null"
              :create="create"
              :open-chunk="openChunk"
            />
          </div>
        </section>
      </template>
    </template>
    <template v-else>
      <PageHero title="Profil">
        <!-- Sous 600 px (planche « Structure téléphone ») : un contrôle segmenté sur toute la largeur. -->
        <SegmentedControl
          :model-value="tab"
          :options="segments"
          label="Profil"
          full
        />
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
          <ProfileParcours
            v-else-if="tab === 'parcours'"
            :part="page?.part ?? 'all'"
            :start-kind="page?.kind ?? null"
            :create="create"
            :open-chunk="openChunk"
          />
          <div
            v-else
            class="narrow-block"
          >
            <IdentityForm />
          </div>
        </div>
      </section>
    </template>
  </div>
</template>
