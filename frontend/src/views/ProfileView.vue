<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import AppIcon from "../components/AppIcon.vue";
import AvatarPicker from "../components/AvatarPicker.vue";
import ProfileImage from "../components/ProfileImage.vue";
import { useProfileImage } from "../composables/useProfileImage";
import CriteriaForm from "../components/CriteriaForm.vue";
import IdentityForm from "../components/IdentityForm.vue";
import PageHero from "../components/PageHero.vue";
import ProfileGauge from "../components/ProfileGauge.vue";
import ProfileParcours from "../components/ProfileParcours.vue";
import SegmentedControl from "../components/SegmentedControl.vue";
import { useNarrow } from "../composables/usePhone";

// Tout ce qui te concerne au même endroit (docs/10 §2 a) ; l'onglet est dans l'URL.
const TABS = [
  { key: "recherche", label: "Critères", icon: "filter" },
  { key: "parcours", label: "Parcours", icon: "folder" },
  { key: "coordonnees", label: "Coordonnées", icon: "mail" },
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
// Ordinateur (maquette du 8 novembre, ProfilOrdinateur) : en tête, l'image de 72 px avec sa pastille crayon, le nom
// en titre et la ville ; « Changer d'image » ouvre la grille (AvatarPicker), « Modifier » les coordonnées.
const router = useRouter();
const image = useProfileImage();
const picking = ref(false);
onMounted(() => void image.load());
// Un sous-titre pour les trois onglets (docs/43 n° 25) : ce que chaque onglet contient est
// dit dans l'onglet lui-même.
</script>

<template>
  <!-- Lot 18 (§10.5) : sur ordinateur, toute la page sur le fond des blocs. -->
  <div class="page-blocks-wide">
    <header
      v-if="!narrow"
      class="jobs-head profile-head"
      data-test="profile-head"
    >
      <div class="profile-head-main">
        <button
          type="button"
          class="profile-head-image"
          aria-label="Changer d'image"
          data-test="profile-image-edit"
          @click="picking = true"
        >
          <ProfileImage
            :choice="image.choice.value"
            :initials="image.initials.value"
            :size="72"
          />
          <span
            class="profile-head-pencil"
            aria-hidden="true"
          ><AppIcon name="pencil" /></span>
        </button>
        <div class="profile-head-text">
          <h1>{{ image.name.value || "Profil" }}</h1>
          <p v-if="image.city.value">
            {{ image.city.value }}
          </p>
        </div>
        <div class="profile-head-actions">
          <button
            type="button"
            class="secondary action-2"
            data-test="change-image"
            @click="picking = true"
          >
            Changer d'image
          </button>
          <button
            type="button"
            class="secondary action-2"
            data-test="profile-edit"
            @click="router.push({ query: { onglet: 'coordonnees' } })"
          >
            Modifier
          </button>
        </div>
      </div>
      <nav
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
            {{ entry.label }}
          </span>
        </RouterLink>
      </nav>
    </header>
    <AvatarPicker
      :open="picking"
      @close="picking = false"
    />
    <PageHero
      v-if="narrow"
      title="Profil"
    >
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
        <ProfileParcours v-else-if="tab === 'parcours'" />
        <div
          v-else
          class="narrow-block"
        >
          <IdentityForm />
        </div>
      </div>
    </section>
  </div>
</template>
