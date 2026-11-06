<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

// L'ancienne série d'illustrations (docs/67), à retirer écran par écran (docs/141 §4) : une image générée, préparée par
// scripts/illustrations.mjs. Chargée seulement quand elle s'affiche ; elle entre une fois, en
// fondu, quand elle est là.
// Décorative par défaut ; `label` la décrit aux lecteurs d'écran quand elle dit quelque chose.
// `sizes` : la largeur affichée, pour que le navigateur choisisse la bonne version.
const props = withDefaults(defineProps<{ name: SceneName; label?: string; sizes?: string }>(), {
  label: "",
  sizes: "(max-width: 820px) 240px, 440px",
});

// Servies telles quelles depuis public/illustrations/, comme le personnage : pas d'adresses hachées dans le
// code (48 adresses de moins dans le budget de poids, docs/117). Pas de série sombre : la claire, assombrie
// par la feuille de style.
const file = (width: number) => `/illustrations/${props.name}-${width}.webp`;
const srcset = computed(() => `${file(480)} 480w, ${file(800)} 800w`);
const loaded = ref(false);
const img = ref<HTMLImageElement | null>(null);
watch(
  () => props.name,
  () => (loaded.value = false),
);
// Une image déjà en cache peut être prête avant que la page écoute son chargement.
onMounted(() => {
  if (img.value?.complete && img.value.naturalWidth) loaded.value = true;
});
</script>

<script lang="ts">
export type SceneName =
  | "accueil-reseau"
  | "actualites-video"
  | "alertes-carte"
  | "aucune-offre"
  | "bilan"
  | "emails-tries"
  | "formations"
  | "lecture-calme"
  | "lieux-carte"
  | "messager"
  | "offres-profils"
  | "porte-ouverte"
  | "preuves-orp"
  | "suivi-envoi"
  | "tableau-de-bord"
  // Série du 27.10 (règle §4) : écrans vides, premiers pas, réussites, erreurs.
  | "reussite"
  | "connexion-perdue"
  | "assistant-vide"
  | "preparer-vide"
  | "ia-vide"
  | "rendez-vous-vide"
  | "formations-vide"
  | "trop-tot"
  | "introuvable";
</script>

<template>
  <span
    :class="['illu', 'no-dark', { loaded }]"
    :role="label ? 'img' : undefined"
    :aria-label="label || undefined"
    :aria-hidden="label ? undefined : 'true'"
    :data-illustration="name"
  >
    <img
      ref="img"
      :key="name"
      :src="file(480)"
      :srcset="srcset"
      :sizes="sizes"
      alt=""
      loading="lazy"
      decoding="async"
      @load="loaded = true"
    >
  </span>
</template>
