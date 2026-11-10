<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import type { ChunkKind } from "../api/client";
import AppIcon from "../components/AppIcon.vue";
import IdentityForm from "../components/IdentityForm.vue";
import ProfileDesktop from "../components/ProfileDesktop.vue";
import ProfileGauge from "../components/ProfileGauge.vue";
import ProfileParcours from "../components/ProfileParcours.vue";
import { useNarrow } from "../composables/usePhone";

// Tout ce qui te concerne au même endroit (docs/10 §2 a). Prompt du 10 novembre (PR 20, décision B) : une page unique
// sur téléphone et sur ordinateur, sans onglets (ProfileDesktop ; maquettes ProfilTel et ProfilOrdinateur). Chaque ligne
// de « Mon parcours » ouvre sa page, ?onglet=… avec un retour. Les anciens liens (?onglet=recherche, parcours,
// coordonnees) mènent toujours au bon endroit : « recherche » est la page unique, où se trouve « Ce que je cherche ».
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
const wanted = computed(() => (typeof route.query.onglet === "string" ? route.query.onglet : ""));
const page = computed<Page | null>(() => PAGES[wanted.value] ?? null);
const openChunk = computed(() => (typeof route.query.bloc === "string" ? Number(route.query.bloc) || null : null));
const create = computed(() => (route.query.nouveau ? (page.value?.kind ?? null) : null));
</script>

<template>
  <!-- Lot 18 (§10.5) : sur ordinateur, toute la page sur le fond des blocs. -->
  <div class="page-blocks-wide">
    <template v-if="!page">
      <!-- Téléphone (ProfilTel) : « Mon profil » avec le retour au Compte, au-dessus de la même page. -->
      <header
        v-if="narrow"
        class="profile-topbar"
        data-test="profile-topbar"
      >
        <RouterLink
          to="/compte"
          class="profile-topbar-back"
          aria-label="Retour au compte"
          data-test="profile-topbar-back"
        >
          <AppIcon name="arrow-left" />
        </RouterLink>
        <h1>Mon profil</h1>
      </header>
      <ProfileDesktop />
    </template>
    <template v-else>
      <header
        :class="['jobs-head', 'profile-subhead', { 'profile-topbar': narrow }]"
        data-test="profile-subhead"
      >
        <RouterLink
          :to="{ query: {} }"
          :class="narrow ? 'profile-topbar-back' : 'profile-back'"
          :aria-label="narrow ? 'Retour au profil' : undefined"
          data-test="profile-back"
        >
          <AppIcon name="arrow-left" /><template v-if="!narrow">
            Profil
          </template>
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
  </div>
</template>
